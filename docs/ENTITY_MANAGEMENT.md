# Entity Management Guide

## Overview

DealCraft's Entity Management System (EMS) provides centralized management for:
- **OEMs** - Original Equipment Manufacturers (Microsoft, Cisco, Dell, etc.)
- **Partners** - Technology partners and resellers
- **Customers** - Government agencies and departments
- **Distributors** - Distribution partners
- **Regions** - Geographic regions with performance bonuses
- **Contract Vehicles** - Government contract vehicles (SEWP V, GSA Schedule, etc.)

All entity data is stored in JSON files in `data/entities/` and is automatically used by the scoring and recommendation engines.

## Data Location

```
data/entities/
├── oems.json               # OEM data
├── partners.json           # Partner data
├── customers.json          # Customer data
├── distributors.json       # Distributor data
├── regions.json            # Region data
└── contract_vehicles.json  # Contract vehicle data
```

## Methods for Managing Entities

### 1. DealCraft TUI (Terminal UI) ⭐ **BEST FOR REAL-TIME MANAGEMENT**

The TUI provides a visual interface for managing entities in real-time:

```bash
# Start the DealCraft TUI
python3 tui/app.py

# Or if you have an alias set up
dctui
```

**In the TUI:**
- Press **`8`** to open Entity Management
- Use **`1-6`** to switch between entity types:
  - `1` = OEMs
  - `2` = Contract Vehicles
  - `3` = Customers
  - `4` = Partners
  - `5` = Distributors
  - `6` = Regions
- Press **`d`** to deactivate selected entity
- Press **`r`** to refresh the list
- Press **`Escape`** or **`q`** to go back

**Features:**
- ✅ Visual table display of all entities
- ✅ Real-time view of entity counts
- ✅ Easy navigation with keyboard shortcuts
- ✅ Soft-delete entities (deactivate)
- ✅ Color-coded status (Active/Inactive)
- ✅ Quick filtering by entity type

**Note:** Adding new entities via TUI will be available in a future update. For now, use the CLI tool for adding entities.

### 2. Interactive CLI Tool (Best for Adding Entities)

Use the management script for easy interactive entity management:

```bash
# Interactive mode - shows menu
python3 scripts/manage_entities.py

# Command-line mode - quick operations
python3 scripts/manage_entities.py list-oems
python3 scripts/manage_entities.py list-customers
python3 scripts/manage_entities.py list-cvs
python3 scripts/manage_entities.py add-oem
python3 scripts/manage_entities.py add-customer
python3 scripts/manage_entities.py add-cv
```

**Example: Adding a New OEM**

```bash
python3 scripts/manage_entities.py add-oem

# You'll be prompted for:
# - OEM ID (e.g., 'juniper')
# - OEM Name (e.g., 'Juniper Networks')
# - Tier (Strategic/Gold/Silver)
# - Programs (comma-separated)
# - Contact information (optional)
```

**Example: Listing All Contract Vehicles**

```bash
python3 scripts/manage_entities.py list-cvs
```

### 3. Direct JSON Editing

You can edit the JSON files directly in `data/entities/`, but ensure you maintain the correct structure:

**Example OEM Entry:**
```json
{
  "id": "juniper",
  "name": "Juniper Networks",
  "active": true,
  "created_at": "2025-11-02T00:00:00+00:00",
  "updated_at": "2025-11-02T00:00:00+00:00",
  "metadata": {},
  "tier": "Gold",
  "contact_name": "John Doe",
  "contact_email": "john@juniper.com",
  "contact_phone": "+1-555-0100",
  "programs": ["Routing", "Switching", "Security"],
  "certifications": [],
  "notes": "Focus on federal networking projects"
}
```

**Important:** Changes to JSON files are loaded automatically when the API starts.

### 4. Python Scripts

Create custom Python scripts for bulk operations:

```python
#!/usr/bin/env python3
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.core.entities import OEM, oem_store

# Add a new OEM
new_oem = OEM(
    id="juniper",
    name="Juniper Networks",
    tier="Gold",
    programs=["Routing", "Switching", "Security"],
    contact_email="partners@juniper.com"
)

oem_store.add(new_oem)
print(f"Added OEM: {new_oem.name}")

# Update an existing OEM
oem = oem_store.get("microsoft")
oem.contact_name = "Jane Smith"
oem_store.update("microsoft", oem)

# Deactivate (soft delete) an OEM
oem_store.delete("old-vendor")

# List all active OEMs
active_oems = oem_store.get_all(active_only=True)
for oem in active_oems:
    print(f"- {oem.name} ({oem.tier})")
```

### 5. Claude Desktop (MCP Server) ⭐ **BEST FOR AI-POWERED MANAGEMENT**

The MCP (Model Context Protocol) server allows you to manage entities using natural language through Claude Desktop:

**Setup:**

1. Install the MCP SDK dependency:
```bash
pip install -r requirements.txt
```

2. Configure Claude Desktop to use the DealCraft MCP server:

