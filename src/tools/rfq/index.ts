import { Tool } from '@modelcontextprotocol/sdk/types.js';
import { getDb, saveDatabase } from '../../database/init.js';
import { logger } from '../../utils/logger.js';
import { getBaseDir, getAttachmentsDir } from '../../utils/env.js';
import { handleOutlookTool } from '../outlook/index.js';
import { existsSync, rmSync, readdirSync, readFileSync } from 'fs';
import { join } from 'path';
import { parse } from 'csv-parse/sync';
import { exec } from 'child_process';
import { promisify } from 'util';
import { createRfqDrafts } from './drafts.js';
import { sendRfqEmail } from '../../email/sendRfqEmail.js';

const execAsync = promisify(exec);

export const rfqTools: Tool[] = [
  {
    name: 'rfq_process_email',
    description: 'Process a single RFQ email - extract attachments, analyze, and store in database',
    inputSchema: {
      type: 'object',
      properties: {
        email_id: {
          type: 'string',
          description: 'Email ID from Outlook',
        },
      },
      required: ['email_id'],
    },
  },
  {
    name: 'rfq_batch_process',
    description: 'Process multiple RFQ emails at once',
    inputSchema: {
      type: 'object',
      properties: {
        limit: {
          type: 'number',
          description: 'Number of recent emails to process (default: 10)',
          default: 10,
        },
        unread_only: {
          type: 'boolean',
          description: 'Only process unread emails',
          default: true,
        },
      },
    },
  },
  {
    name: 'rfq_analyze',
    description: 'Analyze an RFQ for fit, value, and decision recommendation',
    inputSchema: {
      type: 'object',
      properties: {
        rfq_id: {
          type: 'number',
          description: 'RFQ ID from database',
        },
      },
      required: ['rfq_id'],
    },
  },
  {
    name: 'rfq_update_decision',
    description: 'Record GO/NO-GO decision for an RFQ',
    inputSchema: {
      type: 'object',
      properties: {
        rfq_id: {
          type: 'number',
          description: 'RFQ ID from database',
        },
        decision: {
          type: 'string',
          enum: ['GO', 'NO-GO'],
          description: 'Pursuit decision',
        },
        reason: {
          type: 'string',
          description: 'Reason for decision',
        },
        win_probability: {
          type: 'number',
          description: 'Win probability (0-100)',
        },
      },
      required: ['rfq_id', 'decision'],
    },
  },
  {
    name: 'rfq_cleanup_declined',
    description: 'Delete local files, database records, AND Outlook emails for NO-GO RFQs',
    inputSchema: {
      type: 'object',
      properties: {
        rfq_ids: {
          type: 'array',
          items: { type: 'number' },
          description: 'Array of RFQ IDs to clean up',
        },
        delete_from_outlook: {
          type: 'boolean',
          description: 'Also delete the email from Outlook Bid Board (default: true)',
          default: true,
        },
      },
      required: ['rfq_ids'],
    },
  },
  {
    name: 'rfq_list_pending',
    description: 'List all RFQs awaiting decision',
    inputSchema: {
      type: 'object',
      properties: {
        status: {
          type: 'string',
          enum: ['pending', 'processed', 'all'],
          default: 'pending',
        },
      },
    },
  },
  {
    name: 'create_rfq_drafts',
    description: 'Create OEM + Internal RFQ draft emails in Outlook with optional attachments. Local-only; writes Drafts.',
    inputSchema: {
      type: 'object',
      properties: {
        customer: { type: 'string' },
        command: { type: 'string' },
        oem: { type: 'string' },
        rfq_id: { type: 'string' },
        contract_vehicle: { type: 'string' },
        due_date: { type: 'string' },
        est_value: { type: 'number' },
        poc_name: { type: 'string' },
        poc_email: { type: 'string' },
        folder_path: { type: 'string' },
        attachments: { type: 'array', items: { type: 'string' } }
      },
      required: ['customer','command','oem','rfq_id','contract_vehicle','due_date','poc_name','poc_email','folder_path']
    },
  },
  {
    name: 'rfq_send_notification_email',
    description: 'Send the internal RFQ notification email using the HTML template builder',
    inputSchema: {
      type: 'object',
      properties: {
        to: { type: 'array', items: { type: 'string' }, description: 'Recipient email addresses' },
        payload: {
          type: 'object',
          properties: {
            customer: { type: 'string' },
            oem: { type: 'string' },
            rfq_id: { type: 'string' },
            contract_vehicle: { type: 'string' },
            due_date: { type: 'string' },
            opportunity_name: { type: 'string' },
            close_date: { type: 'string' },
            pricing_guidance: { type: 'string' },
            request_registration: { type: 'string' },
            close_probability: { type: 'string' },
            customer_contact: { type: 'string' },
            timezone: { type: 'string' }
          },
          additionalProperties: true
        }
      },
      required: ['to', 'payload']
    },
  }
];

