# Kilo Code Prompt — Add IntroMail Analyzer to MCP

Add a new tool named `intromail:analyzer` that:
1) Accepts args: `csv_path` (required), `output_dir` (optional), `config_path` (optional).
2) Parses the CSV (quoted fields supported), ensures an `email` header is present.
3) Loads config from `config/intromail_analyzer.config.json` (or `INTROMAIL_ANALYZER_CONFIG` env).
4) Scores each row using weights: title seniority, org keywords, notes keywords, plus presence bonuses.
5) Outputs an analyzed CSV to `~/RedRiver/campaigns/analyzer_results/<name>_analyzed.csv` unless `output_dir` is provided.
6) Adds columns: `priority` (High/Medium/Low), `score` (0–100), `recommended_subject`.
7) Returns a JSON summary with path to the output and totals.
8) Export default from `src/tools/intromail_analyzer.ts` and register with `registerTool`.
9) (Optional) Provide `scripts/watch_inbox.ts` to watch `~/RedRiver/campaigns/inbox` and invoke analyzer automatically for new CSVs.
