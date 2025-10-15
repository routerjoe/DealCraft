#!/usr/bin/env node

/**
 * Red River Sales Automation MCP Server
 * 
 * Comprehensive automation for:
 * - RFQ processing from Outlook Bid Board
 * - Sales calculations and pricing
 * - Obsidian CRM integration
 * - Google Drive exports
 * - SQLite analytics
 */

import * as path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import { initializeDatabase } from './database/init.js';
import { logger } from './utils/logger.js';
import { validateEnv } from './utils/env.js';

// Load .env from project root (one level up from dist)
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
dotenv.config({ path: path.resolve(__dirname, '../.env') });

// Import tool handlers
import { outlookTools, handleOutlookTool } from './tools/outlook/index.js';
import { rfqTools, handleRfqTool } from './tools/rfq/index.js';
import { salesTools, handleSalesTool } from './tools/sales/index.js';
import { crmTools, handleCrmTool } from './tools/crm/index.js';
import { analyticsTools, handleAnalyticsTool } from './tools/analytics/index.js';
import { exportTools, handleExportTool } from './tools/export/index.js';
import { fleetingTools, handleFleetingTool } from './tools/fleeting/index.js';
import { intromailTools, handleIntromailTool } from './tools/intromail/index.js';

class RedRiverMCPServer {
  private server: Server;
  private tools: any[];

  constructor() {
    this.server = new Server(
      {
        name: 'red-river-sales-automation',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    // Combine all tools
    this.tools = [
      ...outlookTools,
      ...rfqTools,
      ...salesTools,
      ...crmTools,
      ...analyticsTools,
      ...exportTools,
      ...fleetingTools,
      ...intromailTools,
    ];

    this.setupHandlers();
  }

  private setupHandlers() {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: this.tools,
    }));

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      logger.info('Tool called', { tool: name, args });

      try {
        // Route to appropriate handler based on tool name prefix
        if (name.startsWith('outlook_')) {
          return await handleOutlookTool(name, args);
        } else if (name.startsWith('rfq_')) {
          return await handleRfqTool(name, args);
        } else if (name === 'create_rfq_drafts') {
          // Special-case RFQ draft tool without rfq_ prefix
          return await handleRfqTool(name, args);
        } else if (name.startsWith('sales_')) {
          return await handleSalesTool(name, args);
        } else if (name.startsWith('crm_')) {
          return await handleCrmTool(name, args);
        } else if (name.startsWith('analytics_')) {
          return await handleAnalyticsTool(name, args);
        } else if (name.startsWith('export_')) {
          return await handleExportTool(name, args);
        } else if (name.startsWith('fleeting_')) {
          return await handleFleetingTool(name, args);
        } else if (name.startsWith('intromail')) {
          return await handleIntromailTool(name, args);
        }

        throw new Error(`Unknown tool: ${name}`);
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        logger.error('Tool execution failed', { tool: name, error: errorMessage });
        
        return {
          content: [
            {
              type: 'text',
              text: `Error executing ${name}: ${errorMessage}`,
            },
          ],
          isError: true,
        };
      }
    });
  }

  async start() {
    // Validate environment
    const envValid = validateEnv();
    if (!envValid) {
      logger.error('Environment validation failed');
      process.exit(1);
    }

    // Initialize database
    await initializeDatabase();

    // Start MCP server
    const transport = new StdioServerTransport();
    await this.server.connect(transport);

    logger.info('Red River Sales Automation MCP Server running', {
      tools: this.tools.length,
      version: '1.0.0',
    });
  }
}

// Start server
const server = new RedRiverMCPServer();
server.start().catch((error) => {
  logger.error('Failed to start server', { error });
  process.exit(1);
});
