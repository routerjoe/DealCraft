
# Fleeting Notes — Unified Processor (FINAL v7)
**Updated:** Thursday, October 09, 2025

## What this does
One pass extracts **Meeting Notes**, **Contacts/Companies**, **Tasks/Subtasks**, **Follow-ups**, appends an **Audit**, and avoids double-processing with a state file.

## Files in this bundle
- `kilo_prompt_process_fleeting_v7_FINAL.md` — authoritative Kilo prompt
- `processFleeting_v6.ts` — reference implementation (you can keep name or let Kilo build `processFleeting_v7.ts`)
- `process_fleeting_notes.mcp.json` — MCP manifest (optional)
- `process_fleeting_notes.js` — MCP Node handler (optional)
- `README_Kilo_Integration.md` — step-by-step integration

## Quick start (no coding)
1) Hand this folder to **Kilo**.  
2) Ask Kilo to generate/validate **`processFleeting_v7.ts`** from the final prompt and wire flags.  
3) Set environment variables if your vault paths differ.

## Natural prompts
- process fleeting notes **today**
- process fleeting notes **this week**
- process fleeting notes **this month**
- process fleeting notes **since last run**
- process fleeting notes **2025-10-01..2025-10-31**
- add **dry run** or **force** to any of the above

## Example CLI
```bash
# deps
npm i js-yaml

# run scopes
ts-node processFleeting_v7.ts --today
ts-node processFleeting_v7.ts --this-week
ts-node processFleeting_v7.ts --this-month
ts-node processFleeting_v7.ts --since-last-run
ts-node processFleeting_v7.ts --range 2025-10-01..2025-10-31

# options
ts-node processFleeting_v7.ts --this-month --dry-run
ts-node processFleeting_v7.ts --this-week --force
```
