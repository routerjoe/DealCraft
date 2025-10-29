#!/usr/bin/env node
/**
 * Partners Base Builder
 * 
 * Scans OEM Hub YAML files, extracts data, creates JSONL and SQLite database
 * VAULT_ROOT: /Users/jonolan/Documents/Obsidian Documents/Red River Sales
 */

import * as fs from 'fs';
import * as path from 'path';
import initSqlJs, { Database } from 'sql.js';
import * as yaml from 'yaml';

// Configuration
const VAULT_ROOT = '/Users/jonolan/Documents/Obsidian Documents/Red River Sales';
const OEM_DIR = path.join(VAULT_ROOT, '30 Hubs/OEMs');
const DATA_DIR = path.join(VAULT_ROOT, '80 Reference/data');
const BASE_DIR = path.join(VAULT_ROOT, '80 Reference/bases');
const DASHBOARD_DIR = path.join(VAULT_ROOT, '50 Dashboards');
const DATA_JSONL = path.join(DATA_DIR, 'partners_tiers.jsonl');
const BASE_FILE = path.join(BASE_DIR, 'partners.db');
const DASHBOARD_FILE = path.join(DASHBOARD_DIR, 'Partner_Tiers_Index.md');
const REPORT_FILE = path.join(VAULT_ROOT, '80 Reference/PARTNERS_BASE_REPORT.md');

// Types
interface ProgramTier {
  program: string;
  tier: string;
  as_of: string;
  source_doc: string;
}

interface ResellerTier {
  reseller: string;
  vehicle: string;
  oem_program: string;
  tier: string;
  as_of: string;
  source_doc: string;
}

interface OEMRecord {
  company: string;
  status: string;
  program_tiers: ProgramTier[];
  red_river_tier: ProgramTier | null;
  reseller_tiers: ResellerTier[];
  distributors: string[];
}

interface YAMLFrontmatter {
  name: string;
  category?: string;
  mandatory?: string;
  distributors?: string[];
  contracts?: string[];
  status?: string;
  program_tiers?: ProgramTier[];
  red_river_tier?: ProgramTier;
  reseller_tiers?: ResellerTier[];
}

interface ParseResult {
  success: number;
  failed: number;
  anomalies: string[];
  records: OEMRecord[];
}

interface ValidationResult {
  oem: string;
  passed: boolean;
  checks: {
    name: string;
    passed: boolean;
    reason: string;
  }[];
}

// Utilities
function stripWikiLinks(text: string): string {
  return text.replace(/\[\[([^\]]+)\]\]/g, '$1');
}

function extractYAML(content: string): YAMLFrontmatter | null {
  const match = content.match(/^---\n([\s\S]*?)\n---/);
  if (!match) return null;
  
  try {
    return yaml.parse(match[1]) as YAMLFrontmatter;
  } catch (error) {
    console.error('YAML parse error:', error);
    return null;
  }
}

function scanOEMFiles(): ParseResult {
  const result: ParseResult = {
    success: 0,
    failed: 0,
    anomalies: [],
    records: []
  };

  if (!fs.existsSync(OEM_DIR)) {
    result.anomalies.push(`OEM directory not found: ${OEM_DIR}`);
    return result;
  }

  const files = fs.readdirSync(OEM_DIR)
    .filter(f => f.endsWith('(OEM Hub).md'));

  for (const file of files) {
    const filePath = path.join(OEM_DIR, file);
    
    try {
      const content = fs.readFileSync(filePath, 'utf-8');
      const yamlData = extractYAML(content);
      
      if (!yamlData) {
        result.failed++;
        result.anomalies.push(`Failed to parse YAML in ${file}`);
        continue;
      }

      if (!yamlData.name) {
        result.failed++;
        result.anomalies.push(`Missing 'name' field in ${file}`);
        continue;
      }

      // Build record with extensible structure
      const record: OEMRecord = {
        company: yamlData.name,
        status: yamlData.status || yamlData.mandatory || 'active',
        program_tiers: yamlData.program_tiers || [],
        red_river_tier: yamlData.red_river_tier || null,
        reseller_tiers: yamlData.reseller_tiers || [],
        distributors: (yamlData.distributors || []).map(d => stripWikiLinks(d))
      };

      result.records.push(record);
      result.success++;

    } catch (error) {
      result.failed++;
      result.anomalies.push(`Error processing ${file}: ${error}`);
    }
  }

  return result;
}

