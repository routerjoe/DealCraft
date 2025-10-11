# Master To-Do — Fleeting Notes v7 (MCP)

Updated: 2025-10-11

Scope: Remaining implementation tasks to finish native Fleeting Notes integration in the Red River Sales MCP server. In-scope items exclude tasks already completed (tool skeleton, server routing, shared date and path utilities).

## Checklist

- [-] Refactor v6 to ESM v7 in processor: port logic (meetings, contacts/companies, tasks, audit, state), replace js-yaml with yaml, remove CLI/stdout, and export runFleetingProcessor(options).
- [ ] Fix ensureCompanyHub to return a created boolean only when a new company hub file is written; increment hubs_created based on that; update callers in the processor.
- [ ] Remove or fix parseTodosWithIndent rstrip bug; ensure indentation handling for subtasks or remove the function if unused.
- [ ] Make file writes atomic in processor utils: write to a temp file and rename; guard all writes behind dry_run.
- [ ] Map MCP args to processor options in handler; compute since-last-run from the state file; include scope label and dryRun in JSON summary.
- [ ] Update environment validation and docs: warn (do not fail) if Fleeting paths are missing; document DAILY_NOTES_DIR, MEETING_NOTES_DIR, PEOPLE_DIR, HUB_DIR, TODO_LIST_PATH, STATE_PATH, REVIEW_QUEUE_PATH in mcp_readme.md.
- [ ] Add dev harness at src/dev/test_fleeting.ts to run runFleetingProcessor with target_dir override and dry_run; add npm script test:fleeting.
- [ ] Add minimal sample markdown under samples/fleeting/ for local dry-run testing: meetings, duplicate subjects same day, contacts with/without company, multi-line addresses, nested subtasks, completed items under Backlog.
- [ ] Update docs: add Fleeting tool to Available Tools in mcp_readme.md; align future features/Fleeting Notes /README_FINAL.md and MCP_Cheatsheet.md to v7 MCP-native integration; note environment variables and usage examples.
- [ ] Migrate and sanitize folder names: move future features/Fleeting Notes / assets into docs/fleeting/ with clean paths; archive process_fleeting_notes.mcp.json as historical.
- [ ] Acceptance tests: verify multiple meetings in one note; duplicate meeting subjects same day; contacts (with/without company) including multi-line addresses; nested subtasks; re-run skips without --force; dry_run shows planned actions; audit appended; completed tasks moved; attendee wikilinks applied.

## File references

- Processor target: src/tools/fleeting/processor.ts
- Legacy reference: future features/Fleeting Notes /processFleeting_v6.ts
- Handler: src/tools/fleeting/index.ts
- Date utilities: src/tools/fleeting/date.ts
- Path utilities: src/tools/fleeting/paths.ts
- Server routing: src/index.ts
- Env validation: src/utils/env.ts
- Documentation: mcp_readme.md, future features/Fleeting Notes /README_FINAL.md, future features/Fleeting Notes /MCP_Cheatsheet.md

Notes: When porting, avoid stdout logging; use repository logger only if necessary, and ensure no blocking I/O patterns cause MCP stdio interference.