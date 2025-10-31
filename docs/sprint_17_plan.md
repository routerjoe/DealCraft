# Sprint 17: Partner Tier Sync

**Status**: ✅ Implemented  
**Version**: 1.8.1  
**Branch**: feature/sprint17-partner-sync

## Overview

Partner Tier Sync provides capability to:
- Load partner tier data from CSV/JSON files
- Normalize and validate partner records
- Compute diffs vs existing data
- Update OEM store atomically
- Export to Obsidian markdown

## Architecture

### Core Module
`mcp/core/partners_sync.py`

- **PartnerTierRecord**: Normalized partner tier data model
- **PartnerTierSync**: Main sync orchestrator

### API Endpoints
`mcp/api/v1/partners.py`

Three endpoints:
1. `GET /v1/partners/tiers` - List all partner tiers
2. `POST /v1/partners/sync` - Sync partner data
3. `GET /v1/partners/export/obsidian` - Export to markdown

### Data Storage
- **Store Location**: `data/oems.json`
- **Input Location**: `data/partners/`
- **Output Location**: `$VAULT_ROOT/30 Hubs/OEMs/`

## Data Schema

### Partner Tier Record

```json
{
  "name": "Red River Technology",
  "tier": "Gold",
  "program": "Cisco PTP",
  "oem": "Cisco",
  "poc": "John Doe",
  "notes": "Premier partner",
  "updated_at": "2025-10-30T20:00:00Z",
  "created_at": "2025-10-30T20:00:00Z"
}
```

### Required Fields
- `name` - Partner name
- `tier` - Partner tier (Platinum/Gold/Silver/etc)
- `program` - Partner program name
- `oem` - OEM vendor name

### Optional Fields
- `poc` - Point of contact
- `notes` - Additional notes
- `updated_at` - Last update timestamp (UTC ISO8601)
- `created_at` - Initial creation timestamp (UTC ISO8601)

## Data Formats

### CSV Format

```csv
name,tier,program,oem,poc,notes
Red River Technology,Gold,Cisco PTP,Cisco,John Doe,Premier partner
Tech Solutions,Platinum,Nutanix Elevate,Nutanix,Jane Smith,Top tier
```

**Location**: `data/partners/partners_*.csv`

### JSON Format

```json
{
  "partners": [
    {
      "name": "Red River Technology",
      "tier": "Gold",
      "program": "Cisco PTP",
      "oem": "Cisco",
      "poc": "John Doe",
      "notes": "Premier partner"
    }
  ]
}
```

**Location**: `data/partners/partners_*.json`

## API Usage

### 1. List Partner Tiers

```bash
curl -s http://localhost:8000/v1/partners/tiers | jq
```

**Response**:
```json
[
  {
    "name": "Red River Technology",
    "tier": "Gold",
    "program": "Cisco PTP",
    "oem": "Cisco",
    "poc": "John Doe",
    "notes": "Premier partner",
    "updated_at": "2025-10-30T20:00:00Z",
    "created_at": "2025-10-30T20:00:00Z"
  }
]
```

**Headers**:
- `x-request-id`: Unique request identifier
- `x-latency-ms`: Request latency in milliseconds

### 2. Sync Partner Data

#### Dry Run (Default)

```bash
curl -s -X POST http://localhost:8000/v1/partners/sync \
  -H "Content-Type: application/json" \
  -d '{"dry_run": true}' | jq
```

**Response**:
```json
{
  "dry_run": true,
  "added": [
    {
      "name": "New Partner",
      "tier": "Silver",
      "program": "AWS Partner Network",
      "oem": "AWS",
      "poc": null,
      "notes": null,
      "updated_at": "2025-10-30T20:00:00Z",
      "created_at": "2025-10-30T20:00:00Z"
    }
  ],
  "updated": [],
  "unchanged": [],
  "applied": false
}
```

#### Actual Sync

```bash
curl -s -X POST http://localhost:8000/v1/partners/sync \
  -H "Content-Type: application/json" \
  -d '{"dry_run": false}' | jq
```

**Response**:
```json
{
  "dry_run": false,
  "added": [...],
  "updated": [...],
  "unchanged": [...],
  "applied": true
}
```

