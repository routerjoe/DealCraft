import { z } from 'zod';
import { existsSync, mkdirSync } from 'fs';
import { logger } from './logger.js';

const HOME = process.env.HOME || process.env.USERPROFILE || '';

const EnvSchema = z.object({
  // Base directory for Red River files
  RED_RIVER_BASE_DIR: z.string().min(1).default(HOME ? `${HOME}/RedRiver` : `${process.cwd()}/RedRiver`),

  // Obsidian vault path
  OBSIDIAN_VAULT_PATH: z.string().min(1).default(HOME ? `${HOME}/Documents/RedRiverSales` : `${process.cwd()}/RedRiverSales`),

  // Google Drive credentials (optional for now)
  GOOGLE_APPLICATION_CREDENTIALS: z.string().optional(),

  // SQLite database path (optional, defaults to base_dir/data/rfq_tracking.db)
  SQLITE_DB_PATH: z.string().optional(),

  // Log level
  LOG_LEVEL: z.enum(['debug', 'info', 'warn', 'error']).default('info'),
});

export type Env = z.infer<typeof EnvSchema>;

export function validateEnv(): boolean {
  try {
    const parsed = EnvSchema.parse(process.env);

    // Ensure base directory exists (create if missing)
    if (!existsSync(parsed.RED_RIVER_BASE_DIR)) {
      try {
        mkdirSync(parsed.RED_RIVER_BASE_DIR, { recursive: true });
        logger.info('Created RED_RIVER_BASE_DIR', { path: parsed.RED_RIVER_BASE_DIR });
      } catch (e) {
        logger.error('Failed to create RED_RIVER_BASE_DIR', { path: parsed.RED_RIVER_BASE_DIR, error: e instanceof Error ? e.message : String(e) });
        return false;
      }
    }

    // Ensure attachments directory exists (create if missing)
    const attachmentsDir = process.env.ATTACHMENTS_DIR || `${parsed.RED_RIVER_BASE_DIR}/attachments`;
    if (!existsSync(attachmentsDir)) {
      try {
        mkdirSync(attachmentsDir, { recursive: true });
        logger.info('Created ATTACHMENTS_DIR', { path: attachmentsDir });
      } catch (e) {
        logger.error('Failed to create ATTACHMENTS_DIR', { path: attachmentsDir, error: e instanceof Error ? e.message : String(e) });
        return false;
      }
    }

    // Warn if Obsidian vault does not exist, but do not fail startup
    if (!existsSync(parsed.OBSIDIAN_VAULT_PATH)) {
      logger.warn('OBSIDIAN_VAULT_PATH does not exist (CRM tools will be limited)', {
        path: parsed.OBSIDIAN_VAULT_PATH,
      });
    }

    if (parsed.GOOGLE_APPLICATION_CREDENTIALS && !existsSync(parsed.GOOGLE_APPLICATION_CREDENTIALS)) {
      logger.warn('GOOGLE_APPLICATION_CREDENTIALS file not found', {
        path: parsed.GOOGLE_APPLICATION_CREDENTIALS
      });
    }

    logger.info('Environment validated successfully', {
      baseDir: parsed.RED_RIVER_BASE_DIR,
      obsidianVault: parsed.OBSIDIAN_VAULT_PATH,
      attachmentsDir,
    });
    return true;

  } catch (error) {
    if (error instanceof z.ZodError) {
      logger.error('Environment validation failed', {
        errors: error.errors
      });
    } else {
      logger.error('Unexpected error during environment validation', { error });
    }
    return false;
  }
}

export function getEnv(): Env {
  return EnvSchema.parse(process.env);
}

export function getBaseDir(): string {
  return getEnv().RED_RIVER_BASE_DIR;
}

export function getObsidianPath(): string {
  return getEnv().OBSIDIAN_VAULT_PATH;
}

export function getDbPath(): string {
  const env = getEnv();
  return process.env.SQLITE_DB_PATH || `${env.RED_RIVER_BASE_DIR}/data/rfq_tracking.db`;
}

export function getAttachmentsDir(): string {
  const env = getEnv();
  return process.env.ATTACHMENTS_DIR || `${env.RED_RIVER_BASE_DIR}/attachments`;
}
