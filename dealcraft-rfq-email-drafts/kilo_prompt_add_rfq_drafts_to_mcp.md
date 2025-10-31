# Kilo Code Prompt — Add `create_rfq_drafts` Tool to MCP (Python) and Wire to Outlook (Legacy)

**Objective:** Add an MCP tool named `create_rfq_drafts` that takes an RFQ JSON payload and creates **two Outlook draft emails** (OEM + Internal), with attachments, by calling an AppleScript. Use the existing files from the package I already prepared.

## Repository Targets
- Confirm or create these files/paths:
  - `scripts/create_rfq_drafts.applescript`  *(AppleScript provided below)*
  - `mcp/tools/rfq_draft_email.py`           *(Python wrapper provided below)*
  - `.env`                                   *(from .env.example; do not commit)*

## Tool Contract
- **Tool name:** `create_rfq_drafts`
- **Description:** “Create OEM + Internal RFQ draft emails in Outlook with optional attachments.”
- **Arguments (JSON):**
  ```json
  {
    "customer": "string",
    "command": "string",
    "oem": "string",
    "rfq_id": "string",
    "contract_vehicle": "string",
    "due_date": "YYYY-MM-DD",
    "est_value": 0,
    "poc_name": "string",
    "poc_email": "string",
    "folder_path": "string",
    "attachments": ["string", "string"]
  }
  ```
- **Returns:** `"OK"` on success; otherwise a descriptive error string.

## Implementation Instructions
1. **Place AppleScript and Python files** exactly as shown below.
2. **Register the tool with the MCP server (Python).**
   - If MCP uses FastAPI or a simple tool registry, add a registration call to expose `create_rfq_drafts` with the above schema.
   - The handler should:
     1) Validate input JSON (basic type checks).
     2) Import and call `create_rfq_drafts(RFQ(**payload))` from `mcp/tools/rfq_draft_email.py`.
     3) Return the stdout string.
3. **Environment Variables (.env) — do not hard-code values.**
   - `INSIDE_TEAM_EMAIL=airforceinsideteam@redriver.com`
   - `INSIDE_SALES_NAME=Kristen Bateman`
   - `INSIDE_SALES_EMAIL=kristen.bateman@redriver.com`
   - `SE_NAME=Lewis Hickman`
   - `SE_EMAIL=lewis.hickman@redriver.com`
   - `OEM_REP_NAME=Your OEM Rep`
   - `OEM_REP_EMAIL=oem.rep@example.com`
   - `ACCOUNT_EXEC_NAME=Joe Nolan`
   - `ACCOUNT_EXEC_EMAIL=joe.nolan@redriver.com`
   - `ACCOUNT_EXEC_PHONE=678.951.5584`
4. **macOS requirement:** Legacy Outlook (scriptable as “Microsoft Outlook”). If user is on New Outlook, instruct them to switch to Legacy.
5. **Security/Permissions:**
   - Annotate this tool as **local-only**, no internet I/O.
   - Warn users the tool can write drafts in Outlook; it won’t send.
   - Validate file paths before attempting to attach.
6. **Testing Endpoint:**
   - Add a dev-only endpoint or CLI that calls the tool with the sample payload below.
   - Ensure two drafts appear in Outlook → Drafts.

## Code to Add

