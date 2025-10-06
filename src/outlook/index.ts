import { Tool } from "@anthropic-ai/sdk/resources/messages";
import { executeAppleScript } from "../utils/applescript";

interface OutlookEmail {
  id: string;
  subject: string;
  from: string;
  email: string;
  date: string;
  read: boolean;
  attachmentCount: number;
}

export const outlookGetBidBoardEmails: Tool = {
  name: "outlook_get_bid_board_emails",
  description: "Retrieves emails from the Bid Board folder in Outlook",
  input_schema: {
    type: "object",
    properties: {
      limit: {
        type: "number",
        description: "Maximum number of emails to retrieve (default: 50)",
        default: 50,
      },
      unread_only: {
        type: "boolean",
        description: "Only retrieve unread emails (default: false)",
        default: false,
      },
    },
  },
};

export async function handleOutlookGetBidBoardEmails(
  input: any
): Promise<string> {
  const limit = input.limit || 50;
  const unreadOnly = input.unread_only || false;

  const script = `
    tell application "Microsoft Outlook"
      set inboxFolder to inbox
      
      -- Find Red River folder
      set redRiverFolder to missing value
      repeat with subFolder in mail folders of inboxFolder
        try
          if name of subFolder contains "05 Internal" or name of subFolder contains "Red River Ops" then
            set redRiverFolder to subFolder
            exit repeat
          end if
        end try
      end repeat
      
      if redRiverFolder is missing value then
        return "ERROR: Red River folder not found"
      end if
      
      -- Find Bid Board folder
      set bidBoardFolder to missing value
      repeat with subFolder in mail folders of redRiverFolder
        try
          if name of subFolder contains "Bid Board" then
            set bidBoardFolder to subFolder
            exit repeat
          end if
        end try
      end repeat
      
      if bidBoardFolder is missing value then
        return "ERROR: Bid Board folder not found"
      end if
      
      -- Get messages
      set messageList to messages in bidBoardFolder
      set emailData to ""
      set counter to 0
      set maxCount to ${limit}
      set filterUnread to ${unreadOnly}
      
      repeat with i from 1 to count of messageList
        try
          set theMessage to item i of messageList
          
          -- Check if we should process this message based on read status
          set shouldProcess to true
          if filterUnread is true then
            if read status of theMessage is true then
              set shouldProcess to false
            end if
          end if
          
          -- Process the message if it matches our criteria
          if shouldProcess is true then
            set counter to counter + 1
            if counter > maxCount then exit repeat
            
            set emailData to emailData & "---EMAIL---" & return
            
            -- Get ID
            try
              set emailData to emailData & "ID:" & (id of theMessage as string) & return
            on error
              set emailData to emailData & "ID:UNKNOWN" & return
            end try
            
            -- Get Subject
            try
              set emailData to emailData & "SUBJECT:" & subject of theMessage & return
            on error
              set emailData to emailData & "SUBJECT:No Subject" & return
            end try
            
            -- Get Sender Name
            try
              set theSender to sender of theMessage
              set senderName to name of theSender
              set emailData to emailData & "FROM:" & senderName & return
            on error
              set emailData to emailData & "FROM:Unknown" & return
            end try
            
            -- Get Sender Email
            try
              set theSender to sender of theMessage
              set senderEmail to address of theSender
              set emailData to emailData & "EMAIL:" & senderEmail & return
            on error
              set emailData to emailData & "EMAIL:unknown@unknown.com" & return
            end try
            
            -- Get Date
            try
              set emailData to emailData & "DATE:" & (time received of theMessage as string) & return
            on error
              set emailData to emailData & "DATE:Unknown" & return
            end try
            
            -- Get Read Status
            try
              set emailData to emailData & "READ:" & (read status of theMessage as string) & return
            on error
              set emailData to emailData & "READ:false" & return
            end try
            
            -- Get Attachment Count
            try
              set emailData to emailData & "ATTACHMENTS:" & (count of attachments of theMessage) & return
            on error
              set emailData to emailData & "ATTACHMENTS:0" & return
            end try
          end if
          
        on error errMsg
          -- Log error but continue processing other emails
          set emailData to emailData & "---ERROR---" & return
          set emailData to emailData & "MESSAGE:" & errMsg & return
        end try
      end repeat
      
      if emailData is "" then
        return "ERROR: No emails could be retrieved"
      end if
      
      return emailData
    end tell
  `;

  try {
    const result = await executeAppleScript(script);

    if (result.startsWith("ERROR:")) {
      throw new Error(result);
    }

    // Parse the email data
    const emails = parseEmailData(result);

    if (emails.length === 0) {
      throw new Error("No emails parsed from output");
    }

    return JSON.stringify({ emails, count: emails.length }, null, 2);
  } catch (error) {
    throw error;
  }
}

