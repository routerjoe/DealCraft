import Anthropic from '@anthropic-ai/sdk';
import OpenAI from 'openai';
import { GoogleGenerativeAI } from '@google/generative-ai';
import { readFileSync } from 'fs';
import { join } from 'path';
import { parse } from 'yaml';
import { logger } from '../../utils/logger.js';

// Types
export type AIProvider = 'claude' | 'openai' | 'gemini';

export type AIAnalysisRequest = {
  rfq: any;
  attachments: any[];
  csv_data: any[];
  rule_based_score: {
    score: number;
    recommendation: string;
    factors: string[];
    tier: string;
  };
  rule_outcomes: any[];
};

export type AIAnalysisResponse = {
  provider: AIProvider;
  go_nogo_recommendation: 'GO' | 'NO-GO' | 'REVIEW';
  confidence_level: 'HIGH' | 'MEDIUM' | 'LOW';
  strategic_fit_score: number;
  key_insights: string[];
  risk_factors: string[];
  opportunities: string[];
  recommended_next_steps: string[];
  ai_reasoning: string;
  estimated_win_probability?: number;
};

// Configuration
const AI_CONFIG = {
  enabled: process.env.RFQ_AI_ENABLED?.toLowerCase() === 'true',
  defaultProvider: (process.env.RFQ_AI_DEFAULT_PROVIDER || 'claude') as AIProvider,
  temperature: parseFloat(process.env.RFQ_AI_TEMPERATURE || '0.3'),
  maxTokens: parseInt(process.env.RFQ_AI_MAX_TOKENS || '2000', 10),
};

// Client instances (lazy-initialized)
let anthropicClient: Anthropic | null = null;
let openaiClient: OpenAI | null = null;
let geminiClient: GoogleGenerativeAI | null = null;

function getAnthropicClient(): Anthropic {
  if (!anthropicClient) {
    const apiKey = process.env.ANTHROPIC_API_KEY;
    if (!apiKey) throw new Error('ANTHROPIC_API_KEY not configured');
    anthropicClient = new Anthropic({ apiKey });
  }
  return anthropicClient;
}

function getOpenAIClient(): OpenAI {
  if (!openaiClient) {
    const apiKey = process.env.OPENAI_API_KEY;
    if (!apiKey) throw new Error('OPENAI_API_KEY not configured');
    openaiClient = new OpenAI({ apiKey });
  }
  return openaiClient;
}

function getGeminiClient(): GoogleGenerativeAI {
  if (!geminiClient) {
    const apiKey = process.env.GOOGLE_API_KEY;
    if (!apiKey) throw new Error('GOOGLE_API_KEY not configured');
    geminiClient = new GoogleGenerativeAI(apiKey);
  }
  return geminiClient;
}

// Load agent routing configuration
function loadAgentRoutes(): any {
  try {
    const configPath = join(process.cwd(), 'mcp', 'config', 'agent_routes.yaml');
    const yamlContent = readFileSync(configPath, 'utf-8');
    return parse(yamlContent);
  } catch (error: any) {
    logger.warn('Could not load agent_routes.yaml, using defaults', { error: error.message });
    return {
      defaults: { fallback_model: 'claude' },
      routes: [],
    };
  }
}

// Select appropriate AI provider based on routing rules
export function selectProvider(taskType: string = 'go_nogo', complexity: string = 'medium'): AIProvider {
  const routes = loadAgentRoutes();
  
  // Check routing rules
  for (const route of routes.routes || []) {
    const typeMatch = route.match?.type?.includes(taskType);
    const complexityMatch = route.match?.complexity?.includes(complexity);
    
    if (typeMatch && complexityMatch) {
      const model = route.action?.model;
      if (model === 'claude') return 'claude';
      if (model === 'gpt-5' || model === 'openai') return 'openai';
      if (model === 'gemini') return 'gemini';
    }
  }
  
  // Fallback to default
  const fallback = routes.defaults?.fallback_model || 'claude';
  if (fallback === 'gpt-5') return 'openai';
  return fallback as AIProvider;
}