### A) `scripts/create_rfq_drafts.applescript`
```applescript
-- create_rfq_drafts.applescript
-- Usage: osascript create_rfq_drafts.applescript '<json-string>'
use AppleScript version "2.8"
use framework "Foundation"
use scripting additions

on run argv
	try
		if (count of argv) is 0 then error "Missing JSON argument."
		set jsonText to item 1 of argv

		-- Parse JSON via AppleScriptObjC
		set nsText to current application's NSString's stringWithString:jsonText
		set jsonData to nsText's dataUsingEncoding:(current application's NSUTF8StringEncoding)
		set {obj, err} to current application's NSJSONSerialization's JSONObjectWithData:jsonData options:0 |error|:(reference)
		if obj is missing value then error "Invalid JSON payload."

		-- Extract fields with defaults
		set customer to (obj's valueForKey:"customer") as text
		set command to (obj's valueForKey:"command") as text
		set oem to (obj's valueForKey:"oem") as text
		set rfq_id to (obj's valueForKey:"rfq_id") as text
		set contract_vehicle to (obj's valueForKey:"contract_vehicle") as text
		set due_date to (obj's valueForKey:"due_date") as text
		set est_value to (obj's valueForKey:"est_value") as string
		set poc_name to (obj's valueForKey:"poc_name") as text
		set poc_email to (obj's valueForKey:"poc_email") as text
		set folder_path to (obj's valueForKey:"folder_path") as text

		set attachments_array to obj's valueForKey:"attachments"
		if attachments_array is missing value then
			set attachments_list to {}
		else
			set attachments_list to (attachments_array as list)
		end if

		-- From environment-like overrides (optional)
		set env to (current application's NSProcessInfo's processInfo()'s environment())
		set inside_team_email to (env's objectForKey:"INSIDE_TEAM_EMAIL") as text
		set inside_sales_name to (env's objectForKey:"INSIDE_SALES_NAME") as text
		set inside_sales_email to (env's objectForKey:"INSIDE_SALES_EMAIL") as text
		set se_name to (env's objectForKey:"SE_NAME") as text
		set se_email to (env's objectForKey:"SE_EMAIL") as text
		set oem_rep_name to (env's objectForKey:"OEM_REP_NAME") as text
		set oem_rep_email to (env's objectForKey:"OEM_REP_EMAIL") as text
		set acct_exec_name to (env's objectForKey:"ACCOUNT_EXEC_NAME") as text
		set acct_exec_email to (env's objectForKey:"ACCOUNT_EXEC_EMAIL") as text
		set acct_exec_phone to (env's objectForKey:"ACCOUNT_EXEC_PHONE") as text

		if acct_exec_name is missing value or acct_exec_name = "" then set acct_exec_name to "Joe Nolan"
		if acct_exec_email is missing value or acct_exec_email = "" then set acct_exec_email to "joe.nolan@redriver.com"
		if acct_exec_phone is missing value or acct_exec_phone = "" then set acct_exec_phone to "678.951.5584"

		-- Build email bodies
		set oem_subject to "RFQ Registration Request – " & customer & " – " & oem
		set oem_body to "Hello " & oem_rep_name & "," & return & return & ¬
			"We’ve received a new RFQ from " & customer & " related to " & oem & ". Please register this opportunity under Red River for quoting and deal protection." & return & return & ¬
			"Details:" & return & ¬
			"- Customer: " & customer & return & ¬
			"- RFQ ID: " & rfq_id & return & ¬
			"- Estimated Value: $" & est_value & return & ¬
			"- Contract Vehicle: " & contract_vehicle & return & ¬
			"- Requested Response Date: " & due_date & return & ¬
			"- POC: " & poc_name & " (" & poc_email & ")" & return & ¬
			"- RFQ Folder: " & folder_path & return
		if (count of attachments_list) > 0 then
			set oem_body to oem_body & return & "Attachments: " & (my join_list(attachments_list, ", ")) & return
		end if
		set oem_body to oem_body & return & "Please confirm registration and share the quote reference number once created." & return & return & ¬
			"Thank you," & return & ¬
			acct_exec_name & return & ¬
			"Account Executive | Red River" & return & ¬
			acct_exec_email & " | " & acct_exec_phone

		set team_subject to "New RFQ Logged – " & customer & " – " & oem
		set team_body to "Team," & return & return & ¬
			"A new RFQ has been received and logged in the RFQ Tracker." & return & return & ¬
			"Summary:" & return & ¬
			"- Customer: " & customer & return & ¬
			"- OEM: " & oem & return & ¬
			"- RFQ ID: " & rfq_id & return & ¬
			"- Contract Vehicle: " & contract_vehicle & return & ¬
			"- Due Date: " & due_date & return & ¬
			"- RFQ Folder: " & folder_path & return
		if (count of attachments_list) > 0 then
			set team_body to team_body & return & "Attachments: " & (my join_list(attachments_list, ", ")) & return
		end if
		set team_body to team_body & return & "Next Steps:" & return & ¬
			"- Kristen: Please initiate the quote request and track OEM registration." & return & ¬
			"- Lewis: Review for any technical configuration or BOM validation needs." & return & ¬
			"- Joe: Coordinate customer communication and ensure quote alignment." & return & return & ¬
			"Thanks," & return & ¬
			acct_exec_name & return & ¬
			"Account Executive | Red River" & return & ¬
			acct_exec_email & " | " & acct_exec_phone

		tell application "Microsoft Outlook"
			-- OEM Draft
			set oemMsg to make new outgoing message with properties {subject:oem_subject, content:oem_body}
			if (oem_rep_email is not missing value) and (oem_rep_email is not "") then
				make new recipient at oemMsg with properties {email address:{name:oem_rep_name, address:oem_rep_email}}
			end if
			-- Attach files if provided
			repeat with p in attachments_list
				try
					set p_alias to (POSIX file (p as text)) as alias
					make new attachment at oemMsg with properties {file:p_alias}
				end try
			end repeat
			save oemMsg

			-- Internal Draft
			set teamMsg to make new outgoing message with properties {subject:team_subject, content:team_body}
			if inside_team_email is not missing value and inside_team_email is not "" then
				make new recipient at teamMsg with properties {email address:{address:inside_team_email}}
			end if
			if inside_sales_email is not missing value and inside_sales_email is not "" then
				make new cc recipient at teamMsg with properties {email address:{name:inside_sales_name, address:inside_sales_email}}
			end if
			if se_email is not missing value and se_email is not "" then
				make new cc recipient at teamMsg with properties {email address:{name:se_name, address:se_email}}
			end if
			-- Attach files if provided
			repeat with p in attachments_list
				try
					set p_alias to (POSIX file (p as text)) as alias
					make new attachment at teamMsg with properties {file:p_alias}
				end try
			end repeat
			save teamMsg
		end tell

		return "OK"
	on error errMsg number errNum
		return "ERROR: " & errNum & " - " & errMsg
	end try
end run

on join_list(theList, theSep)
	set AppleScript's text item delimiters to theSep
	set s to theList as text
	set AppleScript's text item delimiters to ""
	return s
end join_list
```

