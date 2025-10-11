// src/dev/create_oem_outlook_draft_eml.ts
// Builds an .eml file draft for OEM email (unsent) to open in Outlook.
// Usage to generate only:
//   npm run build && node dist/dev/create_oem_outlook_draft_eml.js
// To also open in Outlook (macOS):
//   npm run build && OUT=$(node dist/dev/create_oem_outlook_draft_eml.js) && open -a "Microsoft Outlook" "$OUT"

import fs from "fs/promises";
import path from "path";
import dotenv from "dotenv";
import { buildOemRegistrationEmail, type OemPayload } from "../email/buildOemRegistrationEmail.js";

function loadEnv() {
  dotenv.config({ path: path.resolve(process.cwd(), ".env") });
}

function encodeSubjectUtf8B64(s: string): string {
  const b64 = Buffer.from(s, "utf8").toString("base64");
  return `=?UTF-8?B?${b64}?=`;
}

async function main() {
  loadEnv();

  const toAddr = process.env.OEM_PROOF_TO || "joe.nolan@redriver.com";
  const fromAddr = (process.env.MAIL_FROM && process.env.MAIL_FROM.trim() !== "")
    ? process.env.MAIL_FROM!
    : "joe.nolan@redriver.com";

  const payload: OemPayload = {
    customer: "AFCENT",
    oem: "Cisco",
    rfq_id: "361235",
    contract_vehicle: "SEWP V",
    opportunity_name: "AFCENT Collaboration Refresh",
    close_date: "2025-11-15",
    account_executive: "Joe Nolan",
    isam: "Kristen Bateman",
    engineer: "Lewis Hickman",
    partner_tier: "Gold",
    end_user_contact: "Ms. Preston, afcent@example.mil",
    // rfq_folder: "/Users/jonolan/RedRiver/RFQs/361235/", // uncomment to auto-attach LOM
    timezone: "America/New_York",
  };

  const { subject, html } = await buildOemRegistrationEmail(payload);

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
  const outPath = path.join(outDir, "oem_registration_proof.eml");
  await fs.mkdir(outDir, { recursive: true });
  await fs.writeFile(outPath, emlRaw, "utf8");

  console.log(outPath);
}

main().catch((err) => {
  console.error("Error:", err?.message || String(err));
  process.exit(1);
});