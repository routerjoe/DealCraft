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
import { calculateRfqScore, applyRulesFromInputs } from './rules.js';

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
          description: 'Also delete the email from Outlook Bid Board (default: false)',
          default: false,
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
  },
  {
    name: 'rfq_set_attributes',
    description: 'Update RFQ metadata fields used by rules and scoring',
    inputSchema: {
      type: 'object',
      properties: {
        rfq_id: { type: 'number' },
        estimated_value: { type: 'number' },
        competition_level: { type: 'number' },
        tech_vertical: { type: 'string' },
        oem: { type: 'string' },
        has_previous_contract: { type: 'boolean' },
        deadline: { type: 'string' },
        customer: { type: 'string' }
      },
      required: ['rfq_id']
    }
  },
  {
    name: 'rfq_calculate_score',
    description: 'Calculate and persist RFQ score and recommendation from stored attributes',
    inputSchema: {
      type: 'object',
      properties: {
        rfq_id: { type: 'number', description: 'RFQ ID from database' }
      },
      required: ['rfq_id']
    }
  },
  {
    name: 'rfq_apply_rules',
    description: 'Apply automated RFQ rules and compute score; records outcomes. Respects RFQ_AUTO_DECLINE_ENABLED for auto NO-GO, never deletes Outlook.',
    inputSchema: {
      type: 'object',
      properties: {
        rfq_id: { type: 'number' },
        rfq_type: { type: 'string', description: 'e.g., RFI, Market Research Request, renewal' },
        quantity: { type: 'number', description: 'Optional quantity to evaluate R005' }
      },
      required: ['rfq_id']
    }
  },
  {
    name: 'rfq_track_oem_occurrence',
    description: 'Log an OEM occurrence for the RFQ and update tracking counters; uses config tables from rfq_config.sql',
    inputSchema: {
      type: 'object',
      properties: {
        rfq_id: { type: 'number' },
        oem: { type: 'string', description: 'OEM name; defaults to RFQ.oem when omitted' },
        estimated_value: { type: 'number', description: 'Overrides RFQ.estimated_value for this occurrence' },
        competition_level: { type: 'number', description: 'Overrides RFQ.competition_level for this occurrence' },
        technology_vertical: { type: 'string', description: 'Overrides RFQ.tech_vertical for this occurrence' }
      },
      required: ['rfq_id']
    }
  }
];

