-- IntroMail — Creates Outlook Drafts (inline template fallback)
-- csvPath, subjectTemplate, bodyTemplatePath, attachmentPath are injected at runtime by the TS wrapper.

set inlineBody to "
Hi {{first_name}},

I wanted to take a moment to personally introduce myself and the Red River team. I lead strategic accounts across the U.S. Air Force, Space Force, and Federal enterprise sectors — helping organizations like {{company}} modernize infrastructure, strengthen cybersecurity, and advance Zero Trust adoption.

Our team includes senior engineers and solution architects with decades of experience supporting mission networks, hybrid cloud deployments, and enterprise security environments. Collectively, we’ve helped design and implement programs across the Air Force, Space Force, and other Defense agencies ensuring readiness, reliability, and compliance with evolving DoD Zero Trust mandates.

Red River delivers complete solutions spanning networking, hybrid cloud, Zero Trust, cybersecurity, and managed services — backed by partnerships with Cisco, Nutanix, NetApp, Dell, VMware, and others. We deliver through proven federal and enterprise contract vehicles including SEWP, 2GIT, and CHESS.

I’ve attached my latest Red River Line Card for your reference. It provides a quick overview of our core capabilities and OEM ecosystem.

I’d welcome the opportunity to learn more about your current initiatives and share how our team has helped similar organizations accelerate modernization and security alignment. Would you be open to a brief conversation next week?

Respectfully,  
Joe Nolan  
Account Executive | Red River  
joe.nolan@redriver.com | 678.951.5584
"

on readFileAt(thePath)
	try
		set f to (POSIX file thePath) as alias
		set fileRef to open for access f with write permission
		set txt to read fileRef
		close access fileRef
		return txt
	on error errMsg
		try
			close access (POSIX file thePath)
		end try
		error "Failed to read file: " & thePath & " — " & errMsg
	end try
end readFileAt

on replaceAll(theText, token, value)
	set AppleScript's text item delimiters to token
	set parts to text items of theText
	set AppleScript's text item delimiters to value
	set result to parts as text
	set AppleScript's text item delimiters to ""
	return result
end replaceAll

on headerIndex(hName, headers)
	repeat with i from 1 to count of headers
		if (item i of headers) as text is equal to hName then return i
	end repeat
	return 1
end headerIndex

on run
	set templateText to inlineBody
	if bodyTemplatePath is not "" then
		try
			set templateText to readFileAt(bodyTemplatePath)
		end try
	end if

	set csvData to readFileAt(csvPath)
	set csvLines to paragraphs of csvData

	set AppleScript's text item delimiters to ","
	set headerLine to item 1 of csvLines
	set headers to text items of headerLine

	tell application "Microsoft Outlook"
		repeat with i from 2 to count of csvLines
			set thisLine to item i of csvLines
			if thisLine is not "" then
				set fields to text items of thisLine

				set emailIdx to my headerIndex("email", headers)
				set firstNameIdx to my headerIndex("first_name", headers)
				set companyIdx to my headerIndex("company", headers)

				set emailAddr to item emailIdx of fields
				set firstName to ""
				if firstNameIdx ≤ (count of fields) then set firstName to item firstNameIdx of fields
				set company to ""
				if companyIdx ≤ (count of fields) then set company to item companyIdx of fields

				set subj1 to my replaceAll(subjectTemplate, "{{company}}", company)
				set body1 to my replaceAll(templateText, "{{first_name}}", firstName)
				set bodyText to my replaceAll(body1, "{{company}}", company)

				set newMsg to make new outgoing message with properties {subject:subj1, content:bodyText, visible:true}
				make new recipient at newMsg with properties {email address:{address:emailAddr}}

				if attachmentPath is not "" then
					try
						make new attachment at newMsg with properties {file:POSIX file attachmentPath}
					end try
				end if
			end if
		end repeat
	end tell

	return "OK: Drafts created."
end run
