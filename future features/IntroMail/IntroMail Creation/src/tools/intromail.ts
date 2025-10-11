import { spawn } from "node:child_process";
import { mkdtempSync, writeFileSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

type Args = {
  csv_path: string;
  subject_template?: string;
  body_template_path?: string;
  attachment_path?: string;
  dry_run?: boolean;
};

const env = (k: string, d?: string) => process.env[k] ?? d;

function buildHeader(args: Args) {
  const subj = args.subject_template ?? env("INTROMAIL_SUBJECT_DEFAULT", "Intro — Red River + {{company}}");
  const bodyPath = args.body_template_path || "";
  const attach = args.attachment_path ?? env("INTROMAIL_ATTACHMENT_DEFAULT", "");

  const esc = (s: string) => (s ?? "").replace(/\\/g, "\\\\").replace(/"/g, '\\"');

  return `
set csvPath to "${esc(args.csv_path)}"
set subjectTemplate to "${esc(subj)}"
set bodyTemplatePath to "${esc(bodyPath)}"
set attachmentPath to "${esc(attach)}"
`;
}

async function runOsascript(source: string) {
  const tmp = mkdtempSync(join(tmpdir(), "intromail-"));
  const file = join(tmp, "run.applescript");
  writeFileSync(file, source, "utf8");
  return await new Promise<{ code: number; stdout: string; stderr: string }>((resolve) => {
    const child = spawn("osascript", [file], { stdio: ["ignore", "pipe", "pipe"] });
    let out = "", err = "";
    child.stdout.on("data", d => out += d.toString());
    child.stderr.on("data", d => err += d.toString());
    child.on("close", code => resolve({ code: code ?? 0, stdout: out, stderr: err }));
  });
}

export default {
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
  },
  handler: async (args: Args) => {
    if (!args.csv_path) throw new Error("csv_path is required");
    if (!existsSync(args.csv_path)) throw new Error("CSV not found: " + args.csv_path);

    if (args.dry_run) return { ok: true, message: "Dry run OK", args };

    const baseScript = require("fs").readFileSync(require("path").join(process.cwd(), "scripts", "intromail.applescript"), "utf8");
    const header = buildHeader(args);
    const script = header + "\n" + baseScript;

    const { code, stdout, stderr } = await runOsascript(script);
    if (code !== 0) throw new Error(`osascript failed (${code}): ${stderr || stdout}`);
    return { ok: true, message: stdout.trim() || "Completed." };
  }
};
