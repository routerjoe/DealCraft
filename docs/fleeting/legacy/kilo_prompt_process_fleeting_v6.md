
# Kilo Code Prompt — Unified Fleeting Note Processing (v6)

**Updated:** Thursday, October 09, 2025 — Timezone: America/New_York

## Objective
Implement a single-pass pipeline that processes *Fleeting Notes* and extracts:
1) **Meetings** (`## Meeting ...`) → normalized Meeting Notes from a template
2) **Contacts & Companies** (`N:/T:/E:/M:/O:/C:/A:` patterns) → People hub + Company hub (unknown people to People/_Triage)
3) **Tasks** (`- [ ] ...` anywhere, including indented **subtasks**) → To Do List **## Backlog**
4) **Completed Tasks** (`- [x] ...`) → moved to **## 📌 Completed (General Backlog)**
5) **Follow-up** lines (`Follow-up:` or `Due:`) inside meetings → `follow_up_due` frontmatter
6) **Auto-link Attendees** to People files when present
7) **Stateful De-dupe**: per-note SHA-256; skip unchanged unless `--force`
8) **Batch Scopes**: `--today`, `--this-week` (Mon–Sun), `--this-month`, `--since-last-run`, `--range YYYY-MM-DD..YYYY-MM-DD`
9) **Dry-run**: preview without writing
10) **Audit** append to `_Review Queue.md` with counts and scope

## Folder Layout (defaults; make overridable via env)
- DAILY_NOTES_DIR: `/Users/jonolan/Documents/Obsidian Documents/Red River Sales/00 Inbox/Daily Notes`
- MEETING_NOTES_DIR: `/Users/jonolan/Documents/Obsidian Documents/Red River Sales/10 Literature/Meeting Notes`
- PEOPLE_DIR: `/Users/jonolan/Documents/Obsidian Documents/Red River Sales/30 Hubs/People`
- HUB_DIR: `/Users/jonolan/Documents/Obsidian Documents/Red River Sales/30 Hubs`
- TODO_LIST_PATH: `/Users/jonolan/Documents/Obsidian Documents/Red River Sales/00 Inbox/Daily Notes/To Do List.md`
- STATE_PATH: `./.fleeting_state.json`
- REVIEW_QUEUE_PATH: `/Users/jonolan/Documents/Obsidian Documents/Red River Sales/30 Hubs/_Review Queue.md`

## CLI flags to support
- `--today` | `--this-week` | `--this-month` | `--since-last-run` | `--range 2025-09-15..2025-09-30`
- `--dry-run` (no writes)
- `--force` (reprocess even if unchanged)

## Input conventions
- **Daily Note filenames contain date**: `YYYY-MM-DD ... .md`
- **Meeting** block starts at `## Meeting ...` and ends at next `##` or EOF
  - H3 sections (case-insensitive): `### Time`, `### Attendees`, `### Discussion`; any other `###` preserved under **Notes**
  - Attendees may be names or emails; emails normalize to `First Last`
  - Subject normalization: strip “meeting with/on/about/re:” lead-ins
- **Contacts/Companies** are captured by lines beginning with any of:
  - `N:` / `Name:`
  - `T:` / `Title:`
  - `E:` / `Email:`
  - `M:` / `Mobile:`
  - `O:` / `Office:` / `Office Number:`
  - `C:` / `Company:`
  - `A:` / `Address:` (multi-line until blank or next keyed line)
- **Tasks** anywhere: `- [ ] task text`
  - **Subtasks** recognized by indentation before `- [ ]`
- **Completed** anywhere under the To Do List’s **## Backlog**: `- [x] done text`

## Outputs
### Meeting files
- Path: `MEETING_NOTES_DIR`
- Name: `YYYY-MM-DD Meeting <Subject>.md` with duplicate protection (`-1`, `-2`, ...)
- Frontmatter:
  ```yaml
  type: meeting
  title: <Subject>
  date: <YYYY-MM-DD>
  time: "<stored as written>"
  attendees: [string|wikilink]
  organizations: []
  customer: ""
  related_opportunities: []
  related_rfqs: []
  oems: []
  distributors: []
  contract_office: ""
  status: open
  follow_up_due: "<YYYY-MM-DD or blank>"
  action_items: []
  links: []
  created: ""
  updated: ""
  tags: [meeting]
  ```
- Body: keep Dataview header, **Agenda**, **Notes** (Discussion + extra H3), **Action Items**, **Cross-Links**, **Recent Attachments**.
- Re-run on same file → append a timestamped `## Notes (ISO)` section.

### People / Company
- **People files**: `PEOPLE_DIR/<Company>/First Last (Title).md`; unknown company → `PEOPLE_DIR/_Triage/`
- Minimal frontmatter for people (merge emails/phones if updating)
- **Company hubs** (if not found): create `_Triage/<Company>.md` with `type: company`
- Canonicalize company names: strip suffixes (Inc., LLC, Corp., Co., Ltd.)

### To Do List
- Append unique tasks (case-insensitive) to **## Backlog** as:  
  `- [ ] <task> — YYYY-MM-DD [[<Daily Note Title>]]`
- Move completed `- [x]` from **## Backlog** to **## 📌 Completed (General Backlog)** with `> Moved on <ISO timestamp>`

### Audit
- Append to `_Review Queue.md`:
  - When, Scope, Meetings created/updated, Contacts created/updated/triaged, Company hubs created, Tasks added, Tasks moved, Notes processed/skipped

## Attendee Linking
- Build index from all People files (including subfolders and `_Triage`).
- Replace exact matches of normalized “First Last” with `[[First Last (Company Role)]]` if a file exists.

## Non-functional requirements
- Safe writes, idempotent behavior, and clear console JSON summary.
- No external network calls.
- No secrets included in code.

## Deliverables
- A single TypeScript file: `processFleeting_v6.ts`
- A brief Markdown guide
- Optional **MCP integration** (manifest + Node handler) to map natural prompts to CLI:
  - Manifest: `process_fleeting_notes.mcp.json`
  - Handler: `process_fleeting_notes.js` (executes ts-node with flags)

## Testing checklist
- [ ] Multiple meetings in one note
- [ ] Duplicate meeting subject same day
- [ ] Contacts with and without company
- [ ] Multi-line addresses
- [ ] Nested subtasks
- [ ] Re-run without changes (skips)
- [ ] Dry run shows planned actions
- [ ] Audit appended

