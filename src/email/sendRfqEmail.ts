// src/email/sendRfqEmail.ts
import nodemailer from "nodemailer";
import { buildRfqEmail, type RfqPayload } from "./buildRfqEmail.js";
import Anthropic from "@anthropic-ai/sdk";
import OpenAI from "openai";
import { GoogleGenerativeAI } from "@google/generative-ai";
import { readFileSync } from "fs";
import { join } from "path";

// --- Helpers for AI Guidance (email) ---

function _escapeHtml(v: string): string {
  return v.replace(/[&<>"']/g, (ch) => {
    switch (ch) {
      case "&": return "&amp;";
      case "<": return "&lt;";
      case ">": return "&gt;";
      case '"': return "&quot;";
      case "'": return "&#39;";
      default: return ch;
    }
  });
}

function extractSystemPrompt(md: string): string {
  if (!md) return "";
  const anchor = "### 4.3 System Prompt";
  let out = "";
  try {
    const idx = md.indexOf(anchor);
    if (idx >= 0) {
      let sub = md.slice(idx);
      const endIdx = sub.indexOf("\n## ");
      if (endIdx > 0) sub = sub.slice(0, endIdx);
      // Keep only quoted lines starting with '>'
      const lines = sub
        .split("\n")
        .map((l) => l.trim())
        .filter((l) => l.startsWith(">"))
        .map((l) => l.replace(/^>\s?/, ""));
      out = lines.join("\n").trim();
    }
  } catch {
    out = "";
  }
  // Fallback prompt if extraction fails
  if (!out) {
    out =
      "You are Red River’s RFQ Analyst. Analyze the context and produce JSON keys: oem_hits[], contract_hits[], risks[], actions[], summary.";
  }
  return out;
}

async function callLLMJSON(provider: "claude" | "openai" | "gemini", prompt: string): Promise<any> {
  if (provider === "claude") {
    const apiKey = process.env.ANTHROPIC_API_KEY;
    if (!apiKey) throw new Error("ANTHROPIC_API_KEY not configured");
    const client = new Anthropic({ apiKey });
    const resp = await client.messages.create({
      model: "claude-3-5-sonnet-20241022",
      max_tokens: Number(process.env.RFQ_AI_MAX_TOKENS || 1500),
      temperature: parseFloat(process.env.RFQ_AI_TEMPERATURE || "0.3"),
      messages: [{ role: "user", content: prompt }],
    });
    const textPart = resp.content.find((c: any) => c.type === "text");
    if (!textPart || textPart.type !== "text") throw new Error("No text response from Claude");
    let txt = String(textPart.text || "").trim();
    if (txt.startsWith("```json")) txt = txt.replace(/^```json\s*/i, "").replace(/\s*```$/, "");
    else if (txt.startsWith("```")) txt = txt.replace(/^```\s*/i, "").replace(/\s*```$/, "");
    return JSON.parse(txt);
  }
  if (provider === "openai") {
    const apiKey = process.env.OPENAI_API_KEY;
    if (!apiKey) throw new Error("OPENAI_API_KEY not configured");
    const client = new OpenAI({ apiKey });
    const resp = await client.chat.completions.create({
      model: "gpt-4-turbo-preview",
      temperature: parseFloat(process.env.RFQ_AI_TEMPERATURE || "0.3"),
      max_tokens: Number(process.env.RFQ_AI_MAX_TOKENS || 1500),
      response_format: { type: "json_object" },
      messages: [
        { role: "system", content: "You are Red River’s RFQ Analyst. Always return strict JSON." },
        { role: "user", content: prompt },
      ],
    });
    const content = resp.choices[0]?.message?.content;
    if (!content) throw new Error("No response from OpenAI");
    return JSON.parse(content);
  }
  // gemini
  const apiKey = process.env.GOOGLE_API_KEY;
  if (!apiKey) throw new Error("GOOGLE_API_KEY not configured");
  const genAI = new GoogleGenerativeAI(apiKey);
  const model = genAI.getGenerativeModel({ model: "gemini-1.5-pro" });
  const result = await model.generateContent({
    contents: [{ role: "user", parts: [{ text: prompt }] }],
    generationConfig: {
      temperature: parseFloat(process.env.RFQ_AI_TEMPERATURE || "0.3"),
      maxOutputTokens: Number(process.env.RFQ_AI_MAX_TOKENS || 1500),
      responseMimeType: "application/json",
    },
  });
  const text = result.response?.text?.() || "";
  if (!text) throw new Error("No response from Gemini");
  return JSON.parse(text);
}

