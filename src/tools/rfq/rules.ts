import { getDb } from '../../database/init.js';
import { logger } from '../../utils/logger.js';

// Types
export type ScoreResult = {
  score: number;
  recommendation: string;
  factors: string[];
  tier: string;
};

export type OemBusinessCaseResult = {
  oem: string;
  score: number;
  recommendation: string;
  action: string;
  reasons: string[];
  metrics: {
    occurrences_90d: number;
    total_value_90d: number;
    unique_customers: number;
    avg_competition: number;
  };
};

export type RuleOutcome =
  | { rule_id: string; name: string; action: 'AUTO_DECLINE'; reason?: string }
  | { rule_id: string; name: string; action: 'AUTO_DECLINE_AND_LOG'; reason?: string; pattern_note?: string }
  | { rule_id: string; name: string; action: 'LOG_AND_TRACK'; reason?: string; threshold?: number }
  | { rule_id: string; name: string; action: 'STRATEGIC_REVIEW' | 'FLAG_FOR_REVIEW'; priority?: 'HIGH' | 'MEDIUM'; note?: string }
  | { rule_id: string; name: string; action: 'IMMEDIATE_ALERT' | 'ALERT'; priority?: 'CRITICAL' | 'HIGH'; notify?: string[] }
  | { rule_id: string; name: string; action: 'PASS' | 'CONSIDER_DECLINE'; note?: string }
  | { rule_id: string; name: string; action: 'RENEWAL_FLAG' }
  | { rule_id: string; name: string; action: 'TECH_FLAG' };

function lc(s?: string) {
  return (s || '').toLowerCase();
}

// ----- Default constants as fallback if DB seed not present -----
const DEFAULT_STRATEGIC = {
  CRITICAL: [
    'AFCENT',
    'ARCENT',
    'US CYBERCOMMAND',
    'AFSOC',
    'USSOCOM',
    'Space Force',
    'DARPA',
  ],
  HIGH: [
    'AETC',
    'Hill AFB',
    'Eglin AFB',
    'Tyndall AFB',
    'Patrick AFB',
    'Andrews AFB',
    'Bolling AFB',
    'AFOSI',
  ],
};

const DEFAULT_THRESHOLDS = [
  { tier_name: 'TIER_1_CRITICAL', min_value: 1_000_000, max_value: null as number | null, action: 'IMMEDIATE_EXECUTIVE_NOTIFICATION', priority_level: 'CRITICAL' },
  { tier_name: 'TIER_2_HIGH', min_value: 200_000, max_value: 999_999, action: 'SALES_TEAM_NOTIFICATION', priority_level: 'HIGH' },
  { tier_name: 'TIER_3_REVIEW', min_value: 20_000, max_value: 199_999, action: 'FLAG_FOR_REVIEW', priority_level: 'MEDIUM' },
  { tier_name: 'TIER_4_LOW', min_value: 0, max_value: 19_999, action: 'STANDARD_PROCESS', priority_level: 'LOW' },
];

const DEFAULT_TECH = {
  HIGH: ['Zero Trust', 'Data Center', 'Enterprise Networking', 'Cybersecurity'],
  MEDIUM: ['Cloud Migration', 'AI/ML Infrastructure', 'SIEM/Security Analytics', 'SD-WAN', 'Hybrid Cloud', 'Storage/Infrastructure', 'Application Delivery'],
};

const DEFAULT_AUTH_OEMS = ['Cisco', 'Palo Alto Networks', 'Dell/EMC', 'NetApp', 'F5 Networks', 'Microsoft', 'VMware', 'Red Hat'];

