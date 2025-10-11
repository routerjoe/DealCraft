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
		set inside_team_email to my valOrEmpty(env's objectForKey:"INSIDE_TEAM_EMAIL")
		set inside_sales_name to my valOrEmpty(env's objectForKey:"INSIDE_SALES_NAME")
		set inside_sales_email to my valOrEmpty(env's objectForKey:"INSIDE_SALES_EMAIL")
		set se_name to my valOrEmpty(env's objectForKey:"SE_NAME")
		set se_email to my valOrEmpty(env's objectForKey:"SE_EMAIL")
		set oem_rep_name to my valOrEmpty(env's objectForKey:"OEM_REP_NAME")
		set oem_rep_email to my valOrEmpty(env's objectForKey:"OEM_REP_EMAIL")
		set acct_exec_name to my valOrEmpty(env's objectForKey:"ACCOUNT_EXEC_NAME")
		set acct_exec_email to my valOrEmpty(env's objectForKey:"ACCOUNT_EXEC_EMAIL")
		set acct_exec_phone to my valOrEmpty(env's objectForKey:"ACCOUNT_EXEC_PHONE")
		
		if acct_exec_name is missing value or acct_exec_name = "" then set acct_exec_name to "Joe Nolan"
		if acct_exec_email is missing value or acct_exec_email = "" then set acct_exec_email to "joe.nolan@redriver.com"
		if acct_exec_phone is missing value or acct_exec_phone = "" then set acct_exec_phone to "678.951.5584"
		
		-- Build email bodies (plain text with 'return' newlines and bullets; include RFP# in subject)
		set nl to (ASCII character 13) & (ASCII character 10)
		set bullet to "• "
		set oem_subject to "RFQ #" & rfq_id & " Registration Request - " & customer
		set greeting_name to oem_rep_name
		if greeting_name is missing value or greeting_name = "" then
			set greeting_name to (oem & " Team")
		end if
		set oem_body to "Hello " & greeting_name & "," & nl & nl & ¬
			"We’ve received a new RFQ from " & customer & " related to " & oem & ". Red River kindly requests your consideration for opportunity registration or partnering support on this opportunity." & nl & nl & ¬
			"Details:" & nl & ¬
			bullet & "Customer: " & customer & nl & ¬
			bullet & "RFQ ID: " & rfq_id & nl & ¬
			bullet & "Estimated Value: $" & est_value & nl & ¬
			bullet & "Contract Vehicle: " & contract_vehicle & nl & ¬
			bullet & "Requested Response Date: " & due_date & nl & ¬
			bullet & "POC: " & poc_name & " (" & poc_email & ")" & nl
		if (count of attachments_list) > 0 then
			set oem_body to oem_body & nl & nl & "Attachments: " & (my join_list(attachments_list, ", "))
		end if
		set oem_body to oem_body & nl & nl & "Thank you in advance for your consideration and support." & nl & nl & ¬
			"Thank you," & nl & ¬
			acct_exec_name & nl & ¬
			"Account Executive | Red River" & nl & ¬
			acct_exec_email & " | " & acct_exec_phone
		
		set team_subject to "New Opportunity Request (RFQ # " & rfq_id & " - " & customer & " - " & oem & ")"
		-- Pretty due date with timezone (default America/New_York)
		set zoneName to my valOrEmpty(env's objectForKey:"TIMEZONE")
		if zoneName = "" then set zoneName to "America/New_York"
		set pretty_due to due_date
		try
			set isoFmt to current application's NSDateFormatter's alloc()'s init()
			(isoFmt's setDateFormat:"yyyy-MM-dd")
			set d to isoFmt's dateFromString:(due_date)
			if d is not missing value then
				set outFmt to current application's NSDateFormatter's alloc()'s init()
				set tzObj to (current application's NSTimeZone's timeZoneWithName:zoneName)
				if tzObj is not missing value then (outFmt's setTimeZone:tzObj)
				(outFmt's setDateFormat:"EEEE, MMMM d, yyyy")
				set prettyStr to (outFmt's stringFromDate:d) as text
				set pretty_due to prettyStr & " (" & zoneName & ")"
			end if
		end try
		
		-- Optional fields for Opportunity Details and Partner Strategy
		set oppName to my valOrEmpty(obj's valueForKey:"opportunity_name")
		set closeDate to my valOrEmpty(obj's valueForKey:"close_date")
		set pricingGuidance to my valOrEmpty(obj's valueForKey:"pricing_guidance")
		set requestReg to my valOrEmpty(obj's valueForKey:"request_registration")
		set closeProb to my valOrEmpty(obj's valueForKey:"close_probability")
		set custContact to my valOrEmpty(obj's valueForKey:"customer_contact")
		set custEmail to my valOrEmpty(obj's valueForKey:"customer_email")
		set custPhone to my valOrEmpty(obj's valueForKey:"customer_phone")
		set partnerNeeded to my valOrEmpty(obj's valueForKey:"partner_needed")
		set partnerName to my valOrEmpty(obj's valueForKey:"partner_name")
		set partnerMargin to my valOrEmpty(obj's valueForKey:"partner_margin")
		set partnerPrimary to my valOrEmpty(obj's valueForKey:"partner_contact")
		
		set team_body to "Hello," & nl & nl & ¬
			"A new RFQ has been received and I plan on pursuing. Please create a new opportunity in radar and request registration from OEM." & nl & nl & ¬
			"Summary" & nl & ¬
			"Customer: " & customer & nl & ¬
			"OEM: " & oem & nl & ¬
			"RFQ ID: " & rfq_id & nl & ¬
			"Contract Vehicle: " & contract_vehicle & nl & ¬
			"Due Date: " & pretty_due & nl & nl & ¬
			"Opportunity Details" & nl & ¬
			"Opportunity Name: " & oppName & nl & ¬
			"Close Date: " & closeDate & nl & ¬
			"Pricing Guidance: " & pricingGuidance & nl & ¬
			"Request Registration: " & requestReg & nl & ¬
			"Close Probability: " & closeProb & nl & ¬
			"Customer Contact: " & custContact & nl & ¬
			"Customer Email: " & custEmail & nl & ¬
			"Customer Phone: " & custPhone & nl & nl & ¬
			"Partner Strategy " & nl & ¬
			"Partner Needed: " & partnerNeeded & nl & ¬
			"Partner Name: " & partnerName & nl & ¬
			"Partner Margin allocation: " & partnerMargin & nl & ¬
			"Partner Primary contact: " & partnerPrimary & nl & nl & ¬
			"Next Steps" & nl & ¬
			"- Lewis: Review for any technical configuration requirements or BOM validation needs." & nl & ¬
			"- iSAM: Please reply with the following details:" & nl & ¬
			bullet & "Opportunity Number: TBD" & nl & ¬
			bullet & "Cost: TBD" & nl & ¬
			bullet & "Margin: TBD" & nl & ¬
			bullet & "Sell to Price: TBD" & nl & ¬
			bullet & "Registration Number: TBD" & nl & ¬
			bullet & "Registration Expires: TBD" & nl & nl & ¬
			"Thanks," & nl & nl & ¬
			acct_exec_name & nl & ¬
			"Account Executive | Red River" & nl & ¬
			acct_exec_phone & nl & ¬
			acct_exec_email
		
		tell application "Microsoft Outlook"
			-- OEM Draft
			set oemMsg to make new outgoing message with properties {subject:oem_subject, plain text content:oem_body}
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
			try
				save oemMsg
			end try
			
			-- Internal Draft
			set teamMsg to make new outgoing message with properties {subject:team_subject, plain text content:team_body}
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
			try
				save teamMsg
			end try
		end tell
		
		return "OK"
	on error errMsg number errNum
		return "ERROR: " & errNum & " - " & errMsg
	end try
end run

on valOrEmpty(v)
	if v is missing value then return ""
	try
		set s to v as text
		if s = "missing value" then return ""
		return s
	on error
		return ""
	end try
end valOrEmpty

on join_list(theList, theSep)
	set AppleScript's text item delimiters to theSep
	set s to theList as text
	set AppleScript's text item delimiters to ""
	return s
end join_list