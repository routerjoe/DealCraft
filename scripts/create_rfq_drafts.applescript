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