// ----- DB-backed config helpers with safe fallbacks -----
function fetchStrategicList(): { name: string; priority: 'CRITICAL' | 'HIGH' }[] {
  try {
    const db = getDb();
    const res = db.exec("SELECT customer_name, priority_level FROM config_strategic_customers");
    if (!res.length || !res[0].values.length) throw new Error('empty');
    const rows: { name: string; priority: 'CRITICAL' | 'HIGH' }[] = [];
    const cols = res[0].columns;
    for (const v of res[0].values) {
      const obj: any = {};
      cols.forEach((c, i) => (obj[c] = v[i]));
      rows.push({ name: obj.customer_name, priority: (obj.priority_level || 'HIGH') as any });
    }
    return rows;
  } catch {
    return [
      ...DEFAULT_STRATEGIC.CRITICAL.map((n) => ({ name: n, priority: 'CRITICAL' as const })),
      ...DEFAULT_STRATEGIC.HIGH.map((n) => ({ name: n, priority: 'HIGH' as const })),
    ];
  }
}

function fetchThresholds(): { tier_name: string; min_value: number; max_value: number | null }[] {
  try {
    const db = getDb();
    const res = db.exec("SELECT tier_name, min_value, max_value FROM config_value_thresholds");
    if (!res.length || !res[0].values.length) throw new Error('empty');
    const cols = res[0].columns;
    const rows = res[0].values.map((v) => {
      const obj: any = {};
      cols.forEach((c, i) => (obj[c] = v[i]));
      return { tier_name: obj.tier_name, min_value: Number(obj.min_value), max_value: obj.max_value === null ? null : Number(obj.max_value) };
    });
    // Ensure descending by min_value
    rows.sort((a, b) => (b.min_value - a.min_value));
    return rows;
  } catch {
    const rows = DEFAULT_THRESHOLDS.map((t) => ({ tier_name: t.tier_name, min_value: t.min_value, max_value: t.max_value }));
    rows.sort((a, b) => (b.min_value - a.min_value));
    return rows;
  }
}

function fetchTechPriority(): { high: string[]; medium: string[] } {
  try {
    const db = getDb();
    const res = db.exec("SELECT vertical_name, priority_level FROM config_technology_verticals");
    if (!res.length || !res[0].values.length) throw new Error('empty');
    const cols = res[0].columns;
    const high: string[] = [];
    const medium: string[] = [];
    for (const v of res[0].values) {
      const obj: any = {};
      cols.forEach((c, i) => (obj[c] = v[i]));
      if (String(obj.priority_level).toUpperCase() === 'HIGH') high.push(obj.vertical_name);
      else medium.push(obj.vertical_name);
    }
    return { high, medium };
  } catch {
    return { high: DEFAULT_TECH.HIGH.slice(), medium: DEFAULT_TECH.MEDIUM.slice() };
  }
}

function isAuthorizedOem(oem?: string): boolean {
  if (!oem) return false;
  try {
    const db = getDb();
    const res = db.exec(`SELECT currently_authorized FROM config_oem_tracking WHERE LOWER(oem_name)=LOWER('${oem.replace(/'/g, "''")}') LIMIT 1`);
    if (res.length && res[0].values.length) {
      const idx = res[0].columns.indexOf('currently_authorized');
      const val = res[0].values[0][idx];
      return Number(val) === 1;
    }
  } catch {
    // ignore
  }
  // Fallback list
  return DEFAULT_AUTH_OEMS.map(lc).includes(lc(oem));
}

/** Check if a contract vehicle is in the supported list */
function isSupportedContract(vehicle?: string): boolean {
  if (!vehicle) return false;
  try {
    const db = getDb();
    const res = db.exec(`SELECT supported FROM config_contract_vehicles WHERE LOWER(vehicle_name)=LOWER('${vehicle.replace(/'/g, "''")}') LIMIT 1`);
    if (res.length && res[0].values.length) {
      const idx = res[0].columns.indexOf('supported');
      const val = res[0].values[0][idx];
      return Number(val) === 1;
    }
  } catch {
    // ignore
  }
  return false;
}

