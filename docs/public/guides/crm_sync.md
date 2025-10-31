# CRM Sync & Attribution Engine - Technical Guide

**Version:** 1.6.0 (Phase 6)  
**Last Updated:** October 29, 2025

---

## Overview

The CRM Sync & Attribution Engine provides bidirectional integration with CRM systems, revenue attribution tracking, and automated opportunity metadata enrichment.

### Key Features

- **Multi-CRM Support** - Salesforce, HubSpot, Dynamics, Generic JSON/YAML
- **Attribution Engine** - Revenue split across OEMs, partners, regions, teams
- **Validation Framework** - Pre-export validation with detailed error reporting
- **Dry-Run Mode** - Safe testing without actual CRM writes (default: ON)
- **Forecast Integration** - Automatic inclusion of Phase 5 scoring data

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              CRM Sync & Attribution                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │      Attribution Engine                         │    │
│  │  - OEM Revenue Split (60/30/10)                │    │
│  │  - Partner Revenue Pool (20%)                  │    │
│  │  - Region/Team Assignment                      │    │
│  │  - Customer Organization Mapping               │    │
│  └────────────────────────────────────────────────┘    │
│                          ↓                               │
│  ┌────────────────────────────────────────────────┐    │
│  │     Validation & Formatting                     │    │
│  │  - Required Field Checks                       │    │
│  │  - Data Type Validation                        │    │
│  │  - CRM-Specific Formatting                     │    │
│  │  - Forecast Data Integration                   │    │
│  └────────────────────────────────────────────────┘    │
│                          ↓                               │
│  ┌────────────────────────────────────────────────┐    │
│  │       CRM Export Layer                          │    │
│  │  - Salesforce Format                           │    │
│  │  - HubSpot Format                              │    │
│  │  - Generic JSON/YAML                           │    │
│  │  - Dry-Run Safety                              │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Attribution Engine

### Revenue Attribution Model

#### OEM Attribution (Primary/Secondary/Tertiary)

| Position   | Weight | Example (on $1M deal) |
|------------|--------|----------------------|
| Primary    | 60%    | $600,000            |
| Secondary  | 30%    | $300,000            |
| Tertiary   | 10%    | $100,000            |

#### Partner Attribution

- **Pool:** 20% of total deal value
- **Split:** Equal distribution among all partners
- **Example:** 2 partners on $1M deal = $100K each

### Attribution Calculation

```python
from mcp.core.crm_sync import attribution_engine

opportunity = {
    "oems": ["Microsoft", "Cisco"],
    "partners": ["Partner A", "Partner B"],
    "amount": 1000000,
    "region": "East",
    "customer_org": "Department of Defense"
}

attribution = attribution_engine.calculate_full_attribution(opportunity)

# Result:
{
    "oem_attribution": {
        "Microsoft": 600000.0,
        "Cisco": 300000.0
    },
    "partner_attribution": {
        "Partner A": 100000.0,
        "Partner B": 100000.0
    },
    "region": "East",
    "customer_org": "Department of Defense",
    "total_amount": 1000000,
    "attribution_method": "multi_factor_v1",
    "calculated_at": "2025-10-29T01:00:00Z"
}
```

---

## CRM Sync Engine

### Supported Formats

1. **Salesforce** - Standard object mapping
2. **HubSpot** - Deal properties format
3. **Dynamics** - Entity field mapping
4. **Generic JSON** - Complete data export
5. **Generic YAML** - Human-readable export

### Validation Rules

#### Required Fields

- `id` - Unique identifier
- `title` - Opportunity name
- `customer` - Customer name
- `amount` - Deal value (must be > 0)
- `stage` - Current sales stage
- `close_date` - Expected close (ISO 8601)

#### Field Validations

- **Amount:** Must be positive number
- **Close Date:** Valid ISO 8601 format
- **Stage:** Non-empty string
- **All Required:** Must be present and non-empty

### Dry-Run Mode

**Default:** `dry_run=True` (safe by default)

- Validates all data
- Generates formatted output
- **Does NOT** push to CRM
- Returns preview of what would be synced

**Production Mode:** `dry_run=False`
- Performs actual CRM sync
- Requires explicit opt-in
- Logs all sync operations

---

## YAML Schema Extensions (Phase 6)

Added to Obsidian opportunity frontmatter:

```yaml
# Phase 6: CRM & Attribution Fields
customer_org: "Department of Defense"
customer_poc: "[[John Doe (People Hub)]]"
region: "East"
partner_attribution:
  - Partner A
  - Partner B
oem_attribution:
  - Microsoft
  - Cisco
rev_attribution: {}
lifecycle_notes: "Multi-year strategic initiative"
```

---

## Usage Examples

### Export to CRM

```bash
curl -X POST http://localhost:8000/v1/crm/export \
  -H "Content-Type: application/json" \
  -d '{
    "opportunity_ids": ["opp-123"],
    "format": "salesforce",
    "dry_run": true
  }'
```

### Calculate Attribution

```bash
curl -X POST http://localhost:8000/v1/crm/attribution \
  -H "Content-Type: application/json" \
  -d '{
    "opportunity_ids": ["opp-123", "opp-456"]
  }'
```

### Validate Opportunity

```bash
curl http://localhost:8000/v1/crm/validate/opp-123
```

### Get Supported Formats

```bash
curl http://localhost:8000/v1/crm/formats
```

---

## Integration with Phase 5 Forecast

CRM exports automatically include forecast scoring data:

```json
{
  "FY25_Forecast__c": 800000.00,
  "FY26_Forecast__c": 150000.00,
  "FY27_Forecast__c": 50000.00,
  "Win_Probability__c": 72.5,
  "Confidence_Score__c": 85,
  "OEM_Alignment_Score__c": 95.0,
  "Partner_Fit_Score__c": 75.0
}
```

---

## Best Practices

### 1. Always Validate First

```bash
# Validate before export
curl http://localhost:8000/v1/crm/validate/opp-123

# If valid, then export
curl -X POST http://localhost:8000/v1/crm/export \
  -d '{"opportunity_ids": ["opp-123"], "dry_run": true}'
```

### 2. Use Dry-Run for Testing

```python
# Test export format
result = crm_sync_engine.export_opportunity(opp, format="salesforce", dry_run=True)
formatted_data = result["formatted_data"]
# Review formatted_data before production sync
```

### 3. Batch Processing

```bash
# Export multiple opportunities at once
curl -X POST http://localhost:8000/v1/crm/export \
  -d '{
    "opportunity_ids": ["opp-1", "opp-2", "opp-3"],
    "format": "salesforce",
    "dry_run": false
  }'
```

---

## Troubleshooting

### Issue: Validation Failures

**Symptoms:** Export returns `success: false` with errors

**Common Causes:**
- Missing required fields
- Invalid amount (≤ 0)
- Invalid close_date format
- Empty customer/title

**Solution:**
```bash
# Check validation errors
curl http://localhost:8000/v1/crm/validate/opp-123

# Fix YAML frontmatter
# Re-validate
```

### Issue: Attribution Not Calculating

**Cause:** Missing OEMs or partners in opportunity data

**Solution:**
- Ensure `oems` is a list (even with one OEM)
- Ensure `partners` is a list (can be empty)
- Use Obsidian YAML format with list syntax

---

## References

- API Documentation: [`/docs/api/crm_endpoints.md`](../api/crm_endpoints.md)
- Code: [`mcp/api/v1/crm.py`](../../mcp/api/v1/crm.py)
- Engine: [`mcp/core/crm_sync.py`](../../mcp/core/crm_sync.py)
- Tests: [`tests/test_crm_sync.py`](../../tests/test_crm_sync.py)