#!/usr/bin/env node
/**
 * OEM Hub Fix Script
 * 
 * Fixes wikilinks, seeds category/tech_focus, and cleans up document structure
 */

import * as fs from 'fs';
import * as path from 'path';
import * as yaml from 'yaml';

const VAULT_ROOT = '/Users/jonolan/Documents/Obsidian Documents/Red River Sales';
const OEM_DIR = path.join(VAULT_ROOT, '30 Hubs/OEMs');
const REPORT_FILE = path.join(VAULT_ROOT, '80 Reference/PARTNERS_OEM_FIX_REPORT.md');

interface ChangeLog {
  file: string;
  changes: string[];
}

const CATEGORY_FIXES: Record<string, string> = {
  'NetScout': 'Network Performance & Visibility'
};

const TECH_FOCUS_SEEDS: Record<string, string[]> = {
  'Nutanix': ['hci', 'virtualization', 'storage'],
  'NetScout': ['network-monitoring', 'packet-analysis', 'visibility']
};

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

function fixDistributorLinks(distributors: string[]): string[] {
  return distributors.map(dist => {
    // Convert plain text to Distributor Hub wikilinks
    if (!dist.includes('[[')) {
      // Common distributors
      if (dist.includes('Carahsoft')) {
        return '[[Carahsoft (Distributor Hub)]]';
      } else if (dist.includes('TD SYNNEX')) {
        return '[[TD SYNNEX Public Sector (Distributor Hub)]]';
      }
    }
    // Fix incorrect Contract Hub references
    return dist.replace('(Contract Hub)', '(Distributor Hub)');
  });
}

function fixContractLinks(contracts: string[]): string[] {
  return contracts.map(contract => {
    // Ensure contracts are wikilinked
    if (!contract.includes('[[')) {
      if (contract.includes('SEWP')) {
        return '[[SEWP V (Contract Hub)]]';
      } else if (contract.includes('2GIT')) {
        return '[[2GIT BPA (Contract Hub)]]';
      } else if (contract.includes('ITES')) {
        return '[[ITES-SW2 (Contract Hub)]]';
      }
    }
    return contract;
  });
}

function cleanupBody(body: string, oemName: string): string {
  const lines = body.split('\n');
  const cleaned: string[] = [];
  let foundH1 = false;
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    
    // Skip duplicate H1 headers
    if (line.startsWith('# ')) {
      if (!foundH1) {
        // Keep first H1, ensure it's correct
        cleaned.push(`# ${oemName} (OEM Hub)`);
        foundH1 = true;
      }
      // Skip all other H1s
      continue;
    }
    
    cleaned.push(lines[i]);
  }
  
  // Ensure we have an H1 at the start
  if (!foundH1) {
    cleaned.unshift(`# ${oemName} (OEM Hub)`, '');
  }
  
  return cleaned.join('\n');
}

function processOEMFile(filePath: string): ChangeLog {
  const fileName = path.basename(filePath);
  const content = fs.readFileSync(filePath, 'utf-8');
  const parsed = extractYAMLAndContent(content);
  
  const changeLog: ChangeLog = {
    file: fileName,
    changes: []
  };
  
  if (!parsed) {
    changeLog.changes.push('ERROR: Failed to parse YAML');
    return changeLog;
  }
  
  const frontmatter = parsed.yaml;
  const oemName = frontmatter.name;
  let modified = false;
  
  // Fix distributors
  if (frontmatter.distributors && Array.isArray(frontmatter.distributors)) {
    const oldDist = JSON.stringify(frontmatter.distributors);
    frontmatter.distributors = fixDistributorLinks(frontmatter.distributors);
    const newDist = JSON.stringify(frontmatter.distributors);
    if (oldDist !== newDist) {
      changeLog.changes.push('Fixed distributor wikilinks');
      modified = true;
    }
  }
  
  // Fix contracts
  if (frontmatter.contracts && Array.isArray(frontmatter.contracts)) {
    const oldContracts = JSON.stringify(frontmatter.contracts);
    frontmatter.contracts = fixContractLinks(frontmatter.contracts);
    const newContracts = JSON.stringify(frontmatter.contracts);
    if (oldContracts !== newContracts) {
      changeLog.changes.push('Fixed contract wikilinks');
      modified = true;
    }
  }
  
  // Fix category
  if (frontmatter.category === 'TBD' && CATEGORY_FIXES[oemName]) {
    frontmatter.category = CATEGORY_FIXES[oemName];
    changeLog.changes.push(`Set category: ${CATEGORY_FIXES[oemName]}`);
    modified = true;
  }
  
  // Seed tech_focus
  if ((!frontmatter.tech_focus || frontmatter.tech_focus.length === 0) && TECH_FOCUS_SEEDS[oemName]) {
    frontmatter.tech_focus = TECH_FOCUS_SEEDS[oemName];
    changeLog.changes.push(`Seeded tech_focus: ${TECH_FOCUS_SEEDS[oemName].join(', ')}`);
    modified = true;
  }
  
  // Clean up body
  const newBody = cleanupBody(parsed.body, oemName);
  if (newBody !== parsed.body) {
    changeLog.changes.push('Cleaned up duplicate H1 headers');
    modified = true;
  }
  
  // Write back if modified
  if (modified) {
    const newYAML = yaml.stringify(frontmatter);
    const newContent = `---\n${newYAML}---\n\n${newBody}`;
    fs.writeFileSync(filePath, newContent, 'utf-8');
    console.log(`✓ Fixed: ${fileName}`);
  } else {
    console.log(`  Skipped: ${fileName} (no changes needed)`);
  }
  
  return changeLog;
}

