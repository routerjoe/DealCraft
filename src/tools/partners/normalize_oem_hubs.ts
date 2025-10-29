#!/usr/bin/env node
/**
 * OEM Hub Normalization Script
 * 
 * Normalizes all OEM Hub files to a unified YAML schema,
 * creates missing required OEMs, and validates results.
 */

import * as fs from 'fs';
import * as path from 'path';
import * as yaml from 'yaml';
import { execSync } from 'child_process';

// Configuration
const VAULT_ROOT = '/Users/jonolan/Documents/Obsidian Documents/Red River Sales';
const OEM_DIR = path.join(VAULT_ROOT, '30 Hubs/OEMs');
const BACKUP_DIR = path.join(VAULT_ROOT, '80 Reference/backups');
const REPORT_FILE = path.join(VAULT_ROOT, '80 Reference/PARTNERS_NORMALIZATION_REPORT.md');

// Required OEMs that must exist
const REQUIRED_OEMS = ['Cisco', 'VMware', 'Nutanix', 'NetApp', 'Red Hat', 'HYCU', 'cTera'];

// Legacy keys to remove
const LEGACY_KEYS = [
  'mandatory', 'optional', 'placeholders_filled', 'oems', 'oem',
  'oem_name', 'company', 'vendor', 'type', 'zkid', 'created', 'updated',
  'priority', 'partner_tier', 'red_river_status', 'market_focus', 'products',
  'recommended_partners', 'relevance_score', 'fit_notes', 'exclude_keywords',
  'program_notes', 'contacts', 'auto_assign', 'auto_score_enabled'
];

// Authoritative schema with field order
const SCHEMA_ORDER = [
  'name',
  'aliases',
  'status',
  'category',
  'tier_global',
  'tier_redriver',
  'tech_focus',
  'gov_segments',
  'program_tiers',
  'partners',
  'distributors',
  'contracts',
  'esi_bpas',
  'notes',
  'tags'
];

interface NormalizedYAML {
  name: string;
  aliases: string[];
  status: string;
  category: string;
  tier_global: string;
  tier_redriver: string;
  tech_focus: string[];
  gov_segments: string[];
  program_tiers: string[];
  partners: string[];
  distributors: string[];
  contracts: string[];
  esi_bpas: string[];
  notes: string;
  tags: string[];
}

interface FileChange {
  file: string;
  renamed: boolean;
  oldName?: string;
  keysAdded: string[];
  keysRemoved: string[];
  keysModified: string[];
  tierFieldsPresent: boolean;
  partnersLinked: number;
  distributorsLinked: number;
  contractsLinked: number;
  status: string;
  notes: string[];
}

interface DryRunResult {
  totalFiles: number;
  filesToModify: number;
  filesToRename: number;
  filesToCreate: number;
  changes: FileChange[];
}

// Utilities
function extractYAMLAndContent(content: string): { yaml: any; body: string } | null {
  const match = content.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
  if (!match) return null;
  
  try {
    return {
      yaml: yaml.parse(match[1]),
      body: match[2]
    };
  } catch (error) {
    console.error('YAML parse error:', error);
    return null;
  }
}

function stripWikiLinks(text: string): string {
  return text.replace(/\[\[([^\]]+)\]\]/g, '$1');
}

function isWikiLink(text: string): boolean {
  return /^\[\[.+\]\]$/.test(text);
}

function getCategoryFromExisting(existingYaml: any): string {
  if (existingYaml.category) return existingYaml.category;
  if (existingYaml.market_focus && Array.isArray(existingYaml.market_focus)) {
    return existingYaml.market_focus.join(' & ');
  }
  return 'TBD';
}

