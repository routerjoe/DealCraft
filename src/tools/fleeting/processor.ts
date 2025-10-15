import * as fs from 'fs';
import * as path from 'path';
import { createHash, randomBytes } from 'crypto';
import { parse as yamlParse, stringify as yamlStringify } from 'yaml';
import { logger } from '../../utils/logger.js';
import { resolveRange, inRange as dateInRange } from './date.js';
import { getFleetingPaths } from './paths.js';

export type FleetingScope = 'today' | 'this-week' | 'this-month' | 'since-last-run' | 'range';

export interface FleetingOptions {
  scope: FleetingScope;
  range?: string;           // YYYY-MM-DD..YYYY-MM-DD when scope=range
  dryRun?: boolean;         // default false
  force?: boolean;          // default false
  targetDir?: string;       // override DAILY_NOTES_DIR for ad-hoc runs
}

export interface Result {
  meetings_created: number;
  meetings_updated: number;
  contacts_created: number;
  contacts_updated: number;
  contacts_triaged: number;
  company_hubs_created: number;
  tasks_added: number;
  tasks_moved_to_completed: number;
  skipped_notes: number;
  processed_notes: number;
}

export interface FleetingSummary extends Result {
  scope: string;
  dryRun: boolean;
  state_path?: string;
}

/**
 * Atomic file write: write to temp and rename into place.
 */
function writeAtomic(filePath: string, content: string) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  const tmp = `${filePath}.tmp-${randomBytes(6).toString('hex')}`;
  fs.writeFileSync(tmp, content, 'utf8');
  fs.renameSync(tmp, filePath);
}

/**
 * Append by reading existing, concatenating, and atomic rewriting.
 */
function appendAtomic(filePath: string, toAppend: string) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  const current = fs.existsSync(filePath) ? fs.readFileSync(filePath, 'utf8') : '';
  writeAtomic(filePath, current + toAppend);
}

const R = (p: string) => fs.readFileSync(p, 'utf8');
const E = (p: string) => fs.existsSync(p);
const H = (s: string) => createHash('sha256').update(s).digest('hex');
const nowISO = () => new Date().toISOString();

function deriveDate(p: string): string | undefined {
  const b = path.basename(p).replace(/\.md$/i, '');
  const m = b.match(/\d{4}-\d{2}-\d{2}/);
  return m ? m[0] : undefined;
}

// Subject helpers
function normalizeSubject(s: string): string {
  let t = (s || '').trim();
  t = t.replace(/^[-:|–—]+/, '').trim();
  t = t.replace(/^(meeting\s+)?(with|about|on|re:?)[\s-]+/i, '').trim();
  return t.replace(/\s{2,}/g, ' ') || 'Meeting';
}

function normNameFromEmail(s: string): string {
  const local = (s.split('@')[0] || '').replace(/[^\w\s.-]/g, '');
  const parts = local.replace(/[._-]+/g, ' ').split(/\s+/).filter(Boolean);
  return parts.map(p => p[0].toUpperCase() + p.slice(1).toLowerCase()).join(' ') || s;
}

// Meeting parsing
type MeetingBlock = {
  subject: string;
  time?: string;
  attendees?: string[];
  discussion?: string[];
  extra?: { heading: string; lines: string[] }[];
  tasks?: string[]; // unchecked from meeting block area
  links?: string[];
  followup?: string;
};

