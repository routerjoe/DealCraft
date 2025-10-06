import { execFile } from 'child_process';
import { promisify } from 'util';
import { existsSync } from 'fs';
import path from 'path';
import { z } from 'zod';
import { logger } from '../../utils/logger.js';

export const RfqDraftArgsSchema = z.object({
  customer: z.string(),
  command: z.string(),
  oem: z.string(),
  rfq_id: z.string(),
  contract_vehicle: z.string(),
  due_date: z.string(), // Expect YYYY-MM-DD; validated upstream if needed
  est_value: z.number().optional().default(0),
  poc_name: z.string(),
  poc_email: z.string(),
  folder_path: z.string(),
  attachments: z.array(z.string()).optional().default([]),
});

export type RfqDraftArgs = z.infer<typeof RfqDraftArgsSchema>;

const execFileAsync = promisify(execFile);

function resolveAppleScriptPath(): string {
  // When compiled, __dirname will be: dist/tools/rfq
  // Project root is two levels up from dist (dist -> project root), so from dist/tools/rfq it is three levels up.
  const candidates = [
    path.resolve(__dirname, '../../../scripts/create_rfq_drafts.applescript'),
    // Fallbacks for safety in different execution contexts (tests, direct runs)
    path.resolve(process.cwd(), 'scripts/create_rfq_drafts.applescript'),
    path.resolve(__dirname, '../../../../scripts/create_rfq_drafts.applescript'),
  ];
  for (const p of candidates) {
    if (existsSync(p)) return p;
  }
  throw new Error('AppleScript not found at scripts/create_rfq_drafts.applescript');
}

function normalizeAttachments(attachments: string[] | undefined): string[] {
  if (!attachments || attachments.length === 0) return [];
  const result: string[] = [];
  for (const p of attachments) {
    const abs = path.isAbsolute(p) ? p : path.resolve(p);
    if (existsSync(abs)) {
      result.push(abs);
    } else {
      logger.warn('Attachment path not found, skipping', { path: abs });
    }
  }
  return result;
}

/**
 * Local-only tool. Calls osascript with a JSON payload to create two Outlook draft emails (OEM + Internal).
 * Relies on environment variables loaded by dotenv at server start.
 */
export async function createRfqDrafts(args: unknown): Promise<string> {
  const parsed = RfqDraftArgsSchema.parse(args);
  const scriptPath = resolveAppleScriptPath();

  const payload = {
    ...parsed,
    attachments: normalizeAttachments(parsed.attachments),
  };

  try {
    const { stdout } = await execFileAsync('osascript', [scriptPath, JSON.stringify(payload)], {
      env: process.env,
      maxBuffer: 10 * 1024 * 1024,
    });

    const text = (stdout || '').toString().trim();
    if (text.startsWith('ERROR:')) {
      // Surface AppleScript error verbatim
      throw new Error(text);
    }
    // AppleScript returns "OK" on success
    return text || 'OK';
  } catch (error: any) {
    logger.error('create_rfq_drafts osascript invocation failed', {
      error: error?.message || String(error),
    });
    throw error;
  }
}