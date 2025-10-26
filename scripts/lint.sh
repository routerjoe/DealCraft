#!/bin/sh
# Run ruff linter on new sprint code only

set -e

echo "Running ruff linter..."
ruff check mcp/api/ mcp/core/ tests/ --exclude mcp/cli.py