export async function handleRfqTool(name: string, args: any) {
  switch (name) {
    case 'rfq_process_email':
      return await processEmail(args.email_id);
    
    case 'rfq_batch_process':
      return await batchProcess(args.limit || 10, args.unread_only !== false);
    case 'rfq_analyze':
      return await analyzeRfqEnhanced(args.rfq_id);
      
    
    case 'rfq_update_decision':
      return await updateDecision(args.rfq_id, args.decision, args.reason, args.win_probability);
    
    case 'rfq_cleanup_declined':
      return await cleanupDeclined(args.rfq_ids, args.delete_from_outlook === true);
    
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
    case 'rfq_set_attributes': {
      const db = getDb();
      const rfqId = Number(args.rfq_id);
      if (!rfqId) throw new Error('rfq_id is required');

      const fields: any = {
        estimated_value: args.estimated_value,
        competition_level: args.competition_level,
        tech_vertical: args.tech_vertical,
        oem: args.oem,
        has_previous_contract: typeof args.has_previous_contract === 'boolean' ? (args.has_previous_contract ? 1 : 0) : undefined,
        deadline: args.deadline,
        customer: args.customer,
      };

      const sets: string[] = [];
      const vals: any[] = [];
      for (const [k, v] of Object.entries(fields)) {
        if (v !== undefined && v !== null && v !== '') {
          sets.push(`${k} = ?`);
          vals.push(v);
        }
      }
      if (sets.length === 0) {
        return {
          content: [{ type: 'text', text: JSON.stringify({ updated: false, note: 'No fields provided' }) }],
        };
      }

      db.run(`UPDATE rfqs SET ${sets.join(', ')}, updated_at = CURRENT_TIMESTAMP WHERE id = ?`, [...vals, rfqId]);

      const rowRes = db.exec(`SELECT * FROM rfqs WHERE id = ${rfqId}`);
      let row: any = null;
      if (rowRes.length && rowRes[0].values.length) {
        const c = rowRes[0].columns;
        const v = rowRes[0].values[0];
        row = {};
        c.forEach((col, i) => (row[col] = v[i]));
      }

      db.run(`INSERT INTO activity_log (rfq_id, action, details) VALUES (?, ?, ?)`, [rfqId, 'attributes_updated', JSON.stringify(fields)]);
      saveDatabase();
      return {
        content: [{ type: 'text', text: JSON.stringify({ updated: true, rfq: row }, null, 2) }],
      };
    }
    case 'rfq_calculate_score': {
      const db = getDb();
      const rfqId = Number(args.rfq_id);
      if (!rfqId) throw new Error('rfq_id is required');

      const res = db.exec(`SELECT * FROM rfqs WHERE id = ${rfqId}`);
      if (!res.length || !res[0].values.length) throw new Error(`RFQ ${rfqId} not found`);
      const cols = res[0].columns;
      const valsArr = res[0].values[0];
      const rfq: any = {};
      cols.forEach((c, i) => (rfq[c] = valsArr[i]));

      const scoreRes = calculateRfqScore({
        value: Number(rfq.estimated_value || 0),
        competition: Number(rfq.competition_level || 0),
        customer: rfq.customer || '',
        tech_vertical: rfq.tech_vertical || '',
        oem: rfq.oem || '',
        has_previous_contract: !!rfq.has_previous_contract,
      });

      db.run(
        `UPDATE rfqs SET rfq_score = ?, rfq_recommendation = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?`,
        [scoreRes.score, scoreRes.recommendation, rfqId]
      );
      db.run(
        `INSERT INTO activity_log (rfq_id, action, details) VALUES (?, ?, ?)`,
        [rfqId, 'scored', JSON.stringify(scoreRes)]
      );
      saveDatabase();

      return {
        content: [{ type: 'text', text: JSON.stringify(scoreRes, null, 2) }],
      };
    }
    case 'rfq_apply_rules': {
      const db = getDb();
      const rfqId = Number(args.rfq_id);
      if (!rfqId) throw new Error('rfq_id is required');

      const res = db.exec(`SELECT * FROM rfqs WHERE id = ${rfqId}`);
      if (!res.length || !res[0].values.length) throw new Error(`RFQ ${rfqId} not found`);
      const cols = res[0].columns;
      const valsArr = res[0].values[0];
      const rfq: any = {};
      cols.forEach((c, i) => (rfq[c] = valsArr[i]));

      const attCountRes = db.exec(`SELECT COUNT(*) FROM attachments WHERE rfq_id = ${rfqId}`);
      const hasAttachments = attCountRes.length && attCountRes[0].values.length ? Number(attCountRes[0].values[0][0]) > 0 : false;

      const inputs = {
        subject: rfq.subject || '',
        sender: rfq.sender || '',
        rfq_type: String(args.rfq_type || ''),
        competition: Number(rfq.competition_level || 0),
        value: Number(rfq.estimated_value || 0),
        customer: rfq.customer || '',
        tech_vertical: rfq.tech_vertical || '',
        oem: rfq.oem || '',
        has_previous_contract: !!rfq.has_previous_contract,
        quantity: typeof args.quantity === 'number' ? args.quantity : 0,
        deadline: rfq.deadline || undefined,
        has_attachments: hasAttachments,
      };

      const ruleRes = applyRulesFromInputs(inputs);
      const scoreRes = calculateRfqScore({
        value: inputs.value,
        competition: inputs.competition,
        customer: inputs.customer,
        tech_vertical: inputs.tech_vertical,
        oem: inputs.oem,
        has_previous_contract: inputs.has_previous_contract,
      });

      db.run(
        `UPDATE rfqs SET rfq_score = ?, rfq_recommendation = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?`,
        [scoreRes.score, scoreRes.recommendation, rfqId]
      );
      db.run(
        `INSERT INTO activity_log (rfq_id, action, details) VALUES (?, ?, ?)`,
        [rfqId, 'rules_applied', JSON.stringify({ inputs, ruleRes, scoreRes })]
      );

      const autoEnabled = String(process.env.RFQ_AUTO_DECLINE_ENABLED || '').toLowerCase() === 'true';
      let autoDeclined = false;
      if (autoEnabled && ruleRes.auto_decline) {
        await updateDecision(
          rfqId,
          'NO-GO',
          `Auto-decline rules: ${ruleRes.auto_decline_reasons.join('; ')}`,
          undefined
        );
        autoDeclined = true;
      }

      saveDatabase();

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(
              {
                auto_declined: autoDeclined,
                rules: ruleRes.outcomes,
                auto_decline_reasons: ruleRes.auto_decline_reasons,
                score: scoreRes.score,
                recommendation: scoreRes.recommendation,
              },
              null,
              2
            ),
          },
        ],
      };
    }
    case 'rfq_track_oem_occurrence': {
      const db = getDb();
      const rfqId = Number(args.rfq_id);
      if (!rfqId) throw new Error('rfq_id is required');

      const res = db.exec(`SELECT * FROM rfqs WHERE id = ${rfqId}`);
      if (!res.length || !res[0].values.length) throw new Error(`RFQ ${rfqId} not found`);
      const cols = res[0].columns;
      const valsArr = res[0].values[0];
      const rfq: any = {};
      cols.forEach((c, i) => (rfq[c] = valsArr[i]));

      const oem: string | undefined = (args.oem || rfq.oem || '').toString();
      if (!oem) throw new Error('oem is required');

      const estVal = typeof args.estimated_value === 'number' ? args.estimated_value : Number(rfq.estimated_value || 0);
      const comp = typeof args.competition_level === 'number' ? args.competition_level : Number(rfq.competition_level || 0);
      const tech = (args.technology_vertical || rfq.tech_vertical || null) as string | null;

      db.run(
        `INSERT OR IGNORE INTO config_oem_tracking (oem_name, currently_authorized, business_case_threshold, notes) VALUES (?, 0, 5, 'Auto-added by tracker')`,
        [oem]
      );

      db.run(
        `INSERT INTO oem_occurrence_log (oem_name, rfq_id, rfq_number, customer, estimated_value, competition_level, technology_vertical)
         VALUES (?, ?, ?, ?, ?, ?, ?)`,
        [oem, rfqId, String(rfqId), rfq.customer || null, estVal || null, comp || null, tech]
      );

      db.run(
        `UPDATE config_oem_tracking
         SET occurrence_count = COALESCE(occurrence_count, 0) + 1,
             total_value_seen = COALESCE(total_value_seen, 0) + ?,
             updated_at = CURRENT_TIMESTAMP
         WHERE oem_name = ?`,
        [estVal || 0, oem]
      );

      const trackRes = db.exec(
        `SELECT oem_name, occurrence_count, total_value_seen, business_case_threshold, currently_authorized
         FROM config_oem_tracking WHERE oem_name = '${oem.replace(/'/g, "''")}' LIMIT 1`
      );
      let row: any = null;
      if (trackRes.length && trackRes[0].values.length) {
        const c = trackRes[0].columns;
        const v = trackRes[0].values[0];
        row = {};
        c.forEach((col, i) => (row[col] = v[i]));
      }

      saveDatabase();

      return {
        content: [{ type: 'text', text: JSON.stringify({ oem, tracking: row }, null, 2) }],
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
  const csvData: any[] = [];
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

  // Upsert RFQ by email_id to avoid UNIQUE constraint violations
  logger.info('Storing in database...');
  const subject = emailData.subject || 'Unknown';
  const sender = emailData.from || 'Unknown';
  const received = emailData.date || new Date().toISOString();

  const safeEmailId = emailId.replace(/'/g, "''");
  let rfqId: number;
  let alreadyExisted = false;

  const existing = db.exec(`SELECT id FROM rfqs WHERE email_id = '${safeEmailId}'`);
  if (existing.length && existing[0].values.length) {
    rfqId = existing[0].values[0][0] as number;
    alreadyExisted = true;
    // Update metadata in case anything changed
    db.run(
      `UPDATE rfqs SET subject = ?, sender = ?, received_date = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?`,
      [subject, sender, received, rfqId]
    );
    logger.info('RFQ already existed - updated metadata', { rfqId, emailId });
  } else {
    db.run(
      `INSERT INTO rfqs (email_id, subject, sender, received_date, status) VALUES (?, ?, ?, ?, 'pending')`,
      [emailId, subject, sender, received]
    );
    const result = db.exec('SELECT last_insert_rowid() as id');
    rfqId = result[0].values[0][0] as number;
    logger.info('Inserted new RFQ', { rfqId, emailId });
  }

  // Insert attachments (skip duplicates by rfq_id + filename)
  for (const filename of attachData.saved) {
    const ext = filename.split('.').pop()?.toLowerCase() || '';
    const localPath = join(attachDir, filename);
    const safeFilename = filename.replace(/'/g, "''");
    const existsAtt = db.exec(`SELECT id FROM attachments WHERE rfq_id = ${rfqId} AND filename = '${safeFilename}'`);
    if (!existsAtt.length || !existsAtt[0].values.length) {
      db.run(
        `INSERT INTO attachments (rfq_id, filename, file_type, local_path) VALUES (?, ?, ?, ?)`,
        [rfqId, filename, ext, localPath]
      );
    } else {
      logger.debug('Attachment already recorded - skipping insert', { rfqId, filename });
    }
  }

  // Log activity
  db.run(
    `INSERT INTO activity_log (rfq_id, action, details) VALUES (?, ?, ?)`,
    [rfqId, alreadyExisted ? 'reprocessed' : 'processed', JSON.stringify({ attachments: attachData.saved.length, csvs: csvData.length })]
  );

  saveDatabase();

  // Mark Outlook email as read to prevent reprocessing
  try {
    await handleOutlookTool('outlook_mark_as_read', { email_id: emailId });
  } catch (e: any) {
    logger.warn('Failed to mark email as read', { emailId, error: e?.message || String(e) });
  }

  logger.info('RFQ processed successfully', { rfqId, emailId, attachments: attachData.saved.length, alreadyExisted });

  return {
    content: [
      {
        type: 'text',
        text: JSON.stringify(
          {
            rfq_id: rfqId,
            email_id: emailId,
            subject: emailData.subject,
            attachments: attachData.saved,
            csv_data: csvData,
            status: alreadyExisted ? 'already_exists' : 'processed',
          },
          null,
          2
        ),
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

async function cleanupDeclined(rfqIds: number[], deleteFromOutlook: boolean = false) {
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


// Enhanced analyzer that includes scoring, rule flags, and guidance
async function analyzeRfqEnhanced(rfqId: number) {
  const db = getDb();

  // Get RFQ details
  const rfqResult = db.exec(`SELECT * FROM rfqs WHERE id = ${rfqId}`);
  if (!rfqResult.length || !rfqResult[0].values.length) {
    throw new Error(`RFQ ${rfqId} not found`);
  }

  const rfqColumns = rfqResult[0].columns;
  const rfqValues = rfqResult[0].values[0];
  const rfq: any = {};
  rfqColumns.forEach((col, i) => (rfq[col] = rfqValues[i]));

  // Get attachments
  const attResult = db.exec(`SELECT * FROM attachments WHERE rfq_id = ${rfqId}`);
  const attachments: any[] = [];

  if (attResult.length && attResult[0].values.length) {
    const attColumns = attResult[0].columns;
    attResult[0].values.forEach((values) => {
      const att: any = {};
      attColumns.forEach((col, i) => (att[col] = values[i]));
      attachments.push(att);
    });
  }

  // Read CSV data if available
  const csvData: any[] = [];
  for (const att of attachments) {
    if (att.file_type === 'csv' && existsSync(att.local_path)) {
      const content = readFileSync(att.local_path, 'utf-8');
      const records = parse(content, { columns: true, skip_empty_lines: true });
      csvData.push({ filename: att.filename, records });
    }
  }

  // Compute score and rule flags using current metadata
  const hasAttachments = attachments.length > 0;
  const inputs = {
    subject: rfq.subject || '',
    sender: rfq.sender || '',
    rfq_type: '', // optional; provide via rfq_apply_rules for type-specific behavior
    competition: Number(rfq.competition_level || 0),
    value: Number(rfq.estimated_value || 0),
    customer: rfq.customer || '',
    tech_vertical: rfq.tech_vertical || '',
    oem: rfq.oem || '',
    has_previous_contract: !!rfq.has_previous_contract,
    quantity: 0,
    deadline: rfq.deadline || undefined,
    has_attachments: hasAttachments,
  };

  const scoreRes = calculateRfqScore({
    value: inputs.value,
    competition: inputs.competition,
    customer: inputs.customer,
    tech_vertical: inputs.tech_vertical,
    oem: inputs.oem,
    has_previous_contract: inputs.has_previous_contract,
  });

  const rulesRes = applyRulesFromInputs(inputs);

  // Identify missing fields to prompt population before finalizing
  const missing_fields: string[] = [];
  if (rfq.estimated_value == null) missing_fields.push('estimated_value');
  if (rfq.competition_level == null) missing_fields.push('competition_level');
  if (!rfq.tech_vertical) missing_fields.push('tech_vertical');
  if (!rfq.oem) missing_fields.push('oem');
  if (rfq.has_previous_contract == null) missing_fields.push('has_previous_contract');
  if (!rfq.customer) missing_fields.push('customer');
  if (!rfq.deadline) missing_fields.push('deadline');

  return {
    content: [
      {
        type: 'text',
        text: JSON.stringify(
          {
            rfq,
            attachments,
            csv_data: csvData,
            score: scoreRes,
            rule_outcomes: rulesRes.outcomes,
            auto_decline_candidates: rulesRes.auto_decline_reasons,
            missing_fields_checklist: missing_fields,
            guidance: missing_fields.length
              ? 'Use rfq_set_attributes to populate missing fields, then run rfq_apply_rules.'
              : 'Run rfq_apply_rules to record outcomes and optionally auto-decline if enabled.',
          },
          null,
          2
        ),
      },
    ],
  };
}