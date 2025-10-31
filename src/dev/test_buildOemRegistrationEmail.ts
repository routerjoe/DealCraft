// src/dev/test_buildOemRegistrationEmail.ts
// Simple runtime assertions for the OEM Registration/Partnering email builder.
// Run: npm run test:oem-email

import fs from "fs/promises";
import path from "path";
import { buildOemRegistrationEmail, type OemPayload } from "../email/buildOemRegistrationEmail.js";

function assert(condition: boolean, message: string) {
  if (!condition) throw new Error(message);
}

function contains(haystack: string, needle: string): boolean {
  return haystack.indexOf(needle) !== -1;
}

function notContains(haystack: string, needle: string): boolean {
  return haystack.indexOf(needle) === -1;
}

function logPass(name: string) {
  console.log(`PASS: ${name}`);
}

function logFail(name: string, err: any) {
  console.error(`FAIL: ${name}\n${err?.message || String(err)}`);
}

async function testFullPayload() {
  const payload: OemPayload = {
    customer: "Customer Alpha",
    oem: "Cisco",
    rfq_id: "361235",
    contract_vehicle: "SEWP V",
    opportunity_name: "Customer Alpha Collaboration Refresh",
    close_date: "2025-11-15",
    account_executive: "Joe Nolan",
    isam: "Kristen Bateman",
    engineer: "Lewis Hickman",
    partner_tier: "Gold",
    end_user_contact: "Ms. Preston, afcent@example.mil",
    timezone: "America/New_York",
  };

  const { subject, html, attachments } = await buildOemRegistrationEmail(payload);

  // Subject spec
  assert(
    subject === "Request for Registration / Partnering – Customer Alpha | Cisco | SEWP V | RFQ 361235",
    `Unexpected subject: ${subject}`
  );

  // Greeting and opening sentence
  assert(contains(html, "<p>Hello Cisco Team,</p>"), "Greeting line incorrect");
  assert(
    contains(
      html,
      "We would like to request registration or partnering support for the following opportunity. A copy of the List of Materials (LOM) is attached for your reference."
    ),
    "Opening paragraph incorrect"
  );

  // Opportunity Summary fields
  for (const pair of [
    "- Customer: <strong>Customer Alpha</strong>",
    "- RFQ ID: <strong>361235</strong>",
    "- Contract Vehicle: <strong>SEWP V</strong>",
    "- Opportunity Name: <strong>Customer Alpha Collaboration Refresh</strong>",
    "- Estimated Close Date: <strong>November 15, 2025</strong>",
    "- Account Executive: <strong>Joe Nolan</strong>",
    "- Inside Sales (iSAM): <strong>Kristen Bateman</strong>",
    "- Solutions Engineer: <strong>Lewis Hickman</strong>",
    "- Partner Tier: <strong>Gold</strong>",
    "- End User POC: <strong>Ms. Preston, afcent@example.mil</strong>",
  ]) {
    assert(contains(html, pair), `Summary line missing: ${pair}`);
  }

  // Request paragraph mentions OEM name context
  assert(
    contains(html, "would like to confirm Cisco"),
    "Request paragraph missing OEM reference"
  );

  // Signature
  assert(contains(html, "<strong>Joe Nolan</strong>"), "Signature name missing");
  assert(contains(html, "Account Executive | Red River"), "Title line missing");
  assert(contains(html, "joe.nolan@redriver.com"), "Email link missing");

  // No attachments unless rfq_folder provided
  assert(!attachments, "Attachments should be undefined when rfq_folder not set");

  logPass("Full payload");
}

async function testMissingFields() {
  const payload: OemPayload = {
    // Deliberately empty to test defaulting behavior
  };

  const { subject, html } = await buildOemRegistrationEmail(payload);

  // Subject follows exact pattern even with blanks
  assert(subject.startsWith("Request for Registration / Partnering – "), "Subject prefix incorrect");
  assert(contains(subject, " | RFQ "), "Subject pattern missing RFQ placeholder");

  // Preferred TBD fields
  for (const pair of [
    "- Opportunity Name: <strong>TBD</strong>",
    "- Estimated Close Date: <strong>TBD</strong>",
    "- Account Executive: <strong>TBD</strong>",
    "- Inside Sales (iSAM): <strong>TBD</strong>",
    "- Solutions Engineer: <strong>TBD</strong>",
    "- Partner Tier: <strong>TBD</strong>",
    "- End User POC: <strong>TBD</strong>",
  ]) {
    assert(contains(html, pair), `Expected TBD rendering missing: ${pair}`);
  }

  // Non-preferred fields blank
  for (const line of [
    "- Customer: <strong></strong>",
    "- RFQ ID: <strong></strong>",
    "- Contract Vehicle: <strong></strong>",
  ]) {
    assert(contains(html, line), `Expected blank rendering missing: ${line}`);
  }

  logPass("Missing fields");
}

async function testAutoEndUser() {
  const payload: OemPayload = {
    customer: "X",
    oem: "Y",
    rfq_id: "12345",
    contract_vehicle: "Z",
    end_user_contact: "auto", // stub returns "", should render as TBD
  };

  const { html } = await buildOemRegistrationEmail(payload);
  assert(
    contains(html, "- End User POC: <strong>TBD</strong>"),
    "Auto end-user contact should render as TBD when stub returns empty"
  );

  logPass('"auto" end_user_contact');
}

async function testLomAttachmentFirstMatch() {
  const baseDir = path.resolve(process.cwd(), "tmp/test_oem_email");
  await fs.mkdir(baseDir, { recursive: true });

  // Create multiple candidate files; builder should attach only the first match (by base name priority)
  const lomXlsx = path.join(baseDir, "LOM.xlsx");
  const listPdf = path.join(baseDir, "List_of_Materials.pdf");
  await fs.writeFile(listPdf, "pdf");
  await fs.writeFile(lomXlsx, "xlsx");

  const payload: OemPayload = {
    customer: "A",
    oem: "B",
    rfq_id: "C",
    contract_vehicle: "D",
    rfq_folder: baseDir,
  };

  const { attachments } = await buildOemRegistrationEmail(payload);
  if (!(attachments && attachments.length === 1)) {
    throw new Error("Expected exactly one attachment");
  }
  assert(attachments[0].filename === "LOM.xlsx", `Expected LOM.xlsx, got ${attachments[0].filename}`);

  logPass("LOM first-match attachment");
}

async function main() {
  const tests = [
    { name: "Full payload", fn: testFullPayload },
    { name: "Missing fields", fn: testMissingFields },
    { name: '"auto" end_user_contact', fn: testAutoEndUser },
    { name: "LOM first-match attachment", fn: testLomAttachmentFirstMatch },
  ];

  let failed = 0;

  for (const t of tests) {
    try {
      await t.fn();
    } catch (err) {
      failed += 1;
      logFail(t.name, err);
    }
  }

  if (failed > 0) {
    console.error(`\n${failed} test(s) failed.`);
    process.exit(1);
  } else {
    console.log("\nAll tests passed.");
  }
}

main().catch((e) => {
  console.error("Unhandled test runner error:", e?.message || String(e));
  process.exit(1);
});