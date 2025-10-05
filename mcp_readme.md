# Red River Sales Automation MCP Server

> 🚀 Comprehensive MCP server for automating Red River sales operations - RFQ processing, CRM, and analytics

## Overview

This MCP server provides **30+ tools** that automate your entire sales workflow through natural conversation with Claude Desktop, Cursor, or other MCP-compatible tools.

### Key Features

✅ **Outlook Integration** (AppleScript) - Auto-read Bid Board folder  
✅ **RFQ Processing** - Extract, analyze, decide, cleanup  
✅ **Sales Tools** - Margin calc, pricing, SEWP lookup  
✅ **Obsidian CRM** - Update opportunities, customers, contracts  
✅ **SQLite Analytics** - Metrics, tracking, history  
✅ **Google Drive Exports** - Reports, backups  

## Quick Start

### Prerequisites

- **macOS** (for AppleScript Outlook integration)
- **Node.js 18+**
- **Microsoft Outlook** (running)
- **Obsidian** with Red River Sales vault
- **Google Drive** (optional, for exports)

### Installation

```bash
# 1. Clone/download this project
cd red-river-sales-automation

# 2. Run setup script
chmod +x setup.sh
./setup.sh

# 3. Edit .env file
nano .env
# Update OBSIDIAN_VAULT_PATH to your vault location

# 4. Add to Claude Desktop config
# macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "red-river-sales-automation": {
      "command": "node",
      "args": ["/absolute/path/to/red-river-sales-automation/dist/index.js"]
    }
  }
}

# 5. Restart Claude Desktop
```

### Grant Outlook Permissions

For AppleScript to access Outlook:

1. **System Preferences** → **Security & Privacy**
2. Click **Privacy** tab
3. Select **Automation**
4. Find **Terminal** (or Claude Desktop)
5. ✅ Check **Microsoft Outlook**

## Architecture

### Directory Structure

```
~/RedRiver/                      # RED_RIVER_BASE_DIR
├── data/
│   └── rfq_tracking.db         # SQLite (stays local, never syncs)
├── attachments/                # Email attachments
│   └── {email_id}/
├── exports/                    # Google Drive sync
│   ├── rfq_summaries/
│   └── analytics/
└── logs/                       # MCP server logs

~/Documents/RedRiverSales/      # OBSIDIAN_VAULT_PATH
├── Opportunities/              # Syncs via Obsidian (< 1GB)
├── Customers/
├── Contracts/
└── ...
```

### Data Storage Strategy

- **SQLite** → Local only (analytics, metrics, fast queries)
- **Obsidian** → Synced via Obsidian Sync (CRM, notes)
- **Google Drive** → Exports only (reports, backups)

## Available Tools

### Outlook Tools (4 tools)

- `outlook_get_bid_board_emails` - List emails from Bid Board
- `outlook_get_email_details` - Get full email with body
- `outlook_download_attachments` - Save attachments locally
- `outlook_mark_as_read` - Mark email as read

### RFQ Tools (8 tools)

- `rfq_process_email` - Process single RFQ email
- `rfq_batch_process` - Process multiple RFQs
- `rfq_analyze` - Analyze RFQ for fit/value
- `rfq_create_opportunity` - Create Obsidian note
- `rfq_update_decision` - Log GO/NO-GO decision
- `rfq_cleanup_declined` - Delete declined RFQs
- `rfq_get_status` - Check RFQ status
- `rfq_list_pending` - List unprocessed RFQs

### Sales Tools (6 tools)

- `sales_calculate_margin` - Calculate margins
- `sales_partner_split` - Partner margin calculation
- `sales_price_protection` - Check price protection
- `sales_sewp_lookup` - SEWP contract lookup
- `sales_quote_summary` - Generate quote summary
- `sales_pricing_tiers` - Volume pricing tiers

### CRM Tools (Obsidian) (5 tools)

- `crm_create_opportunity` - Create opportunity note
- `crm_update_opportunity` - Update existing note
- `crm_link_entities` - Link customers/contracts
- `crm_search_notes` - Search vault
- `crm_get_note` - Read specific note

### Analytics Tools (4 tools)