Edit your Claude Desktop config file:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Add the DealCraft MCP server:
```json
{
  "mcpServers": {
    "dealcraft": {
      "command": "python3",
      "args": ["/absolute/path/to/DealCraft/mcp_server.py"],
      "env": {}
    }
  }
}
```

**Replace `/absolute/path/to/DealCraft`** with your actual project path.

3. Restart Claude Desktop

**Usage Examples:**

Once configured, you can use natural language in Claude Desktop:

```
"List all Strategic OEMs"
"Show me details for the Microsoft OEM"
"Add a new OEM: Fortinet, tier Gold, programs: Firewall, SASE"
"Update the Cisco OEM contact email to partners@cisco.com"
"Deactivate the old-vendor OEM"
"List all Contract Vehicles with priority above 85"
"Show me all customers in the East region"
"List all active Partners"
```

**Available Operations:**
- ✅ List entities (OEMs, Contract Vehicles, Customers, Partners, Distributors, Regions)
- ✅ Get entity details by ID
- ✅ Add new entities (OEMs, Contract Vehicles, Customers)
- ✅ Update existing entities
- ✅ Deactivate entities (soft delete)
- ✅ Filter by tier, region, active status

**Benefits:**
- Natural language interaction
- No need to remember field names or structure
- AI validates inputs and suggests corrections
- Seamlessly integrated with your Claude Desktop workflow
- Same data as TUI and CLI (shared JSON files)

### 6. Future: REST API (Planned)

REST API endpoints are planned for entity management:

```bash
# Future API endpoints (not yet implemented)
GET    /v1/entities/oems
POST   /v1/entities/oems
PUT    /v1/entities/oems/{id}
DELETE /v1/entities/oems/{id}

GET    /v1/entities/contract-vehicles
POST   /v1/entities/contract-vehicles
# ... etc
```

## Common Operations

### Adding a New OEM

```bash
python3 scripts/manage_entities.py add-oem
```

Then provide:
- **ID**: Lowercase, hyphenated (e.g., `palo-alto`)
- **Name**: Display name (e.g., `Palo Alto Networks`)
- **Tier**: Strategic, Gold, or Silver
- **Programs**: Comma-separated list
- **Contact Info**: Optional

### Adding a New Contract Vehicle

```bash
python3 scripts/manage_entities.py add-cv
```

Provide:
- **ID**: Lowercase, hyphenated (e.g., `stars-iii`)
- **Name**: Display name (e.g., `STARS III`)
- **Priority Score**: 0-100 (higher = better fit)
- **OEMs Supported**: Comma-separated OEM IDs
- **Categories**: IT Hardware, Software, Services, etc.
- **Active BPAs**: Number of active BPAs
- **Ceiling Amount**: Contract ceiling (optional)

### Adding a New Customer

```bash
python3 scripts/manage_entities.py add-customer
```

Provide:
- **ID**: Lowercase, hyphenated (e.g., `dod-navy`)
- **Name**: Display name (e.g., `US Navy`)
- **Category**: DOD or Civilian
- **Region**: East, West, or Central
- **Tier**: Strategic or Standard
- **Annual Spend**: Dollar amount
- **Preferred Vehicles**: Comma-separated CV IDs

### Deactivating an Entity

```bash
python3 scripts/manage_entities.py

# Then select option 10 (Deactivate Entity)
# Enter entity type: oem
# Enter entity ID: old-vendor
```

Deactivated entities remain in the database but won't be used by scoring/recommendation engines.

### Viewing All Entities of a Type

```bash
# List all OEMs
python3 scripts/manage_entities.py list-oems

# List all customers
python3 scripts/manage_entities.py list-customers

# List all contract vehicles
python3 scripts/manage_entities.py list-cvs
```

## Entity Types and Fields

### OEM
- `id`: Unique identifier (lowercase, hyphenated)
- `name`: Display name
- `tier`: Strategic | Gold | Silver
- `programs`: List of partner programs
- `contact_name`, `contact_email`, `contact_phone`: Contact info
- `certifications`: List of certifications
- `notes`: Free-form notes

### Contract Vehicle
- `id`: Unique identifier
- `name`: Display name
- `priority_score`: 0-100 (used for ranking)
- `oems_supported`: List of OEM IDs
- `categories`: Product/service categories
- `active_bpas`: Number of active BPAs
- `ceiling_amount`: Contract ceiling (null = unlimited)
- `contracting_office`: Contracting office name
- `scope`: Contract scope description

### Customer
- `id`: Unique identifier
- `name`: Display name
- `category`: DOD | Civilian
- `region`: East | West | Central
- `tier`: Strategic | Standard
- `annual_spend`: Annual spend amount
- `contract_count`: Number of contracts
- `preferred_vehicles`: List of preferred CV IDs

### Partner
- `id`: Unique identifier
- `name`: Display name
- `tier`: Platinum | Gold | Silver
- `oem_affiliations`: List of OEM IDs
- `specializations`: Areas of expertise
- `regions_served`: List of regions
- `program`: Partner program name

