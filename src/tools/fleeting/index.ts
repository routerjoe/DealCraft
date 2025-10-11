import { Tool } from '@modelcontextprotocol/sdk/types.js';
import { runFleetingProcessor } from './processor.js';

const AllowedScopes = ['today','this-week','this-month','since-last-run','range'] as const;

export const fleetingTools: Tool[] = [
  {
    name: 'fleeting_process_notes',
    description: 'Process Fleeting Notes (meetings, contacts, tasks, audit) with batching, dry-run, and state skip.',
    inputSchema: {
      type: 'object',
      properties: {
        scope: {
          type: 'string',
          enum: ['today','this-week','this-month','since-last-run','range'],
          description: 'Processing scope window.'
        },
        range: {
          type: 'string',
          description: 'Range when scope=range: YYYY-MM-DD..YYYY-MM-DD'
        },
        dry_run: {
          type: 'boolean',
          default: false,
          description: 'Preview changes without writing'
        },
        force: {
          type: 'boolean',
          default: false,
          description: 'Re-process even if unchanged'
        },
        target_dir: {
          type: 'string',
          description: 'Optional override for DAILY_NOTES_DIR'
        }
      },
      required: ['scope']
    }
  }
];

export async function handleFleetingTool(name: string, args: any) {
  switch (name) {
    case 'fleeting_process_notes': {
      const scope = String(args?.scope || '');
      if (!AllowedScopes.includes(scope as any)) {
        throw new Error(`Invalid scope: ${scope}`);
      }
      const summary = await runFleetingProcessor({
        scope: scope as any,
        range: args?.range,
        dryRun: args?.dry_run === true,
        force: args?.force === true,
        targetDir: args?.target_dir
      });
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(summary, null, 2)
          }
        ]
      };
    }
    default:
      throw new Error(`Unknown Fleeting tool: ${name}`);
  }
}