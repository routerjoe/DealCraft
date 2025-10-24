# Red River MCP — Textual TUI (M1)

## Overview
- Color dashboard with System, Watchers, Providers, RFQ Funnel 30d, Pipeline, and Actions
- Polls status every 2 seconds by default (editable in Settings)
- Funnel 30d polls every 10 seconds (configurable via `stats_refresh_sec`)
- Actions wired to MCP CLI; offline fixtures used if CLI is unavailable
- Non-secret Settings panel (providers, router, UI); secrets remain in environment variables

## Requirements
- **Python 3.10+ recommended**
- **Minimum terminal size: 38 rows × 80 columns**
- macOS/Linux (Windows may work with WSL)

### Resizing Your Terminal
- **macOS Terminal/iTerm2**: Drag window or use View > Window Size
- **Linux (GNOME/KDE)**: Drag window or set profile preferences
- **Windows Terminal**: Settings > Profiles > Advanced > Rows/Columns

Option A — Helper script (recommended)
- bash "tui/scripts/rrtui.sh"
- Provisions .venv, installs dependencies, sets RR_MCP_CLI automatically, then runs the TUI

Option B — Makefile
- cd "tui"
- make venv
- make run

Option C — Manual
- cd "tui"
- python3 -m venv .venv
- . .venv/bin/activate
- pip install --upgrade pip
- pip install -r requirements.txt
- python -m rrtui.app

Key bindings
- 1: RFQ Emails - Full RFQ workflow management
- 2: Govly - Govly integration (coming soon)
- 3: IntroMail - Campaign analysis and intro email generation
- 7: Analytics - View analytics and reports
- 9: Settings - Configure providers, router, and UI
- d: Dark toggle
- q: Quit

## Dashboard Panels

### Funnel 30d
- Displays RFQ funnel metrics over the last 30 days
- Shows 6 stages with horizontal bar charts: Received → Validated → Registered → Quoted → Submitted → Awarded
- Polls data every `stats_refresh_sec` (default: 10 seconds)
- Data source (CLI-first with fixture fallback):
  1. Primary: `python mcp/cli.py rfq stats --window 30d --json`
  2. Fallback: `tui/fixtures/rfq_stats_30d.json`
- Expected JSON schema:
```json
{
  "window": "30d",
  "funnel": {
    "received": 42,
    "validated": 39,
    "registered": 37,
    "quoted": 34,
    "submitted": 33,
    "awarded": 31
  },
  "by_day": [ ... ]  // optional
}
```

### Other Panels
- **System**: MCP status, uptime, queue size
- **Watchers**: Outlook RFQ, Fleeting Notes, Radar, Govly status
- **Providers**: Claude, GPT-5, Gemini with p95 latency
- **RFQ Pipeline**: Today's email/RFQ/GO/pending counts
- **RFQ Table**: List of active RFQs with scoring

## CLI Contracts
- Status: `python mcp/cli.py status --json`
- RFQ list: `python mcp/cli.py rfq list --status=all --json`
- RFQ stats: `python mcp/cli.py rfq stats --window 30d --json`
- Analytics: `python mcp/cli.py analytics oem --window 30d --json`
- CLI path resolution:
  - If RR_MCP_CLI is set, the TUI uses it
  - Otherwise, it searches upward from the TUI package for mcp/cli.py in the repo root
  - If the CLI fails or times out, the TUI falls back to fixtures:
    - `tui/fixtures/status.json`
    - `tui/fixtures/rfqs.json`
    - `tui/fixtures/rfq_stats_30d.json`
    - `tui/fixtures/analytics_oem_30d.json`

Settings (non-secrets)
- Press 9 to open Settings
- You can edit:
  - Providers: enabled, model, p95 warn/error ms
  - Router: order, sticky_provider, max_retries
  - UI: theme (light/dark), refresh seconds
- Save persists to: tui/config/settings.yaml
- Secrets are never written to disk
- Test Connection buttons check environment variables only:
  - ANTHROPIC_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY

## IntroMail Integration

The TUI includes a full-featured IntroMail campaign manager accessible via key `3`:

### Features
1. **CSV Analysis** - Score and prioritize contacts (High/Medium/Low)
   - Analyzes title, company, and notes fields
   - Assigns 0-100 scores based on configurable weights
   - Generates recommended subject lines per contact

2. **Draft Generation** - Create personalized Outlook intro emails
   - Uses analyzed CSV data for personalization
   - Supports custom subject templates with {{company}} placeholder
   - Creates drafts in Outlook (never auto-sends)
   - Optional attachment support (e.g., linecards)

### IntroMail Key Bindings
- `a`: Analyze CSV - Score and prioritize contacts
- `g`: Generate Drafts - Create Outlook intro emails
- `s`: Select CSV - Choose campaign file from table
- `r`: Refresh - Update campaign list
- `q`: Back to dashboard

### Workflow
1. Enter or select a CSV file path (sample provided by default)
2. Press `a` to analyze contacts and generate scores
3. Review the prioritized results
4. Press `g` to generate Outlook draft emails
5. Check your Outlook Drafts folder to review and send

### Configuration
- Analysis config: `config/intromail_analyzer.config.json`
- Email template: `templates/intro_email.txt`
- Results directory: `~/RedRiver/campaigns/analyzer_results/`

Actions mapping
- 1 → RFQ Management Screen (Get, Process, Analyze, Email Drafts)
- 2 → Govly (coming soon)
- 3 → IntroMail Campaign Manager (Analyze, Generate)

Theming
- Default theme: light
- Toggle dark with d or set in Settings
- Accent color: cyan
- Dots: ONLINE green, WARN yellow, ERROR red, OFF dim

Environment variables
- Optional runtime config:
  - export RR_MCP_CLI="$(pwd)/mcp/cli.py"
  - export ANTHROPIC_API_KEY=sk_...
  - export OPENAI_API_KEY=sk_...
  - export GOOGLE_API_KEY=sk_...
  - export MCP_ROUTER_ORDER="claude,gpt5,gemini"
  - export MCP_P95_WARN_MS=600
  - export MCP_P95_ERROR_MS=1500

Troubleshooting
- CLI not found:
  - Ensure RR_MCP_CLI points to your repo_root/mcp/cli.py
  - Or run from the repo root so the upward search finds it
- No status data:
  - Fixtures will render
  - Verify your CLI prints JSON and returns within 10s
- Table empty:
  - Verify rfq list returns items or fixtures are present

File map
- TUI entry: tui/rrtui/app.py
- Settings screen: tui/rrtui/settings_view.py
- CLI bridge: tui/rrtui/status_bridge.py and tui/rrtui/rfq_api.py
- Config loader: tui/config/config_loader.py
- Styles: tui/rrtui/styles.tcss
- Fixtures: tui/fixtures/status.json and tui/fixtures/rfqs.json
- Helper script: tui/scripts/rrtui.sh
- Makefile: tui/Makefile

Acceptance checks
- Dashboard renders with fixtures when CLI is absent
- Actions show success/error toasts without crashing
- Settings persist to config/settings.yaml and apply theme/refresh live