- `analytics_rfq_summary` - RFQ stats by period
- `analytics_win_rate` - Win/loss analysis
- `analytics_pipeline_value` - Pipeline metrics
- `analytics_decision_trends` - Decision patterns

### Export Tools (3 tools)

- `export_to_drive` - Export to Google Drive
- `export_backup_db` - Backup SQLite database
- `export_weekly_report` - Generate weekly report

## Usage Examples

### Process New RFQs

```
"Check for new RFQs in my Bid Board folder and process them"
```

Claude will:
1. Get unread emails from Outlook
2. Download attachments
3. Analyze each RFQ
4. Provide recommendations
5. Ask for GO/NO-GO decisions

### Analyze a Specific RFQ

```
"Analyze the Air Force cyber tools RFQ and tell me if we should pursue it"
```

Claude will:
1. Find the RFQ
2. Assess fit (1-10 score)
3. Estimate value
4. Calculate win probability
5. Recommend GO/NO-GO

### Generate Reports

```
"Show me all RFQs from last week and our decision breakdown"
```

Claude will:
1. Query SQLite for recent RFQs
2. Calculate statistics
3. Show decision patterns
4. Export to Google Drive

### Update CRM

```
"Create an opportunity note for the DHS network RFQ we decided to pursue"
```

Claude will:
1. Create Obsidian note
2. Link to customer/contract
3. Set up frontmatter
4. Track in SQLite

## Configuration

### Environment Variables

```bash
# Required
RED_RIVER_BASE_DIR=/Users/joe/RedRiver
OBSIDIAN_VAULT_PATH=/Users/joe/Documents/RedRiverSales

# Optional
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
SQLITE_DB_PATH=/custom/path/rfq_tracking.db
LOG_LEVEL=info
```

### Database Schema

See `src/database/init.ts` for complete schema. Key tables:

- `rfqs` - RFQ tracking
- `attachments` - File metadata
- `decision_log` - GO/NO-GO decisions
- `sales_calculations` - Pricing/margin data
- `activity_log` - Audit trail

## Workflow: RFQ Processing

```
1. Email arrives in Bid Board
   ↓
2. MCP tool: outlook_get_bid_board_emails
   ↓
3. MCP tool: outlook_download_attachments
   ↓
4. MCP tool: rfq_analyze
   ↓
5. Claude provides recommendation
   ↓
6. You decide: GO or NO-GO
   ↓
7a. If GO:
    - rfq_create_opportunity (Obsidian)
    - rfq_update_decision (SQLite)
   ↓
7b. If NO-GO:
    - rfq_update_decision (SQLite)
    - rfq_cleanup_declined (delete from Drive)
```

## Development

### Build & Run

```bash
# Install dependencies
npm install

# Build TypeScript
npm run build

# Run in development mode
npm run dev

# Watch mode
npm run watch
```

### Testing

```bash
# Test Outlook access
python3 test_applescript.py

# Test MCP server
npm run dev
# Then ask Claude: "Do you have Red River sales tools?"
```

### Adding New Tools

1. Create tool definition in appropriate module
2. Add handler function
3. Update index.ts to include tool
4. Rebuild: `npm run build`

## Troubleshooting

### Outlook Access Issues

**Problem:** "Not authorized to send Apple events"

**Solution:**
1. System Preferences → Security & Privacy → Privacy → Automation
2. Enable Terminal/Claude → Microsoft Outlook

### Database Lock

**Problem:** "Database is locked"

**Solution:**
- Don't put SQLite on Google Drive (syncing causes locks)
- Use local storage only

### Obsidian Sync

**Problem:** "Vault too large"

**Solution:**
- Keep notes under 1GB
- Use exports/ folder for large files

## Security

- ✅ No passwords stored in code
- ✅ Local SQLite (sensitive data stays local)
- ✅ Audit logging for all actions
- ✅ Path traversal protection
- ✅ Environment variable validation

## Support

For issues or questions:
1. Check logs: `~/RedRiver/logs/`
2. Review database: `sqlite3 ~/RedRiver/data/rfq_tracking.db`
3. Test Outlook access: `python3 test_applescript.py`

## License

MIT
