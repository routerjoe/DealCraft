// src/email/buildRfqEmail.ts
import { formatInTimeZone } from "date-fns-tz";
import { parseISO } from "date-fns";

export type RfqPayload = {
  customer?: string;
  oem?: string;
  rfq_id?: string;
  contract_vehicle?: string;
  due_date?: string; // ISO string
  opportunity_name?: string;
  close_date?: string;
  pricing_guidance?: string;
  request_registration?: string;
  close_probability?: string;
  customer_contact?: string;
  timezone?: string;
};

function val(v?: string, opts?: { preferTbd?: boolean }) {
  if (!v || v.trim() === "") return opts?.preferTbd ? "TBD" : "";
  return v;
}

function esc(v: string): string {
  return v.replace(/[&<>"']/g, (ch) => {
    switch (ch) {
      case "&":
        return "&amp;";
      case "<":
        return "&lt;";
      case ">":
        return "&gt;";
      case '"':
        return "&quot;";
      case "'":
        return "&#39;";
      default:
        return ch;
    }
  });
}

function fmtDueDate(iso?: string, tz?: string) {
  const zone = tz || "America/New_York";
  if (!iso) return "";
  try {
    const d = parseISO(iso);
    if (isNaN(d.getTime())) return "";
    return `${formatInTimeZone(d, zone, "EEEE, MMMM d, yyyy")} (${zone})`;
  } catch {
    return "";
  }
}

export function buildRfqEmail(payload: RfqPayload): { subject: string; html: string } {
  const zone = payload.timezone || "America/New_York";

  // Escaped values for HTML body
  const customer = esc(val(payload.customer));
  const oem = esc(val(payload.oem));
  const rfqId = esc(val(payload.rfq_id));
  const vehicle = esc(val(payload.contract_vehicle));
  const dueIso = val(payload.due_date);
  const dueDatePretty = esc(fmtDueDate(dueIso, zone));

  const opportunityName = esc(val(payload.opportunity_name, { preferTbd: true }));
  const closeDate = esc(val(payload.close_date, { preferTbd: true }));
  const pricingGuidance = esc(val(payload.pricing_guidance, { preferTbd: true }));
  const requestRegistration = esc(val(payload.request_registration, { preferTbd: true }));
  const closeProbability = esc(val(payload.close_probability, { preferTbd: true }));
  const customerContact = esc(val(payload.customer_contact, { preferTbd: true }));

  // Subject: New RFQ – {customer} | {oem} | {contract_vehicle} | Due {YYYY-MM-DD}
  // If due_date is missing, omit the trailing " | Due ..."
  const subjectCustomer = val(payload.customer);
  const subjectOem = val(payload.oem);
  const subjectVehicle = val(payload.contract_vehicle);
  let subject = `New RFQ – ${subjectCustomer} | ${subjectOem} | ${subjectVehicle}`;
  if (payload.due_date && payload.due_date.trim() !== "") {
    subject += ` | Due ${payload.due_date}`;
  }

  const html = `
  <html>
    <body style="font-family:Arial,sans-serif;font-size:14px;line-height:1.5;">
      <p>Team,</p>
      <p>A new RFQ has been received in the RFQ Tracker.</p>

      <p><strong>Summary</strong><br>
      Customer: <strong>${customer}</strong><br>
      OEM: <strong>${oem}</strong><br>
      RFQ ID: <strong>${rfqId}</strong><br>
      Contract Vehicle: <strong>${vehicle}</strong><br>
      Due Date: <strong>${dueDatePretty}</strong></p>

      <p><strong>Opportunity Details</strong><br>
      Opportunity Name: <strong>${opportunityName}</strong><br>
      Close Date: <strong>${closeDate}</strong><br>
      Pricing Guidance: <strong>${pricingGuidance}</strong><br>
      Request Registration: <strong>${requestRegistration}</strong><br>
      Close Probability: <strong>${closeProbability}</strong><br>
      Customer Contact: <strong>${customerContact}</strong></p>

      <p><strong>Next Steps</strong><br>
      - <strong>iSAM:</strong> Initiate the quote request and track OEM registration.<br>
        Please reply with the following details:<br>
        • Opportunity Number: <strong>TBD</strong><br>
        • Cost: <strong>TBD</strong><br>
        • Margin: <strong>TBD</strong><br>
        • Sell to Price: <strong>TBD</strong><br>
        • Registration Number: <strong>TBD</strong><br>
        • Registration Expires: <strong>TBD</strong><br>
      - <strong>Lewis:</strong> Review for any technical configuration or BOM validation needs.<br>
      - <strong>Joe:</strong> Coordinate customer communication and ensure quote alignment.</p>

      <p>Thanks,<br><br>
      <strong>Joe Nolan</strong><br>
      Account Executive | Red River<br>
      678.951.5584<br>
      <a href="mailto:joe.nolan@redriver.com">joe.nolan@redriver.com</a></p>
    </body>
  </html>
  `.trim();

  return { subject, html };
}