function parseEmailData(data: string): OutlookEmail[] {
  const emails: OutlookEmail[] = [];
  const emailBlocks = data.split("---EMAIL---").filter((block) => block.trim());

  for (const block of emailBlocks) {
    const lines = block.split("\n").filter((line) => line.trim());
    const email: any = {};

    for (const line of lines) {
      const [key, ...valueParts] = line.split(":");
      const value = valueParts.join(":").trim();

      switch (key) {
        case "ID":
          email.id = value;
          break;
        case "SUBJECT":
          email.subject = value;
          break;
        case "FROM":
          email.from = value;
          break;
        case "EMAIL":
          email.email = value;
          break;
        case "DATE":
          email.date = value;
          break;
        case "READ":
          email.read = value === "true";
          break;
        case "ATTACHMENTS":
          email.attachmentCount = parseInt(value) || 0;
          break;
      }
    }

    if (email.id) {
      emails.push(email as OutlookEmail);
    }
  }

  return emails;
}

export const outlookGetEmailDetails: Tool = {
  name: "outlook_get_email_details",
  description:
    "Gets full details of a specific email including body and attachments",
  input_schema: {
    type: "object",
    properties: {
      email_id: {
        type: "string",
        description: "The Outlook email ID",
      },
    },
    required: ["email_id"],
  },
};

export async function handleOutlookGetEmailDetails(
  input: any
): Promise<string> {
  const emailId = input.email_id;

  const script = `
    tell application "Microsoft Outlook"
      try
        set theMessage to first message whose id is ${emailId}
        
        set emailData to ""
        set emailData to emailData & "---EMAIL-DETAILS---" & return
        
        -- Get ID
        set emailData to emailData & "ID:" & (id of theMessage as string) & return
        
        -- Get Subject
        try
          set emailData to emailData & "SUBJECT:" & subject of theMessage & return
        on error
          set emailData to emailData & "SUBJECT:No Subject" & return
        end try
        
        -- Get Body
        try
          set emailData to emailData & "BODY:" & return
          set emailData to emailData & content of theMessage & return
          set emailData to emailData & "---END-BODY---" & return
        on error
          set emailData to emailData & "BODY:Unable to retrieve body" & return
        end try
        
        -- Get Attachments
        try
          set theAttachments to attachments of theMessage
          set emailData to emailData & "ATTACHMENT-COUNT:" & (count of theAttachments) & return
          
          repeat with att in theAttachments
            set emailData to emailData & "ATTACHMENT:" & (name of att) & return
          end repeat
        on error
          set emailData to emailData & "ATTACHMENT-COUNT:0" & return
        end try
        
        return emailData
        
      on error errMsg
        return "ERROR: " & errMsg
      end try
    end tell
  `;

  try {
    const result = await executeAppleScript(script);

    if (result.startsWith("ERROR:")) {
      throw new Error(result);
    }

    return result;
  } catch (error) {
    throw error;
  }
}

export const outlookDownloadAttachments: Tool = {
  name: "outlook_download_attachments",
  description: "Downloads all attachments from a specific email",
  input_schema: {
    type: "object",
    properties: {
      email_id: {
        type: "string",
        description: "The Outlook email ID",
      },
      output_dir: {
        type: "string",
        description: "Optional custom output directory for attachments",
      },
    },
    required: ["email_id"],
  },
};

export async function handleOutlookDownloadAttachments(
  input: any
): Promise<string> {
  const emailId = input.email_id;
  const outputDir =
    input.output_dir || `${process.env.HOME}/Downloads/RFQ_Attachments`;

  const script = `
    tell application "Microsoft Outlook"
      try
        set theMessage to first message whose id is ${emailId}
        set theAttachments to attachments of theMessage
        
        set outputPath to "${outputDir}"
        
        -- Create directory if it doesn't exist
        do shell script "mkdir -p " & quoted form of outputPath
        
        set downloadedFiles to ""
        
        repeat with att in theAttachments
          set attName to name of att
          set savePath to outputPath & "/" & attName
          
          try
            save att in savePath
            set downloadedFiles to downloadedFiles & savePath & return
          on error errMsg
            set downloadedFiles to downloadedFiles & "ERROR:" & attName & ":" & errMsg & return
          end try
        end repeat
        
        if downloadedFiles is "" then
          return "No attachments found"
        end if
        
        return downloadedFiles
        
      on error errMsg
        return "ERROR: " & errMsg
      end try
    end tell
  `;

  try {
    const result = await executeAppleScript(script);

    if (result.startsWith("ERROR:")) {
      throw new Error(result);
    }

    return result;
  } catch (error) {
    throw error;
  }
}

export const outlookMarkAsRead: Tool = {
  name: "outlook_mark_as_read",
  description: "Marks an email as read in Outlook",
  input_schema: {
    type: "object",
    properties: {
      email_id: {
        type: "string",
        description: "The Outlook email ID",
      },
    },
    required: ["email_id"],
  },
};

export async function handleOutlookMarkAsRead(input: any): Promise<string> {
  const emailId = input.email_id;

  const script = `
    tell application "Microsoft Outlook"
      try
        set theMessage to first message whose id is ${emailId}
        set read status of theMessage to true
        return "SUCCESS: Email marked as read"
      on error errMsg
        return "ERROR: " & errMsg
      end try
    end tell
  `;

  try {
    const result = await executeAppleScript(script);

    if (result.startsWith("ERROR:")) {
      throw new Error(result);
    }

    return result;
  } catch (error) {
    throw error;
  }
}
