#!/bin/sh
# Start the FastAPI development server with auto-reload

set -e

echo "Starting Red River Sales MCP API in development mode..."
uvicorn mcp.api.main:app --host 0.0.0.0 --port 8000 --reload