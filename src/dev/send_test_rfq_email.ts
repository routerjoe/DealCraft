// src/dev/send_test_rfq_email.ts
// Sends a test RFQ notification email using the builder/sender.
// Usage: npm run build && node dist/dev/send_test_rfq_email.js

import path from "path";
import dotenv from "dotenv";
import { sendRfqEmail } from "../email/sendRfqEmail.js";
import { type RfqPayload } from "../email/buildRfqEmail.js";

function loadEnv() {
  dotenv.config({ path: path.resolve(process.cwd(), ".env") });
}

async function main() {
  loadEnv();

  // Recipient(s) for proofing
  const to = ["joe.nolan@redriver.com"];

  // Sample payload from the spec with explicit timezone override
  const payload: RfqPayload = {
    customer: "Customer Alpha",
    oem: "Cisco",
    rfq_id: "361235",
    contract_vehicle: "SEWP V",
    due_date: "2025-10-12", // ISO (Sunday)
    opportunity_name: "Customer Alpha – Collab Refresh",
    close_date: "2025-11-15",
    pricing_guidance: "Target 12–15% margin; confirm Cisco EA alignment",
    request_registration: "Yes",
    close_probability: "65%",
    customer_contact: "Ms. Preston, afcent@example.mil",
    timezone: "America/New_York", // enforce user preference for the proof
  };

  await sendRfqEmail(payload, to);
  console.log("Test RFQ email sent to:", to.join(","));
}

main().catch((err) => {
  console.error("Failed to send test RFQ email:", err?.message || String(err));
  process.exit(1);
});