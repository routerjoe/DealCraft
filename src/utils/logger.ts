import { writeFileSync, appendFileSync, existsSync, mkdirSync } from 'fs';
import { join } from 'path';

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  data?: any;
}

class Logger {
  private logLevel: LogLevel;
  private logFile: string;

  constructor() {
    this.logLevel = (process.env.LOG_LEVEL as LogLevel) || 'info';
    
    const home = process.env.HOME || process.env.USERPROFILE || '';
    const defaultBaseDir = home ? join(home, 'RedRiver') : join(process.cwd(), 'RedRiver');
    const baseDir = process.env.RED_RIVER_BASE_DIR || defaultBaseDir;
    const logDir = join(baseDir, 'logs');
    
    if (!existsSync(logDir)) {
      mkdirSync(logDir, { recursive: true });
    }
    
    const date = new Date().toISOString().split('T')[0];
    this.logFile = join(logDir, `mcp-server-${date}.log`);
  }

  private shouldLog(level: LogLevel): boolean {
    const levels: LogLevel[] = ['debug', 'info', 'warn', 'error'];
    const currentIndex = levels.indexOf(this.logLevel);
    const messageIndex = levels.indexOf(level);
    return messageIndex >= currentIndex;
  }

  private writeLog(entry: LogEntry): void {
    const logLine = JSON.stringify(entry) + '\n';
    
    try {
      appendFileSync(this.logFile, logLine);
    } catch (error) {
      // Can't log errors to console in MCP server
      // Silently fail or write to stderr only
    }
    
    // MCP servers must not write to stdout - only to log files
    // Removed console.log to prevent JSON protocol errors
  }

  debug(message: string, data?: any): void {
    if (this.shouldLog('debug')) {
      this.writeLog({
        timestamp: new Date().toISOString(),
        level: 'debug',
        message,
        data,
      });
    }
  }

  info(message: string, data?: any): void {
    if (this.shouldLog('info')) {
      this.writeLog({
        timestamp: new Date().toISOString(),
        level: 'info',
        message,
        data,
      });
    }
  }

  warn(message: string, data?: any): void {
    if (this.shouldLog('warn')) {
      this.writeLog({
        timestamp: new Date().toISOString(),
        level: 'warn',
        message,
        data,
      });
    }
  }

  error(message: string, data?: any): void {
    if (this.shouldLog('error')) {
      this.writeLog({
        timestamp: new Date().toISOString(),
        level: 'error',
        message,
        data,
      });
    }
  }
}

export const logger = new Logger();