function normalizeYAML(existingYaml: any, oemName: string): NormalizedYAML {
  const normalized: NormalizedYAML = {
    name: oemName,
    aliases: Array.isArray(existingYaml.aliases) ? existingYaml.aliases : [],
    status: existingYaml.status || existingYaml.mandatory || 'active',
    category: getCategoryFromExisting(existingYaml),
    tier_global: existingYaml.tier_global || existingYaml.partner_tier || '',
    tier_redriver: existingYaml.tier_redriver || existingYaml.red_river_status || '',
    tech_focus: Array.isArray(existingYaml.tech_focus) 
      ? existingYaml.tech_focus 
      : (Array.isArray(existingYaml.market_focus) ? existingYaml.market_focus : []),
    gov_segments: Array.isArray(existingYaml.gov_segments) 
      ? existingYaml.gov_segments 
      : ['AF', 'DoD', 'SP'],
    program_tiers: Array.isArray(existingYaml.program_tiers) ? existingYaml.program_tiers : [],
    partners: Array.isArray(existingYaml.partners) 
      ? existingYaml.partners 
      : (Array.isArray(existingYaml.contacts) ? existingYaml.contacts : []),
    distributors: Array.isArray(existingYaml.distributors) ? existingYaml.distributors : [],
    contracts: Array.isArray(existingYaml.contracts) ? existingYaml.contracts : [],
    esi_bpas: Array.isArray(existingYaml.esi_bpas) ? existingYaml.esi_bpas : [],
    notes: existingYaml.notes || existingYaml.program_notes || existingYaml.fit_notes || '',
    tags: ['OEM']
  };

  // Normalize status values
  if (normalized.status === 'optional' || normalized.status === 'mandatory') {
    normalized.status = 'active';
  }
  
  return normalized;
}

