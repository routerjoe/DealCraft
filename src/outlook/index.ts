import { exec } from 'child_process';
import { promisify } from 'util';
import fs from 'fs/promises';
import path from 'path';

const execAsync = promisify(exec);

interface OutlookEmail {
  id: string;
  subject: string;
  from: string;
  email: string;
  date: string;
  read: boolean;
  attachments: number;
}

interface OutlookEmailDetails extends OutlookEmail {
  body: string;
  attachmentNames: string[];
}

const MAX_RETRIES = 3;
const RETRY_DELAY = 1500; // ms

async function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function executeAppleScript(script: string, retries = MAX_RETRIES): Promise<string> {
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      const { stdout, stderr } = await execAsync(`osascript -e '${script.replace(/'/g, "'\\''")}'`);
      
      if (stderr) {
        console.error('AppleScript stderr:', stderr);
      }
      
      return stdout.trim();
    } catch (error: any) {
      console.error(`AppleScript execution failed (attempt ${attempt}/${retries}):`, error.message);
      
      if (attempt < retries) {
        await delay(RETRY_DELAY);
      } else {
        throw new Error(`AppleScript failed: ${error.message}`);
      }
    }
  }
  
  throw new Error('Failed to execute AppleScript after all retries');
}

export async function getOutlookBidBoardEmails(
  limit: number = 50,
  unreadOnly: boolean = false
): Promise<OutlookEmail[]> {
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
      
      repeat with i from 1 to count of messageList
        try
          set theMessage to item i of messageList
          
          -- Filter by read status if requested
          ${unreadOnly ? 'if read status of theMessage is true then' : '-- No read filter'}
          ${unreadOnly ? '  next repeat' : ''}
          ${unreadOnly ? 'end if' : ''}
          
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

  const output = await executeAppleScript(script);
  
  if (output.startsWith('ERROR:')) {
    throw new Error(output);
  }
  
  return parseOutlookEmails(output);
}

export async function getOutlookEmailDetails(emailId: string): Promise<OutlookEmailDetails> {
  const script = `
    tell application "Microsoft Outlook"
      set theMessage to first message whose id is ${emailId}
      set emailData to ""
      
      -- Get ID
      set emailData to emailData & "ID:" & (id of theMessage as string) & return
      
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
      
      -- Get Body
      try
        set emailData to emailData & "BODY:" & (plain text content of theMessage) & return
      on error
        set emailData to emailData & "BODY:" & return
      end try
      
      -- Get Attachments
      set emailData to emailData & "ATTACHMENTS:" & (count of attachments of theMessage) & return
      
      set attachmentList to ""
      repeat with theAttachment in attachments of theMessage
        try
          set attachmentList to attachmentList & (name of theAttachment) & "|"
        end try
      end repeat
      
      set emailData to emailData & "ATTACHMENT_NAMES:" & attachmentList & return
      
      return emailData
    end tell
  `;

  const output = await executeAppleScript(script);
  return parseOutlookEmailDetails(output);
}

export async function downloadOutlookAttachments(
  emailId: string,
  outputDir?: string
): Promise<string[]> {
  const baseDir = process.env.BASE_DIR || process.cwd();
  const attachmentDir = outputDir || path.join(baseDir, 'attachments', emailId);
  
  // Create directory
  await fs.mkdir(attachmentDir, { recursive: true });

  const script = `
    tell application "Microsoft Outlook"
      set theMessage to first message whose id is ${emailId}
      set attachmentList to ""
      
      repeat with theAttachment in attachments of theMessage
        try
          set attachmentName to name of theAttachment
          set savePath to "${attachmentDir.replace(/\\/g, '\\\\')}/" & attachmentName
          
          -- Create alias for save location
          set saveLocation to POSIX file savePath
          
          -- Save the attachment
          save theAttachment in saveLocation
          
          set attachmentList to attachmentList & attachmentName & return
        on error errMsg
          set attachmentList to attachmentList & "ERROR:" & errMsg & return
        end try
      end repeat
      
      return attachmentList
    end tell
  `;

  const output = await executeAppleScript(script);
  const attachments = output
    .split('\n')
    .filter(line => line && !line.startsWith('ERROR:'))
    .map(line => line.trim());
  
  return attachments;
}

export async function markOutlookEmailAsRead(emailId: string): Promise<void> {
  const script = `
    tell application "Microsoft Outlook"
      set theMessage to first message whose id is ${emailId}
      set read status of theMessage to read
      return "Success"
    end tell
  `;

  await executeAppleScript(script);
}

function parseOutlookEmails(output: string): OutlookEmail[] {
  const emails: OutlookEmail[] = [];
  const emailBlocks = output.split('---EMAIL---').filter(block => block.trim());

  for (const block of emailBlocks) {
    try {
      const lines = block.split('\n').filter(line => line.trim());
      const email: Partial<OutlookEmail> = {};

      for (const line of lines) {
        const [key, ...valueParts] = line.split(':');
        const value = valueParts.join(':').trim();

        switch (key) {
          case 'ID':
            email.id = value;
            break;
          case 'SUBJECT':
            email.subject = value;
            break;
          case 'FROM':
            email.from = value;
            break;
          case 'EMAIL':
            email.email = value;
            break;
          case 'DATE':
            email.date = value;
            break;
          case 'READ':
            email.read = value.toLowerCase() === 'true';
            break;
          case 'ATTACHMENTS':
            email.attachments = parseInt(value) || 0;
            break;
        }
      }

      if (email.id && email.subject) {
        emails.push(email as OutlookEmail);
      }
    } catch (error) {
      console.error('Error parsing email block:', error);
    }
  }

  if (emails.length === 0) {
    throw new Error('No emails parsed from output');
  }

  return emails;
}

function parseOutlookEmailDetails(output: string): OutlookEmailDetails {
  const lines = output.split('\n');
  const details: Partial<OutlookEmailDetails> = {
    attachmentNames: []
  };

  let inBody = false;
  let bodyLines: string[] = [];

  for (const line of lines) {
    if (inBody && !line.startsWith('ATTACHMENTS:') && !line.startsWith('ATTACHMENT_NAMES:')) {
      bodyLines.push(line);
      continue;
    }

    const [key, ...valueParts] = line.split(':');
    const value = valueParts.join(':').trim();

    switch (key) {
      case 'ID':
        details.id = value;
        break;
      case 'SUBJECT':
        details.subject = value;
        break;
      case 'FROM':
        details.from = value;
        break;
      case 'EMAIL':
        details.email = value;
        break;
      case 'DATE':
        details.date = value;
        break;
      case 'READ':
        details.read = value.toLowerCase() === 'true';
        break;
      case 'BODY':
        inBody = true;
        break;
      case 'ATTACHMENTS':
        inBody = false;
        details.attachments = parseInt(value) || 0;
        break;
      case 'ATTACHMENT_NAMES':
        details.attachmentNames = value
          .split('|')
          .filter(name => name.trim())
          .map(name => name.trim());
        break;
    }
  }

  details.body = bodyLines.join('\n').trim();

  return details as OutlookEmailDetails;
}