**Headers**:
- `x-request-id`: Unique request identifier
- `x-latency-ms`: Request latency in milliseconds

### 3. Export to Obsidian

```bash
curl -s http://localhost:8000/v1/partners/export/obsidian | jq
```

**Response**:
```json
{
  "status": "success",
  "files_written": [
    "/path/to/vault/30 Hubs/OEMs/Cisco.md",
    "/path/to/vault/30 Hubs/OEMs/Nutanix.md"
  ],
  "oems_count": 2
}
```

**Headers**:
- `x-request-id`: Unique request identifier
- `x-latency-ms`: Request latency in milliseconds

**Requirements**:
- `VAULT_ROOT` environment variable must be set
- Creates directory structure: `$VAULT_ROOT/30 Hubs/OEMs/`

## Obsidian Export Format

Per-OEM markdown files are created at:
```
$VAULT_ROOT/30 Hubs/OEMs/<oem_name>.md
```

### Example Output

**File**: `Cisco.md`

```markdown
# Cisco

## Partner Tiers

### Red River Technology
- **Tier**: Gold
- **Program**: Cisco PTP
- **POC**: John Doe
- **Notes**: Premier partner
- **Updated**: 2025-10-30T20:00:00Z

### Global Tech Partners
- **Tier**: Platinum
- **Program**: Cisco Premier
- **POC**: Jane Smith
- **Updated**: 2025-10-30T20:00:00Z
```

## Normalization

### Tier Normalization
- `platinum` → `Platinum`
- `gold` → `Gold`
- `silver` → `Silver`
- `bronze` → `Bronze`
- Other values title-cased

### OEM Normalization
Common OEM names are normalized:
- `cisco` → `Cisco`
- `nutanix` → `Nutanix`
- `dell` → `Dell`
- `hp` → `HP`
- `hpe` → `HPE`
- `vmware` → `VMware`
- `microsoft` → `Microsoft`
- `aws` → `AWS`
- `red hat` → `Red Hat`

### Data Cleanup
- Whitespace trimmed from all fields
- Empty strings converted to `None`
- Timestamps auto-generated if missing

## Diff Logic

The sync computes three categories:

1. **Added**: Partners not in existing store
2. **Updated**: Partners with changed fields (tier, program, oem, poc, notes)
3. **Unchanged**: Partners with identical data

**Note**: `created_at` is preserved for updated records.

## Testing

### Run Tests

```bash
pytest tests/test_partners_sync_contract.py -v
```

### Test Coverage

- PartnerTierRecord normalization
- CSV loading
- JSON loading
- Record validation
- Diff computation
- Dry-run mode
- Write operations
- Obsidian export
- API endpoint contracts

## Environment Variables

### Required for Obsidian Export
- `VAULT_ROOT` - Path to Obsidian vault root directory

### Example
```bash
export VAULT_ROOT="/Users/username/Documents/Obsidian"
```

## Error Handling

### Common Errors

1. **Missing VAULT_ROOT** (Export endpoint)
   ```json
   {
     "detail": "VAULT_ROOT environment variable not set"
   }
   ```

2. **Invalid Data Format**
   ```json
   {
     "detail": "Validation failed: Record 0: missing name"
   }
   ```

3. **File Loading Error**
   ```json
   {
     "detail": "Failed to load data/partners/partners.csv: ..."
   }
   ```

## Backward Compatibility

- Existing OEMStore format preserved
- Old OEMPartner records compatible
- No breaking changes to existing endpoints

## Future Enhancements

- [ ] Support for additional data formats (YAML, XML)
- [ ] Partner relationship tracking
- [ ] Historical change tracking
- [ ] Automated sync scheduling
- [ ] Partner tier alerts/notifications
- [ ] Integration with CRM systems

## Version History

### 1.8.1 (Current)
- Full partner tier sync implementation
- CSV/JSON data loading
- Schema normalization
- Diff computation
- Obsidian markdown export
- Comprehensive test suite

### 1.8.0
- Initial stub implementation
- Basic API endpoint contracts

## Related Documentation

- [Sprint Index](sprint_index.md)
- [API Endpoints](api/endpoints.md)
- [OEM Intelligence Guide](guides/oem_intel.md)