// Build analysis prompt
function buildAnalysisPrompt(request: AIAnalysisRequest): string {
  const { rfq, csv_data, rule_based_score, rule_outcomes } = request;
  
  return `You are an expert business development analyst for Red River Technology, specializing in government RFQ evaluation and GO/NO-GO decisions.

# RFQ DETAILS
Subject: ${rfq.subject || 'N/A'}
Sender: ${rfq.sender || 'N/A'}
Customer: ${rfq.customer || 'Not specified'}
Estimated Value: $${(rfq.estimated_value || 0).toLocaleString()}
Competition Level: ${rfq.competition_level || 'Unknown'}
Technology Vertical: ${rfq.tech_vertical || 'Not specified'}
OEM: ${rfq.oem || 'Not specified'}
Deadline: ${rfq.deadline || 'Not specified'}
Has Previous Contract: ${rfq.has_previous_contract ? 'Yes' : 'No'}

# RULE-BASED ANALYSIS (Already Completed)
Algorithmic Score: ${rule_based_score.score}/100
Tier: ${rule_based_score.tier}
Recommendation: ${rule_based_score.recommendation}
Scoring Factors: ${rule_based_score.factors.join('; ')}

# AUTOMATED RULES APPLIED
${rule_outcomes.map((r: any) => `- ${r.rule_id}: ${r.name} → ${r.action}${r.reason ? ` (${r.reason})` : ''}`).join('\n')}

${csv_data.length > 0 ? `# LINE ITEMS (from CSV)
${JSON.stringify(csv_data.slice(0, 20), null, 2)}` : '# No CSV line items available'}

# YOUR TASK
Provide a comprehensive AI-powered analysis that ENHANCES the rule-based scoring with strategic insights, market intelligence, and business judgment.

Analyze this RFQ and provide:
1. **GO/NO-GO Recommendation**: GO, NO-GO, or REVIEW (with confidence level)
2. **Strategic Fit Score**: 1-100 rating of strategic alignment with Red River's capabilities
3. **Key Insights**: 3-5 critical observations about this opportunity
4. **Risk Factors**: Specific risks or challenges to be aware of
5. **Opportunities**: Strategic advantages or upsides
6. **Recommended Next Steps**: Concrete actions to take
7. **AI Reasoning**: Your detailed analysis and rationale
8. **Estimated Win Probability**: 0-100% if applicable

Consider:
- Strategic customer relationships and long-term value
- Technology alignment with Red River's core competencies
- Competitive landscape and win probability
- Resource requirements vs. potential return
- Political/relationship factors not captured in rules
- Market trends and future opportunity pipeline
- Risk vs. reward balance

Respond in JSON format:
{
  "go_nogo_recommendation": "GO" | "NO-GO" | "REVIEW",
  "confidence_level": "HIGH" | "MEDIUM" | "LOW",
  "strategic_fit_score": <number 1-100>,
  "key_insights": [<string>, ...],
  "risk_factors": [<string>, ...],
  "opportunities": [<string>, ...],
  "recommended_next_steps": [<string>, ...],
  "ai_reasoning": "<detailed analysis>",
  "estimated_win_probability": <number 0-100 or null>
}`;
}

// Call Claude API
async function analyzeWithClaude(request: AIAnalysisRequest): Promise<AIAnalysisResponse> {
  const client = getAnthropicClient();
  const prompt = buildAnalysisPrompt(request);
  
  logger.info('Calling Claude API for RFQ analysis', { rfq_id: request.rfq.id });
  
  const response = await client.messages.create({
    model: 'claude-3-5-sonnet-20241022',
    max_tokens: AI_CONFIG.maxTokens,
    temperature: AI_CONFIG.temperature,
    messages: [
      {
        role: 'user',
        content: prompt,
      },
    ],
  });
  
  const textContent = response.content.find((c) => c.type === 'text');
  if (!textContent || textContent.type !== 'text') {
    throw new Error('No text response from Claude');
  }
  
  // Parse JSON response (Claude often wraps in ```json blocks)
  let jsonText = textContent.text.trim();
  if (jsonText.startsWith('```json')) {
    jsonText = jsonText.replace(/^```json\s*/, '').replace(/\s*```$/, '');
  } else if (jsonText.startsWith('```')) {
    jsonText = jsonText.replace(/^```\s*/, '').replace(/\s*```$/, '');
  }
  
  const parsed = JSON.parse(jsonText);
  
  return {
    provider: 'claude',
    ...parsed,
  };
}

// Call OpenAI API
async function analyzeWithOpenAI(request: AIAnalysisRequest): Promise<AIAnalysisResponse> {
  const client = getOpenAIClient();
  const prompt = buildAnalysisPrompt(request);
  
  logger.info('Calling OpenAI API for RFQ analysis', { rfq_id: request.rfq.id });
  
  const response = await client.chat.completions.create({
    model: 'gpt-4-turbo-preview',
    temperature: AI_CONFIG.temperature,
    max_tokens: AI_CONFIG.maxTokens,
    response_format: { type: 'json_object' },
    messages: [
      {
        role: 'system',
        content: 'You are an expert business development analyst. Always respond with valid JSON.',
      },
      {
        role: 'user',
        content: prompt,
      },
    ],
  });
  
  const content = response.choices[0]?.message?.content;
  if (!content) throw new Error('No response from OpenAI');
  
  const parsed = JSON.parse(content);
  
  return {
    provider: 'openai',
    ...parsed,
  };
}