export async function handleRfqTool(name: string, args: any) {
  switch (name) {
    case 'rfq_process_email':
      return await processEmail(args.email_id);
    
    case 'rfq_batch_process':
      return await batchProcess(args.limit || 10, args.unread_only !== false);
    
    case 'rfq_analyze':
      return await analyzeRfq(args.rfq_id);
    
    case 'rfq_update_decision':
      return await updateDecision(args.rfq_id, args.decision, args.reason, args.win_probability);
    
    case 'rfq_cleanup_declined':
      return await cleanupDeclined(args.rfq_ids, args.delete_from_outlook !== false);
    
    case 'rfq_list_pending':
      return await listPending(args.status || 'pending');
    
    case 'create_rfq_drafts': {
      const status = await createRfqDrafts(args);
      return {
        content: [
          {
            type: 'text',
            text: status || 'OK',
          },
        ],
      };
    }
    case 'rfq_send_notification_email': {
      const to: string[] = Array.isArray(args.to) ? args.to : [String(args.to)];
      await sendRfqEmail(args.payload || {}, to);
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({ sent: true, to }, null, 2),
          },
        ],
      };
    }
    default:
      throw new Error(`Unknown RFQ tool: ${name}`);
  }
}

async function processEmail(emailId: string) {
  const db = getDb();
  
  logger.info('Starting email processing', { emailId });
  
  // Get email details
  logger.info('Fetching email details...');
  const emailResult = await handleOutlookTool('outlook_get_email_details', { email_id: emailId });
  const emailData = JSON.parse(emailResult.content[0].text);
  
  // Download attachments
  logger.info('Downloading attachments...');
  const attachResult = await handleOutlookTool('outlook_download_attachments', { email_id: emailId });
  const attachData = JSON.parse(attachResult.content[0].text);
  
  // Parse CSVs if any
  const csvData = [];
  const attachDir = attachData.directory;
  
  logger.info('Parsing CSV files...', { count: attachData.saved.length });
  for (const filename of attachData.saved) {
    if (filename.toLowerCase().endsWith('.csv')) {
      const csvPath = join(attachDir, filename);
      const content = readFileSync(csvPath, 'utf-8');
      const records = parse(content, { columns: true, skip_empty_lines: true });
      csvData.push({ filename, records });
    }
  }
  
  // Insert into database using sql.js
  logger.info('Storing in database...');
  db.run(
    `INSERT INTO rfqs (email_id, subject, sender, received_date, status) VALUES (?, ?, ?, ?, 'pending')`,
    [emailId, emailData.subject || 'Unknown', emailData.from || 'Unknown', emailData.date || new Date().toISOString()]
  );
  
  // Get the inserted ID
  const result = db.exec('SELECT last_insert_rowid() as id');
  const rfqId = result[0].values[0][0] as number;
  
  // Insert attachments
  for (const filename of attachData.saved) {
    const ext = filename.split('.').pop()?.toLowerCase() || '';
    db.run(
      `INSERT INTO attachments (rfq_id, filename, file_type, local_path) VALUES (?, ?, ?, ?)`,
      [rfqId, filename, ext, join(attachDir, filename)]
    );
  }
  
  // Log activity
  db.run(
    `INSERT INTO activity_log (rfq_id, action, details) VALUES (?, ?, ?)`,
    [rfqId, 'processed', JSON.stringify({ attachments: attachData.saved.length, csvs: csvData.length })]
  );
  
  saveDatabase();
  logger.info('RFQ processed successfully', { rfqId, emailId, attachments: attachData.saved.length });
  
  return {
    content: [
      {
        type: 'text',
        text: JSON.stringify({
          rfq_id: rfqId,
          email_id: emailId,
          subject: emailData.subject,
          attachments: attachData.saved,
          csv_data: csvData,
          status: 'processed',
        }, null, 2),
      },
    ],
  };
}

