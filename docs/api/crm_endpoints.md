# CRM API Endpoints Reference

**Version:** 2.0.0-rc2 (Phase 12)  
**Base URL:** `http://localhost:8000`

---

## Write-Safety Gate (Phase 12)

**IMPORTANT:** By default, all CRM write operations run in **dry-run mode** to prevent accidental data modifications. This is a safety feature to protect against unintended external changes.

### Key Principles

1. **Default Behavior:** Safe (dry-run mode, no external changes)
2. **Explicit Opt-In Required:** Clients MUST set `"dry_run": false` to perform actual writes
3. **No Ambiguity:** Missing or `null` `dry_run` field defaults to `true` (safe)
4. **Clear Responses:** Response includes `dry_run` field indicating actual mode used

### Usage

**Safe Mode (Default):**
```json
{
  "format": "salesforce"
  // No dry_run field = defaults to true (safe)
}
```

**Explicit Safe Mode:**
```json
{
  "format": "salesforce",
  "dry_run": true
}
```

**Write Mode (Explicit):**
```json
{
  "format": "salesforce",
  "dry_run": false  // REQUIRED for actual writes
}
```

### Response Indicators

**Dry-Run Response:**
```json
{
  "status": "ok",
  "dry_run": true,
  "note": "no external changes applied",
  "total": 10
}
```

**Write-Enabled Response:**
```json
{
  "status": "accepted",
  "dry_run": false,
  "note": "write path allowed but integration target not configured",
  "total": 10
}
```

---

## Endpoints

### POST /v1/crm/export

Export opportunities to CRM system with attribution data.

**Write-Safety:** This endpoint is protected by the write-safety gate. See section above for details.

**Request (Dry-Run, Default):**
```json
{
  "opportunity_ids": ["opp-123"],
  "format": "salesforce"
  // dry_run omitted = defaults to true (safe)
}
```

**Request (Write Mode):**
```json
{
  "opportunity_ids": ["opp-123"],
  "format": "salesforce",
  "dry_run": false  // Explicit false required for writes
}
```

**Response (Dry-Run):**
```json
{
  "request_id": "uuid",
  "status": "ok",
  "dry_run": true,
  "note": "no external changes applied",
  "total": 1,
  "opportunities_validated": 1,
  "format": "salesforce"
}
```

**Response (Write Mode):**
```json
{
  "request_id": "uuid",
  "status": "accepted",
  "dry_run": false,
  "note": "write path allowed but integration target not configured",
  "total": 1,
  "format": "salesforce",
  "would_export": 1
}
```

**Parameters:**
- `opportunity_ids` (optional): Array of opportunity IDs to export. If omitted, exports all.
- `format` (required): CRM format - see GET /v1/crm/formats for options
- `dry_run` (optional): Boolean. Defaults to `true` (safe). Must explicitly set to `false` for writes.

### POST /v1/crm/attribution

Calculate revenue attribution for opportunities.

**Response:**
```json
{
  "total": 2,
  "attributions": [{
    "opportunity_id": "opp-123",
    "oem_attribution": {"Microsoft": 600000, "Cisco": 300000},
    "partner_attribution": {"Partner A": 100000},
    "region": "East",
    "total_amount": 1000000
  }]
}
```

### GET /v1/crm/formats

Get supported CRM formats.

**Response:**
```json
["salesforce", "hubspot", "dynamics", "generic_json", "generic_yaml"]
```

### GET /v1/crm/validate/{opportunity_id}

Validate opportunity for CRM export.

**Response:**
```json
{
  "opportunity_id": "opp-123",
  "valid": true,
  "errors": []
}
```

---

## Field Mappings

### Salesforce Mapping

| Obsidian Field | Salesforce Field | Type |
|----------------|------------------|------|
| title | Name | string |
| customer_org | AccountId | string |
| amount | Amount | decimal |
| close_date | CloseDate | date |
| stage | StageName | picklist |
| oems[0] | OEM_Primary__c | string |
| partners | Partner_Names__c | string |
| contract_vehicle | Contract_Vehicle__c | string |
| forecast.projected_amount_FY25 | FY25_Forecast__c | decimal |
| forecast.win_prob | Win_Probability__c | percent |
| region | Region__c | string |

---

See full guide: [`docs/guides/crm_sync.md`](../guides/crm_sync.md)
