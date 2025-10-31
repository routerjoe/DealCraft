# MCP Mapping Cheatsheet — Fleeting v7

Natural language → tool args

- process fleeting notes today → { "scope": "today" }
- process fleeting notes this week → { "scope": "this-week" }
- process fleeting notes this month → { "scope": "this-month" }
- process fleeting notes since last run → { "scope": "since-last-run" }
- process fleeting notes 2025-10-01..2025-10-31 → { "scope": "range", "range": "2025-10-01..2025-10-31" }
- add dry run → "dry_run": true
- add force → "force": true

Tool name: fleeting_process_notes
Required when scope=range: range string "YYYY-MM-DD..YYYY-MM-DD"

Example: { "scope": "this-week", "dry_run": true }