async function batchProcess(limit: number, unreadOnly: boolean) {
  logger.info('Starting batch process', { limit, unreadOnly });
  
  // Get emails from Outlook
  const emailsResult = await handleOutlookTool('outlook_get_bid_board_emails', {
    limit,
    unread_only: unreadOnly,
  });
  
  const emailsData = JSON.parse(emailsResult.content[0].text);
  const processed = [];
  
  logger.info('Processing emails...', { count: emailsData.emails.length });
  
  for (const email of emailsData.emails) {
    try {
      const result = await processEmail(email.id);
      const data = JSON.parse(result.content[0].text);
      processed.push(data);
    } catch (error: any) {
      logger.error('Failed to process email', { emailId: email.id, error: error.message });
    }
  }
  
  logger.info('Batch process complete', { total: emailsData.emails.length, processed: processed.length });
  
  return {
    content: [
      {
        type: 'text',
        text: JSON.stringify({
          total: emailsData.emails.length,
          processed: processed.length,
          rfqs: processed,
        }, null, 2),
      },
    ],
  };
}

async function analyzeRfq(rfqId: number) {
  const db = getDb();
  
  // Get RFQ details
  const rfqResult = db.exec(`SELECT * FROM rfqs WHERE id = ${rfqId}`);
  if (!rfqResult.length || !rfqResult[0].values.length) {
    throw new Error(`RFQ ${rfqId} not found`);
  }
  
  const rfqColumns = rfqResult[0].columns;
  const rfqValues = rfqResult[0].values[0];
  const rfq: any = {};
  rfqColumns.forEach((col, i) => rfq[col] = rfqValues[i]);
  
  // Get attachments
  const attResult = db.exec(`SELECT * FROM attachments WHERE rfq_id = ${rfqId}`);
  const attachments: any[] = [];
  
  if (attResult.length && attResult[0].values.length) {
    const attColumns = attResult[0].columns;
    attResult[0].values.forEach(values => {
      const att: any = {};
      attColumns.forEach((col, i) => att[col] = values[i]);
      attachments.push(att);
    });
  }
  
  // Read CSV data if available
  const csvData = [];
  for (const att of attachments) {
    if (att.file_type === 'csv' && existsSync(att.local_path)) {
      const content = readFileSync(att.local_path, 'utf-8');
      const records = parse(content, { columns: true, skip_empty_lines: true });
      csvData.push({ filename: att.filename, records });
    }
  }
  
  return {
    content: [
      {
        type: 'text',
        text: JSON.stringify({
          rfq,
          attachments,
          csv_data: csvData,
          analysis_note: 'Review the RFQ data above and provide a GO/NO-GO recommendation based on fit, value, and strategic alignment.',
        }, null, 2),
      },
    ],
  };
}