function writeJSONL(records: OEMRecord[]): void {
  // Ensure directory exists
  if (!fs.existsSync(DATA_DIR)) {
    fs.mkdirSync(DATA_DIR, { recursive: true });
  }

  const lines = records.map(r => JSON.stringify(r)).join('\n');
  fs.writeFileSync(DATA_JSONL, lines, 'utf-8');
  console.log(`✓ Wrote ${records.length} records to ${DATA_JSONL}`);
}

async function buildDatabase(records: OEMRecord[]): Promise<void> {
  // Ensure directory exists
  if (!fs.existsSync(BASE_DIR)) {
    fs.mkdirSync(BASE_DIR, { recursive: true });
  }

  // Initialize SQL.js
  const SQL = await initSqlJs();
  const db = new SQL.Database();

  // Create schema
  db.exec(`
    CREATE TABLE oems (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      company TEXT UNIQUE NOT NULL,
      status TEXT,
      updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE program_tiers (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      oem_id INTEGER NOT NULL,
      program TEXT NOT NULL,
      tier TEXT,
      as_of TEXT,
      source_doc TEXT,
      FOREIGN KEY (oem_id) REFERENCES oems(id)
    );

    CREATE TABLE red_river_tiers (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      oem_id INTEGER NOT NULL,
      program TEXT,
      tier TEXT,
      as_of TEXT,
      source_doc TEXT,
      FOREIGN KEY (oem_id) REFERENCES oems(id)
    );

    CREATE TABLE reseller_tiers (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      oem_id INTEGER NOT NULL,
      reseller TEXT NOT NULL,
      vehicle TEXT,
      oem_program TEXT,
      tier TEXT,
      as_of TEXT,
      source_doc TEXT,
      FOREIGN KEY (oem_id) REFERENCES oems(id)
    );

    CREATE TABLE distributors (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      oem_id INTEGER NOT NULL,
      name TEXT NOT NULL,
      FOREIGN KEY (oem_id) REFERENCES oems(id)
    );

    CREATE INDEX idx_oems_company ON oems(company);
    CREATE INDEX idx_program_tiers_oem ON program_tiers(oem_id);
    CREATE INDEX idx_reseller_tiers_oem ON reseller_tiers(oem_id);
    CREATE INDEX idx_distributors_oem ON distributors(oem_id);
  `);

  // Insert data
  db.run('BEGIN TRANSACTION');

  try {
    for (const record of records) {
      // Insert OEM
      db.run('INSERT INTO oems (company, status) VALUES (?, ?)', [record.company, record.status]);
      
      // Get the last inserted ID
      const result = db.exec('SELECT last_insert_rowid() as id');
      const oemId = result[0].values[0][0] as number;

      // Insert program tiers
      for (const tier of record.program_tiers) {
        db.run(
          'INSERT INTO program_tiers (oem_id, program, tier, as_of, source_doc) VALUES (?, ?, ?, ?, ?)',
          [oemId, tier.program, tier.tier, tier.as_of, stripWikiLinks(tier.source_doc)]
        );
      }

      // Insert Red River tier
      if (record.red_river_tier) {
        db.run(
          'INSERT INTO red_river_tiers (oem_id, program, tier, as_of, source_doc) VALUES (?, ?, ?, ?, ?)',
          [
            oemId,
            record.red_river_tier.program,
            record.red_river_tier.tier,
            record.red_river_tier.as_of,
            stripWikiLinks(record.red_river_tier.source_doc)
          ]
        );
      }

      // Insert reseller tiers
      for (const tier of record.reseller_tiers) {
        db.run(
          'INSERT INTO reseller_tiers (oem_id, reseller, vehicle, oem_program, tier, as_of, source_doc) VALUES (?, ?, ?, ?, ?, ?, ?)',
          [oemId, tier.reseller, tier.vehicle, tier.oem_program, tier.tier, tier.as_of, stripWikiLinks(tier.source_doc)]
        );
      }

      // Insert distributors
      for (const dist of record.distributors) {
        db.run('INSERT INTO distributors (oem_id, name) VALUES (?, ?)', [oemId, dist]);
      }
    }

    db.run('COMMIT');
  } catch (error) {
    db.run('ROLLBACK');
    throw error;
  }

  // Export database to file
  const data = db.export();
  const buffer = Buffer.from(data);
  fs.writeFileSync(BASE_FILE, buffer);
  db.close();

  console.log(`✓ Built SQLite database at ${BASE_FILE}`);
}