function getNewBusinessOemThreshold(oem?: string): number | null {
  if (!oem) return null;
  try {
    const db = getDb();
    const res = db.exec(`SELECT business_case_threshold FROM config_oem_tracking WHERE LOWER(oem_name)=LOWER('${oem.replace(/'/g, "''")}') AND currently_authorized=0 LIMIT 1`);
    if (res.length && res[0].values.length) {
      const idx = res[0].columns.indexOf('business_case_threshold');
      return Number(res[0].values[0][idx]);
    }
  } catch {
    // ignore
  }
  // Fallback thresholds
  const fallback: Record<string, number> = {
    'atlassian': 5,
    'graylog': 5,
    'logrhythm': 5,
    'sparx': 8,
    'quest/toad': 5,
  };
  return fallback[lc(oem)] ?? null;
}

// ----- Strategic customer helpers -----
function getStrategicPriority(customer?: string): 'CRITICAL' | 'HIGH' | null {
  if (!customer) return null;
  const list = fetchStrategicList();
  const target = lc(customer);
  for (const row of list) {
    if (target.includes(lc(row.name))) {
      return row.priority;
    }
  }
  return null;
}

export function isStrategicCustomer(customer?: string): boolean {
  return getStrategicPriority(customer) !== null;
}

// ----- Value tier -----
export function getValueTier(value: number): string {
  const thresholds = fetchThresholds();
  for (const t of thresholds) {
    if (t.max_value === null) {
      if (value >= t.min_value) return t.tier_name;
    } else if (value >= t.min_value && value <= t.max_value) {
      return t.tier_name;
    }
  }
  return 'TIER_4_LOW';
}

// ----- Scoring -----
export function calculateRfqScore(args: {
  value: number;
  competition: number;
  customer?: string;
  tech_vertical?: string;
  oem?: string;
  has_previous_contract?: boolean;
  contract_vehicle?: string;
}): ScoreResult {
  const factors: string[] = [];
  let score = 0;

  // Value
  const tier = getValueTier(args.value || 0);
  const valueScores: Record<string, number> = {
    TIER_1_CRITICAL: 40,
    TIER_2_HIGH: 30,
    TIER_3_REVIEW: 20,
    TIER_4_LOW: 10,
  };
  score += valueScores[tier] ?? 0;
  factors.push(`Value: ${tier} (+${valueScores[tier] ?? 0})`);

  // Customer priority
  const pr = getStrategicPriority(args.customer);
  if (pr === 'CRITICAL') {
    score += 25;
    factors.push('Customer: CRITICAL (+25)');
  } else if (pr === 'HIGH') {
    score += 15;
    factors.push('Customer: HIGH (+15)');
  } else {
    factors.push('Customer: Standard (+0)');
  }

  // Competition
  const comp = Number(args.competition || 0);
  if (comp < 20) {
    score += 15;
    factors.push('Competition: Low (<20) (+15)');
  } else if (comp < 50) {
    score += 10;
    factors.push('Competition: Medium (<50) (+10)');
  } else if (comp < 100) {
    score += 5;
    factors.push('Competition: High (<100) (+5)');
  } else {
    factors.push(`Competition: Very High (${comp}) (+0)`);
  }

  // Tech vertical
  const techCfg = fetchTechPriority();
  if (args.tech_vertical && techCfg.high.includes(args.tech_vertical)) {
    score += 10;
    factors.push('Tech: High Priority (+10)');
  } else if (args.tech_vertical && techCfg.medium.includes(args.tech_vertical)) {
    score += 5;
    factors.push('Tech: Medium Priority (+5)');
  } else {
    factors.push('Tech: Standard (+0)');
  }

  // OEM relationship
  if (isAuthorizedOem(args.oem)) {
    score += 10;
    factors.push('OEM: Authorized Partner (+10)');
  } else {
    factors.push('OEM: Not authorized (+0)');
  }

  // Contract vehicle support
  const vehicle = args.contract_vehicle || '';
  if (vehicle && isSupportedContract(vehicle)) {
    score += 5;
    factors.push('Contract: Supported (+5)');
  } else if (vehicle) {
    factors.push('Contract: Not in supported list (+0)');
  }

  // Renewal
  if (args.has_previous_contract) {
    score += 10;
    factors.push('Renewal: Existing Customer (+10)');
  }

  let recommendation: string;
  if (score >= 75) recommendation = 'GO - High Priority';
  else if (score >= 60) recommendation = 'GO - Consider Pursuit';
  else if (score >= 45) recommendation = 'REVIEW - Conditional GO';
  else if (score >= 30) recommendation = 'REVIEW - Likely NO-GO';
  else recommendation = 'NO-GO - Auto-Decline';

  return { score, recommendation, factors, tier };
}

