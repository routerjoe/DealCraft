import { exec } from 'child_process';
import { promisify } from 'util';
import fs from 'fs/promises';
import path from 'path';
import { logger } from '../utils/logger.js';
import { getAttachmentsDir } from '../utils/env.js';

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

/**
 * Normalize AppleScript/osascript output line endings (handles CR-only returns).
 */
function normalizeEol(text: string): string {
  return text.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
}

async function executeAppleScript(script: string, retries = MAX_RETRIES): Promise<string> {
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      const { stdout, stderr } = await execAsync(`osascript -e '${script.replace(/'/g, "'\\''")}'`);
      
      if (stderr) {
        logger.warn('AppleScript stderr', { stderr });
      }
      
      return stdout.trim();
    } catch (error: any) {
      logger.error('AppleScript execution failed', { attempt, retries, error: error?.message || String(error) });
      
      if (attempt < retries) {
        await delay(RETRY_DELAY);
      } else {
        throw new Error(`AppleScript failed: ${error?.message || String(error)}`);
      }
    }
  }
  
  throw new Error('Failed to execute AppleScript after all retries');
}

export async function getOutlookBidBoardEmails(
  limit: number = 50,
  unreadOnly: boolean = false,
  scanWindow: number = 1000,
  newestFirst: boolean = true
): Promise<OutlookEmail[]> {
  const script = `
    tell application "Microsoft Outlook"
      set inboxFolder to inbox
      
      -- Find Red River folder
      set redRiverFolder to missing value
      repeat with subFolder in mail folders of inboxFolder
        try
          if name of subFolder is "05 Internal (Red River Ops)" or name of subFolder contains "05 Internal" or name of subFolder contains "Red River Ops" then
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
      set messageList to messages of bidBoardFolder
      set emailData to ""
      set counter to 0
      set maxCount to ${limit}
      set filterUnread to ${unreadOnly}
      set scanWindow to ${scanWindow}
      set newestFirst to ${newestFirst}
      set totalCount to count of messageList
      set scanned to 0

      if newestFirst is true then
        set startIndex to totalCount
        set endIndex to 1
        set stepVal to -1
      else
        set startIndex to 1
        set endIndex to totalCount
        set stepVal to 1
      end if
      
      repeat with i from startIndex to endIndex by stepVal
        try
          set theMessage to item i of messageList
          set scanned to scanned + 1
          
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
          
          if scanned is greater than or equal to scanWindow then exit repeat
          
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
      set theMessage to missing value
      try
        set theMessage to first message whose id is "${emailId}"
      on error
        -- Fallback: search the Bid Board folder and find by id as string
        set inboxFolder to inbox
        set redRiverFolder to missing value
        repeat with subFolder in mail folders of inboxFolder
          try
            if name of subFolder is "05 Internal (Red River Ops)" or name of subFolder contains "05 Internal" or name of subFolder contains "Red River Ops" then
              set redRiverFolder to subFolder
              exit repeat
            end if
          end try
        end repeat
        if redRiverFolder is missing value then error "Red River folder not found"
        set bidBoardFolder to missing value
        repeat with subFolder in mail folders of redRiverFolder
          try
            if name of subFolder contains "Bid Board" then
              set bidBoardFolder to subFolder
              exit repeat
            end if
          end try
        end repeat
        if bidBoardFolder is missing value then error "Bid Board folder not found"
        repeat with m in messages of bidBoardFolder
          try
            if (id of m as string) is equal to "${emailId}" then
              set theMessage to m
              exit repeat
            end if
          end try
        end repeat
        if theMessage is missing value then error "Message not found in Bid Board"
      end try
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
  const baseAttachmentsDir = getAttachmentsDir();
  const attachmentDir = outputDir || path.join(baseAttachmentsDir, emailId);
  
  // Create directory
  await fs.mkdir(attachmentDir, { recursive: true });

  const script = `
    tell application "Microsoft Outlook"
      set theMessage to missing value
      try
        set theMessage to first message whose id is "${emailId}"
      on error
        -- Fallback: search the Bid Board folder and find by id as string
        set inboxFolder to inbox
        set redRiverFolder to missing value
        repeat with subFolder in mail folders of inboxFolder
          try
            if name of subFolder is "05 Internal (Red River Ops)" or name of subFolder contains "05 Internal" or name of subFolder contains "Red River Ops" then
              set redRiverFolder to subFolder
              exit repeat
            end if
          end try
        end repeat
        if redRiverFolder is missing value then error "Red River folder not found"
        set bidBoardFolder to missing value
        repeat with subFolder in mail folders of redRiverFolder
          try
            if name of subFolder contains "Bid Board" then
              set bidBoardFolder to subFolder
              exit repeat
            end if
          end try
        end repeat
        if bidBoardFolder is missing value then error "Bid Board folder not found"
        repeat with m in messages of bidBoardFolder
          try
            if (id of m as string) is equal to "${emailId}" then
              set theMessage to m
              exit repeat
            end if
          end try
        end repeat
        if theMessage is missing value then error "Message not found in Bid Board"
      end try
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
  const normalized = output.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
  const attachments = normalized
    .split('\n')
    .filter(line => line && !line.startsWith('ERROR:'))
    .map(line => line.trim());
  
  return attachments;
}

export async function markOutlookEmailAsRead(emailId: string): Promise<boolean> {
  const script = `
    tell application "Microsoft Outlook"
      set resultText to "ERROR: Unknown"
      try
        set theMessage to missing value
        try
          set theMessage to first message whose id is "${emailId}"
        on error
          -- Fallback: search the Bid Board folder and find by id as string
          set inboxFolder to inbox
          set redRiverFolder to missing value
          repeat with subFolder in mail folders of inboxFolder
            try
              if name of subFolder is "05 Internal (Red River Ops)" or name of subFolder contains "05 Internal" or name of subFolder contains "Red River Ops" then
                set redRiverFolder to subFolder
                exit repeat
              end if
            end try
          end repeat
          if redRiverFolder is missing value then error "Red River folder not found"
          set bidBoardFolder to missing value
          repeat with subFolder in mail folders of redRiverFolder
            try
              if name of subFolder contains "Bid Board" then
                set bidBoardFolder to subFolder
                exit repeat
              end if
            end try
          end repeat
          if bidBoardFolder is missing value then error "Bid Board folder not found"
          repeat with m in messages of bidBoardFolder
            try
              if (id of m as string) is equal to "${emailId}" then
                set theMessage to m
                exit repeat
              end if
            end try
          end repeat
          if theMessage is missing value then error "Message not found in Bid Board"
        end try
        try
          set (read status of theMessage) to true
          set resultText to "Success"
        on error errMsg
          set resultText to "ERROR: " & (errMsg as string)
        end try
      on error errMsg2
        set resultText to "ERROR: " & (errMsg2 as string)
      end try
      return resultText
    end tell
  `;

  const output = await executeAppleScript(script);
  return output.trim() === "Success";
}

function parseOutlookEmails(output: string): OutlookEmail[] {
  const emails: OutlookEmail[] = [];
  const normalized = normalizeEol(output);
  const emailBlocks = normalized.split('---EMAIL---').filter(block => block.trim());

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
      logger.error('Error parsing email block', { error: error instanceof Error ? error.message : String(error) });
    }
  }

  if (emails.length === 0) {
    logger.warn('No emails parsed from Outlook output');
    return [];
  }

  return emails;
}

function parseOutlookEmailDetails(output: string): OutlookEmailDetails {
  const lines = normalizeEol(output).split('\n');
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