async function updateDecision(rfqId: number, decision: string, reason?: string, winProbability?: number) {
  const db = getDb();
  
  // Update RFQ
  db.run(
    `UPDATE rfqs SET decision = ?, decision_reason = ?, status = 'processed', processed_date = CURRENT_TIMESTAMP WHERE id = ?`,
    [decision, reason || null, rfqId]
  );
  
  // Log decision
  db.run(
    `INSERT INTO decision_log (rfq_id, decision, reason, win_probability, decided_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)`,
    [rfqId, decision, reason || null, winProbability || null]
  );
  
  // Log activity
  db.run(
    `INSERT INTO activity_log (rfq_id, action, details) VALUES (?, ?, ?)`,
    [rfqId, 'decision', JSON.stringify({ decision, reason, winProbability })]
  );
  
  saveDatabase();
  logger.info('RFQ decision recorded', { rfqId, decision });
  
  return {
    content: [
      {
        type: 'text',
        text: JSON.stringify({
          rfq_id: rfqId,
          decision,
          reason,
          win_probability: winProbability,
          status: 'Decision recorded successfully',
        }, null, 2),
      },
    ],
  };
}

async function cleanupDeclined(rfqIds: number[], deleteFromOutlook: boolean = true) {
  const db = getDb();
  const cleaned = [];
  
  for (const rfqId of rfqIds) {
    // Verify it's a NO-GO decision
    const result = db.exec(`SELECT * FROM rfqs WHERE id = ${rfqId} AND decision = 'NO-GO'`);
    
    if (!result.length || !result[0].values.length) {
      logger.warn('Skipping cleanup - not a NO-GO RFQ', { rfqId });
      continue;
    }
    
    const rfqColumns = result[0].columns;
    const rfqValues = result[0].values[0];
    const rfq: any = {};
    rfqColumns.forEach((col, i) => rfq[col] = rfqValues[i]);
    
    // Delete attachment files
    const emailId = rfq.email_id;
    const attachDir = join(getAttachmentsDir(), emailId);
    
    if (existsSync(attachDir)) {
      rmSync(attachDir, { recursive: true, force: true });
      logger.info('Deleted attachment directory', { rfqId, dir: attachDir });
    }
    
    // Delete from Outlook if requested
    if (deleteFromOutlook) {
      try {
        const script = `
          tell application "Microsoft Outlook"
            set theMessage to first message whose id is "${emailId}"
            delete theMessage
            return "deleted"
          end tell
        `;
        
        await execAsync(`osascript -e '${script.replace(/'/g, "'\\''")}'`);
        logger.info('Deleted email from Outlook', { rfqId, emailId });
      } catch (error: any) {
        logger.error('Failed to delete from Outlook', { rfqId, emailId, error: error.message });
      }
    }
    
    // Delete from database
    db.run(`DELETE FROM rfqs WHERE id = ?`, [rfqId]);
    
    cleaned.push({
      rfq_id: rfqId,
      email_id: emailId,
      subject: rfq.subject,
      deleted_from_outlook: deleteFromOutlook,
      deleted: true,
    });
  }
  
  saveDatabase();
  logger.info('Cleaned up declined RFQs', { count: cleaned.length, deletedFromOutlook: deleteFromOutlook });
  
  return {
    content: [
      {
        type: 'text',
        text: JSON.stringify({
          cleaned_count: cleaned.length,
          rfqs: cleaned,
          note: deleteFromOutlook 
            ? 'Local files, database records, AND Outlook emails deleted.'
            : 'Local files and database records deleted. Emails remain in Outlook.',
        }, null, 2),
      },
    ],
  };
}

async function listPending(status: string) {
  const db = getDb();
  
  let query = 'SELECT * FROM rfqs';
  if (status !== 'all') {
    query += ` WHERE status = '${status}'`;
  }
  query += ' ORDER BY received_date DESC';
  
  const result = db.exec(query);
  const rfqs: any[] = [];
  
  if (result.length && result[0].values.length) {
    const columns = result[0].columns;
    result[0].values.forEach(values => {
      const rfq: any = {};
      columns.forEach((col, i) => rfq[col] = values[i]);
      rfqs.push(rfq);
    });
  }
  
  return {
    content: [
      {
        type: 'text',
        text: JSON.stringify({
          count: rfqs.length,
          status,
          rfqs,
        }, null, 2),
      },
    ],
  };
}
