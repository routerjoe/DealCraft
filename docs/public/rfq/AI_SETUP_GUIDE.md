# RFQ AI Analysis Setup Guide

## Overview

The RFQ analysis system now supports AI-powered strategic analysis alongside the existing rule-based scoring. This hybrid approach combines deterministic algorithmic rules with AI insights from Claude, ChatGPT, or Gemini.

## Features

### Hybrid Analysis Architecture
- **Rule-Based Scoring**: Fast, consistent algorithmic analysis (always runs)
- **AI Strategic Insights**: Deep contextual analysis of opportunities (optional)
- **Multi-Provider Support**: Choose between Claude (Anthropic), ChatGPT (OpenAI), or Gemini (Google)
- **Intelligent Routing**: Automatic provider selection based on agent routes configuration

### AI Analysis Provides
- Strategic fit assessment
- Competitive positioning insights
- Risk identification
- Opportunity recommendations
- Win probability estimation
- Confidence scoring
- Detailed rationale

## Setup Instructions

### 1. Configure API Keys

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```bash
# AI Configuration
AI_ENABLED=true
DEFAULT_AI_PROVIDER=claude  # Options: claude, openai, gemini

# Provider API Keys (add at least one)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# Model Selection (optional - defaults shown)
ANTHROPIC_MODEL=claude-sonnet-4-20250514
OPENAI_MODEL=gpt-4-turbo-preview
GOOGLE_MODEL=gemini-1.5-pro

# Cost Controls
AI_MAX_COST_PER_ANALYSIS=0.50  # Maximum cost per RFQ analysis
AI_ENABLE_COST_WARNINGS=true
```

### 2. Install Dependencies

The required AI SDK packages are already in `package.json`:
```bash
npm install
```

This installs:
- `@anthropic-ai/sdk` - Claude AI
- `openai` - ChatGPT
- `@google/generative-ai` - Gemini

### 3. Configure Agent Routes (Optional)

Edit `mcp/config/agent_routes.yaml` to customize which AI provider handles RFQ analysis:

```yaml
agent_routes:
  rfq_analysis:
    provider: claude  # or openai, gemini
    model: claude-sonnet-4-20250514
    temperature: 0.3
    max_tokens: 2000
```

## Usage

### Via TUI

1. Launch TUI: `bash tui/scripts/rrtui.sh`
2. Press `1` to open **RFQ Management**
3. Press `a` for **Analyze RFQs** (with AI support)
4. The system will use AI if configured

### Via MCP Tools

#### Analyze Single RFQ with AI

```json
{
  "tool": "rfq_analyze",
  "arguments": {
    "rfq_id": 98,
    "use_ai": true,
    "ai_provider": "claude"
  }
}
```

#### Analyze RFQ with Specific Provider

```json
{
  "tool": "rfq_analyze",
  "arguments": {
    "rfq_id": 97,
    "use_ai": true,
    "ai_provider": "openai"
  }
}
```

#### Analyze Without AI (Rule-Based Only)

```json
{
  "tool": "rfq_analyze",
  "arguments": {
    "rfq_id": 95,
    "use_ai": false
  }
}
```

### Response Format with AI

When `use_ai=true`, the response includes additional fields:

```json
{
  "rfq_id": 98,
  "score": 75,
  "recommendation": "GO",
  "rules_applied": [...],
  
  // AI-enhanced fields
  "ai_recommendation": "GO",
  "ai_confidence": 0.85,
  "strategic_fit": "HIGH",
  "ai_insights": [
    "Strong alignment with Federal Department A transportation vertical",
    "Excellent relationship with customer",
    "Competitive advantage in logistics solutions"
  ],
  "ai_risks": [
    "Tight deadline may require resource acceleration",
    "Potential competition from incumbent vendor"
  ],
  "ai_opportunities": [
    "Potential for follow-on contracts",
    "Strategic foothold in Federal Department A logistics"
  ],
  "ai_rationale": "Detailed explanation of recommendation..."
}
```

## Cost Considerations

### Estimated Costs per Analysis
- **Claude Sonnet 4**: ~$0.15-0.30 per RFQ
- **GPT-4 Turbo**: ~$0.10-0.25 per RFQ  
- **Gemini 1.5 Pro**: ~$0.05-0.15 per RFQ

### Cost Controls
- Set `AI_MAX_COST_PER_ANALYSIS` to limit spending per RFQ
- Enable `AI_ENABLE_COST_WARNINGS` for cost alerts
- Monitor usage in AI provider dashboards