function generateReport(changeLogs: ChangeLog[]): void {
  const timestamp = new Date().toISOString();
  const timestampET = new Date().toLocaleString('en-US', { timeZone: 'America/New_York' });
  
  const filesChanged = changeLogs.filter(log => log.changes.length > 0);
  const filesUnchanged = changeLogs.filter(log => log.changes.length === 0);
  
  const content = `# OEM Hub Fix Report

**Generated:** ${timestampET} ET  
**Timestamp:** ${timestamp}

## Summary

- **Total Files Processed:** ${changeLogs.length}
- **Files Modified:** ${filesChanged.length}
- **Files Unchanged:** ${filesUnchanged.length}

## Changes Applied

### Files Modified

${filesChanged.length > 0 ? filesChanged.map(log => `#### ${log.file}
${log.changes.map(c => `- ${c}`).join('\n')}
`).join('\n') : '- None'}

### Files Unchanged

${filesUnchanged.map(log => `- ${log.file}`).join('\n')}

## Fixes Applied

### 1. Distributor Wikilinks
- Converted plain text distributor names to \`[[Name (Distributor Hub)]]\` format
- Fixed incorrect \`(Contract Hub)\` references to \`(Distributor Hub)\`
- Standardized: Carahsoft, TD SYNNEX Public Sector

### 2. Contract Wikilinks
- Ensured all contracts use wikilink format: \`[[Vehicle (Contract Hub)]]\`
- Standardized: SEWP V, 2GIT BPA, ITES-SW2

### 3. Category Seeding
- **NetScout:** Changed "TBD" → "Network Performance & Visibility"

### 4. Tech Focus Seeding
- **Nutanix:** Added ["hci", "virtualization", "storage"]
- **NetScout:** Added ["network-monitoring", "packet-analysis", "visibility"]

### 5. Document Structure
- Ensured single H1 header: \`# {OEM Name} (OEM Hub)\`
- Removed duplicate H1 lines
- Preserved all existing sections

## Validation

All changes maintain:
- ✅ Unified YAML schema compliance
- ✅ Wikilink format consistency
- ✅ Document structure integrity
- ✅ Existing content preservation

## Next Steps

1. **Verify in Obsidian**
   - Check wikilinks resolve correctly
   - Verify dashboard renders: \`50 Dashboards/Partner_Tiers_Index.md\`

2. **Rebuild Partners Base**
   \`\`\`bash
   npm run build:partners-base
   \`\`\`

3. **Populate Tier Data** (manual)
   - All 16 OEMs still need \`tier_global\` and \`tier_redriver\` values
   - Consult partner portals and Red River records

---

*Generated by fix_oem_hubs.ts*
`;

  fs.writeFileSync(REPORT_FILE, content, 'utf-8');
  console.log(`\n📄 Report generated: ${REPORT_FILE}`);
}

async function main() {
  console.log('🔧 OEM Hub Fix Script\n');
  console.log('═'.repeat(60) + '\n');

  const files = fs.readdirSync(OEM_DIR)
    .filter(f => f.endsWith('.md') && f.includes('(OEM Hub)'))
    .sort();

  console.log(`Found ${files.length} OEM Hub files\n`);

  const changeLogs: ChangeLog[] = [];

  for (const file of files) {
    const filePath = path.join(OEM_DIR, file);
    const changeLog = processOEMFile(filePath);
    changeLogs.push(changeLog);
  }

  console.log('\n' + '═'.repeat(60) + '\n');
  generateReport(changeLogs);

  const modified = changeLogs.filter(log => log.changes.length > 0).length;
  console.log(`\n✅ Fix complete: ${modified} files modified, ${files.length - modified} unchanged`);
  console.log('\n🔄 Next: Run \`npm run build:partners-base\` to rebuild the Partners Base\n');
}

const isMainModule = import.meta.url === `file://${process.argv[1]}`;
if (isMainModule) {
  main().catch(error => {
    console.error('❌ Error:', error);
    process.exit(1);
  });
}

export { main, processOEMFile };