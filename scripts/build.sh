#!/bin/sh
# Run linter and tests

set -e

echo "Running build checks..."
echo ""
echo "Step 1: Linting..."
bash scripts/lint.sh
echo ""
echo "Step 2: Testing..."
bash scripts/test.sh
echo ""
echo "Build checks completed successfully!"