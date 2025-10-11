import fs from "node:fs";
import path from "node:path";
import { execSync } from "node:child_process";

const home = process.env.HOME || process.env.USERPROFILE || ".";
const inbox = process.env.INTROMAIL_INBOX_DIR || path.join(home, "RedRiver", "campaigns", "inbox");
const analyzerToolPath = path.join(process.cwd(), "dist", "src", "tools", "intromail_analyzer.js"); // after build

if (!fs.existsSync(inbox)) fs.mkdirSync(inbox, { recursive: true });
console.log("[IntroMail] Watching inbox:", inbox);

fs.watch(inbox, { persistent: true }, (event, filename) => {
  if (!filename || !filename.endsWith(".csv")) return;
  const full = path.join(inbox, filename);
  setTimeout(() => {
    if (fs.existsSync(full)) {
      try {
        console.log("[IntroMail] Detected CSV:", full, "→ running analyzer...");
        execSync(`node "${analyzerToolPath}" --csv_path "${full}"`, { stdio: "inherit" });
      } catch (e) {
        console.error("[IntroMail] Analyzer failed:", e);
      }
    }
  }, 500); // slight delay for file write completion
});
