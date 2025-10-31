// src/dev/test_buildRfqEmail.ts
// Simple runtime assertions for the RFQ email builder without a test framework.
// Run: npm run test:rfq-email

import { buildRfqEmail, type RfqPayload } from "../email/buildRfqEmail.js";

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

  // Subject spec
  assert(
    subject === "New RFQ – Customer Alpha | Cisco | SEWP V | Due 2025-10-12",
    `Unexpected subject: ${subject}`
  );

  // No "logged" anywhere
  assert(notContains(subject.toLowerCase(), "logged"), "Subject must not include 'logged'");
  assert(notContains(html.toLowerCase(), "logged"), "Body must not include 'logged'");

  // Summary fields
  assert(contains(html, "Customer: <strong>Customer Alpha</strong>"), "Customer not rendered correctly");
  assert(contains(html, "OEM: <strong>Cisco</strong>"), "OEM not rendered correctly");
  assert(contains(html, "RFQ ID: <strong>361235</strong>"), "RFQ ID not rendered correctly");
  assert(contains(html, "Contract Vehicle: <strong>SEWP V</strong>"), "Contract vehicle incorrect");

  // Date formatting with day-of-week + TZ
  assert(
    contains(html, "Sunday, October 12, 2025 (America/New_York)"),
    "Due Date pretty format incorrect"
  );

  // iSAM action language and reply list
  assert(contains(html, "<strong>iSAM:</strong>"), "iSAM label missing");
  assert(contains(html, "Please reply with the following details:"), "iSAM reply line missing");
  for (const field of [
    "Opportunity Number",
    "Cost",
    "Margin",
    "Sell to Price",
    "Registration Number",
    "Registration Expires",
  ]) {
    assert(
      contains(html, `• ${field}: <strong>TBD</strong>`),
      `iSAM reply field missing: ${field}`
    );
  }

  // Footer signature
  assert(contains(html, "Joe Nolan"), "Signature missing");
  assert(contains(html, "Account Executive | Red River"), "Title missing");
  assert(contains(html, "joe.nolan@redriver.com"), "Email link missing");

  logPass("Full payload");
}

async function testMissingFields() {
  const payload: RfqPayload = {
    // All primary fields omitted
    // Ensure timezone default applies
  };

  const { subject, html } = buildRfqEmail(payload);

  // Minimal subject - starts with required prefix, and should not include "Due " since date is missing
  assert(subject.startsWith("New RFQ –"), "Subject prefix incorrect");
  assert(notContains(subject, " | Due "), "Subject should omit Due when date is missing");

  // Preferred TBD fields must show "TBD"
  for (const pair of [
    "Opportunity Name: <strong>TBD</strong>",
    "Close Date: <strong>TBD</strong>",
    "Pricing Guidance: <strong>TBD</strong>",
    "Request Registration: <strong>TBD</strong>",
    "Close Probability: <strong>TBD</strong>",
    "Customer Contact: <strong>TBD</strong>",
  ]) {
    assert(contains(html, pair), `Expected TBD rendering missing for: ${pair}`);
  }

  // Non-preferred fields should be blank when missing
  for (const line of [
    "Customer: <strong></strong>",
    "OEM: <strong></strong>",
    "RFQ ID: <strong></strong>",
    "Contract Vehicle: <strong></strong>",
    "Due Date: <strong></strong>",
  ]) {
    assert(contains(html, line), `Expected blank rendering missing for: ${line}`);
  }

  // Ensure no "RFQ Folder" line is present
  assert(notContains(html, "RFQ Folder"), "RFQ Folder line must not be rendered");

  logPass("Missing fields");
}

async function testInvalidDates() {
  const payload: RfqPayload = {
    customer: "X",
    oem: "Y",
    contract_vehicle: "Z",
    due_date: "not-a-date",
    timezone: "America/New_York",
  };

  const { subject, html } = buildRfqEmail(payload);

  // Body should leave pretty date blank when invalid
  assert(contains(html, "Due Date: <strong></strong>"), "Invalid date should render blank pretty date");

  // We do not enforce subject behavior for invalid date; builder currently passes through the string if provided.
  // This test ensures no crash and a valid HTML output.
  assert(contains(subject, "New RFQ – "), "Subject prefix missing for invalid date");
  assert(typeof html === "string" && html.length > 0, "HTML must be non-empty");

  logPass("Invalid dates");
}

async function main() {
  const results = [
    { name: "Full payload", fn: testFullPayload },
    { name: "Missing fields", fn: testMissingFields },
    { name: "Invalid dates", fn: testInvalidDates },
  ];

  let failed = 0;

  for (const t of results) {
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