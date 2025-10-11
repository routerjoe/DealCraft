// src/email/buildOemRegistrationEmail.ts
import path from "path";
import { globSync } from "glob";
import { formatInTimeZone } from "date-fns-tz";
import { parseISO } from "date-fns";

export type OemPayload = {
  customer?: string;
  oem?: string;
  rfq_id?: string;
  contract_vehicle?: string;
  opportunity_name?: string;
  close_date?: string;             // ISO date
  account_executive?: string;
  isam?: string;
  engineer?: string;
  partner_tier?: string;
  end_user_contact?: string;       // literal or "auto"
  rfq_folder?: string;
  timezone?: string;
};

const PREFER_TBD = new Set([
  "opportunity_name",
  "close_date",
  "account_executive",
  "isam",
  "engineer",
  "partner_tier",
  "end_user_contact",
]);

function val(v?: string, preferTbd = false): string {
  if (!v || v.trim() === "") return preferTbd ? "TBD" : "";
  return v.trim();
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

function fmtDate(iso?: string, tz?: string): string {
  const zone = tz || "America/New_York";
  if (!iso) return "TBD";
  try {
    const d = parseISO(iso);
    if (isNaN(d.getTime())) return "TBD";
    return formatInTimeZone(d, zone, "MMMM d, yyyy");
  } catch {
    return "TBD";
  }
}

// Stub signature — implement to read latest bid board email/thread for this RFQ.
export async function extractEndUserFromBidBoardEmail(rfq_id?: string): Promise<string> {
  // TODO: integrate with your storage/mail parser; return "Name, email@domain" or "".
  return "";
}

const BASE_NAMES = ["LOM", "List_of_Materials", "List-of-Materials", "List of Materials"];
const ALLOWED_EXTS = new Set([".xlsx", ".csv", ".pdf"]);

function findFirstLom(rfqFolder?: string): { filename: string; path: string } | undefined {
  if (!rfqFolder || rfqFolder.trim() === "") return undefined;
  for (const base of BASE_NAMES) {
    const pattern = path.join(rfqFolder, `${base}.*`);
    const matches = globSync(pattern, { nocase: true });
    for (const m of matches) {
      const ext = path.extname(m).toLowerCase();
      if (ALLOWED_EXTS.has(ext)) {
        return { filename: path.basename(m), path: m };
      }
    }
  }
  return undefined;
}

export async function buildOemRegistrationEmail(payload: OemPayload): Promise<{
  subject: string;
  html: string;
  attachments?: { filename: string; path: string }[];
}> {
  const tz = payload.timezone || "America/New_York";

  // Raw values for subject/body (subject does not escape HTML)
  const customerRaw = val(payload.customer);
  const oemRaw = val(payload.oem);
  const rfqIdRaw = val(payload.rfq_id);
  const vehicleRaw = val(payload.contract_vehicle);

  // Escaped values for HTML
  const customer = esc(customerRaw);
  const oem = esc(oemRaw);
  const rfqId = esc(rfqIdRaw);
  const vehicle = esc(vehicleRaw);
  const oppName = esc(val(payload.opportunity_name, true));
  const closeDatePretty = esc(fmtDate(payload.close_date, tz));
  const ae = esc(val(payload.account_executive, true));
  const isam = esc(val(payload.isam, true));
  const se = esc(val(payload.engineer, true));
  const tier = esc(val(payload.partner_tier, true));

  let endUser = val(payload.end_user_contact, true);
  if ((payload.end_user_contact || "").toLowerCase() === "auto") {
    const auto = await extractEndUserFromBidBoardEmail(rfqIdRaw);
   endUser = val(auto, true);
  }
  const endUserEsc = esc(endUser);

  const subject = `Request for Registration / Partnering – ${customerRaw} | ${oemRaw} | ${vehicleRaw} | RFQ ${rfqIdRaw || ""}`;

  const html = `
<html>
<body style="font-family:Arial,sans-serif;font-size:14px;line-height:1.5;">
  <p>Hello ${oem} Team,</p>
  <p>We would like to request registration or partnering support for the following opportunity. A copy of the List of Materials (LOM) is attached for your reference.</p>

  <p><strong>Opportunity Summary</strong><br>
  - Customer: <strong>${customer}</strong><br>
  - RFQ ID: <strong>${rfqId}</strong><br>
  - Contract Vehicle: <strong>${vehicle}</strong><br>
  - Opportunity Name: <strong>${oppName}</strong><br>
  - Estimated Close Date: <strong>${closeDatePretty}</strong><br>
  - Account Executive: <strong>${ae}</strong><br>
  - Inside Sales (iSAM): <strong>${isam}</strong><br>
  - Solutions Engineer: <strong>${se}</strong><br>
  - Partner Tier: <strong>${tier}</strong><br>
  - End User POC: <strong>${endUserEsc}</strong></p>

  <p><strong>Request</strong><br>
  Red River is pursuing this opportunity and would like to confirm ${oem}’s support for registration or partnering. Once this request is approved, my iSAM will proceed to submit the official registration request through the Partner Portal.</p>

  <p>Please let us know if you require any additional information or documentation to initiate the process.</p>

  <p>Thank you,<br><br>
  <strong>Joe Nolan</strong><br>
  Account Executive | Red River<br>
  678.951.5584<br>
  <a href="mailto:joe.nolan@redriver.com">joe.nolan@redriver.com</a></p>
</body>
</html>
`.trim();

  const firstLom = findFirstLom(payload.rfq_folder);
  const attachments = firstLom ? [firstLom] : undefined;

  return { subject, html, attachments };
}