// ----- OEM Business Case evaluation -----
export function evaluateNewOemBusinessCase(args: {
  oem: string;
  occurrences_90d: number;
  total_value_90d: number;
  unique_customers: number;
  avg_competition: number;
}): OemBusinessCaseResult {
  const { oem, occurrences_90d, total_value_90d, unique_customers, avg_competition } = args;
  let score = 0;
  const reasons: string[] = [];

  // Frequency
  if (occurrences_90d >= 8) {
    score += 40;
    reasons.push(`High frequency: ${occurrences_90d} RFQs in 90 days`);
  } else if (occurrences_90d >= 5) {
    score += 25;
    reasons.push(`Moderate frequency: ${occurrences_90d} RFQs in 90 days`);
  } else if (occurrences_90d >= 3) {
    score += 10;
    reasons.push(`Some frequency: ${occurrences_90d} RFQs in 90 days`);
  }

  // Value
  if (total_value_90d >= 250_000) {
    score += 40;
    reasons.push(`High value: $${total_value_90d.toLocaleString(undefined, { maximumFractionDigits: 0 })} total`);
  } else if (total_value_90d >= 100_000) {
    score += 25;
    reasons.push(`Moderate value: $${total_value_90d.toLocaleString(undefined, { maximumFractionDigits: 0 })} total`);
  } else if (total_value_90d >= 50_000) {
    score += 10;
    reasons.push(`Some value: $${total_value_90d.toLocaleString(undefined, { maximumFractionDigits: 0 })} total`);
  }

  // Customer diversity
  if (unique_customers >= 5) {
    score += 10;
    reasons.push(`Good customer diversity: ${unique_customers} customers`);
  } else if (unique_customers >= 3) {
    score += 5;
    reasons.push(`Some customer diversity: ${unique_customers} customers`);
  }

  // Competition
  if (avg_competition < 50) {
    score += 10;
    reasons.push(`Favorable competition: avg ${avg_competition} bidders`);
  }

  let recommendation: string;
  let action: string;

  if (score >= 60) {
    recommendation = 'PURSUE - Strong business case';
    action = 'Initiate partnership discussions immediately';
  } else if (score >= 40) {
    recommendation = 'CONSIDER - Moderate opportunity';
    action = 'Continue monitoring for 30 more days';
  } else if (score >= 20) {
    recommendation = 'MONITOR - Weak case currently';
    action = 'Continue tracking, reassess in 90 days';
  } else {
    recommendation = 'NO ACTION - Insufficient opportunity';
    action = 'Stop active tracking';
  }

  return {
    oem,
    score,
    recommendation,
    action,
    reasons,
    metrics: {
      occurrences_90d,
      total_value_90d,
      unique_customers,
      avg_competition,
    },
  };
}

// ----- Rule implementations (R001 - R009) -----
export function applyRuleR001(rfqSubject: string, rfqSender: string): RuleOutcome {
  const patterns = [
    'GSA eBuy Requests and Quotes/Bids (Consolidated Notice)',
    'saved search matches',
  ];
  const senders = [
    'ebuy_admin@gsa.gov',
    'opportunities@govly.com',
  ];
  const hit = patterns.some((p) => rfqSubject.includes(p)) || senders.map(lc).includes(lc(rfqSender));
  if (hit) {
    return { rule_id: 'R001', name: 'Auto-Decline Consolidated Notices', action: 'AUTO_DECLINE', reason: 'Consolidated notice' };
  }
  return { rule_id: 'R001', name: 'Auto-Decline Consolidated Notices', action: 'PASS' };
}