### Best Practices
1. **Use AI Selectively**: Enable for high-value or complex opportunities
2. **Batch Processing**: Process multiple RFQs in single session to minimize overhead
3. **Provider Selection**: Choose based on analysis needs:
   - **Claude**: Best for strategic analysis and nuanced decision-making
   - **ChatGPT**: Good balance of cost and quality
   - **Gemini**: Most cost-effective for volume processing

## Workflow Examples

### Claude-Style Workflow in TUI

This matches your Claude workflow from the task description:

```
Press '1' → RFQ Management Screen

[g] Get Emails          → Retrieves bid board emails from Outlook
[p] Process RFQs        → Extracts RFQ data from emails
[a] Analyze RFQs        → Runs hybrid analysis (rules + AI)
[r] Run Full Workflow   → Executes Get → Process → Analyze sequentially
```

### Step-by-Step Example

1. **Get Emails**: Press `g`
   ```
   ✓ Retrieved 29 emails from Bid Board
   ✓ Categorized and prioritized SEWP communications
   ```

2. **Process RFQs**: Press `p`
   ```
   ✓ Batch processed emails
   ✓ Extracted RFQ data
   ✓ Found 14 pending RFQs
   ```

3. **Analyze RFQs**: Press `a`
   ```
   ✓ Running hybrid analysis on 14 pending RFQs
   ✓ Applied rule-based scoring
   ✓ Enhanced with AI strategic insights
   ✓ Generated GO/NO-GO recommendations
   ```

### Result Display

```
📊 Bid Board Processing Summary
Total Emails Retrieved: 29
Pending RFQs for Decision: 14

Recent RFQs Analyzed:
┌────┬────────────────────────────┬───────┬──────┬──────────┐
│ ID │ Subject                    │ Score │ Reco │ AI Fit   │
├────┼────────────────────────────┼───────┼──────┼──────────┤
│ 98 │ Federal Department A Transportation         │ 75    │ GO   │ HIGH     │
│ 97 │ Air Force Units            │ 68    │ GO   │ MEDIUM   │
│ 95 │ Air Force Education        │ 45    │ NO-GO│ LOW      │
└────┴────────────────────────────┴───────┴──────┴──────────┘
```

## Troubleshooting

### "tsc: command not found"
This is a PATH issue with the terminal. TypeScript runs via Node.js at runtime using ES modules - no compilation needed for execution. The MCP server works without building.

### AI Provider Errors

**Error**: "Invalid API key"
- Verify API key in `.env` file
- Ensure no extra spaces or quotes
- Check key is active in provider dashboard

**Error**: "Rate limit exceeded"
- Wait before retrying
- Consider switching providers temporarily
- Reduce batch sizes

**Error**: "Model not available"
- Check model name in `.env` matches provider's available models
- Update to latest model versions in configuration

### Missing AI Analysis in Results

If AI fields are missing from results:
1. Ensure `use_ai=true` in tool call
2. Verify API key is configured
3. Check logs for AI provider errors
4. System falls back to rule-based analysis on AI failure

## Advanced Configuration

### Custom Prompts

The AI analysis prompt can be customized by editing the `buildAnalysisPrompt()` function in [`src/tools/rfq/ai-analyzer.ts`](src/tools/rfq/ai-analyzer.ts:1).

### Provider Fallback Chain

Configure fallback providers in code:
```typescript
// In ai-analyzer.ts
const FALLBACK_CHAIN = ['claude', 'openai', 'gemini'];
```

### Temperature Tuning

Adjust AI creativity vs. consistency:
- **Lower (0.0-0.3)**: More consistent, deterministic
- **Medium (0.4-0.7)**: Balanced
- **Higher (0.8-1.0)**: More creative, varied

Edit in `agent_routes.yaml`:
```yaml
rfq_analysis:
  temperature: 0.3  # Adjust as needed
```

## Integration with Existing Workflow

The AI enhancement integrates seamlessly with existing tools:

1. **Email Watching**: `outlook_get_bid_board_emails` → unchanged
2. **Email Processing**: `rfq_process_email`, `rfq_batch_process` → unchanged  
3. **RFQ Listing**: `rfq_list_pending` → unchanged
4. **Analysis**: `rfq_analyze` → **now AI-enhanced** (optional)

## Next Steps

1. Configure at least one AI provider API key
2. Test with a single RFQ: `rfq_analyze` with `use_ai=true`
3. Review results and adjust configuration as needed
4. Consider cost implications for batch processing
5. Monitor performance and adjust provider selection

## Support

For issues or questions:
- Check logs for error details
- Verify API keys and configuration
- Test with individual RFQs before batch processing
- Review cost usage in provider dashboards