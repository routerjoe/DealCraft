import { z } from 'zod';
import { existsSync } from 'fs';
import { logger } from './logger.js';

const EnvSchema = z.object({
  // Base directory for Red River files
  RED_RIVER_BASE_DIR: z.string().min(1),
  
  // Obsidian vault path
  OBSIDIAN_VAULT_PATH: z.string().min(1),
  
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
    
    // Check if directories exist
    if (!existsSync(parsed.RED_RIVER_BASE_DIR)) {
      logger.error('RED_RIVER_BASE_DIR does not exist', { 
        path: parsed.RED_RIVER_BASE_DIR 
      });
      return false;
    }
    
    if (!existsSync(parsed.OBSIDIAN_VAULT_PATH)) {
      logger.error('OBSIDIAN_VAULT_PATH does not exist', { 
        path: parsed.OBSIDIAN_VAULT_PATH 
      });
      return false;
    }
    
    if (parsed.GOOGLE_APPLICATION_CREDENTIALS && !existsSync(parsed.GOOGLE_APPLICATION_CREDENTIALS)) {
      logger.warn('GOOGLE_APPLICATION_CREDENTIALS file not found', {
        path: parsed.GOOGLE_APPLICATION_CREDENTIALS
      });
    }
    
    logger.info('Environment validated successfully');
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
  return process.env.RED_RIVER_BASE_DIR || '';
}

export function getObsidianPath(): string {
  return process.env.OBSIDIAN_VAULT_PATH || '';
}

export function getDbPath(): string {
  return process.env.SQLITE_DB_PATH || `${getBaseDir()}/data/rfq_tracking.db`;
}
