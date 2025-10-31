# IntroMail Analyzer (MCP) — Pre-Send Lead Ranking

**Date:** Saturday, October 11, 2025 (America/New_York)  
**Purpose:** Analyze a campaign CSV and rank contacts (High/Medium/Low) with a numeric score (0–100), then emit an `*_analyzed.csv` with recommended subject lines. Intended to run **before** `intromail:intros`.

## What it does
- Parses your CSV (must include `email`; other columns become features).
- Scores each row using configurable weights:
  - **Title seniority** (CIO, Director, Colonel, GS-14/15...)
  - **Organization match** (Customer Alpha, Customer Beta, Space Systems…)
  - **Notes keywords** (“EBC”, “follow-up”, “requested briefing”, etc.)
- Outputs:  
  - `priority` (High/Medium/Low)  
  - `score` (0–100)  
  - `recommended_subject` (optional enhancer for `intromail:intros`)

## Files
- `src/tools/intromail_analyzer.ts` — MCP tool implementation (TypeScript, no external deps)
- `config/intromail_analyzer.config.json` — Weights & keyword rules
- `scripts/watch_inbox.ts` — Optional “dropbox intake” watcher
- `samples/sample_input.csv` and `samples/sample_output_analyzed.csv`
- `.env.example` — Base directories for inbox and results
- `prompts/kilo_intromail_analyzer_prompt.md` — Kilo Code prompt to add the tool

## Install
1) Copy this bundle into your Red River Sales MCP repo.
2) Add `.env` based on `.env.example` (paths only; no secrets).
3) Register the tool:
```ts
import introMailAnalyzer from "./src/tools/intromail_analyzer";
registerTool(introMailAnalyzer);
```

## Invoke (Analyzer first, IntroMail second)
**Analyzer:**
```json
{"tool":"intromail:analyzer","args":{"csv_path":"/Users/jonolan/RedRiver/campaigns/afcent_intros.csv"}}
```
Creates:
```
~/RedRiver/campaigns/analyzer_results/afcent_intros_analyzed.csv
```

**IntroMail:**
Use the analyzed file with `intromail:intros` to generate Outlook drafts.

## CSV Requirements
`email` header required. Other suggested headers: `first_name,last_name,company,title,notes`.

## Optional: Dropbox Intake Watcher
Run `scripts/watch_inbox.ts` to auto-run the analyzer whenever a new CSV appears in your inbox directory.

## Security
- No secrets are hard-coded.
- The analyzer does not read mailboxes or external systems.
- Logs exclude PII beyond file names and paths.