function generateDashboard(recordCount: number): void {
  // Ensure directory exists
  if (!fs.existsSync(DASHBOARD_DIR)) {
    fs.mkdirSync(DASHBOARD_DIR, { recursive: true });
  }

  const timestamp = new Date().toISOString();
  
  const content = `---
title: Partner Tiers Index
type: dashboard
created: ${timestamp}
updated: ${timestamp}
---

# Partner Tiers Index

> **Note:** YAML in OEM Hub files is the authoritative source. This dashboard provides interactive views via Bases plugin with Dataview fallback.

## Overview

- **Total OEMs:** ${recordCount}
- **Last Sync:** ${new Date().toLocaleString()}
- **Data Source:** \`80 Reference/data/partners_tiers.jsonl\`
- **Database:** \`80 Reference/bases/partners.db\`

---

## 📊 Bases Queries

### OEM Summary

\`\`\`bases
DATABASE: [[80 Reference/bases/partners.db]]
QUERY:
SELECT 
  o.company,
  o.status,
  rr.tier as red_river_tier,
  rr.as_of as rr_as_of,
  COUNT(DISTINCT pt.program) as program_count,
  MAX(pt.as_of) as latest_tier_date
FROM oems o
LEFT JOIN red_river_tiers rr ON o.id = rr.oem_id
LEFT JOIN program_tiers pt ON o.id = pt.oem_id
GROUP BY o.id
ORDER BY o.company;
\`\`\`

### Program Tiers by OEM

\`\`\`bases
DATABASE: [[80 Reference/bases/partners.db]]
QUERY:
SELECT 
  o.company,
  pt.program,
  pt.tier,
  pt.as_of,
  pt.source_doc
FROM oems o
JOIN program_tiers pt ON o.id = pt.oem_id
ORDER BY o.company, pt.program, pt.as_of DESC;
\`\`\`

### Reseller/Vehicle Tiers

\`\`\`bases
DATABASE: [[80 Reference/bases/partners.db]]
QUERY:
SELECT 
  o.company,
  rt.reseller,
  rt.vehicle,
  rt.oem_program,
  rt.tier,
  rt.as_of,
  rt.source_doc
FROM oems o
JOIN reseller_tiers rt ON o.id = rt.oem_id
ORDER BY o.company, rt.reseller, rt.as_of DESC;
\`\`\`

### Distributors by OEM

\`\`\`bases
DATABASE: [[80 Reference/bases/partners.db]]
QUERY:
SELECT 
  o.company,
  GROUP_CONCAT(d.name, ', ') as distributors
FROM oems o
LEFT JOIN distributors d ON o.id = d.oem_id
GROUP BY o.id
ORDER BY o.company;
\`\`\`

---

## 📋 Dataview Fallback

> **If Bases plugin is not available**, these Dataview queries provide similar functionality:

### OEM Summary Table

\`\`\`dataview
TABLE WITHOUT ID
  company as "OEM",
  status as "Status",
  red_river_tier.tier as "RR Tier",
  length(program_tiers) as "Programs",
  length(reseller_tiers) as "Resellers"
FROM "80 Reference/data/partners_tiers.jsonl"
SORT company ASC
\`\`\`

### All Program Tiers

\`\`\`dataview
TABLE WITHOUT ID
  company as "OEM",
  tier.program as "Program",
  tier.tier as "Tier",
  tier.as_of as "As Of",
  tier.source_doc as "Source"
FROM "80 Reference/data/partners_tiers.jsonl"
FLATTEN program_tiers as tier
SORT company ASC, tier.as_of DESC
\`\`\`

### Reseller Tiers

\`\`\`dataview
TABLE WITHOUT ID
  company as "OEM",
  tier.reseller as "Reseller",
  tier.vehicle as "Vehicle",
  tier.oem_program as "Program",
  tier.tier as "Tier",
  tier.as_of as "As Of"
FROM "80 Reference/data/partners_tiers.jsonl"
FLATTEN reseller_tiers as tier
SORT company ASC, tier.reseller ASC
\`\`\`

### Distributors by OEM

\`\`\`dataview
TABLE WITHOUT ID
  company as "OEM",
  join(distributors, ", ") as "Distributors"
FROM "80 Reference/data/partners_tiers.jsonl"
SORT company ASC
\`\`\`

---

## 🔄 Maintenance

To rebuild this index and database:

\`\`\`bash
npm run build:partners-base
\`\`\`

Or manually:

\`\`\`bash
node src/tools/partners/build_partners_base.ts
\`\`\`

**Last Sync:** ${new Date().toLocaleString('en-US', { timeZone: 'America/New_York' })} ET
`;

  fs.writeFileSync(DASHBOARD_FILE, content, 'utf-8');
  console.log(`✓ Generated dashboard at ${DASHBOARD_FILE}`);
}