function serializeYAML(data: NormalizedYAML): string {
  const lines: string[] = ['---'];
  
  for (const key of SCHEMA_ORDER) {
    const value = data[key as keyof NormalizedYAML];
    
    if (Array.isArray(value)) {
      if (value.length === 0) {
        lines.push(`${key}: []`);
      } else {
        lines.push(`${key}:`);
        value.forEach(item => {
          const itemStr = String(item);
          // Escape quotes in values
          const escapedItem = itemStr.replace(/"/g, '\\"');
          lines.push(`  - "${escapedItem}"`);
        });
      }
    } else if (typeof value === 'string') {
      if (value === '') {
        lines.push(`${key}: ""`);
      } else {
        // Always quote strings to avoid YAML parsing issues
        const escapedValue = value.replace(/"/g, '\\"').replace(/\n/g, '\\n');
        lines.push(`${key}: "${escapedValue}"`);
      }
    } else {
      lines.push(`${key}: ${value}`);
    }
  }
  
  lines.push('---');
  return lines.join('\n');
}

function ensureCanonicalSections(body: string): string {
  const sections = [
    '# ',  // Title will be added separately
    '## Opportunities',
    '## Pricing & Contracting',
    '## Tech & Products',
    '## Related Customers',
    '## Related Contracts'
  ];
  
  let result = body.trim();
  
  // Check which sections exist
  for (const section of sections.slice(1)) {  // Skip title
    if (!result.includes(section)) {
      result += `\n\n${section}\n- (To be populated)\n`;
    }
  }
  
  return result;
}

function analyzeFile(filePath: string, oemName: string): FileChange {
  const content = fs.readFileSync(filePath, 'utf-8');
  const parsed = extractYAMLAndContent(content);
  
  const change: FileChange = {
    file: path.basename(filePath),
    renamed: false,
    keysAdded: [],
    keysRemoved: [],
    keysModified: [],
    tierFieldsPresent: false,
    partnersLinked: 0,
    distributorsLinked: 0,
    contractsLinked: 0,
    status: 'OK',
    notes: []
  };

  if (!parsed) {
    change.status = 'ERROR';
    change.notes.push('Failed to parse YAML frontmatter');
    return change;
  }

  const normalized = normalizeYAML(parsed.yaml, oemName);
  const existingKeys = Object.keys(parsed.yaml);
  const normalizedKeys = Object.keys(normalized);

  // Check for added keys
  for (const key of normalizedKeys) {
    if (!existingKeys.includes(key)) {
      change.keysAdded.push(key);
    }
  }

  // Check for removed keys (legacy)
  for (const key of existingKeys) {
    if (LEGACY_KEYS.includes(key) || !normalizedKeys.includes(key)) {
      change.keysRemoved.push(key);
    }
  }

  // Check for modified keys
  for (const key of normalizedKeys) {
    if (existingKeys.includes(key)) {
      const oldVal = parsed.yaml[key];
      const newVal = normalized[key as keyof NormalizedYAML];
      if (JSON.stringify(oldVal) !== JSON.stringify(newVal)) {
        change.keysModified.push(key);
      }
    }
  }

  // Check tier fields
  change.tierFieldsPresent = !!(normalized.tier_global || normalized.tier_redriver);

  // Count linked items
  change.partnersLinked = normalized.partners.filter(isWikiLink).length;
  change.distributorsLinked = normalized.distributors.filter(isWikiLink).length;
  change.contractsLinked = normalized.contracts.filter(isWikiLink).length;

  // Check if file needs renaming
  const expectedName = `${oemName} (OEM Hub).md`;
  if (path.basename(filePath) !== expectedName) {
    change.renamed = true;
    change.oldName = path.basename(filePath);
  }

  // Add notes
  if (change.keysAdded.length > 0) {
    change.notes.push(`Added: ${change.keysAdded.join(', ')}`);
  }
  if (change.keysRemoved.length > 0) {
    change.notes.push(`Removed: ${change.keysRemoved.join(', ')}`);
  }
  if (!change.tierFieldsPresent) {
    change.notes.push('Tier fields empty - need population');
  }
  if (normalized.partners.length > 0 && change.partnersLinked === 0) {
    change.notes.push('Partners not linked to People Hubs');
  }

  return change;
}

function dryRun(): DryRunResult {
  console.log('🔍 DRY RUN: Scanning OEM Hub files...\n');

  if (!fs.existsSync(OEM_DIR)) {
    throw new Error(`OEM directory not found: ${OEM_DIR}`);
  }

  const files = fs.readdirSync(OEM_DIR)
    .filter(f => f.endsWith('.md') && !f.includes('99 Archive'));

  const result: DryRunResult = {
    totalFiles: files.length,
    filesToModify: 0,
    filesToRename: 0,
    filesToCreate: 0,
    changes: []
  };

  // Analyze existing files
  for (const file of files) {
    const filePath = path.join(OEM_DIR, file);
    const oemName = file.replace(' (OEM Hub).md', '').replace('.md', '');
    
    const change = analyzeFile(filePath, oemName);
    result.changes.push(change);

    if (change.keysAdded.length > 0 || change.keysRemoved.length > 0 || change.keysModified.length > 0) {
      result.filesToModify++;
    }
    if (change.renamed) {
      result.filesToRename++;
    }
  }

  // Check for missing required OEMs
  const existingOEMs = result.changes.map(c => stripWikiLinks(c.file).replace(' (OEM Hub).md', ''));
  const missingOEMs = REQUIRED_OEMS.filter(oem => !existingOEMs.includes(oem));
  result.filesToCreate = missingOEMs.length;

  // Add placeholders for missing OEMs
  for (const oem of missingOEMs) {
    result.changes.push({
      file: `${oem} (OEM Hub).md`,
      renamed: false,
      keysAdded: SCHEMA_ORDER,
      keysRemoved: [],
      keysModified: [],
      tierFieldsPresent: false,
      partnersLinked: 0,
      distributorsLinked: 0,
      contractsLinked: 0,
      status: 'TO_CREATE',
      notes: ['Will be created from template']
    });
  }

  return result;
}

function createBackup(): string {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
  const backupFile = path.join(BACKUP_DIR, `oems_backup_${timestamp}.zip`);

  if (!fs.existsSync(BACKUP_DIR)) {
    fs.mkdirSync(BACKUP_DIR, { recursive: true });
  }

  console.log('💾 Creating backup...');
  
  try {
    execSync(`cd "${OEM_DIR}" && zip -r "${backupFile}" *.md`, { stdio: 'pipe' });
    const stats = fs.statSync(backupFile);
    console.log(`✓ Backup created: ${backupFile} (${(stats.size / 1024).toFixed(2)} KB)\n`);
    return backupFile;
  } catch (error) {
    console.error('Failed to create backup:', error);
    throw error;
  }
}

function applyNormalization(dryRun: boolean = false): FileChange[] {
  const files = fs.readdirSync(OEM_DIR)
    .filter(f => f.endsWith('.md') && !f.includes('99 Archive'));

  const changes: FileChange[] = [];

  for (const file of files) {
    const filePath = path.join(OEM_DIR, file);
    const content = fs.readFileSync(filePath, 'utf-8');
    const parsed = extractYAMLAndContent(content);

    if (!parsed) {
      console.log(`⚠️  Skipping ${file}: Failed to parse YAML`);
      continue;
    }

    const oemName = file.replace(' (OEM Hub).md', '').replace('.md', '');
    const normalized = normalizeYAML(parsed.yaml, oemName);
    const change = analyzeFile(filePath, oemName);

    // Generate new content
    const newYAML = serializeYAML(normalized);
    const newBody = ensureCanonicalSections(parsed.body);
    const newContent = `${newYAML}\n\n# ${oemName} (OEM Hub)\n\n${newBody}`;

    if (!dryRun) {
      fs.writeFileSync(filePath, newContent, 'utf-8');
      
      // Rename file if needed
      if (change.renamed && change.oldName) {
        const newPath = path.join(OEM_DIR, `${oemName} (OEM Hub).md`);
        fs.renameSync(filePath, newPath);
        console.log(`📝 Normalized & renamed: ${change.oldName} → ${oemName} (OEM Hub).md`);
      } else {
        console.log(`📝 Normalized: ${file}`);
      }
    }

    changes.push(change);
  }

  return changes;
}

function createMissingOEMs(dryRun: boolean = false): string[] {
  const existingFiles = fs.readdirSync(OEM_DIR);
  const existingOEMs = existingFiles
    .filter(f => f.endsWith('.md'))
    .map(f => f.replace(' (OEM Hub).md', '').replace('.md', ''));

  const missingOEMs = REQUIRED_OEMS.filter(oem => !existingOEMs.includes(oem));

  for (const oem of missingOEMs) {
    const normalized: NormalizedYAML = {
      name: oem,
      aliases: [],
      status: 'active',
      category: 'TBD',
      tier_global: '',
      tier_redriver: '',
      tech_focus: [],
      gov_segments: ['AF', 'DoD', 'SP'],
      program_tiers: [],
      partners: [],
      distributors: ['[[Carahsoft (Contract Hub)]]', '[[TD SYNNEX Public Sector (Contract Hub)]]'],
      contracts: ['[[SEWP V (Contract Hub)]]', '[[2GIT BPA (Contract Hub)]]', '[[ITES-SW2 (Contract Hub)]]'],
      esi_bpas: [],
      notes: '',
      tags: ['OEM']
    };

    const yamlContent = serializeYAML(normalized);
    const body = `# ${oem} (OEM Hub)

## Opportunities
- (Backlinks will appear here)

## Pricing & Contracting
- Notes on discounts, SKUs, registration timelines

## Tech & Products
- [[Zettel – ${oem} Tech Notes]]

## Related Customers
- [[Customer Hub]]

## Related Contracts
- [[Contract Hub]]
`;

    const content = `${yamlContent}\n\n${body}`;
    const filePath = path.join(OEM_DIR, `${oem} (OEM Hub).md`);

    if (!dryRun) {
      fs.writeFileSync(filePath, content, 'utf-8');
      console.log(`✨ Created: ${oem} (OEM Hub).md`);
    }
  }

  return missingOEMs;
}

function validateNormalized(): FileChange[] {
  console.log('\n✅ Validating normalized files...\n');

  const files = fs.readdirSync(OEM_DIR)
    .filter(f => f.endsWith('.md') && f.includes('(OEM Hub)'));

  const validations: FileChange[] = [];

  for (const file of files) {
    const filePath = path.join(OEM_DIR, file);
    const oemName = file.replace(' (OEM Hub).md', '');
    const validation = analyzeFile(filePath, oemName);
    
    // Post-normalization, these should all be clean
    if (validation.keysAdded.length === 0 && validation.keysRemoved.length === 0) {
      validation.status = 'PASS';
    }

    validations.push(validation);
  }

  const passed = validations.filter(v => v.status === 'PASS').length;
  const failed = validations.filter(v => v.status !== 'PASS').length;
  
  console.log(`Validation: ${passed} PASS, ${failed} FAIL`);

  return validations;
}

function generateReport(
  dryRunResult: DryRunResult,
  backupPath: string,
  finalValidations: FileChange[],
  createdOEMs: string[]
): void {
  const timestamp = new Date().toISOString();
  const timestampET = new Date().toLocaleString('en-US', { timeZone: 'America/New_York' });

  const content = `# OEM Hub Normalization Report

**Generated:** ${timestampET} ET  
**Timestamp:** ${timestamp}

## Summary

- **Total Files Scanned:** ${dryRunResult.totalFiles}
- **Files Modified:** ${dryRunResult.filesToModify}
- **Files Renamed:** ${dryRunResult.filesToRename}
- **Files Created:** ${createdOEMs.length}
- **Backup Location:** \`${path.basename(backupPath)}\`

## Created OEMs

${createdOEMs.length > 0 
  ? createdOEMs.map(oem => `- ${oem}`).join('\n')
  : '- None (all required OEMs existed)'
}

## Validation Results

| File | Renamed | Keys Fixed | Tier Fields | Partners | Distributors | Contracts | Status | Notes |
|------|---------|------------|-------------|----------|--------------|-----------|--------|-------|
${finalValidations.map(v => {
  const keysFixed = v.keysAdded.length + v.keysRemoved.length + v.keysModified.length;
  const tierStatus = v.tierFieldsPresent ? '✓' : '✗';
  const notesStr = v.notes.length > 0 ? v.notes.join('; ') : 'None';
  return `| ${v.file} | ${v.renamed ? 'Yes' : 'No'} | ${keysFixed} | ${tierStatus} | ${v.partnersLinked} | ${v.distributorsLinked} | ${v.contractsLinked} | ${v.status} | ${notesStr} |`;
}).join('\n')}

### Validation Summary
- **Total OEMs:** ${finalValidations.length}
- **Passed:** ${finalValidations.filter(v => v.status === 'PASS').length}
- **Failed:** ${finalValidations.filter(v => v.status !== 'PASS').length}

## Schema Applied

All OEM Hub files now conform to the following YAML schema:

\`\`\`yaml
name: <OEM Name>
aliases: []
status: active  # active | niche | deprecated
category: <Category>
tier_global: ""
tier_redriver: ""
tech_focus: []
gov_segments:
  - AF
  - DoD
  - SP
program_tiers: []
partners: []
distributors:
  - "[[Carahsoft (Contract Hub)]]"
  - "[[TD SYNNEX Public Sector (Contract Hub)]]"
contracts:
  - "[[SEWP V (Contract Hub)]]"
  - "[[2GIT BPA (Contract Hub)]]"
  - "[[ITES-SW2 (Contract Hub)]]"
esi_bpas: []
notes: ""
tags:
  - OEM
\`\`\`

## Removed Legacy Keys

The following keys were removed during normalization:
${LEGACY_KEYS.map(k => `- \`${k}\``).join('\n')}

## Manual Follow-ups

${finalValidations.filter(v => v.notes && v.notes.length > 0 && v.notes.some(n => n.includes('need population') || n.includes('not linked'))).length > 0 ? `
### Tier Data Population Needed

The following OEMs have empty tier fields:
${finalValidations.filter(v => !v.tierFieldsPresent).map(v => `- **${v.file.replace(' (OEM Hub).md', '')}**: Populate \`tier_global\` and \`tier_redriver\``).join('\n')}

