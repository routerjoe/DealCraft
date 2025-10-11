// src/email/sendRfqEmail.ts
import nodemailer from "nodemailer";
import { buildRfqEmail, type RfqPayload } from "./buildRfqEmail.js";

export async function sendRfqEmail(payload: RfqPayload | any, to: string[]) {
  if (!Array.isArray(to) || to.length === 0) {
    throw new Error("sendRfqEmail: 'to' must be a non-empty array of recipient emails");
  }

  const { subject, html } = buildRfqEmail(payload || {});

  const host = process.env.SMTP_HOST;
  const port = Number(process.env.SMTP_PORT || 587);
  const secure =
    String(process.env.SMTP_SECURE || "").toLowerCase() === "true" || port === 465;
  const user = process.env.SMTP_USER;
  const pass = process.env.SMTP_PASS;

  // For O365, from should be the authenticated mailbox unless the tenant allows send-as
  const from = (process.env.MAIL_FROM && process.env.MAIL_FROM.trim() !== "")
    ? process.env.MAIL_FROM!
    : (user || "rfq@redriver.com");

  // Hardened transport for Office 365 (STARTTLS on 587)
  const transporter = nodemailer.createTransport({
    host,
    port,
    secure,            // false for 587, true for 465
    requireTLS: true,  // force STARTTLS upgrade
    auth: user && pass ? { user, pass } : undefined,
    // Prefer LOGIN for O365; falls back if unsupported
    // Types allow this on SMTP transport options
    authMethod: (process.env.SMTP_AUTH_METHOD as any) || "LOGIN",
    tls: {
      minVersion: "TLSv1.2",
    },
  } as any);

  // Verify connection/auth before sending to surface clearer errors
  await transporter.verify();

  await transporter.sendMail({
    from,
    to: to.join(","),
    subject,
    html, // ensure Content-Type: text/html
  });
}