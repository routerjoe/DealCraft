# OEM Partner Intelligence Guide

## Overview

The OEM Partner Intelligence feature (Phase 16) provides a comprehensive system for tracking and managing relationships with Original Equipment Manufacturer (OEM) partners. This feature enables you to:

- Store and manage OEM partner information
- Track partner tiers, contacts, and notes
- Export partner data in Obsidian-compatible markdown format
- Query partner information via REST API

## Data Model

### OEMPartner

Each OEM partner is represented with the following fields:

- **oem_name** (string, required): The name of the OEM partner
- **tier** (string, required): Partner tier level (e.g., "Platinum", "Gold", "Silver", "Diamond")
- **partner_poc** (string, optional): Partner point of contact name
- **notes** (string, optional): Additional notes about the partnership
- **updated_at** (datetime, auto-generated): Timestamp of last update (UTC)

### Storage

- Data is persisted to `data/oems.json` as a JSON array
- File is auto-created if missing
- No secrets or sensitive data should be stored
- Atomic write operations ensure data integrity

## API Endpoints

All OEM Partner Intelligence endpoints are under `/v1/oems`:

### Get All OEM Partners

```bash
GET /v1/oems/all
```

Returns a list of all OEM partners with their details.

**Response:** 200 OK
```json
[
  {
    "oem_name": "Dell Technologies",
    "tier": "Platinum",
    "partner_poc": "John Doe",
    "notes": "Primary hardware vendor",
    "updated_at": "2025-10-30T23:15:00.123456Z"
  }
]
```

### Add or Update OEM Partner

```bash
POST /v1/oems/add
Content-Type: application/json

{
  "oem_name": "Dell Technologies",
  "tier": "Platinum",
  "partner_poc": "John Doe",
  "notes": "Primary hardware vendor"
}
```

If a partner with the same `oem_name` exists, it will be updated. Otherwise, a new partner is created.

**Response:** 201 Created
```json
{
  "oem_name": "Dell Technologies",
  "tier": "Platinum",
  "partner_poc": "John Doe",
  "notes": "Primary hardware vendor",
  "updated_at": "2025-10-30T23:15:00.123456Z"
}
```

### Get Specific OEM Partner

```bash
GET /v1/oems/{name}
```

Retrieves details for a specific OEM partner by name.

**Example:**
```bash
curl http://localhost:8000/v1/oems/Dell%20Technologies
```

**Response:** 200 OK (partner found) or 404 Not Found

### Export to Obsidian Markdown

```bash
GET /v1/oems/export/obsidian
```

Exports all OEM partners as Obsidian-compatible markdown text. This endpoint returns plain text, not JSON.

**Response:** 200 OK (text/plain)

## Usage Examples

### Using cURL

**Add a new OEM partner:**
```bash
curl -X POST http://localhost:8000/v1/oems/add \
  -H "Content-Type: application/json" \
  -d '{
    "oem_name": "Cisco Systems",
    "tier": "Diamond",
    "partner_poc": "Sarah Johnson",
    "notes": "Networking infrastructure partner"
  }'
```

**Get all partners:**
```bash
curl http://localhost:8000/v1/oems/all
```

**Get specific partner:**
```bash
curl http://localhost:8000/v1/oems/Cisco%20Systems
```

**Export to markdown:**
```bash
curl http://localhost:8000/v1/oems/export/obsidian > oem_partners.md
```

### Using Python

```python
import requests

BASE_URL = "http://localhost:8000"

# Add a partner
response = requests.post(
    f"{BASE_URL}/v1/oems/add",
    json={
        "oem_name": "HP Inc",
        "tier": "Gold",
        "partner_poc": "Mike Smith",
        "notes": "Print and compute solutions"
    }
)
print(response.json())

# Get all partners
response = requests.get(f"{BASE_URL}/v1/oems/all")
partners = response.json()
print(f"Total partners: {len(partners)}")

# Export markdown
response = requests.get(f"{BASE_URL}/v1/oems/export/obsidian")
with open("oem_partners.md", "w") as f:
    f.write(response.text)
```

## Markdown Export Format

The Obsidian export produces markdown in the following format:

```markdown
# OEM Partners

## OEM: Cisco Systems
Tier: Diamond
POC: Sarah Johnson
Updated: 2025-10-30 23:15:00 UTC
Notes:
Networking infrastructure partner

## OEM: Dell Technologies
Tier: Platinum
POC: John Doe
Updated: 2025-10-30 23:10:00 UTC
Notes:
Primary hardware vendor

## OEM: HP Inc
Tier: Gold
POC: Mike Smith
Updated: 2025-10-30 23:12:00 UTC
Notes:
Print and compute solutions
```

Partners are sorted alphabetically by name. If a field is empty, it shows "N/A".

## Headers

All API responses include standard headers:
- `x-request-id`: Unique request identifier for tracking
- `x-latency-ms`: Request processing time in milliseconds

## Error Handling

### 404 Not Found
Returned when requesting a specific partner that doesn't exist:
```json
{
  "detail": "OEM partner 'NonExistent' not found"
}
```

### 422 Unprocessable Entity
Returned when request data is invalid (e.g., missing required fields):
```json
{
  "detail": [
    {
      "loc": ["body", "oem_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## Best Practices

1. **Unique Names**: Use consistent naming for OEM partners (e.g., "Dell Technologies" not "Dell" or "DELL")
2. **Tier Naming**: Standardize tier names across your organization (e.g., "Platinum", "Gold", "Silver")
3. **Regular Updates**: Update partner information when POCs or tier status changes
4. **Export Regularly**: Use the Obsidian export to sync with your knowledge base
5. **No Secrets**: Never store passwords, API keys, or other sensitive data in notes

## Integration with Obsidian

The markdown export is designed to integrate seamlessly with Obsidian:

1. Export OEM data using the `/v1/oems/export/obsidian` endpoint
2. Save the output to your Obsidian vault (e.g., `Partners/OEM_Partners.md`)
3. Use Obsidian's search and linking features to cross-reference with opportunities
4. Set up automated exports using cron or scheduled tasks

Example automated export script:
```bash
#!/bin/bash
# Export OEM partners to Obsidian vault
curl -s http://localhost:8000/v1/oems/export/obsidian > ~/ObsidianVault/Partners/OEM_Partners.md
echo "OEM partners exported at $(date)"
```

## Testing

Run the comprehensive test suite:
```bash
pytest tests/test_oems_phase16.py -v
```

The tests cover:
- Data model validation
- Store persistence and loading
- CRUD operations
- Markdown export formatting
- API endpoint functionality
- System contracts (headers, /v1/info)

## Troubleshooting

### Issue: "Failed to load OEM data"
**Cause**: Corrupted JSON file
**Solution**: Delete `data/oems.json` and restart - it will auto-create

### Issue: Partner not appearing in export
**Cause**: Partner may not have been saved
**Solution**: Check response from `/v1/oems/add` for success status

### Issue: Cannot find partner by name
**Cause**: Name mismatch or URL encoding issue
**Solution**: Use exact name with proper URL encoding (spaces as `%20`)

## Related Documentation

- [API Endpoints Overview](../api/endpoints.md)
- [Obsidian Integration](../obsidian/README.md)
- [CRM Sync Guide](./crm_sync.md)

## Version History

- **v1.7.0** (Phase 16): Initial OEM Partner Intelligence implementation
