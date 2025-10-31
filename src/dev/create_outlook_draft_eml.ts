// src/dev/create_outlook_draft_eml.ts
// Builds an .eml file with the RFQ HTML and opens cleanly in Outlook as an unsent draft.
// Usage to generate only:
//   npm run build && node dist/dev/create_outlook_draft_eml.js
// To also open in Outlook (macOS):
//   npm run build && OUT=$(node dist/dev/create_outlook_draft_eml.js) && open -a "Microsoft Outlook" "$OUT"

import fs from "fs/promises";
import path from "path";
import dotenv from "dotenv";
import { buildRfqEmail, type RfqPayload } from "../email/buildRfqEmail.js";

function loadEnv() {
  dotenv.config({ path: path.resolve(process.cwd(), ".env") });
}

function encodeSubjectUtf8B64(s: string): string {
  const b64 = Buffer.from(s, "utf8").toString("base64");
  return `=?UTF-8?B?${b64}?=`;
}

async function main() {
  loadEnv();

  // Recipient for proofing (can be edited inline if needed)
  const toAddr = "joe.nolan@redriver.com";
  // Use MAIL_FROM when available; otherwise fall back to the same address
  const fromAddr = (process.env.MAIL_FROM && process.env.MAIL_FROM.trim() !== "")
    ? process.env.MAIL_FROM!
    : "joe.nolan@redriver.com";

  // Sample payload from spec with explicit timezone for proof
  const payload: RfqPayload = {
    customer: "Customer Alpha",
    oem: "Cisco",
    rfq_id: "361235",
    contract_vehicle: "SEWP V",
    due_date: "2025-10-12", // Sunday
    opportunity_name: "Customer Alpha – Collab Refresh",
    close_date: "2025-11-15",
    pricing_guidance: "Target 12–15% margin; confirm Cisco EA alignment",
    request_registration: "Yes",
    close_probability: "65%",
    customer_contact: "Ms. Preston, afcent@example.mil",
    timezone: "America/New_York",
  };

  const { subject, html } = buildRfqEmail(payload);

  // Compose minimal RFC 5322 .eml with HTML body
  // X-Unsent: 1 hints to Outlook that this is an unsent draft
  const headers = [
    "X-Unsent: 1",
    `From: Joe Nolan <${fromAddr}>`,
    `To: ${toAddr}`,
    `Subject: ${encodeSubjectUtf8B64(subject)}`,
    `Date: ${new Date().toUTCString()}`,
    "MIME-Version: 1.0",
    "Content-Type: text/html; charset=UTF-8",
    "Content-Transfer-Encoding: 8bit",
  ];

  const emlRaw = headers.join("\r\n") + "\r\n\r\n" + html.replace(/\r?\n/g, "\r\n");

  const outDir = path.resolve(process.cwd(), "tmp");
  const outPath = path.join(outDir, "rfq_proof.eml");
  await fs.mkdir(outDir, { recursive: true });
  await fs.writeFile(outPath, emlRaw, "utf8");

  // Print the file path so callers can capture and open it
  console.log(outPath);
}

main().catch((err) => {
  console.error("Error:", err?.message || String(err));
  process.exit(1);
});