function buildGuidanceHtmlFromJson(data: any): string {
  if (!data || typeof data !== "object") return "";
  const summary = data.summary ? String(data.summary) : "";
  const oemHits: string[] = Array.isArray(data.oem_hits) ? data.oem_hits : [];
  const contractHits: string[] = Array.isArray(data.contract_hits) ? data.contract_hits : [];
  const risks: string[] = Array.isArray(data.risks) ? data.risks : [];
  const actions: string[] = Array.isArray(data.actions) ? data.actions : [];

  const bullets = (arr: string[]) =>
    arr && arr.length ? " - " + arr.map((s) => _escapeHtml(String(s))).join("<br> - ") : "";

  const parts: string[] = [];
  parts.push(`<p><strong>AI Guidance</strong><br>Summary: <strong>${_escapeHtml(summary)}</strong></p>`);
  if (oemHits.length) parts.push(`<p><strong>OEM Focus:</strong> ${_escapeHtml(oemHits.join(", "))}</p>`);
  if (contractHits.length) parts.push(`<p><strong>Contract Vehicles:</strong> ${_escapeHtml(contractHits.join(", "))}</p>`);
  if (risks.length) parts.push(`<p><strong>Risks</strong><br>${bullets(risks)}</p>`);
  if (actions.length) parts.push(`<p><strong>Recommended Next Steps</strong><br>${bullets(actions)}</p>`);
  return parts.join("\n");
}

function injectGuidance(originalHtml: string, guidanceHtml: string): string {
  if (!guidanceHtml) return originalHtml;
  try {
    // Replace the existing "Next Steps" paragraph block if present
    const replaced = originalHtml.replace(
      /<p><strong>Next Steps<\/strong>[\s\S]*?<\/p>/i,
      guidanceHtml
    );
    if (replaced !== originalHtml) return replaced;
  } catch {
    // ignore
  }
  // Fallback: insert before signature "Thanks,"
  try {
    return originalHtml.replace(
      /<p>Thanks,<br>/i,
      `${guidanceHtml}\n\n      <p>Thanks,<br>`
    );
  } catch {
    return originalHtml + "\n" + guidanceHtml;
  }
}

export async function sendRfqEmail(payload: RfqPayload | any, to: string[]) {
  if (!Array.isArray(to) || to.length === 0) {
    throw new Error("sendRfqEmail: 'to' must be a non-empty array of recipient emails");
  }

  let { subject, html } = buildRfqEmail(payload || {});

  // Optionally augment HTML with AI Guidance from docs/rfq/rfq_guidance_kilocode_prompt.md
  const useAIGuidance = String(process.env.RFQ_EMAIL_AI_GUIDANCE || "").toLowerCase() === "true";
  if (useAIGuidance) {
    try {
      const mdPath = join(process.cwd(), "docs", "rfq", "rfq_guidance_kilocode_prompt.md");
      let md = "";
      try {
        md = readFileSync(mdPath, "utf-8");
      } catch {
        md = "";
      }
      const systemPrompt = extractSystemPrompt(md);

      // Build concise context for the model
      const context = JSON.stringify(
        {
          subject,
          payload: {
            customer: payload?.customer || null,
            oem: payload?.oem || null,
            rfq_id: payload?.rfq_id || null,
            contract_vehicle: payload?.contract_vehicle || null,
            due_date: payload?.due_date || null,
            opportunity_name: payload?.opportunity_name || null,
            close_date: payload?.close_date || null,
            pricing_guidance: payload?.pricing_guidance || null,
            request_registration: payload?.request_registration || null,
            close_probability: payload?.close_probability || null,
            customer_contact: payload?.customer_contact || null,
            timezone: payload?.timezone || null,
          },
        },
        null,
        2
      );

      const finalPrompt =
        `${systemPrompt}\n\nCONTEXT:\n${context}\n\n` +
        `Output JSON with keys exactly: {"oem_hits":[],"contract_hits":[],"risks":[],"actions":[],"summary":""}`;

      const pref = String(process.env.RFQ_AI_DEFAULT_PROVIDER || "claude").toLowerCase();
      const provider: "claude" | "openai" | "gemini" =
        pref.includes("gpt") || pref.includes("openai")
          ? "openai"
          : pref.includes("gemini") || pref.includes("google")
          ? "gemini"
          : "claude";

      const data = await callLLMJSON(provider, finalPrompt);
      const guidanceHtml = buildGuidanceHtmlFromJson(data);
      if (guidanceHtml) {
        html = injectGuidance(html, guidanceHtml);
      }
    } catch {
      // best-effort; fall back to static HTML if AI guidance fails
    }
  }

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