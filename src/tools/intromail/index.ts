import { Tool } from '@modelcontextprotocol/sdk/types.js';
import { readFileSync, writeFileSync, mkdirSync, existsSync, mkdtempSync } from 'node:fs';
import { join, basename } from 'node:path';
import { spawn } from 'node:child_process';
import { tmpdir } from 'node:os';

type AnalyzerArgs = {
  csv_path: string;
  output_dir?: string;
  config_path?: string;
};

type IntrosArgs = {
  csv_path: string;
  subject_template?: string;
  body_template_path?: string;
  attachment_path?: string;
  dry_run?: boolean;
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
  if (field.length || current.length) {
    current.push(field);
    rows.push(current);
  }
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

  for (const [k, v] of Object.entries(cfg.weights.title_seniority)) {
    if ((title || "").toLowerCase().includes(k.toLowerCase())) score += v;
  }
  for (const [k, v] of Object.entries(cfg.weights.org_keywords)) {
    if ((company || "").toLowerCase().includes(k.toLowerCase())) score += v;
  }
  let focusKey = "";
  for (const [k, v] of Object.entries(cfg.weights.notes_keywords)) {
    if ((notes || "").toLowerCase().includes(k.toLowerCase())) {
      score += v;
      if (!focusKey) focusKey = k;
    }
  }
  if (company) score += cfg.weights.bonus_rules.has_company;
  if (title) score += cfg.weights.bonus_rules.has_title;
  if (notes) score += cfg.weights.bonus_rules.has_notes;

  score = Math.max(0, Math.min(100, score));
  let priority = "Low";
  if (score >= cfg.priority_thresholds.high) priority = "High";
  else if (score >= cfg.priority_thresholds.medium) priority = "Medium";

  const focus = cfg.focus_map[focusKey] || (priority === "High" ? "Mission Fit" : priority);
  const tpl = priority === "High" ? cfg.subject_templates.high : (priority === "Medium" ? cfg.subject_templates.medium : cfg.subject_templates.low);
  const subject = (tpl || "Intro — Red River + {{company}}").replace("{{company}}", company || "your team").replace("{{focus}}", focus);

  return { score, priority, recommended_subject: subject };
}

async function handleAnalyzer(args: AnalyzerArgs) {
  const inputPath = args.csv_path;
  if (!inputPath || !existsSync(inputPath)) {
    throw new Error("CSV not found: " + inputPath);
  }
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
    const email = (row[emailIdx] || "").trim();
    if (!email) continue;
    const res = scoreRow(headers, row, cfg);
    outRows.push([...row, res.priority, String(res.score), res.recommended_subject]);
  }

  const base = basename(inputPath).replace(/\.csv$/i, "");
  const outputPath = join(resultsDir, `${base}_analyzed.csv`);
  writeFileSync(outputPath, toCSV(outRows), "utf8");

  const counts = { High: 0, Medium: 0, Low: 0 };
  for (let i = 1; i < outRows.length; i++) {
    const pr = outRows[i][headers.length];
    if (pr === "High") counts.High++;
    else if (pr === "Medium") counts.Medium++;
    else counts.Low++;
  }

  const summary = {
    input: inputPath,
    output: outputPath,
    totals: { rows: rows.length - 1, high: counts.High, medium: counts.Medium, low: counts.Low }
  };

  return {
    content: [
      { type: 'text', text: JSON.stringify({ ok: true, message: "Analysis complete", summary }, null, 2) }
    ]
  };
}

function buildHeader(args: IntrosArgs) {
  const subj = args.subject_template ?? (process.env.INTROMAIL_SUBJECT_DEFAULT || "Intro — Red River + {{company}}");
  const bodyPath = args.body_template_path || "";
  const attach = args.attachment_path ?? (process.env.INTROMAIL_ATTACHMENT_DEFAULT || "");
  const esc = (s: string) => (s ?? "").replace(/\\/g, "\\\\").replace(/"/g, '\\"');
  return `
set csvPath to "${esc(args.csv_path)}"
set subjectTemplate to "${esc(subj)}"
set bodyTemplatePath to "${esc(bodyPath)}"
set attachmentPath to "${esc(attach)}"
`;
}

async function runOsascript(source: string) {
  const dir = mkdtempSync(join(tmpdir(), "intromail-"));
  const file = join(dir, "run.applescript");
  writeFileSync(file, source, "utf8");
  return await new Promise<{ code: number; stdout: string; stderr: string }>((resolve) => {
    const child = spawn("osascript", [file], { stdio: ["ignore", "pipe", "pipe"] });
    let out = "", err = "";
    child.stdout.on("data", d => out += d.toString());
    child.stderr.on("data", d => err += d.toString());
    child.on("close", code => resolve({ code: code ?? 0, stdout: out, stderr: err }));
  });
}

async function handleIntros(args: IntrosArgs) {
  if (!args.csv_path) throw new Error("csv_path is required");
  if (!existsSync(args.csv_path)) throw new Error("CSV not found: " + args.csv_path);
  if (args.dry_run) {
    return { content: [ { type: 'text', text: JSON.stringify({ ok: true, message: "Dry run OK", args }, null, 2) } ] };
  }
  const scriptPath = join(process.cwd(), "scripts", "intromail.applescript");
  const baseScript = readFileSync(scriptPath, "utf8");
  const header = buildHeader(args);
  const script = header + "\n" + baseScript;
  const { code, stdout, stderr } = await runOsascript(script);
  if (code !== 0) throw new Error(`osascript failed (${code}): ${stderr || stdout}`);
  const msg = (stdout || "").toString().trim() || "Completed.";
  return { content: [ { type: 'text', text: JSON.stringify({ ok: true, message: msg }, null, 2) } ] };
}

export const intromailTools: Tool[] = [
  {
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
    }
  },
  {
    name: "intromail:intros",
    description: "Generate Outlook Draft intro emails from CSV (macOS). Drafts only; never auto-sends.",
    inputSchema: {
      type: "object",
      required: ["csv_path"],
      properties: {
        csv_path: { type: "string" },
        subject_template: { type: "string" },
        body_template_path: { type: "string" },
        attachment_path: { type: "string" },
        dry_run: { type: "boolean" }
      }
    }
  }
];

export async function handleIntromailTool(name: string, args: any) {
  switch (name) {
    case "intromail:analyzer":
      return await handleAnalyzer(args as AnalyzerArgs);
    case "intromail:intros":
      return await handleIntros(args as IntrosArgs);
    default:
      throw new Error(`Unknown IntroMail tool: ${name}`);
  }
}