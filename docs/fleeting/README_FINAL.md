# Fleeting Notes — Native MCP Integration (v7)

This MCP tool processes your Daily Notes to:
- Normalize Meeting Notes from `## Meeting …` blocks, appending on re-runs
- Extract Contacts and Companies from `N:/T:/E:/M:/O:/C:/A:` sections
- Capture Tasks and Subtasks (`- [ ] …`) and move completed to 📌 Completed
- Detect Follow-up/Due and store to meeting frontmatter
- Append Audit to `_Review Queue.md`
- Skip unchanged notes unless `force`

## Tool

- Name: `fleeting_process_notes`
- Input:
  - `scope`: today | this-week | this-month | since-last-run | range
  - `range`: YYYY-MM-DD..YYYY-MM-DD (required when scope=range)
  - `dry_run`: boolean (no writes)
  - `force`: boolean (reprocess even if unchanged)
  - `target_dir`: optional override for Daily Notes directory (dev/testing)

## Environment variables (optional)

Defaults are derived from `OBSIDIAN_VAULT_PATH`. You may override any:

- `DAILY_NOTES_DIR`
- `MEETING_NOTES_DIR`
- `PEOPLE_DIR`
- `HUB_DIR`
- `TODO_LIST_PATH`
- `STATE_PATH`
- `REVIEW_QUEUE_PATH`

## Examples

- Process today:
  - `{ "scope": "today" }`
- Process this week (dry run):
  - `{ "scope": "this-week", "dry_run": true }`
- Process explicit range:
  - `{ "scope": "range", "range": "2025-10-01..2025-10-31" }`

## Dev harness

- Build: `npm run build`
- Run: `npm run test:fleeting`
  - Uses samples from `samples/fleeting/`
  - Harness source: `src/dev/test_fleeting.ts`

## Implementation notes

- Processor uses atomic writes and honors `dry_run`
- Idempotent via per-note content hash
- `since-last-run` clamps end date to today