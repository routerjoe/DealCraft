# Partners Base System

A comprehensive system for managing OEM partner tier information in Obsidian, providing both SQLite database access (via Bases plugin) and Dataview fallback queries.

## Overview

The Partners Base System scans OEM Hub YAML files, extracts partner tier data, and generates:

1. **JSONL Data File** - Machine-readable tier data
2. **SQLite Database** - For interactive Bases plugin queries
3. **Markdown Dashboard** - Visual interface with Bases and Dataview queries
4. **Sync Report** - Build statistics and anomalies

## Architecture

```
Obsidian Vault Structure:
├── 30 Hubs/OEMs/              # Source: OEM Hub markdown files with YAML
├── 50 Dashboards/              # Output: Partner_Tiers_Index.md
└── 80 Reference/
    ├── bases/                  # Output: partners.db (SQLite)
    ├── data/                   # Output: partners_tiers.jsonl
    └── PARTNERS_BASE_REPORT.md # Output: Sync report
```

## Data Model

### YAML Schema (in OEM Hub files)

```yaml
---
name: "OEM Company Name"
status: "active" | "optional" | "inactive"
distributors:
  - "[[Distributor Name (Contract Hub)]]"
program_tiers:           # Optional - populated when available
  - program: "Partner Program Name"
    tier: "Gold" | "Silver" | etc.
    as_of: "2024-01-01"
    source_doc: "[[Source Document]]"
red_river_tier:          # Optional - Red River's specific tier
  program: "Program Name"
  tier: "Platinum"
  as_of: "2024-01-01"
  source_doc: "[[Source Document]]"
reseller_tiers:          # Optional - Reseller/vehicle specific tiers
  - reseller: "Reseller Name"
    vehicle: "SEWP V" | "ITES-SW2" | etc.
    oem_program: "Program Name"
    tier: "Gold"
    as_of: "2024-01-01"
    source_doc: "[[Source Document]]"
---
```

### Database Schema

**oems**
- `id` (INTEGER PRIMARY KEY)
- `company` (TEXT UNIQUE)
- `status` (TEXT)
- `updated_at` (TEXT)

**program_tiers**
- `id` (INTEGER PRIMARY KEY)
- `oem_id` (INTEGER FK → oems.id)
- `program` (TEXT)
- `tier` (TEXT)
- `as_of` (TEXT)
- `source_doc` (TEXT)

**red_river_tiers**
- `id` (INTEGER PRIMARY KEY)
- `oem_id` (INTEGER FK → oems.id)
- `program` (TEXT)
- `tier` (TEXT)
- `as_of` (TEXT)
- `source_doc` (TEXT)

**reseller_tiers**
- `id` (INTEGER PRIMARY KEY)
- `oem_id` (INTEGER FK → oems.id)
- `reseller` (TEXT)
- `vehicle` (TEXT)
- `oem_program` (TEXT)
- `tier` (TEXT)
- `as_of` (TEXT)
- `source_doc` (TEXT)

**distributors**
- `id` (INTEGER PRIMARY KEY)
- `oem_id` (INTEGER FK → oems.id)
- `name` (TEXT)

## Usage

### Build/Rebuild the System

```bash
# From project root
npm run build:partners-base
```

This command:
1. Scans all `30 Hubs/OEMs/*.md` files
2. Extracts YAML frontmatter
3. Creates/updates JSONL data file
4. Rebuilds SQLite database
5. Generates dashboard with queries
6. Creates sync report

### Viewing Data

#### Option 1: Bases Plugin (Recommended)

Open `50 Dashboards/Partner_Tiers_Index.md` in Obsidian with the Bases plugin installed. The dashboard provides interactive SQL queries:

- **OEM Summary** - Overview of all OEMs with tier counts
- **Program Tiers** - Filterable list of all program tiers
- **Reseller Tiers** - Reseller/vehicle specific tier information
- **Distributors** - Distribution partners by OEM

#### Option 2: Dataview Fallback

If Bases plugin is not available, the same dashboard includes Dataview queries that read directly from the JSONL file.

### Adding Tier Data

To add tier information to an OEM:

1. Edit the OEM Hub file (e.g., `30 Hubs/OEMs/Cisco (OEM Hub).md`)
2. Add tier data to the YAML frontmatter:

```yaml
---
name: Cisco
status: optional
distributors:
  - "[[Carahsoft (Contract Hub)]]"
program_tiers:
  - program: "Cisco Partner Program"
    tier: "Gold"
    as_of: "2024-01-15"
    source_doc: "[[Partner Agreement 2024]]"
red_river_tier:
  program: "Cisco Federal"
  tier: "Platinum"
  as_of: "2024-01-15"
  source_doc: "[[RR Tier Letter]]"
---
```

3. Rebuild the system: `npm run build:partners-base`

## Features

### Idempotent Operation

The system is designed to be run repeatedly without side effects:
- Database is recreated from scratch each run
- JSONL file is overwritten
- Dashboard and report are regenerated
- No manual cleanup required

### Data Integrity

- YAML files remain authoritative source
- No modifications to OEM Hub content
- Wiki links (`[[...]]`) are normalized in database
- Foreign key constraints ensure referential integrity

### Extensibility

The schema supports future extensions:
- Additional tier types (e.g., `technical_tiers`, `support_tiers`)
- Custom fields per tier type
- Historical tier tracking
- Multi-program support per OEM

### Error Handling

- Validates YAML structure
- Reports parse failures
- Lists anomalies in sync report
- Continues processing on individual file errors

## File Structure

```
src/tools/partners/
├── build_partners_base.ts    # Main builder script
└── README.md                  # This file

Generated files (in Obsidian vault):
├── 50 Dashboards/
│   └── Partner_Tiers_Index.md
└── 80 Reference/
    ├── bases/
    │   └── partners.db
    ├── data/
    │   └── partners_tiers.jsonl
    └── PARTNERS_BASE_REPORT.md
```

## Dependencies

- `sql.js` - SQLite database in-memory operations
- `yaml` - YAML parsing
- `fs`, `path` - Node.js file system operations

## Maintenance

### Sync Report

After each build, check `80 Reference/PARTNERS_BASE_REPORT.md` for:
- Parse success/failure counts
- Detected anomalies
- Record statistics
- Generated file locations

### Troubleshooting

**Problem:** YAML parse errors
- **Solution:** Validate YAML syntax in affected OEM Hub file

**Problem:** Missing tier data
- **Solution:** Tier fields are optional; system works with minimal data

**Problem:** Bases queries not working
- **Solution:** Verify Bases plugin is installed; fall back to Dataview queries

## Future Enhancements

Potential features for future development:

1. **Tier History Tracking** - Track tier changes over time
2. **Automated Alerts** - Notify when tiers change or expire
3. **Tier Comparison** - Compare Red River tier vs. standard tiers
4. **Export Formats** - CSV, Excel, or JSON exports
5. **API Integration** - Sync with external partner portals
6. **Visual Analytics** - Charts and graphs in dashboard

## Related Documentation

- [Obsidian Bases Plugin](https://github.com/RafaelGB/obsidian-db-folder)
- [Obsidian Dataview Plugin](https://blacksmithgu.github.io/obsidian-dataview/)
- [SQL.js Documentation](https://sql.js.org/)

---

*Last Updated: 2025-10-28*