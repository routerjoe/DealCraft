#!/usr/bin/env node
/**
 * Bridge script to call TypeScript MCP tools from Python CLI
 * Usage: node mcp/bridge.mjs <tool_name> <json_args>
 */

import { fileURLToPath } from 'url';
import { pathToFileURL } from 'url';
import path from 'path';
import dotenv from 'dotenv';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, '..');

// Load environment
dotenv.config({ path: path.join(projectRoot, '.env') });

async function main() {
    const toolName = process.argv[2];
    const argsJson = process.argv[3] || '{}';
    
    if (!toolName) {
        console.error('Usage: node bridge.mjs <tool_name> <json_args>');
        process.exit(1);
    }
    
    try {
        const toolArgs = JSON.parse(argsJson);
        
        // Initialize database first
        const dbPath = path.join(projectRoot, 'src/database/init.ts');
        const dbUrl = pathToFileURL(dbPath).href;
        const { initializeDatabase } = await import(dbUrl);
        await initializeDatabase();
        
        // Determine which handler to use based on tool name
        let result;
        
        if (toolName.startsWith('outlook_')) {
            // Outlook tools
            const toolPath = path.join(projectRoot, 'src/tools/outlook/index.ts');
            const toolUrl = pathToFileURL(toolPath).href;
            const { handleOutlookTool } = await import(toolUrl);
            result = await handleOutlookTool(toolName, toolArgs);
        } else if (toolName.startsWith('rfq_') || toolName === 'create_rfq_drafts' || toolName === 'rfq_draft_oem_registration') {
            // RFQ tools
            const toolPath = path.join(projectRoot, 'src/tools/rfq/index.ts');
            const toolUrl = pathToFileURL(toolPath).href;
            const { handleRfqTool } = await import(toolUrl);
            result = await handleRfqTool(toolName, toolArgs);
        } else if (toolName.startsWith('intromail_')) {
            // IntroMail tools
            const toolPath = path.join(projectRoot, 'src/tools/intromail/index.ts');
            const toolUrl = pathToFileURL(toolPath).href;
            const { handleIntromailTool } = await import(toolUrl);
            result = await handleIntromailTool(toolName, toolArgs);
        } else {
            throw new Error(`Unknown tool prefix: ${toolName}`);
        }
        
        // Extract and output the result
        if (result && result.content && Array.isArray(result.content)) {
            for (const item of result.content) {
                if (item.type === 'text') {
                    console.log(item.text);
                }
            }
        } else {
            console.log(JSON.stringify(result));
        }
        
    } catch (error) {
        console.error(`Error executing ${toolName}:`, error.message);
        if (error.stack) {
            console.error(error.stack);
        }
        process.exit(1);
    }
}

main();