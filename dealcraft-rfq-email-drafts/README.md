# Red River RFQ Draft Emails – MCP + Outlook (macOS)

**Purpose:** Generate two Outlook Draft emails automatically from RFQ data:
1) OEM Registration / Quote Request
2) Internal Team Notification

**Tested:** macOS + Legacy Outlook (scriptable as `Microsoft Outlook`).

## Quick Start (Local Test)
1. Ensure Legacy Outlook is installed.
2. Open Terminal and run:
   ```bash
   cd "/mnt/data/red-river-rfq-email-drafts"
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt  # (none required now, placeholder)
   # Set environment variables (update values)
   cp .env.example .env
   # Run a test (uses sample JSON below)
   python mcp/tools/rfq_draft_email.py --sample
   ```

3. Confirm two drafts appear in Outlook’s **Drafts** folder.

## Environment (.env)
Never hard-code secrets. Configure these in `.env`:
```
INSIDE_TEAM_EMAIL=airforceinsideteam@redriver.com
INSIDE_SALES_NAME=Kristen Bateman
INSIDE_SALES_EMAIL=kristen.bateman@redriver.com
SE_NAME=Lewis Hickman
SE_EMAIL=lewis.hickman@redriver.com
OEM_REP_NAME=Your OEM Rep
OEM_REP_EMAIL=oem.rep@example.com
ACCOUNT_EXEC_NAME=Joe Nolan
ACCOUNT_EXEC_EMAIL=joe.nolan@redriver.com
ACCOUNT_EXEC_PHONE=678.951.5584
```

## Wire into MCP (Claude/Kilo Code)
Expose the Python script as a **tool** that accepts an RFQ JSON payload and returns a status:
- **Name:** `create_rfq_drafts`
- **Args:** RFQ fields (customer, command, oem, rfq_id, contract_vehicle, due_date, est_value, poc_name, poc_email, attachments[], folder_path)
- **Action:** Calls the AppleScript via `osascript`, passing a JSON string. AppleScript builds two Drafts.

### Example RFQ JSON
```json
{
  "customer": "Customer Alpha",
  "command": "Customer Alpha",
  "oem": "Cisco",
  "rfq_id": "361235",
  "contract_vehicle": "SEWP V",
  "due_date": "2025-10-12",
  "est_value": 701430,
  "poc_name": "Ms. Preston",
  "poc_email": "ms.preston@example.mil",
  "folder_path": "/Users/jonolan/RedRiver/RFQs/361235/",
  "attachments": [
    "/Users/jonolan/RedRiver/RFQs/attachments/361235_Cisco_SOW.pdf"
  ]
}
```

## Files
- `scripts/create_rfq_drafts.applescript` – Creates two Drafts in Outlook.
- `mcp/tools/rfq_draft_email.py` – CLI + importable function for MCP servers.
- `templates/email_rfq_communications.md` – The two email templates (reference).

---

## Notes
- The AppleScript uses AppleScriptObjC (`Foundation`) to parse JSON safely.
- Drafts are saved (not sent). Outlook puts new outgoing messages in Drafts by default.
- Attachments are now **automatically attached** to both drafts if file paths are provided in `attachments`.
- If you use New Outlook (non-scriptable), switch back to Legacy Outlook for this automation.
