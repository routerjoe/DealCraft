-- scripts/create_oem_draft.applescript
-- Usage:
--   osascript scripts/create_oem_draft.applescript '<json-payload>'
-- JSON payload schema mirrors OemPayload with optional fields:
-- {
--   "customer": "AFCENT",
--   "oem": "Cisco",
--   "rfq_id": "361235",
--   "contract_vehicle": "SEWP V",
--   "opportunity_name": "AFCENT Collaboration Refresh",
--   "close_date": "2025-11-15",           -- ISO
--   "account_executive": "Joe Nolan",
--   "isam": "Kristen Bateman",
--   "engineer": "Lewis Hickman",
--   "partner_tier": "Gold",
--   "end_user_contact": "auto",            -- "auto" renders TBD here
--   "rfq_folder": "/Users/jonolan/RedRiver/RFQs/361235/",
--   "timezone": "America/New_York",
--   "to": "optional@recipient"             -- optional
-- }

use AppleScript version "2.8"
use framework "Foundation"
use scripting additions

on run argv
	try
		if (count of argv) is 0 then error "Missing JSON argument."
		set jsonText to item 1 of argv
		
		-- Parse JSON
		set nsText to current application's NSString's stringWithString:jsonText
		set jsonData to nsText's dataUsingEncoding:(current application's NSUTF8StringEncoding)
		set {obj, err} to current application's NSJSONSerialization's JSONObjectWithData:jsonData options:0 |error|:(reference)
		if obj is missing value then error "Invalid JSON payload."
		
		script S
			on valOrEmpty(v)
				if v is missing value then return ""
				try
					set t to v as text
				on error
					set t to ""
				end try
				if t is "" then return ""
				return t
			end valOrEmpty
			
			on valOrTbd(v)
				set t to my valOrEmpty(v)
				if t is "" then return "TBD"
				return t
			end valOrTbd
		end script
		
		-- Extract fields
		set customer to S's valOrEmpty(obj's valueForKey:"customer")
		set oem to S's valOrEmpty(obj's valueForKey:"oem")
		set rfq_id to S's valOrEmpty(obj's valueForKey:"rfq_id")
		set contract_vehicle to S's valOrEmpty(obj's valueForKey:"contract_vehicle")
		set opportunity_name to S's valOrTbd(obj's valueForKey:"opportunity_name")
		set close_date_iso to S's valOrEmpty(obj's valueForKey:"close_date")
		set account_executive to S's valOrTbd(obj's valueForKey:"account_executive")
		set isam to S's valOrTbd(obj's valueForKey:"isam")
		set engineer to S's valOrTbd(obj's valueForKey:"engineer")
		set partner_tier to S's valOrTbd(obj's valueForKey:"partner_tier")
		set end_user_contact_raw to S's valOrEmpty(obj's valueForKey:"end_user_contact")
		set rfq_folder to S's valOrEmpty(obj's valueForKey:"rfq_folder")
		set timezone to S's valOrEmpty(obj's valueForKey:"timezone")
		if timezone = "" then set timezone to "America/New_York"
		set to_addr to S's valOrEmpty(obj's valueForKey:"to")
		
		-- End user contact: "auto" -> TBD
		set end_user_contact to end_user_contact_raw
		if end_user_contact_raw is not "" then
			set endLower to (current application's NSString's stringWithString:end_user_contact_raw)'s lowercaseString() as text
			if endLower = "auto" then set end_user_contact to "TBD"
		end if
		if end_user_contact = "" then set end_user_contact to "TBD"
		
		-- Date formatting: Month D, YYYY or TBD
		set pretty_close_date to "TBD"
		if close_date_iso is not "" then
			try
				set isoFmt to current application's NSISO8601DateFormatter's alloc()'s init()
				set d to isoFmt's dateFromString:(close_date_iso)
				if d is not missing value then
					set df to current application's NSDateFormatter's alloc()'s init()
					(df's setDateFormat:"MMMM d, yyyy")
					set tzObj to (current application's NSTimeZone's timeZoneWithName:timezone)
					if tzObj is not missing value then (df's setTimeZone:tzObj)
					set pretty_close_date to (df's stringFromDate:d) as text
				end if
			end try
		end if
		
		-- Subject (exact copy)
		set subj to "Request for Registration / Partnering – " & customer & " | " & oem & " | " & contract_vehicle & " | RFQ " & rfq_id
		
		-- Body (plain text version of the specified copy)
		set bodyLines to {}
		copy ("Hello " & oem & " Team,") to end of bodyLines
		copy "" to end of bodyLines
		copy "We would like to request registration or partnering support for the following opportunity. A copy of the List of Materials (LOM) is attached for your reference." to end of bodyLines
		copy "" to end of bodyLines
		copy "Opportunity Summary" to end of bodyLines
		copy "- Customer: " & customer to end of bodyLines
		copy "- RFQ ID: " & rfq_id to end of bodyLines
		copy "- Contract Vehicle: " & contract_vehicle to end of bodyLines
		copy "- Opportunity Name: " & opportunity_name to end of bodyLines
		copy "- Estimated Close Date: " & pretty_close_date to end of bodyLines
		copy "- Account Executive: " & account_executive to end of bodyLines
		copy "- Inside Sales (iSAM): " & isam to end of bodyLines
		copy "- Solutions Engineer: " & engineer to end of bodyLines
		copy "- Partner Tier: " & partner_tier to end of bodyLines
		copy "- End User POC: " & end_user_contact to end of bodyLines
		copy "" to end of bodyLines
		copy "Request" to end of bodyLines
		copy ("Red River is pursuing this opportunity and would like to confirm " & oem & "’s support for registration or partnering. Once this request is approved, my iSAM will proceed to submit the official registration request through the Partner Portal.") to end of bodyLines
		copy "" to end of bodyLines
		copy "Please let us know if you require any additional information or documentation to initiate the process." to end of bodyLines
		copy "" to end of bodyLines
		copy "Thank you," to end of bodyLines
		copy "" to end of bodyLines
		copy "Joe Nolan" to end of bodyLines
		copy "Account Executive | Red River" to end of bodyLines
		copy "678.951.5584" to end of bodyLines
		copy "joe.nolan@redriver.com" to end of bodyLines
		
		set AppleScript's text item delimiters to linefeed
		set bodyText to bodyLines as text
		set AppleScript's text item delimiters to ""
		
		-- Find first LOM to attach, if any
		set firstAttachment to ""
		if rfq_folder is not "" then
			try
				set sh to "cd " & quoted form of rfq_folder & " && /bin/ls -1 | /usr/bin/awk 'BEGIN{IGNORECASE=1} /^(LOM|List_of_Materials|List-of-Materials|List of Materials)\\.(xlsx|csv|pdf)$/ {print; exit}'"
				set fn to do shell script sh
				if fn is not "" then set firstAttachment to (rfq_folder & "/" & fn)
			end try
		end if
		
		-- Create Outlook draft by opening and closing (saving=yes) which places it in Drafts
		tell application "Microsoft Outlook"
			set msg to make new outgoing message with properties {subject:subj, content:bodyText}
			if to_addr is not "" then
				make new recipient at msg with properties {email address:{address:to_addr}}
			end if
			if firstAttachment is not "" then
				try
					set p_alias to (POSIX file firstAttachment) as alias
					make new attachment at msg with properties {file:p_alias}
				end try
			end if
			try
				open msg
				delay 0.2
				close msg saving yes
			on error
				-- Fallback: try simple save (some Outlook builds accept this)
				try
					save msg
				end try
			end try
		end tell
		
		return "OK"
	on error errMsg number errNum
		return "ERROR: " & errNum & " - " & errMsg
	end try
end run