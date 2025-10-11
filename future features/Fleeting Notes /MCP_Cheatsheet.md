
# MCP Mapping Cheatsheet
Natural language → handler params

- "process fleeting notes today" → { "scope": "today" }
- "process fleeting notes this week" → { "scope": "this-week" }
- "process fleeting notes this month" → { "scope": "this-month" }
- "process fleeting notes since last run" → { "scope": "since-last-run" }
- "process fleeting notes 2025-10-01..2025-10-31" → { "scope": "range", "range": "2025-10-01..2025-10-31" }
- Add "dry run" → `"dry_run": true`
- Add "force" → `"force": true`
