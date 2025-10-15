import { Tool } from '@modelcontextprotocol/sdk/types.js';
import { getDb } from '../../database/init.js';

export const analyticsTools: Tool[] = [
  {
    name: 'analytics_rfq_summary',
    description: 'Get RFQ statistics for a time period',
    inputSchema: {
      type: 'object',
      properties: {
        start_date: {
          type: 'string',
          description: 'Start date (YYYY-MM-DD)',
        },
        end_date: {
          type: 'string',
          description: 'End date (YYYY-MM-DD)',
        },
      },
    },
  },
  {
    name: 'analytics_oem_business_case_90d',
    description: 'View OEM business case rollup computed over last 90 days from v_oem_business_case_90d',
    inputSchema: {
      type: 'object',
      properties: {
        min_occurrences: { type: 'number', description: 'Minimum occurrences_90d to include', default: 0 },
        min_total_value: { type: 'number', description: 'Minimum total_value_90d to include', default: 0 }
      }
    }
  },
  {
    name: 'analytics_rule_triggers',
    description: 'Summarize RFQ rule triggers and auto-decline candidates for a period based on activity_log rules_applied entries',
    inputSchema: {
      type: 'object',
      properties: {
        start_date: { type: 'string', description: 'Start date YYYY-MM-DD' },
        end_date: { type: 'string', description: 'End date YYYY-MM-DD' }
      }
    }
  }
];