**Recommended Sources:**
- Red River partner sheets
- OEM partner portal dashboards
- Distributor partner confirmations
- Sales team knowledge base

### Partner Linking

The following OEMs have partners that need to be linked to People Hubs:
${finalValidations.filter(v => v.partnersLinked === 0 && finalValidations.some(x => x.file === v.file)).map(v => `- **${v.file.replace(' (OEM Hub).md', '')}**: Convert partner names to \`[[Person Name (People Hub)]]\` links`).join('\n') || '- None at this time'}
` : '- No manual follow-ups required at this time'}

## Next Steps

1. **Rebuild Partners Base**
   \`\`\`bash
   npm run build:partners-base
   \`\`\`

2. **Populate Tier Data**
   - Review each OEM's partner portal
   - Update \`tier_global\` and \`tier_redriver\` fields
   - Re-run normalization if needed

3. **Link Partners**
   - Create or identify People Hub notes for AEs and SEs
   - Update \`partners\` arrays with wiki links

4. **Verify in Obsidian**
   - Open dashboard: \`50 Dashboards/Partner_Tiers_Index.md\`
   - Check Bases queries and Dataview tables
   - Validate all OEM Hubs render correctly

---

*Generated by normalize_oem_hubs.ts*
`;

  fs.writeFileSync(REPORT_FILE, content, 'utf-8');
  console.log(`\n📄 Report generated: ${REPORT_FILE}`);
}

