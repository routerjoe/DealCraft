#!/usr/bin/env bash
set -euo pipefail

echo "▶ Linting with ruff..."
ruff check .

echo "▶ Running tests with pytest..."
pytest -v

echo "▶ Build check (lint + tests)..."
echo "✅ Build complete"