function validateData(records: OEMRecord[]): ValidationResult[] {
  const validations: ValidationResult[] = [];

  for (const record of records) {
    const checks: ValidationResult['checks'] = [];

    // Check 1: Company name is present and non-empty
    checks.push({
      name: 'Company Name',
      passed: !!record.company && record.company.trim().length > 0,
      reason: record.company ? 'Valid' : 'Missing or empty company name'
    });

    // Check 2: Status is valid
    const validStatuses = ['active', 'optional', 'inactive', 'mandatory'];
    checks.push({
      name: 'Status',
      passed: validStatuses.includes(record.status?.toLowerCase() || ''),
      reason: validStatuses.includes(record.status?.toLowerCase() || '')
        ? 'Valid status'
        : `Invalid status: ${record.status || 'missing'}`
    });

    // Check 3: For OEMs with distributors, validate they are not empty
    if (record.distributors && record.distributors.length > 0) {
      const hasValidDistributors = record.distributors.every(d => d && d.trim().length > 0);
      checks.push({
        name: 'Distributors',
        passed: hasValidDistributors,
        reason: hasValidDistributors
          ? `${record.distributors.length} distributor(s)`
          : 'One or more empty distributor entries'
      });
    } else {
      checks.push({
        name: 'Distributors',
        passed: true,
        reason: 'No distributors defined (optional)'
      });
    }

    // Check 4: Tier data validation (if present)
    if (record.program_tiers && record.program_tiers.length > 0) {
      const validTiers = record.program_tiers.every(t =>
        t.program && t.tier && t.as_of && t.source_doc
      );
      checks.push({
        name: 'Program Tiers',
        passed: validTiers,
        reason: validTiers
          ? `${record.program_tiers.length} tier(s)`
          : 'Incomplete tier data (missing required fields)'
      });
    }

    if (record.red_river_tier) {
      const validRRTier = record.red_river_tier.program &&
                          record.red_river_tier.tier &&
                          record.red_river_tier.as_of &&
                          record.red_river_tier.source_doc;
      checks.push({
        name: 'Red River Tier',
        passed: validRRTier,
        reason: validRRTier ? 'Valid' : 'Incomplete tier data'
      });
    }

    if (record.reseller_tiers && record.reseller_tiers.length > 0) {
      const validResellerTiers = record.reseller_tiers.every(t =>
        t.reseller && t.vehicle && t.oem_program && t.tier && t.as_of && t.source_doc
      );
      checks.push({
        name: 'Reseller Tiers',
        passed: validResellerTiers,
        reason: validResellerTiers
          ? `${record.reseller_tiers.length} tier(s)`
          : 'Incomplete reseller tier data'
      });
    }

    const allPassed = checks.every(c => c.passed);
    validations.push({
      oem: record.company,
      passed: allPassed,
      checks
    });
  }

  return validations;
}