// Call Gemini API
async function analyzeWithGemini(request: AIAnalysisRequest): Promise<AIAnalysisResponse> {
  const client = getGeminiClient();
  const model = client.getGenerativeModel({ model: 'gemini-1.5-pro' });
  
  const prompt = buildAnalysisPrompt(request);
  
  logger.info('Calling Gemini API for RFQ analysis', { rfq_id: request.rfq.id });
  
  const result = await model.generateContent({
    contents: [{ role: 'user', parts: [{ text: prompt }] }],
    generationConfig: {
      temperature: AI_CONFIG.temperature,
      maxOutputTokens: AI_CONFIG.maxTokens,
      responseMimeType: 'application/json',
    },
  });
  
  const text = result.response.text();
  if (!text) throw new Error('No response from Gemini');
  
  const parsed = JSON.parse(text);
  
  return {
    provider: 'gemini',
    ...parsed,
  };
}

// Main analysis function with provider selection
export async function analyzeRfqWithAI(
  request: AIAnalysisRequest,
  preferredProvider?: AIProvider
): Promise<AIAnalysisResponse> {
  if (!AI_CONFIG.enabled) {
    throw new Error('AI analysis is disabled. Set RFQ_AI_ENABLED=true in .env');
  }
  
  const provider = preferredProvider || selectProvider('go_nogo', 'medium');
  
  logger.info('Starting AI RFQ analysis', {
    rfq_id: request.rfq.id,
    provider,
    subject: request.rfq.subject,
  });
  
  try {
    let result: AIAnalysisResponse;
    
    switch (provider) {
      case 'claude':
        result = await analyzeWithClaude(request);
        break;
      case 'openai':
        result = await analyzeWithOpenAI(request);
        break;
      case 'gemini':
        result = await analyzeWithGemini(request);
        break;
      default:
        throw new Error(`Unknown AI provider: ${provider}`);
    }
    
    logger.info('AI analysis completed', {
      rfq_id: request.rfq.id,
      provider: result.provider,
      recommendation: result.go_nogo_recommendation,
      confidence: result.confidence_level,
      strategic_fit: result.strategic_fit_score,
    });
    
    return result;
  } catch (error: any) {
    logger.error('AI analysis failed', {
      rfq_id: request.rfq.id,
      provider,
      error: error.message,
    });
    throw error;
  }
}

// Hybrid analysis: combines rule-based + AI insights
export async function getHybridAnalysis(
  request: AIAnalysisRequest,
  preferredProvider?: AIProvider
): Promise<{
  rule_based: typeof request.rule_based_score;
  ai_analysis: AIAnalysisResponse;
  final_recommendation: string;
  confidence: string;
  combined_insights: string[];
}> {
  const aiAnalysis = await analyzeRfqWithAI(request, preferredProvider);
  
  // Combine rule-based and AI recommendations
  const ruleScore = request.rule_based_score.score;
  const aiScore = aiAnalysis.strategic_fit_score;
  const avgScore = Math.round((ruleScore + aiScore) / 2);
  
  // Determine final recommendation
  let finalRecommendation: string;
  let confidence: string;
  
  if (aiAnalysis.go_nogo_recommendation === request.rule_based_score.recommendation.split(' ')[0]) {
    // Agreement between AI and rules
    finalRecommendation = aiAnalysis.go_nogo_recommendation;
    confidence = aiAnalysis.confidence_level;
  } else {
    // Disagreement - use AI with note
    finalRecommendation = `${aiAnalysis.go_nogo_recommendation} (AI override of rule-based ${request.rule_based_score.recommendation})`;
    confidence = 'MEDIUM';
  }
  
  // Combine insights
  const combinedInsights = [
    `Rule-based score: ${ruleScore}/100 (${request.rule_based_score.tier})`,
    `AI strategic fit: ${aiScore}/100`,
    `Combined average: ${avgScore}/100`,
    ...aiAnalysis.key_insights,
  ];
  
  return {
    rule_based: request.rule_based_score,
    ai_analysis: aiAnalysis,
    final_recommendation: finalRecommendation,
    confidence,
    combined_insights: combinedInsights,
  };
}