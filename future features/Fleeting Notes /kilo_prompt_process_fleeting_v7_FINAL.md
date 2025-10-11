
# Kilo Code Prompt — Fleeting Notes Unified Processor (FINAL v7)

**Date:** Thursday, October 09, 2025 — **Timezone:** America/New_York

## Goal
Ship a single-pass processor that ingests *Fleeting Notes* and outputs:
- Normalized **Meeting Notes** from `## Meeting …` blocks
- **Contacts & Companies** from `N:/T:/E:/M:/O:/C:/A:` sections
- **Tasks & Subtasks** from `- [ ] …` anywhere (indented allowed) → To Do List Backlog
- Moves completed tasks `- [x] …` → **📌 Completed (General Backlog)**
- **Follow-up/Due** dates captured to meeting frontmatter
- **Auto-link attendees** to People hub if a matching file exists
- **Idempotent** re-runs with state-hash and **skip unchanged** (override with `--force`)
- **Batch scopes** + **dry-run**, and an **Audit** appended to `_Review Queue.md`

## Inputs (Vault layout; make overridable by ENV)
- `DAILY_NOTES_DIR`: `/Users/jonolan/Documents/Obsidian Documents/Red River Sales/00 Inbox/Daily Notes`
- `MEETING_NOTES_DIR`: `/Users/jonolan/Documents/Obsidian Documents/Red River Sales/10 Literature/Meeting Notes`
- `PEOPLE_DIR`: `/Users/jonolan/Documents/Obsidian Documents/Red River Sales/30 Hubs/People`
- `HUB_DIR`: `/Users/jonolan/Documents/Obsidian Documents/Red River Sales/30 Hubs` (company triage lives here)
- `TODO_LIST_PATH`: `/Users/jonolan/Documents/Obsidian Documents/Red River Sales/00 Inbox/Daily Notes/To Do List.md`
- `STATE_PATH`: `./.fleeting_state.json`
- `REVIEW_QUEUE_PATH`: `/Users/jonolan/Documents/Obsidian Documents/Red River Sales/30 Hubs/_Review Queue.md`

## CLI
- Scopes: `--today` | `--this-week` | `--this-month` | `--since-last-run` | `--range YYYY-MM-DD..YYYY-MM-DD`
- Flags: `--dry-run` (preview); `--force` (process even if unchanged)

## Parsing rules
- **Daily Note filename** carries date: `YYYY-MM-DD … .md`
- **Meeting block**: starts at `## Meeting …`, ends at next `##` or EOF
  - Recognize H3: `### Time`, `### Attendees`, `### Discussion`; preserve other H3 under **Notes**
  - Subject normalization: drop leading “meeting with/on/about/re:” tokens
  - Attendees may be names or emails; emails normalize to `First Last` (title case)
  - Detect `Follow-up:` or `Due:` → `follow_up_due` (YYYY-MM-DD)
- **Contacts/Companies**:
  - Keys: `N|Name`, `T|Title`, `E|Email`, `M|Mobile`, `O|Office[ Number]`, `C|Company`, `A|Address` (Address is multi-line until blank or another key)
  - Unknown-company people → `PEOPLE_DIR/_Triage/`
  - Company hubs created to `HUB_DIR/_Triage/<Company>.md` if not present
  - Canonicalize company names: strip Inc./LLC/Corp./Co./Ltd., trim quotes/spaces
- **Tasks**: capture `- [ ] …` anywhere; **subtasks** are recognized by indentation before the checkbox
- **Completed**: only move checked items that are under **## Backlog** in the To Do List

## Outputs
### Meeting file (create-or-append)
- File: `MEETING_NOTES_DIR/YYY-MM-DD Meeting <Subject>.md` (dedupe with `-1`, `-2`, …)
- Frontmatter (YAML):
  ```yaml
  type: meeting
  title: <Subject>
  date: <YYYY-MM-DD>
  time: "<as written>"
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
- Body includes Dataview header, **Agenda**, **Notes**, **Action Items**, **Cross-Links**, **Recent Attachments**
- Re-run on same name → append `## Notes (<ISO timestamp>)`

### People / Company
- People files: `PEOPLE_DIR/<Company>/<First Last> (Title).md`; unknown → `PEOPLE_DIR/_Triage/`
- Merge behavior on update: union emails/mobiles/offices; prefer new title/company if present
- Company hubs: create minimal frontmatter (`type: company`, `name`, `created`, `updated`)

### To Do List
- Unique, case-insensitive append to **## Backlog** as:  
  `- [ ] <task> — YYYY-MM-DD [[<Daily Note Title>]]`
- Move `- [x] …` under **Backlog** → **## 📌 Completed (General Backlog)** with `> Moved on <ISO timestamp>`

### Audit
- Append to `_Review Queue.md`:
  - When, Scope, Meetings created/updated
  - Contacts created/updated/triaged, Company hubs created
  - Tasks added, Tasks moved
  - Notes processed/skipped

## Attendee linking
- Build an index of People files (recursive, include `_Triage`)
- If normalized “First Last” matches base filename (without the “(Title)”), convert to `[[First Last (Title)]]`

## Acceptance criteria
- Deterministic output given same inputs and ENV
- Idempotent re-runs (state hash)
- JSON summary printed to STDOUT with all counted metrics
- No network calls; no secrets in code

## Deliverables
- `processFleeting_v7.ts` (single file)
- `README_FINAL.md` (how to run)
- (Optional) MCP: `process_fleeting_notes.mcp.json` + `process_fleeting_notes.js`