export function applyRuleR002(competition: number, value: number, rfqType?: string): RuleOutcome {
  const t = lc(rfqType);
  const isRenewal = t.includes('software renewal') || t.includes('license renewal') || t === 'renewal';
  const hit = competition >= 125 && value < 15_000 && isRenewal;
  if (hit) {
    return { rule_id: 'R002', name: 'High Competition Low Value', action: 'AUTO_DECLINE', reason: '125+ bidders and < $15K renewal' };
  }
  return { rule_id: 'R002', name: 'High Competition Low Value', action: 'PASS' };
}

export function applyRuleR003(oem?: string): RuleOutcome {
  const threshold = getNewBusinessOemThreshold(oem);
  if (threshold !== null) {
    return {
      rule_id: 'R003',
      name: 'Track Niche OEMs for New Business',
      action: 'LOG_AND_TRACK',
      reason: `Tracking ${oem} for potential new business line`,
      threshold,
    };
  }
  return { rule_id: 'R003', name: 'Track Niche OEMs for New Business', action: 'PASS' };
}

export function applyRuleR004(rfqType?: string, customer?: string, estimated_value: number = 0): RuleOutcome {
  const t = lc(rfqType);
  if (t === 'rfi' || t === 'market research request' || t === 'mrr') {
    const strat = isStrategicCustomer(customer || '');
    if (strat || estimated_value > 50_000) {
      return { rule_id: 'R004', name: 'RFI/MRR Strategic Review', action: 'STRATEGIC_REVIEW', priority: 'HIGH', note: 'Response recommended for future RFQ consideration' };
    }
    if (estimated_value >= 25_000) {
      return { rule_id: 'R004', name: 'RFI/MRR Strategic Review', action: 'FLAG_FOR_REVIEW', priority: 'MEDIUM', note: 'Evaluate case-by-case' };
    }
    return { rule_id: 'R004', name: 'RFI/MRR Strategic Review', action: 'CONSIDER_DECLINE', note: 'Low priority - log decision reasoning' };
  }
  return { rule_id: 'R004', name: 'RFI/MRR Strategic Review', action: 'PASS' };
}

export function applyRuleR005(value: number = 0, quantity: number = 0, rfqType?: string): RuleOutcome {
  const t = lc(rfqType);
  const isRenewal = t.includes('renewal') || t.includes('license');
  const hit = value < 2_000 || (quantity === 1 && isRenewal);
  if (hit) return { rule_id: 'R005', name: 'Ultra Low Value Auto-Decline', action: 'AUTO_DECLINE', reason: 'Ultra low value or single license renewal' };
  return { rule_id: 'R005', name: 'Ultra Low Value Auto-Decline', action: 'PASS' };
}

export function applyRuleR006(daysToDeadline: number, hasAttachments: boolean): RuleOutcome {
  if (daysToDeadline <= 2 && hasAttachments) {
    return {
      rule_id: 'R006',
      name: 'Late RFQ Auto-Decline with Pattern Tracking',
      action: 'AUTO_DECLINE_AND_LOG',
      reason: 'Insufficient time for quality response',
      pattern_note: 'Late notification - investigate source',
    };
  }
  return { rule_id: 'R006', name: 'Late RFQ Auto-Decline with Pattern Tracking', action: 'PASS' };
}

export function applyRuleR007(value: number, competition: number, customer?: string): RuleOutcome {
  const tier = getValueTier(value);
  const strat = isStrategicCustomer(customer || '');
  if (tier === 'TIER_1_CRITICAL' || (tier === 'TIER_2_HIGH' && strat)) {
    return { rule_id: 'R007', name: 'High-Value Priority Alert', action: 'IMMEDIATE_ALERT', priority: 'CRITICAL', notify: ['executive', 'sales_team'] };
  }
  if (tier === 'TIER_2_HIGH' || (tier === 'TIER_3_REVIEW' && competition < 20)) {
    return { rule_id: 'R007', name: 'High-Value Priority Alert', action: 'ALERT', priority: 'HIGH', notify: ['sales_team'] };
  }
  if (tier === 'TIER_3_REVIEW') {
    return { rule_id: 'R007', name: 'High-Value Priority Alert', action: 'FLAG_FOR_REVIEW', priority: 'MEDIUM' };
  }
  return { rule_id: 'R007', name: 'High-Value Priority Alert', action: 'PASS' };
}

