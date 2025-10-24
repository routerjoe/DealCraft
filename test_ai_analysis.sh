#!/bin/bash
# Test script to verify AI-enhanced RFQ analysis

echo "Testing AI-Enhanced RFQ Analysis Integration"
echo "=============================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ ERROR: .env file not found"
    echo "   Please create .env from .env.example and add your API keys"
    exit 1
fi

# Check if API keys are configured
if ! grep -q "ANTHROPIC_API_KEY=sk-" .env && \
   ! grep -q "OPENAI_API_KEY=sk-" .env && \
   ! grep -q "GOOGLE_API_KEY=" .env | grep -v "^#" | grep -v "=$"; then
    echo "⚠️  WARNING: No API keys found in .env"
    echo "   Add at least one API key to enable AI analysis"
fi

# Check AI enabled setting
if grep -q "RFQ_AI_ENABLED=true" .env; then
    echo "✓ AI Analysis: ENABLED"
else
    echo "⚠️  AI Analysis: DISABLED (set RFQ_AI_ENABLED=true in .env)"
fi

# Show configured provider
provider=$(grep "RFQ_AI_DEFAULT_PROVIDER=" .env | cut -d'=' -f2)
echo "✓ AI Provider: ${provider:-claude}"
echo ""

# Test the CLI analyze command
echo "Running: python3 mcp/cli.py rfq analyze"
echo "----------------------------------------"
python3 mcp/cli.py rfq analyze

echo ""
echo "=============================================="
echo "If you see 'AI Recommendation' and 'AI Confidence' above,"
echo "then AI analysis is working!"
echo ""
echo "If you only see mock data, the Python→TypeScript bridge"
echo "needs MCP server to be running."