function parseMeetings(md: string): MeetingBlock[] {
  const lines = md.split(/\r?\n/);
  const blocks: MeetingBlock[] = [];
  let i = 0;
  while (i < lines.length) {
    const head = lines[i].match(/^##\s*Meeting\s*(.*)$/i);
    if (!head) { i++; continue; }
    const subject = normalizeSubject(head[1] || '');
    const block: string[] = [];
    i++;
    while (i < lines.length && !/^##\s+/.test(lines[i])) {
      block.push(lines[i]); i++;
    }

    // split by ### sections
    let j = 0, current: { name: string; lines: string[] } | null = null;
    const sections: Record<string, string[]> = {};
    while (j < block.length) {
      const h3 = block[j].match(/^###\s*(.+?)\s*$/);
      if (h3) {
        if (current) sections[current.name.toLowerCase()] = current.lines;
        current = { name: h3[1].trim(), lines: [] };
      } else if (current) {
        current.lines.push(block[j]);
      }
      j++;
    }
    if (current) sections[current.name.toLowerCase()] = current.lines;

    const pick = (k: string) => Object.keys(sections).find(s => s.toLowerCase() === k.toLowerCase());
    const timeKey = pick('time');
    const attKey = pick('attendees');
    const discKey = pick('discussion');

    const time = timeKey ? sections[timeKey].join(' ').trim() : '';
    const attendees = attKey ? sections[attKey]
      .map(s => s.replace(/^[\-\*]\s*/, '').trim())
      .map(a => /@/.test(a) ? normNameFromEmail(a) : a) : [];
    const discussion = discKey ? sections[discKey] : [];
    const extra: { heading: string; lines: string[] }[] = [];
    for (const k of Object.keys(sections)) {
      if (k !== timeKey && k !== attKey && k !== discKey) {
        extra.push({ heading: k, lines: sections[k] });
      }
    }

    const all = block.join('\n');
    const tasks = (all.match(/^\s*- \[ \]\s+.*$/gmi) || []).map(s => s.trim());
    const links = (all.match(/\bhttps?:\/\/\S+/g) || []);
    const fupm = all.match(/(?:follow[-\s]*up|due)\s*:\s*(\d{4}-\d{2}-\d{2})/i);
    const followup = fupm ? fupm[1] : undefined;

    blocks.push({ subject, time: time || undefined, attendees, discussion, extra, tasks, links, followup });
  }
  return blocks;
}

// People / Company extraction
type ParsedContact = {
  kind: 'person' | 'company';
  full_name?: string;
  title?: string;
  emails: string[];
  mobile: string[];
  office: string[];
  company?: string;
  address?: string;
  sourceNote?: string;
};

function canonicalCompany(s?: string): string {
  if (!s) return '';
  return s.replace(/\b(inc\.?|llc|corp\.?|co\.?|ltd)\b/gi, '')
    .replace(/[“”"]/g, '')
    .replace(/\s{2,}/g, ' ')
    .trim();
}

function parseContacts(md: string, relNote: string): ParsedContact[] {
  const lines = md.split(/\r?\n/);
  const out: ParsedContact[] = [];
  let cur: ParsedContact | null = null;
  let inAddress = false;

  const keyed = /^(?:N|Name|T|Title|E|Email|M|Mobile|C|Company|O|Office(?:\s+Number)?|A|Address)\s*[:\-—|]/i;

  function push() {
    if (!cur) return;
    if (cur.company) cur.company = canonicalCompany(cur.company);
    out.push(cur); cur = null; inAddress = false;
  }

  for (const raw of lines) {
    const line = raw.trimRight();
    if (line.trim() === '') { inAddress = false; continue; }

    const startPerson = /^(?:N|Name)\s*[:\-—|]/i.test(line);
    const startCompany = /^(?:C|Company)\s*[:\-—|]\s*$/i.test(line); // bare "C:" opens company block
    if (startPerson || startCompany) {
      if (cur) push();
      cur = { kind: startPerson ? 'person' : 'company', emails: [], mobile: [], office: [], sourceNote: relNote };
    }
    if (!cur) continue;

    if (inAddress && !keyed.test(line)) {
      cur.address = (cur.address ? cur.address + '\n' : '') + line.trim();
      continue;
    } else if (inAddress && keyed.test(line)) {
      inAddress = false;
    }

    let m: RegExpMatchArray | null;
    if (m = line.match(/^(?:N|Name)\s*[:\-—|]\s*(.+)$/i)) cur.full_name = m[1].trim();
    else if (m = line.match(/^(?:T|Title)\s*[:\-—|]\s*(.+)$/i)) cur.title = m[1].trim();
    else if (m = line.match(/^(?:E|Email)\s*[:\-—|]\s*(.+)$/i)) {
      const emails = m[1].split(/[,;\s]+/).map(s => s.trim().toLowerCase()).filter(Boolean);
      cur.emails.push(...emails);
    }
    else if (m = line.match(/^(?:M|Mobile)\s*[:\-—|]\s*(.+)$/i)) cur.mobile.push(m[1].trim());
    else if (m = line.match(/^(?:O|Office(?:\s+Number)?)\s*[:\-—|]\s*(.+)$/i)) cur.office.push(m[1].trim());
    else if (m = line.match(/^(?:C|Company)\s*[:\-—|]\s*(.+)$/i)) cur.company = (m[1] || '').trim();
    else if (m = line.match(/^(?:A|Address)\s*[:\-—|]\s*(.+)$/i)) { cur.address = (cur.address ? cur.address + '\n' : '') + m[1].trim(); inAddress = true; }
  }
  if (cur) push();
  return out;
}

function personFileName(c: ParsedContact): string {
  const name = (c.full_name || 'Unknown').trim();
  return `${name}${c.title ? ` (${c.title})` : ''}`.trim();
}

function ensureCompanyHub(company: string | undefined, HUB: string, dry: boolean): { path?: string; created: boolean } {
  if (!company) return { created: false };
  const base = path.join(HUB, '_Triage');
  const fname = `${company}.md`;
  const p = path.join(base, fname);
  if (!E(p)) {
    const fm = ['---', yamlStringify({ type: 'company', name: company, created: nowISO(), updated: '' }).trim(), '---'].join('\n');
    if (!dry) writeAtomic(p, fm + '\n\n# Company Hub\n');
    return { path: p, created: true };
  }
  return { path: p, created: false };
}

function savePerson(c: ParsedContact, PEOPLE: string, dry: boolean): { path: string; created: boolean } {
  const companyFolder = c.company ? path.join(PEOPLE, c.company) : path.join(PEOPLE, '_Triage');
  const fname = personFileName(c) + '.md';
  const p = path.join(companyFolder, fname);

  const primaryEmail = (c.emails && c.emails[0]) ? c.emails[0] : '';
  const primaryPhone = (c.mobile && c.mobile[0]) ? c.mobile[0] : ((c.office && c.office[0]) ? c.office[0] : '');

  const baseFm: any = {
    type: 'hub.people',
    person_name: c.full_name || '',
    zkid: '',
    created: nowISO(),
    updated: '',
    tags: ['person'],
    role: c.title || '',
    orgs: c.company ? [`[[${c.company}]]`] : [],
    email: primaryEmail || '',
    phone: primaryPhone || '',
    accounts: [],
    oems: [],
    contracts: [],
    notes: ''
  };

  const peopleBodyTemplate = () => `
# \`= default(this.person_name, this.file.name)\` (People)

## Overview
- Role: \`= default(this.role, "—")\`
- Orgs: \`= default(join(this.orgs, ", "), "—")\`
- Email: \`= default(this.email, "—")\`
- Phone: \`= default(this.phone, "—")\`

## Affiliations
- Accounts: \`= default(join(this.accounts, ", "), "—")\`
- OEMs: \`= default(join(this.oems, ", "), "—")\`
- Contracts: \`= default(join(this.contracts, ", "), "—")\`

## Notes
- \`= default(this.notes, "—")\`

## Related RFQs
\`\`\`dataview
TABLE rfq_id, radar_id, status, est_close, customer
FROM "60 Sources"
WHERE type = "rfq" AND contains(links, this.file.link)
\`\`\`

## Related Opportunities
\`\`\`dataview
TABLE file.link AS Opportunity, stage, radar_level, customer, contract_vehicle, est_close
FROM "40 Projects"
WHERE type = "opportunity" AND contains(links, this.file.link)
SORT est_close ASC
\`\`\`
`.trim() + '\n';

  // Create new file with template FM + body
  if (!E(p)) {
    const fm = ['---', yamlStringify(baseFm, { lineWidth: 100 }).trim(), '---'].join('\n');
    if (!dry) writeAtomic(p, fm + '\n\n' + peopleBodyTemplate());
    return { path: p, created: true };
  }

  // Update existing file: normalize to hub.people and merge fields
  const cur = R(p);
  try {
    const m = cur.match(/^---\n([\s\S]+?)\n---/);
    const afterFm = m ? cur.slice(m[0].length) : cur;
    const obj: any = m ? (yamlParse(m[1]) || {}) : {};

    // If legacy or missing, transform to new schema
    const out: any = (obj && obj.type === 'hub.people') ? { ...obj } : { ...baseFm, created: obj.created || baseFm.created };

    // Ensure required fields/sane defaults
    out.type = 'hub.people';
    out.tags = Array.isArray(out.tags) ? Array.from(new Set([...out.tags, 'person'])) : ['person'];

    // Merge values from parsed contact
    if (!out.person_name && c.full_name) out.person_name = c.full_name;
    if (!out.role && c.title) out.role = c.title;

    // Orgs as wiki links
    const wikiCompany = c.company ? `[[${c.company}]]` : undefined;
    out.orgs = Array.isArray(out.orgs) ? out.orgs : (out.orgs ? [out.orgs] : []);
    if (wikiCompany && !out.orgs.includes(wikiCompany)) out.orgs.push(wikiCompany);

    if ((!out.email || out.email === '') && primaryEmail) out.email = primaryEmail;
    if ((!out.phone || out.phone === '') && primaryPhone) out.phone = primaryPhone;

    // Preserve created if present; bump updated timestamp
    out.created = out.created || baseFm.created;
    out.updated = nowISO();

    // Rebuild FM with explicit key order matching template
    const fmNewObj: any = {
      type: 'hub.people',
      person_name: out.person_name || '',
      zkid: out.zkid || '',
      created: out.created || baseFm.created,
      updated: out.updated || '',
      tags: out.tags || ['person'],
      role: out.role || '',
      orgs: out.orgs || [],
      email: out.email || '',
      phone: out.phone || '',
      accounts: out.accounts || [],
      oems: out.oems || [],
      contracts: out.contracts || [],
      notes: out.notes || ''
    };
    const fmNew = ['---', yamlStringify(fmNewObj, { lineWidth: 100 }).trim(), '---'].join('\n');

    // Always enforce People display template body
    const bodyOut = '\n' + peopleBodyTemplate();

    if (!dry) writeAtomic(p, fmNew + bodyOut);
  } catch {
    // If anything goes wrong, do not corrupt existing file
  }
  return { path: p, created: false };
}

// People index for attendee linking
function buildPeopleIndex(PEOPLE: string): Record<string, string> {
  const idx: Record<string, string> = {};
  function addDir(dir: string) {
    if (!E(dir)) return;
    for (const e of fs.readdirSync(dir)) {
      const p = path.join(dir, e);
      const st = fs.statSync(p);
      if (st.isDirectory()) addDir(p);
      else if (st.isFile() && e.toLowerCase().endsWith('.md')) {
        const name = e.replace(/\.md$/i, '');
        const plain = name.replace(/\(.+?\)$/, '').trim().toLowerCase();
        idx[plain] = name;
      }
    }
  }
  addDir(PEOPLE);
  return idx;
}

function linkifyAttendees(att: string[], idx: Record<string, string>): string[] {
  return att.map(raw => {
    // Support optional suffix " - Role - Org" (or with em dash)
    const parts = raw.split(/\s+[—-]\s+/);
    const namePart = (parts[0] || raw).trim();
    const extraSuffix = parts.slice(1).join(' - ').trim();

    const key = namePart.replace(/\(.+?\)$/, '').trim().toLowerCase();
    const fileName = idx[key];

    let link = fileName ? `[[${fileName}]]` : namePart;

    // If no suffix provided, try to derive Title from People filename "(Title)"
    let suffix = extraSuffix;
    if (!suffix && fileName) {
      const m = fileName.match(/\((.+?)\)$/);
      if (m) suffix = m[1];
    }

    return suffix ? `${link} - ${suffix}` : link;
  });
}

// Meeting writers
function fmMeeting(opts: { title: string; date: string; time?: string; attendees: string[]; links: string[]; followup?: string; }): string {
  const fm: any = {
    type: 'meeting',
    title: opts.title,
    date: opts.date,
    time: opts.time || '',
    attendees: opts.attendees,
    customer: '',
    opportunity: null,
    oems: [],
    distributors: [null],
    contract: null,
    contract_office: null,
    tags: ['meeting'],
    status: 'open'
  };
  return ['---', yamlStringify(fm, { lineWidth: 100 }).trim(), '---'].join('\n');
}

function bodyMeeting(discussion?: string[], extra?: { heading: string; lines: string[] }[], tasks?: string[]) {
  const discLines = (discussion || []).map(l => l.trim()).filter(Boolean);
  // Use first non-bullet line as a summary if available; else first line (without bullet); else em dash
  const summary = discLines.find(l => !/^\s*[-*]/.test(l)) || (discLines[0] ? discLines[0].replace(/^\s*[-*]\s*/, '') : '—');
  const notesSection = discLines.join('\n');

  // Convert unchecked checkbox tasks into numbered ACTIONS list
  const numberedActions = (tasks || []).map((t, i) => `${i + 1}. ${t.replace(/^\s*-\s*\[\s\]\s*/, '').trim()}`);

  // Preserve any additional H3 sections under their headings (before Notes / Discussion)
  const extraBlocks = (extra || []).map(e => `### ${e.heading}\n${e.lines.join('\n')}`).join('\n\n');

  return [
    '### Summary',
    summary || '—',
    '',
    extraBlocks ? extraBlocks + '\n' : '',
    '### Notes / Discussion',
    notesSection || '—',
    '',
    '### ACTIONS',
    numberedActions.length ? numberedActions.join('\n') : '—',
    '',
    '### TARGETS / FOLLOW UPS',
    '- —',
    ''
  ].join('\n');
}

function nextAvailablePath(dir: string, baseName: string): string {
  const ext = '.md';
  const base = baseName.replace(/\.md$/i, '');
  let candidate = path.join(dir, base + ext);
  if (!E(candidate)) return candidate;
  let n = 1;
  while (true) {
    candidate = path.join(dir, `${base}-${n}${ext}`);
    if (!E(candidate)) return candidate;
    n++;
  }
}

// Tasks / Subtasks integration
function ensureSection(txt: string, heading: string): string {
  if (new RegExp(`^##\\s*${heading}\\s*$`, 'mi').test(txt)) return txt;
  return `${txt.trim()}\n\n## ${heading}\n`;
}

function existingBacklog(todoTxt: string): Set<string> {
  const set = new Set<string>();
  const lines = todoTxt.split(/\r?\n/);
  let i = lines.findIndex(l => /^##\s*Backlog\s*$/.test(l));
  if (i === -1) return set;
  i++;
  while (i < lines.length && !/^##\s+/.test(lines[i])) {
    const ln = lines[i];
    const m = ln.match(/^- \[ \]\s+(.*)$/);
    if (m) set.add(m[1].trim().toLowerCase());
    i++;
  }
  return set;
}

function appendBacklog(todoPath: string, tasks: string[], context: { date: string; source: string }, dry: boolean): number {
  if (tasks.length === 0) return 0;
  let txt = E(todoPath) ? R(todoPath) : '';
  txt = ensureSection(txt, 'Backlog');
  const existing = existingBacklog(txt);
  const toAdd: string[] = [];
  for (const t of tasks) {
    const body = t.replace(/^\s*- \[ \]\s+/, '');
    if (!existing.has(body.trim().toLowerCase())) {
      toAdd.push(`- [ ] ${body} — ${context.date} [[${context.source}]]`);
    }
  }
  if (toAdd.length === 0) { if (!dry) writeAtomic(todoPath, txt); return 0; }
  const newTxt = txt.replace(/^##\s*Backlog\s*$/mi, m => `${m}\n${toAdd.join('\n')}\n`);
  if (!dry) writeAtomic(todoPath, newTxt);
  return toAdd.length;
}

function sweepCompleted(todoPath: string, dry: boolean): number {
  if (!E(todoPath)) return 0;
  let txt = R(todoPath);
  txt = ensureSection(txt, '📌 Completed (General Backlog)');
  const lines = txt.split(/\r?\n/);
  const start = lines.findIndex(l => /^##\s*Backlog\s*$/.test(l));
  if (start === -1) { if (!dry) writeAtomic(todoPath, txt); return 0; }
  let i = start + 1; const idxs: number[] = [];
  while (i < lines.length && !/^##\s+/.test(lines[i])) { if (/^- \[[xX]\]\s+/.test(lines[i])) idxs.push(i); i++; }
  if (idxs.length === 0) return 0;
  const completed = idxs.map(n => lines[n]);
  for (let k = idxs.length - 1; k >= 0; k--) lines.splice(idxs[k], 1);
  const stamp = nowISO();
  const compIdx = lines.findIndex(l => /^##\s*📌 Completed \(General Backlog\)\s*$/.test(l));
  if (compIdx !== -1) lines.splice(compIdx + 1, 0, `\n> Moved on ${stamp}`, ...completed, '');
  else lines.push('\n## 📌 Completed (General Backlog)', `> Moved on ${stamp}`, ...completed, '');
  const out = lines.join('\n');
  if (!dry) writeAtomic(todoPath, out);
  return completed.length;
}

// State
type StateRecord = Record<string, { hash: string; processed_at: string }>;
function loadState(STATE: string): StateRecord { try { return JSON.parse(R(STATE)); } catch { return {}; } }
function saveState(STATE: string, s: any, dry: boolean) { if (!dry) writeAtomic(STATE, JSON.stringify(s, null, 2)); }
function lastProcessedAt(state: StateRecord): string | undefined {
  const times = Object.values(state).map(v => v.processed_at).filter(Boolean).sort();
  return times.length ? times[times.length - 1].slice(0, 10) : undefined;
}

// Audit
function appendAudit(REVIEW: string, scope: string, res: Result, dry: boolean) {
  const stamp = nowISO();
  const lines = [
    '## Fleeting Processing Audit',
    `- When: ${stamp}`,
    `- Scope: ${scope}`,
    `- Meetings created: ${res.meetings_created}`,
    `- Meetings updated: ${res.meetings_updated}`,
    `- Contacts created: ${res.contacts_created}`,
    `- Contacts updated: ${res.contacts_updated}`,
    `- Contacts triaged: ${res.contacts_triaged}`,
    `- Company hubs created: ${res.company_hubs_created}`,
    `- Tasks added to Backlog: ${res.tasks_added}`,
    `- Tasks moved to Completed: ${res.tasks_moved_to_completed}`,
    `- Notes processed: ${res.processed_notes}`,
    `- Notes skipped (unchanged): ${res.skipped_notes}`,
    '',
  ].join('\n');
  const cur = E(REVIEW) ? R(REVIEW) : '# Review Queue\n';
  if (!dry) writeAtomic(REVIEW, cur + '\n' + lines);
}

// Per-note processing
function processNote(
  file: string,
  peopleIdx: Record<string, string>,
  paths: ReturnType<typeof getFleetingPaths>,
  dry: boolean
): { res: Partial<Result>; stateHash: string } {
  const { MEET, TODO, HUB, PEOPLE } = paths;
  const md = R(file);
  const date = deriveDate(file) || '';
  const title = path.basename(file, '.md');

  // meetings
  const blocks = parseMeetings(md);
  let meetings_created = 0, meetings_updated = 0;
  for (const b of blocks) {
    const baseName = `${date} Meeting ${b.subject}`.replace(/[\\/:*?"<>|]/g, '-') + '.md';
    const outDir = MEET; fs.mkdirSync(outDir, { recursive: true });
    let outPath = path.join(outDir, baseName);
    const linkedAtt = linkifyAttendees(b.attendees || [], peopleIdx);
    const fm = fmMeeting({ title: b.subject, date, time: b.time, attendees: linkedAtt, links: b.links || [], followup: b.followup });
    const body = bodyMeeting(b.discussion, b.extra, b.tasks);
    if (!E(outPath)) { if (!dry) writeAtomic(outPath, `${fm}\n${body}`); meetings_created++; }
    else {
      const alt = nextAvailablePath(outDir, baseName);
      if (alt !== outPath) { if (!dry) writeAtomic(alt, `${fm}\n${body}`); meetings_created++; outPath = alt; }
      else { if (!dry) appendAtomic(outPath, `\n\n---\n## Notes (${nowISO()})\n${(b.discussion || []).join('\n')}\n`); meetings_updated++; }
    }
  }

  // tasks anywhere (unchecked)
  const allTasks = (md.match(/^\s*- \[ \]\s+.*$/gmi) || []).map(s => s);
  const tasks_added = appendBacklog(TODO, allTasks, { date, source: title }, dry);
  const tasks_moved_to_completed = sweepCompleted(TODO, dry);

  // contacts
  const parsed = parseContacts(md, title);
  let contacts_created = 0, contacts_updated = 0, contacts_triaged = 0, company_hubs_created = 0;
  for (const c of parsed) {
    if (c.kind === 'person') {
      const hub = ensureCompanyHub(c.company, HUB, dry);
      if (hub.created) company_hubs_created++;
      const res = savePerson(c, PEOPLE, dry);
      if (res.created) contacts_created++; else contacts_updated++;
      if (!c.company) contacts_triaged++;
    } else if (c.kind === 'company') {
      const hub = ensureCompanyHub(c.company, HUB, dry);
      if (hub.created) company_hubs_created++;
    }
  }

  const stateHash = H(md);
  return {
    res: {
      meetings_created, meetings_updated,
      tasks_added, tasks_moved_to_completed,
      contacts_created, contacts_updated, contacts_triaged, company_hubs_created,
    },
    stateHash
  };
}

function listMarkdown(entry: string): string[] {
  const acc: string[] = [];
  const st = fs.statSync(entry);
  if (st.isFile() && entry.toLowerCase().endsWith('.md')) return [entry];
  function walk(dir: string) {
    for (const e of fs.readdirSync(dir)) {
      const p = path.join(dir, e);
      const st2 = fs.statSync(p);
      if (st2.isDirectory()) walk(p);
      else if (st2.isFile() && e.toLowerCase().endsWith('.md')) acc.push(p);
    }
  }
  if (st.isDirectory()) walk(entry);
  return acc;
}

export async function runFleetingProcessor(options: FleetingOptions): Promise<FleetingSummary> {
  const dry = options.dryRun === true;
  const force = options.force === true;
  const paths = getFleetingPaths(options.targetDir);
  const { DAILY, STATE, REVIEW, PEOPLE } = paths;

  // Load and compute range
  const state = loadState(STATE);
  const since = lastProcessedAt(state);
  const range = resolveRange(options.scope, options.range, since, new Date());

  const files = listMarkdown(DAILY);

  const peopleIdx = buildPeopleIndex(PEOPLE);
  const summary: Result = {
    meetings_created: 0, meetings_updated: 0, contacts_created: 0, contacts_updated: 0,
    contacts_triaged: 0, company_hubs_created: 0, tasks_added: 0, tasks_moved_to_completed: 0,
    skipped_notes: 0, processed_notes: 0,
  };

  for (const f of files) {
    const date = deriveDate(f);
    if (!date || !dateInRange(date, range.start, range.end)) continue;

    const md = R(f);
    const h = H(md);
    const prev = state[f];
    if (!force && prev && prev.hash === h) { summary.skipped_notes++; continue; }

    try {
      const { res, stateHash } = processNote(f, peopleIdx, paths, dry);
      summary.meetings_created += res.meetings_created || 0;
      summary.meetings_updated += res.meetings_updated || 0;
      summary.contacts_created += res.contacts_created || 0;
      summary.contacts_updated += res.contacts_updated || 0;
      summary.contacts_triaged += res.contacts_triaged || 0;
      summary.company_hubs_created += res.company_hubs_created || 0;
      summary.tasks_added += res.tasks_added || 0;
      summary.tasks_moved_to_completed += res.tasks_moved_to_completed || 0;
      summary.processed_notes++;
      state[f] = { hash: stateHash, processed_at: nowISO() };
    } catch (e: any) {
      logger.error('Fleeting note processing failed', { file: f, error: e?.message || String(e) });
    }
  }

  // Audit & state
  appendAudit(REVIEW, range.label, summary, dry);
  saveState(STATE, state, dry);

  return { scope: range.label, dryRun: dry, state_path: STATE, ...summary };
}

/** =======================
 *  Upgrade existing notes
 *  ======================= */
export interface UpgradeOptions {
  upgradePeople?: boolean;
  upgradeMeetings?: boolean;
  targetDir?: string;   // not used for scanning (we scan PEOPLE_DIR/MEET), but kept for future
  dryRun?: boolean;
}

function splitFrontmatter(txt: string): { fm: any | null; fmRaw: string; body: string } {
  const m = txt.match(/^---\n([\s\S]*?)\n---\n?/);
  if (!m) return { fm: null, fmRaw: '', body: txt };
  let obj: any = null;
  try { obj = yamlParse(m[1]) || {}; } catch { obj = {}; }
  const body = txt.slice(m[0].length);
  return { fm: obj, fmRaw: m[1], body };
}

function isWikiLink(s: string): boolean { return /^\s*\[\[.+\]\]\s*$/.test(s || ''); }
function toWikiLink(s?: string): string {
  if (!s) return '';
  return isWikiLink(s) ? s : `[[${s}]]`;
}

function peopleBodyTemplateForUpgrade(): string {
  return [
    '# `= default(this.person_name, this.file.name)` (People)',
    '',
    '## Overview',
    '- Role: `= default(this.role, "—")`',
    '- Orgs: `= default(join(this.orgs, ", "), "—")`',
    '- Email: `= default(this.email, "—")`',
    '- Phone: `= default(this.phone, "—")`',
    '',
    '## Affiliations',
    '- Accounts: `= default(join(this.accounts, ", "), "—")`',
    '- OEMs: `= default(join(this.oems, ", "), "—")`',
    '- Contracts: `= default(join(this.contracts, ", "), "—")`',
    '',
    '## Notes',
    '- `= default(this.notes, "—")`',
    '',
    '## Related RFQs',
    '```dataview',
    'TABLE rfq_id, radar_id, status, est_close, customer',
    'FROM "60 Sources"',
    'WHERE type = "rfq" AND contains(links, this.file.link)',
    '```',
    '',
    '## Related Opportunities',
    '```dataview',
    'TABLE file.link AS Opportunity, stage, radar_level, customer, contract_vehicle, est_close',
    'FROM "40 Projects"',
    'WHERE type = "opportunity" AND contains(links, this.file.link)',
    'SORT est_close ASC',
    '```',
    ''
  ].join('\n');
}

function walkDir(dir: string): string[] {
  const acc: string[] = [];
  if (!E(dir)) return acc;
  const st = fs.statSync(dir);
  if (st.isFile() && dir.toLowerCase().endsWith('.md')) return [dir];
  function rec(d: string) {
    for (const e of fs.readdirSync(d)) {
      const p = path.join(d, e);
      const st2 = fs.statSync(p);
      if (st2.isDirectory()) rec(p);
      else if (st2.isFile() && p.toLowerCase().endsWith('.md')) acc.push(p);
    }
  }
  if (st.isDirectory()) rec(dir);
  return acc;
}

function normalizePeopleFile(p: string, dry: boolean): boolean {
  const txt = R(p);
  const { fm, body } = splitFrontmatter(txt);

  // Build new FM from existing data
  const nameFromFile = path.basename(p, '.md').replace(/\(.+?\)$/, '').trim();
  const primaryEmail = (fm?.email) || (Array.isArray(fm?.emails) ? (fm.emails[0] || '') : '');
  const primaryPhone = fm?.phone || (Array.isArray(fm?.mobile) ? (fm.mobile[0] || '') : (Array.isArray(fm?.office) ? (fm.office[0] || '') : ''));

  const orgsRaw = Array.isArray(fm?.orgs) ? fm.orgs : (fm?.company ? [fm.company] : []);
  const orgs = orgsRaw.map((s: string) => toWikiLink(s)).filter(Boolean);

  const out: any = {
    type: 'hub.people',
    person_name: fm?.person_name || fm?.name || nameFromFile,
    zkid: fm?.zkid || '',
    created: fm?.created || nowISO(),
    updated: nowISO(),
    tags: Array.isArray(fm?.tags) ? Array.from(new Set([...fm.tags, 'person'])) : ['person'],
    role: fm?.role || fm?.title || '',
    orgs,
    email: primaryEmail || '',
    phone: primaryPhone || '',
    accounts: Array.isArray(fm?.accounts) ? fm.accounts : [],
    oems: Array.isArray(fm?.oems) ? fm.oems : [],
    contracts: Array.isArray(fm?.contracts) ? fm.contracts : [],
    notes: fm?.notes || ''
  };

  const fmNew = ['---', yamlStringify(out, { lineWidth: 100 }).trim(), '---'].join('\n');
  const hasPeopleHeader = /# `= default\(this\.person_name, this\.file\.name\)` \(People\)/.test(body);
  const bodyOut = hasPeopleHeader ? body : ('\n' + peopleBodyTemplateForUpgrade());

  const next = fmNew + bodyOut;
  const changed = next !== txt;
  if (changed && !dry) writeAtomic(p, next);
  return changed;
}

function extractDiscussionFromBody(body: string): { discussion: string[]; tasks: string[] } {
  const lines = body.split(/\r?\n/);
  // Try to isolate "## Notes" (or "## Notes / Discussion") section, else use full body
  let start = lines.findIndex(l => /^##\s*Notes(?:\s*\/\s*Discussion)?\s*$/i.test(l));
  if (start === -1) start = 0;
  let end = lines.length;
  for (let i = start + 1; i < lines.length; i++) {
    if (/^##\s+/.test(lines[i])) { end = i; break; }
  }
  const disc = lines.slice(start === 0 ? 0 : start + 1, end).map(l => l.trim());
  const tasks = body.match(/^\s*-\s*\[\s\]\s+.*$/gmi)?.map(s => s.trim()) || [];
  return { discussion: disc, tasks };
}

function normalizeMeetingFile(p: string, peopleIdx: Record<string, string>, dry: boolean): boolean {
  const txt = R(p);
  const { fm, body } = splitFrontmatter(txt);

  // Build new FM per preferred schema
  const attendeesRaw: string[] = Array.isArray(fm?.attendees) ? fm.attendees : [];
  const attendees = linkifyAttendees(attendeesRaw, peopleIdx);

  const out: any = {
    type: 'meeting',
    title: fm?.title || path.basename(p, '.md'),
    date: fm?.date || deriveDate(p) || '',
    time: (fm?.time || '').toString(),
    attendees,
    customer: fm?.customer || '',
    opportunity: fm?.opportunity ?? null,
    oems: Array.isArray(fm?.oems) ? fm.oems : [],
    distributors: Array.isArray(fm?.distributors) ? fm.distributors : [null],
    contract: fm?.contract ?? null,
    contract_office: fm?.contract_office ?? null,
    tags: Array.isArray(fm?.tags) ? Array.from(new Set([...fm.tags, 'meeting'])) : ['meeting'],
    status: fm?.status || 'open'
  };

  const fmNew = ['---', yamlStringify(out, { lineWidth: 100 }).trim(), '---'].join('\n');

  // Regenerate body from existing content
  const { discussion, tasks } = extractDiscussionFromBody(body || '');
  const newBody = '\n' + bodyMeeting(discussion, [], tasks);
  const next = fmNew + newBody;

  const changed = next !== txt;
  if (changed && !dry) writeAtomic(p, next);
  return changed;
}

export async function upgradeExisting(opts: UpgradeOptions): Promise<{
  dryRun: boolean;
  people_scanned: number;
  people_upgraded: number;
  meetings_scanned: number;
  meetings_upgraded: number;
}> {
  const dry = opts.dryRun === true;
  const paths = getFleetingPaths(opts.targetDir);
  const { PEOPLE, MEET } = paths;

  let people_scanned = 0, people_upgraded = 0;
  if (opts.upgradePeople !== false) {
    const peopleFiles = walkDir(PEOPLE);
    for (const f of peopleFiles) {
      people_scanned++;
      try { if (normalizePeopleFile(f, dry)) people_upgraded++; } catch (e:any) { logger.error('upgrade people failed', { file: f, error: e?.message || String(e) }); }
    }
  }

  let meetings_scanned = 0, meetings_upgraded = 0;
  if (opts.upgradeMeetings !== false) {
    const peopleIdx = buildPeopleIndex(PEOPLE);
    const meetingFiles = walkDir(MEET);
    for (const f of meetingFiles) {
      meetings_scanned++;
      try { if (normalizeMeetingFile(f, peopleIdx, dry)) meetings_upgraded++; } catch (e:any) { logger.error('upgrade meetings failed', { file: f, error: e?.message || String(e) }); }
    }
  }

  return { dryRun: dry, people_scanned, people_upgraded, meetings_scanned, meetings_upgraded };
}