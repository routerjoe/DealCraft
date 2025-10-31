
# Fleeting Note Processing — Unified Pipeline (v6)
**Updated:** Thursday, October 09, 2025

## What v6 does (single pass)
- **Meetings → Meeting Notes** using your template and naming.
- **Contacts & Companies** (`N:/C:/T:/E:/M:/O:/A:`) → People hub & Company hub (unknown people to People/_Triage).
- **Tasks** (`- [ ] ...`) from *anywhere*, plus **Subtasks** (indented `- [ ]`).
- **Completed sweep**: moves `- [x]` from Backlog to **📌 Completed (General Backlog)**.
- **Follow-up** from meeting blocks → `follow_up_due`.
- **Auto-link attendees** to People hub.
- **Duplicate protection and state**: notes skipped if unchanged (override with `--force`).
- **Scopes**: `--today`, `--this-week`, `--this-month`, `--since-last-run`, or `--range A..B`.
- **Dry run**: preview changes without writing.
- **Audit log** to `_Review Queue.md`.

## Quick prompts (natural language)
- process fleeting notes **today**
- process fleeting notes **this week**
- process fleeting notes **this month**
- process fleeting notes **since last run**
- process fleeting notes **2025-10-01..2025-10-31**
- process fleeting notes **this month dry run**
- process fleeting notes **this week force**

## Paths (defaults; override with env)
- DAILY_NOTES_DIR — `.../00 Inbox/Daily Notes`
- MEETING_NOTES_DIR — `.../10 Literature/Meeting Notes`
- PEOPLE_DIR — `.../30 Hubs/People`
- HUB_DIR — `.../30 Hubs`
- TODO_LIST_PATH — `.../00 Inbox/Daily Notes/To Do List.md`
- STATE_PATH — `./.fleeting_state.json`
- REVIEW_QUEUE_PATH — `.../30 Hubs/_Review Queue.md`

## Run examples
```bash
npm i js-yaml

# examples
ts-node processFleeting_v6.ts --today
ts-node processFleeting_v6.ts --this-week
ts-node processFleeting_v6.ts --this-month
ts-node processFleeting_v6.ts --range 2025-09-15..2025-09-30
ts-node processFleeting_v6.ts --since-last-run
ts-node processFleeting_v6.ts --this-month --dry-run
```