function generateReport(parseResult: ParseResult, validations: ValidationResult[]): void {
  const timestamp = new Date().toISOString();
  
  const content = `# Partners Base Build Report

**Generated:** ${new Date().toLocaleString('en-US', { timeZone: 'America/New_York' })} ET
**Timestamp:** ${timestamp}

## Summary

- **Total Files Scanned:** ${parseResult.success + parseResult.failed}
- **Successfully Parsed:** ${parseResult.success}
- **Failed to Parse:** ${parseResult.failed}
- **Anomalies Detected:** ${parseResult.anomalies.length}

## OEM Records

${parseResult.records.map(r => `- **${r.company}** (${r.status})
  - Program Tiers: ${r.program_tiers.length}
  - Red River Tier: ${r.red_river_tier ? '✓' : '✗'}
  - Reseller Tiers: ${r.reseller_tiers.length}
  - Distributors: ${r.distributors.length}`).join('\n')}

## Anomalies

${parseResult.anomalies.length > 0
  ? parseResult.anomalies.map(a => `- ${a}`).join('\n')
  : '- None detected'
}

## Validation Results

| OEM | Status | Issues |
|-----|--------|--------|
${validations.map(v => {
  const status = v.passed ? 'PASS' : 'FAIL';
  const failedChecks = v.checks.filter(c => !c.passed);
  const issues = failedChecks.length > 0
    ? failedChecks.map(c => `${c.name}: ${c.reason}`).join('; ')
    : 'None';
  return `| ${v.oem} | ${status} | ${issues} |`;
}).join('\n')}

### Summary
- **Total OEMs Validated:** ${validations.length}
- **Passed:** ${validations.filter(v => v.passed).length}
- **Failed:** ${validations.filter(v => !v.passed).length}

## Files Generated

- **JSONL Data:** \`80 Reference/data/partners_tiers.jsonl\`
- **SQLite DB:** \`80 Reference/bases/partners.db\`
- **Dashboard:** \`50 Dashboards/Partner_Tiers_Index.md\`
- **This Report:** \`80 Reference/PARTNERS_BASE_REPORT.md\`

## Database Schema

### Tables Created

1. **oems** - Core OEM information
2. **program_tiers** - OEM program tier levels
3. **red_river_tiers** - Red River specific tiers
4. **reseller_tiers** - Reseller/vehicle tier information
5. **distributors** - Distribution partners per OEM

### Indexes

- \`idx_oems_company\`
- \`idx_program_tiers_oem\`
- \`idx_reseller_tiers_oem\`
- \`idx_distributors_oem\`

## Notes

- YAML frontmatter in OEM Hub files remains authoritative
- This database is for interactive querying via Bases plugin
- Run idempotently - safe to rebuild at any time
- Currently, tier data is prepared but not yet populated in YAML files
- System is ready for tier data when available

---

*Generated by build_partners_base.ts*
`;

  fs.writeFileSync(REPORT_FILE, content, 'utf-8');
  console.log(`✓ Generated report at ${REPORT_FILE}`);
}

// Main execution
async function main() {
  console.log('🚀 Building Partners Base System...\n');

  console.log('Step 1: Scanning OEM Hub files...');
  const parseResult = scanOEMFiles();
  console.log(`  ✓ Parsed ${parseResult.success} OEM files`);
  if (parseResult.failed > 0) {
    console.log(`  ⚠ ${parseResult.failed} files failed to parse`);
  }

  console.log('\nStep 2: Writing JSONL data...');
  writeJSONL(parseResult.records);

  console.log('\nStep 3: Building SQLite database...');
  await buildDatabase(parseResult.records);

  console.log('\nStep 4: Generating dashboard...');
  generateDashboard(parseResult.records.length);

  console.log('\nStep 5: Validating data...');
  const validations = validateData(parseResult.records);
  const failedValidations = validations.filter(v => !v.passed);
  console.log(`  ✓ Validated ${validations.length} OEMs`);
  if (failedValidations.length > 0) {
    console.log(`  ⚠ ${failedValidations.length} validation(s) failed`);
  }

  console.log('\nStep 6: Generating sync report...');
  generateReport(parseResult, validations);

  console.log('\n✅ Partners Base build complete!\n');
  console.log('📍 Files created:');
  console.log(`   - ${DATA_JSONL}`);
  console.log(`   - ${BASE_FILE}`);
  console.log(`   - ${DASHBOARD_FILE}`);
  console.log(`   - ${REPORT_FILE}`);

  // Generate git diff plan
  console.log('\n📋 Git Commit Plan:');
  console.log('\nFiles to stage:');
  console.log('   - src/tools/partners/build_partners_base.ts');
  console.log('   - src/tools/partners/README.md');
  console.log('   - package.json');
  console.log('   - (Obsidian vault files are external to git)');
  
  console.log('\n📝 Suggested commit message:');
  console.log('   "feat(partners): add Partners Base system with SQLite + dashboard');
  console.log('   ');
  console.log('   - Create build_partners_base.ts to scan OEM YAML files');
  console.log('   - Generate JSONL data, SQLite database, and Markdown dashboard');
  console.log('   - Add Bases queries with Dataview fallback');
  console.log('   - Include validation and sync reporting');
  console.log('   - Add npm script: build:partners-base"');
  
  console.log('\n🚀 Commands to run:');
  console.log('   git add src/tools/partners/');
  console.log('   git add package.json');
  console.log('   git commit -m "feat(partners): add Partners Base system with SQLite + dashboard"');
  console.log('   git push');
  console.log('');
}

// Run if executed directly
const isMainModule = import.meta.url === `file://${process.argv[1]}`;
if (isMainModule) {
  main().catch(error => {
    console.error('❌ Error:', error);
    process.exit(1);
  });
}

export { main, scanOEMFiles, writeJSONL, buildDatabase, generateDashboard };