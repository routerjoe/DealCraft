# CRM API Endpoints Reference

**Version:** 1.6.0 (Phase 6)  
**Base URL:** `http://localhost:8000`

---

## Endpoints

### POST /v1/crm/export

Export opportunities to CRM system with attribution data.

**Request:**
```json
{
  "opportunity_ids": ["opp-123"],
  "format": "salesforce",
  "dry_run": true
}
```

**Response:**
```json
{
  "request_id": "uuid",
  "total": 1,
  "success_count": 1,
  "error_count": 0,
  "dry_run": true,
  "results": [{
    "success": true,
    "opportunity_id": "opp-123",
    "format": "salesforce",
    "formatted_data": {...}
  }]
}
```

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