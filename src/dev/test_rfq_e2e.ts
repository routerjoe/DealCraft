// src/dev/test_rfq_e2e.ts
// End-to-end smoke test for RFQ workflow without Outlook dependency.
// Flow:
// 1) Initialize DB and seed config
// 2) Create a test RFQ row directly in SQLite
// 3) Set attributes via tool
// 4) Calculate score via tool
// 5) Apply rules via tool
// 6) Track OEM occurrence and query analytics view
// 7) Cleanup test RFQ
//
// Run: npm run build && node dist/dev/test_rfq_e2e.js

import path from 'path';
import dotenv from 'dotenv';
import { initializeDatabase, getDb, saveDatabase } from '../database/init.js';
import { handleRfqTool } from '../tools/rfq/index.js';
import { handleAnalyticsTool } from '../tools/analytics/index.js';

function loadEnv() {
  dotenv.config({ path: path.resolve(process.cwd(), '.env') });
}

function assert(cond: boolean, msg: string) {
  if (!cond) throw new Error(msg);
}

function contains(haystack: string, needle: string): boolean {
  return haystack.indexOf(needle) !== -1;
}

function logPass(name: string) {
  console.log(`PASS: ${name}`);
}

function logFail(name: string, err: any) {
  console.error(`FAIL: ${name}\n${err?.message || String(err)}`);
}

async function createTestRfq(): Promise<number> {
  const db = getDb();

  const emailId = `TEST-E2E-${Date.now()}`;
  const subject = 'E2E RFQ – Space Force Zero Trust';
  const sender = 'test@example.com';
  const received = new Date().toISOString();

  // Ensure unique and clean slate
  db.run(`DELETE FROM rfqs WHERE email_id = ?`, [emailId]);

  db.run(
    `INSERT INTO rfqs (email_id, subject, sender, received_date, status, customer) VALUES (?, ?, ?, ?, 'pending', ?)`,
    [emailId, subject, sender, received, 'Space Force']
  );

  const res = db.exec(`SELECT last_insert_rowid() as id`);
  const rfqId = res[0]?.values?.[0]?.[0] as number;
  assert(typeof rfqId === 'number' && rfqId > 0, 'Failed to get new RFQ id');

  return rfqId;
}

async function cleanupTestRfq(rfqId: number) {
  const db = getDb();
  db.run(`DELETE FROM rfqs WHERE id = ?`, [rfqId]);
  saveDatabase();
}

async function main() {
  loadEnv();
  await initializeDatabase();

  let rfqId = -1;

  try {
    // 1) Create RFQ
    rfqId = await createTestRfq();
    console.log('Created test RFQ id:', rfqId);

    // 2) Set attributes needed for rules/scoring
    {
      const due = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10); // +7 days YYYY-MM-DD
      const setRes = await handleRfqTool('rfq_set_attributes', {
        rfq_id: rfqId,
        estimated_value: 250000,         // TIER_2_HIGH
        competition_level: 15,           // <20
        tech_vertical: 'Zero Trust',     // HIGH
        oem: 'Cisco',                    // authorized
        has_previous_contract: true,     // renewal bonus
        deadline: due,
        customer: 'Space Force',         // CRITICAL
      });
      const text = setRes.content?.[0]?.text || '';
      assert(contains(text, '"updated": true'), 'rfq_set_attributes did not update fields');
      logPass('rfq_set_attributes');
    }

    // 3) Calculate score and persist
    {
      const scoreRes = await handleRfqTool('rfq_calculate_score', { rfq_id: rfqId });
      const text = scoreRes.content?.[0]?.text || '{}';
      const parsed = JSON.parse(text);
      console.log('Score result:', parsed);
      assert(parsed.score === 100, `Expected score 100, got ${parsed.score}`);
      assert(contains(parsed.recommendation, 'GO - High Priority'), 'Expected GO - High Priority recommendation');
      logPass('rfq_calculate_score');
    }

    // 4) Apply rules (auto-decline disabled by default)
    {
      const applyRes = await handleRfqTool('rfq_apply_rules', {
        rfq_id: rfqId,
        rfq_type: 'renewal',
        quantity: 1,
      });
      const text = applyRes.content?.[0]?.text || '{}';
      const parsed = JSON.parse(text);
      console.log('Rules result:', parsed);

      // With defaults, should not auto-decline
      assert(parsed.auto_declined === false, 'auto_declined should be false with RFQ_AUTO_DECLINE_ENABLED=false');
      assert(parsed.recommendation && contains(parsed.recommendation, 'GO'), 'Expected GO recommendation in rules result');
      logPass('rfq_apply_rules');
    }

    // 5) Track OEM occurrence and verify analytics view
    {
      const trackRes = await handleRfqTool('rfq_track_oem_occurrence', {
        rfq_id: rfqId,
        oem: 'Atlassian',
        estimated_value: 15000,
        competition_level: 80,
        technology_vertical: 'DevOps/Collaboration',
      });
      const tText = trackRes.content?.[0]?.text || '{}';
      const tracked = JSON.parse(tText);
      console.log('OEM track result:', tracked);
      assert(tracked?.oem === 'Atlassian', 'rfq_track_oem_occurrence did not log Atlassian');

      const viewRes = await handleAnalyticsTool('analytics_oem_business_case_90d', { min_occurrences: 0, min_total_value: 0 });
      const vText = viewRes.content?.[0]?.text || '{}';
      const view = JSON.parse(vText);
      console.log('Analytics view result:', view);

      const item = (view.items || []).find((x: any) => (x.oem_name || x.oem || '').toLowerCase() === 'atlassian');
      assert(item, 'analytics_oem_business_case_90d did not include Atlassian after occurrence');
      logPass('analytics_oem_business_case_90d');
    }

    console.log('\nE2E RFQ workflow test passed.');
  } catch (err: any) {
    logFail('E2E RFQ workflow', err);
    process.exit(1);
  } finally {
    if (rfqId > 0) {
      await cleanupTestRfq(rfqId);
    }
  }
}

main().catch((e) => {
  console.error('Unhandled E2E runner error:', e?.message || String(e));
  process.exit(1);
});