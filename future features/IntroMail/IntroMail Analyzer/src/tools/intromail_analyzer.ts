import { readFileSync, writeFileSync, mkdirSync, existsSync, rmSync } from "node:fs";
import { dirname, join, basename } from "node:path";

type Args = {
  csv_path: string;
  output_dir?: string; // optional override for results
  config_path?: string; // optional custom config
};

type Config = {
  weights: {
    title_seniority: Record<string, number>;
    org_keywords: Record<string, number>;
    notes_keywords: Record<string, number>;
    bonus_rules: { has_company: number; has_title: number; has_notes: number };
  };
  priority_thresholds: { high: number; medium: number };
  subject_templates: { high: string; medium: string; low: string };
  focus_map: Record<string, string>;
};

// Simple CSV parser supporting quoted fields
function parseCSV(text: string): string[][] {
  const rows: string[][] = [];
  let current: string[] = [];
  let field = "";
  let inQuotes = false;

  for (let i = 0; i < text.length; i++) {
    const ch = text[i];

    if (ch === '"') {
      if (inQuotes && text[i + 1] === '"') { field += '"'; i++; }
      else inQuotes = !inQuotes;
    } else if (ch === ',' && !inQuotes) {
      current.push(field);
      field = "";
    } else if ((ch === '\n' || ch === '\r') && !inQuotes) {
      if (ch === '\r' && text[i + 1] === '\n') i++;
      current.push(field);
      rows.push(current);
      current = [];
      field = "";
    } else {
      field += ch;
    }
  }
  // last field/row
  if (field.length || current.length) {
    current.push(field);
    rows.push(current);
  }
  // remove empty trailing lines
  return rows.filter(r => r.join("").trim().length > 0);
}

function toCSV(rows: string[][]): string {
  const esc = (v: string) => {
    if (/[",\n\r]/.test(v)) return `"${v.replace(/"/g, '""')}"`;
    return v;
  };
  return rows.map(r => r.map(esc).join(",")).join("\n") + "\n";
}

function loadConfig(p?: string): Config {
  const defaultPath = process.env.INTROMAIL_ANALYZER_CONFIG || join(process.cwd(), "config", "intromail_analyzer.config.json");
  const pathToUse = p || defaultPath;
  const raw = readFileSync(pathToUse, "utf8");
  return JSON.parse(raw);
}

function scoreRow(headers: string[], row: string[], cfg: Config): { score: number; priority: string; recommended_subject: string } {
  const idx = (name: string) => headers.findIndex(h => h.toLowerCase() === name.toLowerCase());
  const get = (name: string) => {
    const i = idx(name);
    return i >= 0 && i < row.length ? (row[i] || "").trim() : "";
  };

  const title = get("title");
  const company = get("company");
  const notes = get("notes");
  const email = get("email");
  if (!email) throw new Error("Missing email in a row");

  let score = 0;

  // Title seniority scoring (contains match)
  for (const [k, v] of Object.entries(cfg.weights.title_seniority)) {
    if (title.toLowerCase().includes(k.toLowerCase())) score += v;
  }

  // Organization keywords (company field)
  for (const [k, v] of Object.entries(cfg.weights.org_keywords)) {
    if (company.toLowerCase().includes(k.toLowerCase())) score += v;
  }

  // Notes keywords
  let focusKey = "";
  for (const [k, v] of Object.entries(cfg.weights.notes_keywords)) {
    if (notes.toLowerCase().includes(k.toLowerCase())) {
      score += v;
      if (!focusKey) focusKey = k;
    }
  }

  // Bonus presence
  if (company) score += cfg.weights.bonus_rules.has_company;
  if (title) score += cfg.weights.bonus_rules.has_title;
  if (notes) score += cfg.weights.bonus_rules.has_notes;

  // Clamp to 100
  score = Math.max(0, Math.min(100, score));

  // Priority thresholds
  let priority = "Low";
  if (score >= cfg.priority_thresholds.high) priority = "High";
  else if (score >= cfg.priority_thresholds.medium) priority = "Medium";

  // Subject recommendation
  const focus = cfg.focus_map[focusKey] || (priority === "High" ? "Mission Fit" : priority);
  const tpl = priority === "High" ? cfg.subject_templates.high : (priority === "Medium" ? cfg.subject_templates.medium : cfg.subject_templates.low);
  const subject = tpl.replace("{{company}}", company || "your team").replace("{{focus}}", focus);

  return { score, priority, recommended_subject: subject };
}

export default {
  name: "intromail:analyzer",
  description: "Analyze a campaign CSV and rank contacts (High/Medium/Low) with a 0–100 score; outputs *_analyzed.csv",
  inputSchema: {
    type: "object",
    required: ["csv_path"],
    properties: {
      csv_path: { type: "string", description: "Absolute path to input CSV" },
      output_dir: { type: "string", description: "Optional output directory; defaults to ~/RedRiver/campaigns/analyzer_results" },
      config_path: { type: "string", description: "Optional custom config path" }
    }
  },
  handler: async (args: Args) => {
    const inputPath = args.csv_path;
    const cfg = loadConfig(args.config_path);

    const home = process.env.HOME || process.env.USERPROFILE || ".";
    const resultsDir = args.output_dir || join(home, "RedRiver", "campaigns", "analyzer_results");
    if (!existsSync(resultsDir)) mkdirSync(resultsDir, { recursive: true });

    const raw = readFileSync(inputPath, "utf8");
    const rows = parseCSV(raw);
    if (!rows.length) throw new Error("CSV is empty");
    const headers = rows[0];
    const emailIdx = headers.findIndex(h => h.toLowerCase() === "email");
    if (emailIdx < 0) throw new Error("CSV must include an 'email' header");

    const outHeaders = [...headers, "priority", "score", "recommended_subject"];
    const outRows: string[][] = [outHeaders];

    for (let i = 1; i < rows.length; i++) {
      const row = rows[i];
      if (!row || row.length === 0) continue;
      const email = row[emailIdx]?.trim();
      if (!email) continue;
      const res = scoreRow(headers, row, cfg);
      outRows.push([...row, res.priority, String(res.score), res.recommended_subject]);
    }

    const base = basename(inputPath).replace(/\.csv$/i, "");
    const outputPath = join(resultsDir, `${base}_analyzed.csv`);
    writeFileSync(outputPath, toCSV(outRows), "utf8");

    // Summary
    const counts = { High: 0, Medium: 0, Low: 0 };
    for (let i = 1; i < outRows.length; i++) counts[outRows[i][headers.length]]++;

    const summary = {
      input: inputPath,
      output: outputPath,
      totals: { rows: rows.length - 1, high: counts.High, medium: counts.Medium, low: counts.Low }
    };

    return { ok: true, message: "Analysis complete", summary };
  }
};