### B) `mcp/tools/rfq_draft_email.py`
```python
import os, json, argparse, subprocess, pathlib
from dataclasses import dataclass, asdict
from typing import List, Optional

SCRIPT_PATH = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "create_rfq_drafts.applescript"

@dataclass
class RFQ:
    customer: str
    command: str
    oem: str
    rfq_id: str
    contract_vehicle: str
    due_date: str
    est_value: float
    poc_name: str
    poc_email: str
    folder_path: str
    attachments: Optional[List[str]] = None

def run_osascript_with_json(payload: dict) -> str:
    if not SCRIPT_PATH.exists():
        raise FileNotFoundError(f"AppleScript not found at {SCRIPT_PATH}")
    json_arg = json.dumps(payload, ensure_ascii=False)
    cmd = ["osascript", str(SCRIPT_PATH), json_arg]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"osascript failed: {result.stderr.strip()}")
    return result.stdout.strip()

def create_rfq_drafts(rfq: RFQ) -> str:
    payload = asdict(rfq)
    return run_osascript_with_json(payload)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", help="Path to RFQ JSON file")
    parser.add_argument("--sample", action="store_true", help="Use a built-in sample payload")
    args = parser.parse_args()

    if args.sample:
        sample = RFQ(
            customer="Customer Alpha",
            command="Customer Alpha",
            oem="Cisco",
            rfq_id="361235",
            contract_vehicle="SEWP V",
            due_date="2025-10-12",
            est_value=701430.00,
            poc_name="Ms. Preston",
            poc_email="ms.preston@example.mil",
            folder_path="/Users/jonolan/RedRiver/RFQs/361235/",
            attachments=["/Users/jonolan/RedRiver/RFQs/attachments/361235_Cisco_SOW.pdf"],
        )
        print(create_rfq_drafts(sample))
    else:
        if not args.json:
            raise SystemExit("Provide --json or --sample")
        with open(args.json, "r") as f:
            data = json.load(f)
        print(create_rfq_drafts(RFQ(**data)))
```

### C) Register Tool in MCP Server (Python example)
> Adjust this to your server structure (FastAPI, Flask, or simple dispatcher).
```python
# mcp/server/tools.py (example)
from mcp.tools.rfq_draft_email import create_rfq_drafts, RFQ

def register_tools(tool_registry):
    tool_registry.register(
        name="create_rfq_drafts",
        description="Create OEM + Internal RFQ draft emails in Outlook with optional attachments.",
        schema={
            "type": "object",
            "properties": {
                "customer": {"type": "string"},
                "command": {"type": "string"},
                "oem": {"type": "string"},
                "rfq_id": {"type": "string"},
                "contract_vehicle": {"type": "string"},
                "due_date": {"type": "string"},
                "est_value": {"type": "number"},
                "poc_name": {"type": "string"},
                "poc_email": {"type": "string"},
                "folder_path": {"type": "string"},
                "attachments": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["customer","command","oem","rfq_id","contract_vehicle","due_date","poc_name","poc_email","folder_path"]
        },
        handler=lambda args: create_rfq_drafts(RFQ(**args))
    )
```

## Sample Payload for Testing
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
  "attachments": ["/Users/jonolan/RedRiver/RFQs/attachments/361235_Cisco_SOW.pdf"]
}
```

## Acceptance Criteria
- Tool appears in MCP tool list as `create_rfq_drafts`.
- Calling tool with sample payload returns `"OK"`.
- Legacy Outlook shows **two drafts** with subjects, bodies, and **attachments**.
- No secrets committed; `.env` governs team addresses/names.

## Post-Add Checklist
- [ ] Verify `.env` values on the target Mac.
- [ ] Confirm Legacy Outlook (not “New Outlook”).
- [ ] Test from Claude with the tool call payload above.
- [ ] Optional: add auto-BCC or program alias via new `.env` vars.