### Distributor
- `id`: Unique identifier
- `name`: Display name
- `tier`: Premier | Standard
- `oem_authorizations`: List of authorized OEM IDs
- `regions_served`: List of regions served
- `product_categories`: Product categories
- `payment_terms`: Payment terms (e.g., "Net 30")
- `delivery_options`: Delivery methods

### Region
- `id`: Unique identifier (east, west, central)
- `name`: Display name
- `bonus`: Bonus points for region (float)
- `description`: Region description

## How Entities Affect Scoring

### OEMs
- OEM tier affects base score (Strategic = 95, Gold = 85-90, Silver = 70-80)
- Loaded from `data/entities/oems.json`
- Used in opportunity scoring and partner matching

### Contract Vehicles
- Priority score determines recommendation ranking
- OEM support affects vehicle-to-opportunity fit
- BPAs increase recommendation score by +3 points
- Ceiling amount filters out oversized deals

### Regions
- Region bonus added to opportunity score
- East = +2.5, West = +2.0, Central = +1.5

### Customers
- Category affects bonus (DOD = +4.0, Civilian = +3.0)
- Preferred vehicles influence recommendations
- Tier affects relationship scoring

## Backup and Recovery

Entity stores automatically create timestamped backups when saving:

```
data/entities/
├── oems.json
├── oems.backup20251102000000
├── customers.json
└── customers.backup20251102000000
```

To restore from backup:
```bash
cp data/entities/oems.backup20251102000000 data/entities/oems.json
```

## Validation

Entity stores use Pydantic models for validation:
- Required fields must be present
- Field types must match (string, int, float, list, etc.)
- Enum fields must use valid values
- Invalid data causes clear error messages

## Migration from Hardcoded Data

If you're migrating from hardcoded data, use the migration script:

```bash
python3 scripts/migrate_entities.py
```

This extracts data from `mcp/core/scoring.py` and `mcp/core/cv_recommender.py` into JSON files.

## Best Practices

1. **Use the CLI tool** for quick, safe updates
2. **Backup before bulk changes** - copy entity JSON files
3. **Use meaningful IDs** - lowercase, hyphenated (e.g., `palo-alto`)
4. **Keep tier structure consistent** - Strategic > Gold > Silver
5. **Document in notes field** - reasons for tier changes, etc.
6. **Test after changes** - run scoring tests to verify
7. **Commit entity changes to git** - track configuration changes

## Troubleshooting

### Error: "Entity with ID 'xxx' already exists"
The ID must be unique. Choose a different ID or update the existing entity.

### Error: "Invalid tier value"
Use only: Strategic, Gold, Silver (or Platinum for partners)

### Changes not reflected in API
Restart the API server to reload entity data:
```bash
./scripts/dev.sh
```

### JSON syntax errors
Use a JSON validator or the CLI tool to avoid syntax errors.

## Examples

### Example 1: Adding a New OEM (Arista)

```bash
python3 scripts/manage_entities.py add-oem

# Inputs:
# ID: arista
# Name: Arista Networks
# Tier: Gold
# Programs: CloudVision, EOS, Campus Networking
# Contact: partners@arista.com
```

### Example 2: Adding a New Contract Vehicle (OASIS+)

```bash
python3 scripts/manage_entities.py add-cv

# Inputs:
# ID: oasis-plus
# Name: OASIS+
# Priority Score: 86
# OEMs: microsoft,cisco,dell,hpe,aws,google
# Categories: IT Services, Professional Services, Cloud
# Active BPAs: 1
# Ceiling: 60000000000
# Contracting Office: GSA
# Scope: IT Services for Federal Agencies
```

### Example 3: Bulk Import from CSV

Create a script to import from CSV:

```python
import csv
from mcp.core.entities import OEM, oem_store

with open('oems.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        oem = OEM(
            id=row['id'],
            name=row['name'],
            tier=row['tier'],
            programs=row['programs'].split(';')
        )
        oem_store.add(oem)
        print(f"Added: {oem.name}")
```

## Summary

The Entity Management System provides:
- ✅ Centralized configuration
- ✅ Type-safe validation
- ✅ Automatic backups
- ✅ Visual TUI management (press 8 in dashboard)
- ✅ Easy maintenance via CLI
- ✅ Natural language management via Claude Desktop (MCP)
- ✅ Direct JSON editing
- ✅ Python API for automation
- ⏳ REST API (coming soon)

**Recommended Workflows:**
- **Quick browsing**: Use TUI (press 8)
- **Adding entities**: Use CLI tool (`python3 scripts/manage_entities.py`)
- **AI-powered management**: Use Claude Desktop with MCP server
- **Bulk operations**: Write Python scripts using entity stores
- **Direct edits**: Edit JSON files in `data/entities/`

For questions or issues, check the test files in `tests/test_entity_stores.py` for usage examples.
