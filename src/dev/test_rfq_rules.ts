// src/dev/test_rfq_rules.ts
// Extended tests for RFQ scoring, rules helpers, and OEM business case.
// Run: npm run build && node dist/dev/test_rfq_rules.js

import path from 'path';
import dotenv from 'dotenv';
import { initializeDatabase, getDb } from '../database/init.js';
import {
  calculateRfqScore,
  evaluateNewOemBusinessCase,
  isStrategicCustomer,
  getValueTier,
} from '../tools/rfq/rules.js';

function loadEnv() {
  dotenv.config({ path: path.resolve(process.cwd(), '.env') });
}

function assert(cond: boolean, msg: string) {
  if (!cond) throw new Error(msg);
}

function logPass(name: string) {
  console.log(`PASS: ${name}`);
}

function logFail(name: string, err: any) {
  console.error(`FAIL: ${name}\n${err?.message || String(err)}`);
}

// ----- Unit tests for helpers -----

async function testStrategicCustomer() {
  assert(isStrategicCustomer('Customer Alpha') === true, 'Customer Alpha should be strategic');
  assert(isStrategicCustomer('Hill AFB') === true, 'Hill AFB should be strategic');
  assert(isStrategicCustomer('Random Base') === false, 'Random Base should not be strategic');
  assert(isStrategicCustomer('afcent') === true, 'Case insensitive strategic match failed');
  logPass('isStrategicCustomer detection');
}

async function testValueTier() {
  assert(getValueTier(1_500_000) === 'TIER_1_CRITICAL', '1.5M should be TIER_1_CRITICAL');
  assert(getValueTier(500_000) === 'TIER_2_HIGH', '500K should be TIER_2_HIGH');
  assert(getValueTier(75_000) === 'TIER_3_REVIEW', '75K should be TIER_3_REVIEW');
  assert(getValueTier(5_000) === 'TIER_4_LOW', '5K should be TIER_4_LOW');
  logPass('getValueTier thresholds');
}

async function testConfigCounts() {
  // Verify the seeded configuration exists; falls back to defaults if missing, but we expect seeding during initializeDatabase
  const db = getDb();

  const sc = db.exec(`SELECT COUNT(*) as c FROM config_strategic_customers`);
  const scCount = sc.length && sc[0].values.length ? Number(sc[0].values[0][0]) : 0;
  assert(scCount >= 15, `Expected >=15 strategic customers, got ${scCount}`);

  const vt = db.exec(`SELECT COUNT(*) as c FROM config_value_thresholds`);
  const vtCount = vt.length && vt[0].values.length ? Number(vt[0].values[0][0]) : 0;
  assert(vtCount >= 4, `Expected >=4 value thresholds, got ${vtCount}`);

  const oem = db.exec(`SELECT COUNT(*) as c FROM config_oem_tracking WHERE currently_authorized = 0`);
  const oemCount = oem.length && oem[0].values.length ? Number(oem[0].values[0][0]) : 0;
  assert(oemCount >= 5, `Expected >=5 tracked new-business OEMs, got ${oemCount}`);

  logPass('Seeded config counts');
}

// ----- Scoring tests -----

async function testScoringHighPriority() {
  const res = calculateRfqScore({
    value: 250000,             // TIER_2_HIGH = 30
    competition: 15,           // <20 = +15
    customer: 'Space Force',   // CRITICAL = +25
    tech_vertical: 'Zero Trust', // HIGH = +10
    oem: 'Cisco',              // authorized = +10
    has_previous_contract: true, // renewal = +10
  });
  assert(res.score === 100, `Expected 100, got ${res.score}`);
  assert(res.recommendation.includes('GO - High Priority'), `Unexpected recommendation: ${res.recommendation}`);
  logPass('High priority RFQ scoring (100 points, GO - High Priority)');
}

async function testScoringAutoDecline() {
  const res = calculateRfqScore({
    value: 5000,                // TIER_4_LOW = 10
    competition: 127,           // 100+ = +0
    customer: 'Unknown Base',   // +0
    tech_vertical: 'Misc',      // +0
    oem: 'Unknown Vendor',      // +0
    has_previous_contract: false,
  });
  assert(res.score === 10, `Expected 10, got ${res.score}`);
  assert(res.recommendation.includes('NO-GO'), `Expected NO-GO recommendation, got: ${res.recommendation}`);
  logPass('Low priority RFQ scoring (10 points, NO-GO)');
}

// ----- OEM business case tests -----

async function testBusinessCaseStrong() {
  const r = evaluateNewOemBusinessCase({
    oem: 'Atlassian',
    occurrences_90d: 8,      // +40
    total_value_90d: 200000, // +25
    unique_customers: 5,     // +10
    avg_competition: 45,     // +10
  });
  assert(r.score >= 60, `Expected score >= 60, got ${r.score}`);
  assert(r.recommendation.startsWith('PURSUE'), `Expected PURSUE, got: ${r.recommendation}`);
  logPass('OEM Business Case: Strong opportunity (PURSUE)');
}

async function testBusinessCaseWeak() {
  const r = evaluateNewOemBusinessCase({
    oem: 'Sparx',
    occurrences_90d: 2,       // +0
    total_value_90d: 15000,   // +0
    unique_customers: 1,      // +0
    avg_competition: 120,     // +0
  });
  assert(r.score < 20, `Expected score < 20, got ${r.score}`);
  assert(r.recommendation.startsWith('NO ACTION'), `Expected NO ACTION, got: ${r.recommendation}`);
  logPass('OEM Business Case: Weak opportunity (NO ACTION)');
}

async function main() {
  loadEnv();
  await initializeDatabase();

  const tests = [
    { name: 'isStrategicCustomer detection', fn: testStrategicCustomer },
    { name: 'getValueTier thresholds', fn: testValueTier },
    { name: 'Seeded config counts', fn: testConfigCounts },
    { name: 'High priority RFQ scoring', fn: testScoringHighPriority },
    { name: 'Low priority RFQ scoring', fn: testScoringAutoDecline },
    { name: 'OEM business case strong', fn: testBusinessCaseStrong },
    { name: 'OEM business case weak', fn: testBusinessCaseWeak },
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
    console.log('\nAll RFQ rule tests passed.');
  }
}

main().catch((e) => {
  console.error('Unhandled test runner error:', e?.message || String(e));
  process.exit(1);
});