import { Tool } from '@modelcontextprotocol/sdk/types.js';
import { runFleetingProcessor, upgradeExisting } from './processor.js';

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
        },
        state_path: {
          type: 'string',
          description: 'Optional absolute path for state file (.fleeting_state.json)'
        }
      },
      required: ['scope']
    }
  },
  {
    name: 'fleeting_upgrade_notes',
    description: 'Upgrade existing People and Meeting notes to the latest templates (hub.people and preferred meeting schema/body).',
    inputSchema: {
      type: 'object',
      properties: {
        upgrade_people: {
          type: 'boolean',
          default: true,
          description: 'Upgrade People notes in PEOPLE_DIR'
        },
        upgrade_meetings: {
          type: 'boolean',
          default: true,
          description: 'Upgrade Meeting notes in MEETING_NOTES_DIR'
        },
        dry_run: {
          type: 'boolean',
          default: false,
          description: 'Preview upgrade without writing'
        },
        target_dir: {
          type: 'string',
          description: 'Optional override for DAILY_NOTES_DIR (not typically needed for upgrades)'
        }
      }
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
      // Allow explicit state_path override for hosts with read-only cwd
      if (args?.state_path) {
        process.env.STATE_PATH = String(args.state_path);
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
    case 'fleeting_upgrade_notes': {
      const res = await upgradeExisting({
        upgradePeople: args?.upgrade_people !== false,
        upgradeMeetings: args?.upgrade_meetings !== false,
        targetDir: args?.target_dir,
        dryRun: args?.dry_run === true
      });
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(res, null, 2)
          }
        ]
      };
    }
    default:
      throw new Error(`Unknown Fleeting tool: ${name}`);
  }
}