export async function handleAnalyticsTool(name: string, args: any) {
  const db = getDb();

  if (name === 'analytics_oem_business_case_90d') {
    const result = db.exec(`SELECT * FROM v_oem_business_case_90d`);
    let rows: any[] = [];
    if (result.length && result[0].values.length) {
      const cols = result[0].columns;
      rows = result[0].values.map((v) => {
        const obj: any = {};
        cols.forEach((c, i) => (obj[c] = v[i]));
        return obj;
      });
    }

    const minOcc =
      typeof args?.min_occurrences === 'number' ? args.min_occurrences : 0;
    const minVal =
      typeof args?.min_total_value === 'number' ? args.min_total_value : 0;

    const filtered = rows.filter((r) => {
      const occ = typeof r.occurrences_90d === 'number' ? r.occurrences_90d : Number(r.occurrences_90d || 0);
      const val = typeof r.total_value_90d === 'number' ? r.total_value_90d : Number(r.total_value_90d || 0);
      return occ >= minOcc && val >= minVal;
    });

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({ count: filtered.length, items: filtered }, null, 2),
        },
      ],
    };
  }

  if (name === 'analytics_rfq_summary') {
    const start = typeof args?.start_date === 'string' ? args.start_date : null;
    const end = typeof args?.end_date === 'string' ? args.end_date : null;

    function count(sql: string): number {
      const r = db.exec(sql);
      if (!r.length || !r[0].values.length) return 0;
      const idx = 0;
      return Number(r[0].values[0][idx] || 0);
    }

    function selectNumbers(sql: string): number[] {
      const r = db.exec(sql);
      if (!r.length || !r[0].values.length) return [];
      const vals: number[] = [];
      for (const v of r[0].values) {
        vals.push(Number(v[0]));
      }
      return vals;
    }

    const dateFilter = start && end ? `WHERE date(received_date) BETWEEN date('${start}') AND date('${end}')` : '';
    const dateFilterLog = start && end ? `WHERE date(created_at) BETWEEN date('${start}') AND date('${end}')` : '';

    const total = count(`SELECT COUNT(*) FROM rfqs ${dateFilter}`);
    const processed = count(`SELECT COUNT(*) FROM rfqs ${dateFilter ? dateFilter + ' AND' : 'WHERE'} status = 'processed'`);
    const pending = count(`SELECT COUNT(*) FROM rfqs ${dateFilter ? dateFilter + ' AND' : 'WHERE'} status = 'pending'`);
    const goCount = count(`SELECT COUNT(*) FROM rfqs ${dateFilter ? dateFilter + ' AND' : 'WHERE'} decision = 'GO'`);
    const noGoCount = count(`SELECT COUNT(*) FROM rfqs ${dateFilter ? dateFilter + ' AND' : 'WHERE'} decision = 'NO-GO'`);
    const avgScore = (() => {
      const r = db.exec(`SELECT AVG(rfq_score) as avg FROM rfqs ${dateFilter}`);
      if (!r.length || !r[0].values.length) return null;
      return r[0].values[0][0] !== null ? Number(r[0].values[0][0]) : null;
    })();

    // Score buckets
    const scores = selectNumbers(`SELECT rfq_score FROM rfqs ${dateFilter} AND rfq_score IS NOT NULL`);
    let buckets = { go_high: 0, go_consider: 0, review_conditional: 0, review_weak: 0, no_go: 0 };
    for (const s of scores) {
      if (s >= 75) buckets.go_high++;
      else if (s >= 60) buckets.go_consider++;
      else if (s >= 45) buckets.review_conditional++;
      else if (s >= 30) buckets.review_weak++;
      else buckets.no_go++;
    }

    // Recommendation breakdown
    const recRows = db.exec(`SELECT rfq_recommendation, COUNT(*) as c FROM rfqs ${dateFilter} AND rfq_recommendation IS NOT NULL GROUP BY rfq_recommendation`);
    const recommendations: Record<string, number> = {};
    if (recRows.length && recRows[0].values.length) {
      const cols = recRows[0].columns;
      const recIdx = cols.indexOf('rfq_recommendation');
      const cIdx = cols.indexOf('c');
      for (const v of recRows[0].values) {
        recommendations[String(v[recIdx])] = Number(v[cIdx]);
      }
    }

    const rulesAppliedCount = count(`SELECT COUNT(*) FROM activity_log ${dateFilterLog ? dateFilterLog + ' AND' : 'WHERE'} action = 'rules_applied'`);

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(
            {
              period: { start, end },
              rfqs: {
                total,
                processed,
                pending,
                go: goCount,
                no_go: noGoCount,
              },
              scores: {
                avg: avgScore,
                buckets,
                recommendations,
              },
              rules: {
                rules_applied_events: rulesAppliedCount,
              },
            },
            null,
            2
          ),
        },
      ],
    };
  }

  if (name === 'analytics_rule_triggers') {
    const start = typeof args?.start_date === 'string' ? args.start_date : null;
    const end = typeof args?.end_date === 'string' ? args.end_date : null;

    // Pull rules_applied events and summarize in JS (details is JSON)
    const rows = db.exec(
      `SELECT rfq_id, details, created_at FROM activity_log WHERE action = 'rules_applied' ${
        start && end ? `AND date(created_at) BETWEEN date('${start}') AND date('${end}')` : ''
      } ORDER BY created_at DESC`
    );

    let events: { rfq_id: number; details: any; created_at: string }[] = [];
    if (rows.length && rows[0].values.length) {
      const cols = rows[0].columns;
      const idxId = cols.indexOf('rfq_id');
      const idxDetails = cols.indexOf('details');
      const idxCreated = cols.indexOf('created_at');
      for (const v of rows[0].values) {
        let parsed: any = null;
        try {
          parsed = JSON.parse(String(v[idxDetails] || '{}'));
        } catch {
          parsed = null;
        }
        events.push({
          rfq_id: Number(v[idxId]),
          details: parsed,
          created_at: String(v[idxCreated] || ''),
        });
      }
    }

    const ruleCounts: Record<string, { total: number; actions: Record<string, number> }> = {};
    const autoDeclineByRule: Record<string, number> = {};
    let autoDeclineCandidates = 0;
    let totalOutcomes = 0;

    for (const ev of events) {
      const outcomes = ev?.details?.ruleRes?.outcomes || ev?.details?.outcomes || [];
      for (const o of outcomes) {
        const rid = String(o?.rule_id || 'UNKNOWN');
        const act = String(o?.action || 'PASS');

        if (!ruleCounts[rid]) ruleCounts[rid] = { total: 0, actions: {} };
        ruleCounts[rid].total += 1;
        ruleCounts[rid].actions[act] = (ruleCounts[rid].actions[act] || 0) + 1;

        if (act === 'AUTO_DECLINE' || act === 'AUTO_DECLINE_AND_LOG') {
          autoDeclineByRule[rid] = (autoDeclineByRule[rid] || 0) + 1;
          autoDeclineCandidates += 1;
        }
        totalOutcomes += 1;
      }
    }

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(
            {
              period: { start, end },
              totals: {
                events: events.length,
                outcomes: totalOutcomes,
                auto_decline_candidates: autoDeclineCandidates,
              },
              by_rule: ruleCounts,
              auto_decline_by_rule: autoDeclineByRule,
              note:
                'AUTO_DECLINE candidates are diagnostic unless RFQ_AUTO_DECLINE_ENABLED=true. Use this to evaluate misfire risk before enabling.',
            },
            null,
            2
          ),
        },
      ],
    };
  }

  return {
    content: [
      {
        type: 'text',
        text: `Analytics tool "${name}" not yet implemented. Coming soon!`,
      },
    ],
  };
}
