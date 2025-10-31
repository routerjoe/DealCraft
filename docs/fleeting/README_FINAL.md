# Fleeting Notes — Native MCP Integration (v8)

This MCP tool processes your Daily Notes to:
- Normalize Meeting Notes from `## Meeting …` blocks, appending on re-runs
- Extract Contacts and Companies with **flexible parsing** (supports both strict `N:/T:/E:` format and freeform text)
- **Auto-strip markdown formatting** (bold, italics, links, code) from all contact fields
- Support new fields: **Organization/Customer** (O:), **Website** (W:), **LinkedIn** (L:), **Twitter/X** (X:)
- **Normalize phone numbers** to digits-only format for consistent storage
- Capture Tasks and Subtasks (`- [ ] …`) and move completed to 📌 Completed
- Detect Follow-up/Due and store to meeting frontmatter
- Append Audit to `_Review Queue.md`
- Skip unchanged notes unless `force`

## What's New in v8

### Enhanced Contact Parsing
1. **Flexible/Smart Parser**: Automatically detects contacts even without strict N:/T:/E: format
   - Finds email addresses as anchors
   - Detects phone numbers in various formats
   - Identifies names by capitalization
   - Recognizes common job titles
   - Extracts company/organization names
   - Falls back to strict parser if ambiguous

2. **Markdown Stripping**: All fields automatically cleaned
   - `**bold**` → `bold`
   - `*italic*` → `italic`
   - `[text](url)` → `text`
   - `` `code` `` → `code`

3. **New Fields**:
   - **O:** Organization/Customer (e.g., "AFCENT A63", "AETC")
   - **C:** Company (employer, e.g., "Cisco", "Palo Alto Networks")
   - **W:** Website URL
   - **L:** LinkedIn profile URL
   - **X:** Twitter/X handle
   - **phone_normalized:** Auto-generated digits-only phone (e.g., "5712653865")

4. **Phone Normalization**: All phone numbers stored in both original and normalized formats

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

## Todo List Structure

The processor expects the following sections in your `To Do List.md`:
- `## 📌 Running List (General Backlog)` - where new tasks are added
- `## 📌 Completed (General Backlog)` - where completed tasks are moved

Tasks are automatically:
- Added to Running List with date and source note links
- Moved from Running List to Completed when marked with `[x]`
- Deduplicated (case-insensitive)