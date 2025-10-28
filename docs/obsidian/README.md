# Obsidian Integration Documentation

Documentation for Obsidian vault integration, dashboards, and opportunity templates.

## Purpose

This directory contains documentation related to Obsidian vault integration, including:
- Dashboard query examples
- Opportunity template specifications
- Sprint summaries and integration notes
- Obsidian-specific workflows

These files remain browsable on GitHub while supporting Obsidian vault functionality.

## Directory Structure

```
docs/obsidian/
├── dashboards/          # Dashboard query files and examples
├── opportunity/         # Opportunity template notes and specs
├── sprint_summaries/    # Development sprint summaries
└── README.md           # This file
```

## Dashboards

### Opportunities Dashboard
- **Location in Vault:** `obsidian/50 Dashboards/Opportunities Dashboard.md`
- **Features:**
  - Pipeline by Stage with aggregated totals
  - Upcoming Closes (90-day rolling window)
  - By Federal Fiscal Year breakdown
  - Top Opportunities (>$500K)
  - By OEM/Vendor and Customer breakdowns
  - Triage Queue monitoring
  - Recent Activity tracking

### Forecast Dashboard (v1.4.0+)
- **Location in Vault:** `obsidian/50 Dashboards/Forecast Dashboard.md`
- **Features:**
  - FY25/FY26/FY27 projections
  - Confidence distribution (High/Medium/Low)
  - Customer breakdowns by forecast value
  - High-confidence opportunities (≥75%)

## Opportunity Templates

### Template Structure
Opportunity notes include:
- **Frontmatter Fields:**
  - `id`, `title`, `customer`, `oem`, `amount`, `stage`
  - `close_date`, `source`, `type`
  - Dashboard aliases: `est_amount`, `est_close`, `oems`, `partners`, `contract_vehicle`
  - Forecast fields (v1.4.0+): `projected_amount_FY25`, `projected_amount_FY26`, `projected_amount_FY27`, `confidence_score`
  - Triage flag for webhook-ingested opportunities

### Federal FY Routing
Opportunities are automatically routed to fiscal year folders:
- **FY25:** Close dates Oct 2024 - Sep 2025
- **FY26:** Close dates Oct 2025 - Sep 2026
- **Triage:** Invalid or missing close dates

### Dataview Query Pattern
```dataview
TABLE WITHOUT ID
  file.link AS Opportunity,
  customer AS Customer,
  (oems ?? [oem]) AS OEMs,
  (amount ?? est_amount) AS "Est. Amount"
FROM "40 Projects/Opportunities"
WHERE type = "opportunity"
SORT (amount ?? est_amount) DESC
```

## Sprint Summaries

Development sprint summaries documenting integration work:
- Phase 3 integration summary
- Future sprint documentation as they occur

## Integration with Main Vault

The actual Obsidian vault resides at:
```
obsidian/
├── 40 Projects/Opportunities/  # Opportunity notes (FY-routed)
├── 50 Dashboards/              # Live dashboard files
└── 60 Projects/                # Project notes and sprint summaries
```

Documentation here provides reference and examples for vault structure.

## YAML Aliases

Non-breaking aliases enable dashboard compatibility:

| Original | Alias | Purpose |
|----------|-------|---------|
| `amount` | `est_amount` | Numeric aggregations |
| `close_date` | `est_close` | Date filtering |
| `oem` | `oems` | Multi-vendor support (list) |
| N/A | `partners` | Future partner tracking |
| N/A | `contract_vehicle` | Contract type field |

## Webhook Integration (v1.4.0+)

Webhook-ingested opportunities:
- Auto-generated with minimal frontmatter
- Flagged with `triage: true` for manual review
- Located in `Triage/` folder until validated

## Related Documentation
- [Phase 3 Overview](../guides/phase3_overview.md) - Feature details
- [Architecture](../architecture/phase3.md) - System design
- [Releases](../releases/v1.4.0.md) - Latest features

---

**Note:** Obsidian documentation reflects the current vault structure and integration patterns.