// Main execution
async function main() {
  console.log('🚀 OEM Hub Normalization\n');
  console.log('═'.repeat(60) + '\n');

  try {
    // Step 1: Dry run
    console.log('STEP 1: DRY RUN\n');
    const dryRunResult = dryRun();
    
    console.log('\n📊 DRY RUN SUMMARY:');
    console.log(`   Total files: ${dryRunResult.totalFiles}`);
    console.log(`   Files to modify: ${dryRunResult.filesToModify}`);
    console.log(`   Files to rename: ${dryRunResult.filesToRename}`);
    console.log(`   Files to create: ${dryRunResult.filesToCreate}`);
    console.log('\n' + '─'.repeat(60) + '\n');

    // Step 2: Backup
    console.log('STEP 2: BACKUP\n');
    const backupPath = createBackup();
    console.log('─'.repeat(60) + '\n');

    // Step 3: Apply normalization
    console.log('STEP 3: APPLY NORMALIZATION\n');
    const changes = applyNormalization(false);
    console.log(`\n✓ Normalized ${changes.length} files`);
    console.log('\n' + '─'.repeat(60) + '\n');

    // Step 4: Create missing OEMs
    console.log('STEP 4: CREATE MISSING OEMS\n');
    const createdOEMs = createMissingOEMs(false);
    if (createdOEMs.length > 0) {
      console.log(`\n✓ Created ${createdOEMs.length} OEMs: ${createdOEMs.join(', ')}`);
    } else {
      console.log('\n✓ All required OEMs exist');
    }
    console.log('\n' + '─'.repeat(60) + '\n');

    // Step 5: Validate
    console.log('STEP 5: VALIDATION\n');
    const validations = validateNormalized();
    console.log('\n' + '─'.repeat(60) + '\n');

    // Step 6: Generate report
    console.log('STEP 6: GENERATE REPORT\n');
    generateReport(dryRunResult, backupPath, validations, createdOEMs);
    console.log('\n' + '═'.repeat(60) + '\n');

    // Step 7: Summary
    console.log('✅ NORMALIZATION COMPLETE\n');
    console.log(`📍 Backup: ${backupPath}`);
    console.log(`📍 Report: ${REPORT_FILE}`);
    console.log('\n🔄 Next: Run `npm run build:partners-base` to rebuild the Partners Base');

  } catch (error) {
    console.error('\n❌ Error during normalization:', error);
    process.exit(1);
  }
}

// Run if executed directly
const isMainModule = import.meta.url === `file://${process.argv[1]}`;
if (isMainModule) {
  main().catch(error => {
    console.error('❌ Fatal error:', error);
    process.exit(1);
  });
}

export { main, dryRun, applyNormalization, createMissingOEMs, validateNormalized };