export function applyRuleR008(has_previous_contract: boolean): RuleOutcome {
  if (has_previous_contract) return { rule_id: 'R008', name: 'Existing Customer Renewal Flag', action: 'RENEWAL_FLAG' };
  return { rule_id: 'R008', name: 'Existing Customer Renewal Flag', action: 'PASS' };
}

export function applyRuleR009(tech_vertical?: string, value: number = 0): RuleOutcome {
  const cfg = fetchTechPriority();
  if (tech_vertical && cfg.high.includes(tech_vertical)) {
    return { rule_id: 'R009', name: 'Strategic Technology Flag', action: 'TECH_FLAG' };
  }
  if (tech_vertical && cfg.medium.includes(tech_vertical) && value > 50_000) {
    return { rule_id: 'R009', name: 'Strategic Technology Flag', action: 'TECH_FLAG' };
  }
  return { rule_id: 'R009', name: 'Strategic Technology Flag', action: 'PASS' };
}

// ----- Utilities -----
export function computeDaysToDeadline(deadlineIso?: string): number {
  if (!deadlineIso) return Number.POSITIVE_INFINITY;
  const now = new Date();
  const due = new Date(deadlineIso);
  if (isNaN(due.getTime())) return Number.POSITIVE_INFINITY;
  const ms = due.getTime() - now.getTime();
  return Math.ceil(ms / (1000 * 60 * 60 * 24));
}

// ----- Rule aggregator -----
export function applyRulesFromInputs(args: {
  subject?: string;
  sender?: string;
  rfq_type?: string;
  competition?: number;
  value?: number;
  customer?: string;
  tech_vertical?: string;
  oem?: string;
  has_previous_contract?: boolean;
  quantity?: number;
  deadline?: string;
  has_attachments?: boolean;
}): { outcomes: RuleOutcome[]; auto_decline: boolean; auto_decline_reasons: string[] } {
  const subject = args.subject || '';
  const sender = args.sender || '';
  const rfqType = args.rfq_type || '';
  const competition = Number(args.competition || 0);
  const value = Number(args.value || 0);
  const customer = args.customer || '';
  const tech_vertical = args.tech_vertical || '';
  const oem = args.oem || '';
  const has_previous_contract = !!args.has_previous_contract;
  const quantity = Number(args.quantity || 0);
  const has_attachments = !!args.has_attachments;
  const daysToDeadline = computeDaysToDeadline(args.deadline);

  const outcomes: RuleOutcome[] = [];

  outcomes.push(applyRuleR001(subject, sender));
  outcomes.push(applyRuleR002(competition, value, rfqType));
  outcomes.push(applyRuleR003(oem));
  outcomes.push(applyRuleR004(rfqType, customer, value));
  outcomes.push(applyRuleR005(value, quantity, rfqType));
  outcomes.push(applyRuleR006(daysToDeadline, has_attachments));
  outcomes.push(applyRuleR007(value, competition, customer));
  outcomes.push(applyRuleR008(has_previous_contract));
  outcomes.push(applyRuleR009(tech_vertical, value));

  const autoReasons: string[] = [];
  for (const o of outcomes) {
    if (o.action === 'AUTO_DECLINE' || o.action === 'AUTO_DECLINE_AND_LOG') {
      if ('reason' in o && o.reason) autoReasons.push(o.reason);
      else autoReasons.push(o.name);
    }
  }

  // Respect environment flag
  const autoEnabled = String(process.env.RFQ_AUTO_DECLINE_ENABLED || '').toLowerCase() === 'true';
  const auto_decline = autoEnabled && autoReasons.length > 0;

  return { outcomes, auto_decline, auto_decline_reasons: autoReasons };
}