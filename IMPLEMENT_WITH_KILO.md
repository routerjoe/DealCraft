# Implement with Kilo Code — Prompts & Steps
Date: Friday, October 17 2025 EDT

## 1) Drop this folder at your MCP root
`rr_mcp_tui_bundle/` contains everything. Move files into your repo root preserving subfolders.

## 2) Kilo Code — Prompt (copy/paste)
"""
You are Kilo Code. Integrate the provided TUI scaffold into the Red River MCP project.

Goals:
1) Add a curses-based TUI with a main dashboard showing green/red status for:
   - MCP (running/queue)
   - Watchers: Outlook RFQ, Fleeting Notes, Radar, Govly Sync
   - Providers: Claude, ChatGPT-5, Gemini
2) Wire the menu actions:
   - [1] Get Emails → call existing CLI or Python function (bidboard fetch)
   - [2] Process RFQs → batch normalize/index
   - [3] Analyze → run rules engine summary popup
   - [4] LOM → open rfq_lom_view.show()
   - [5] Artifacts → open rfq_artifacts_view.show()
   - [7] OEM Analytics → open tui_analytics.show_analytics()
3) Replace providers_status.get_status() with a real status loader:
   - Prefer CLI: `python mcp/cli.py status --json`
   - Else HTTP: GET /status returns JSON like providers_status.get_status()
4) Keep runtime SIMPLE (Claude-only). Do not enable routing yet.
5) Ensure zero external dependencies.

Deliverables:
- Running TUI with the screens above
- Status updates every 2 seconds
- Clean exit with 'q'
"""

## 3) After integration — test plan
1. `python3 main_menu.py` — opens dashboard.
2. Press `7` → Analytics (graphs).
3. Press `4` → LOM (toggle OEM with `F`).
4. Press `5` → Artifacts (tabs with ←/→).
5. Replace providers_status.get_status() to load real `/status` JSON.
