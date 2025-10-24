
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
export RR_MCP_CLI="${RR_MCP_CLI:-$REPO_ROOT/mcp/cli.py}"

cd "$REPO_ROOT"
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  source .venv/bin/activate
  pip install --upgrade pip
  pip install -r "$REPO_ROOT/tui/requirements.txt"
else
  source .venv/bin/activate
fi

cd "$REPO_ROOT/tui" && python -m rrtui.app
