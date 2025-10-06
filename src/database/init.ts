import initSqlJs, { Database as SqlJsDatabase } from 'sql.js';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'fs';
import { dirname, join } from 'path';
import { createRequire } from 'module';
import { getDbPath } from '../utils/env.js';
import { logger } from '../utils/logger.js';

let db: SqlJsDatabase | null = null;
let SQL: any = null;

export function getDb(): SqlJsDatabase {
  if (!db) {
    throw new Error('Database not initialized. Call initializeDatabase() first.');
  }
  return db;
}

export async function initializeDatabase(): Promise<void> {
  const dbPath = getDbPath();
  const dbDir = dirname(dbPath);

  // Create directory if it doesn't exist
  if (!existsSync(dbDir)) {
    mkdirSync(dbDir, { recursive: true });
    logger.info('Created database directory', { path: dbDir });
  }

  // Initialize SQL.js
  {
    const require = createRequire(import.meta.url);
    const wasmPath = require.resolve('sql.js/dist/sql-wasm.wasm');
    SQL = await initSqlJs({
      locateFile: (file: string) => join(dirname(wasmPath), file),
    });
  }

  // Load existing database or create new one
  if (existsSync(dbPath)) {
    const buffer = readFileSync(dbPath);
    db = new SQL.Database(buffer);
    logger.info('Loaded existing database', { path: dbPath });
  } else {
    db = new SQL.Database();
    logger.info('Created new database', { path: dbPath });
  }

  // Create tables
  createTables();

  // Save database to disk
  saveDatabase();
}

function createTables(): void {
  if (!db) return;

  // RFQs table
  db.run(`
    CREATE TABLE IF NOT EXISTS rfqs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      email_id TEXT UNIQUE NOT NULL,
      subject TEXT NOT NULL,
      sender TEXT,
      received_date TEXT NOT NULL,
      processed_date TEXT,
      status TEXT DEFAULT 'pending',
      decision TEXT,
      decision_reason TEXT,
      estimated_value REAL,
      customer TEXT,
      agency TEXT,
      deadline TEXT,
      obsidian_note_path TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
  `);

  // Attachments table
  db.run(`
    CREATE TABLE IF NOT EXISTS attachments (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      rfq_id INTEGER NOT NULL,
      filename TEXT NOT NULL,
      file_type TEXT,
      file_size INTEGER,
      local_path TEXT,
      gdrive_url TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (rfq_id) REFERENCES rfqs(id) ON DELETE CASCADE
    )
  `);

  // Decisions log table
  db.run(`
    CREATE TABLE IF NOT EXISTS decision_log (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      rfq_id INTEGER NOT NULL,
      decision TEXT NOT NULL,
      reason TEXT,
      win_probability INTEGER,
      resource_requirements TEXT,
      strategic_value TEXT,
      decided_by TEXT,
      decided_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (rfq_id) REFERENCES rfqs(id) ON DELETE CASCADE
    )
  `);

  // Sales calculations table
  db.run(`
    CREATE TABLE IF NOT EXISTS sales_calculations (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      rfq_id INTEGER,
      calc_type TEXT NOT NULL,
      input_data TEXT,
      result_data TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (rfq_id) REFERENCES rfqs(id) ON DELETE SET NULL
    )
  `);

  // Activity log table
  db.run(`
    CREATE TABLE IF NOT EXISTS activity_log (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      rfq_id INTEGER,
      action TEXT NOT NULL,
      details TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (rfq_id) REFERENCES rfqs(id) ON DELETE SET NULL
    )
  `);

  // Create indexes for performance
  db.run(`CREATE INDEX IF NOT EXISTS idx_rfqs_status ON rfqs(status)`);
  db.run(`CREATE INDEX IF NOT EXISTS idx_rfqs_decision ON rfqs(decision)`);
  db.run(`CREATE INDEX IF NOT EXISTS idx_rfqs_received_date ON rfqs(received_date)`);
  db.run(`CREATE INDEX IF NOT EXISTS idx_activity_log_created_at ON activity_log(created_at)`);

  logger.info('Database tables created successfully');
}

export function saveDatabase(): void {
  if (!db) return;
  
  const dbPath = getDbPath();
  const data = db.export();
  const buffer = Buffer.from(data);
  writeFileSync(dbPath, buffer);
  logger.debug('Database saved to disk', { path: dbPath });
}

export function closeDatabase(): void {
  if (db) {
    saveDatabase();
    db.close();
    db = null;
    logger.info('Database connection closed');
  }
}
