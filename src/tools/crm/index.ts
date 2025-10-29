import { Tool } from '@modelcontextprotocol/sdk/types.js';

const API_BASE = process.env.API_BASE_URL || 'http://localhost:8000';

export const crmTools: Tool[] = [
  {
    name: 'crm_export',
    description: 'Export opportunities to CRM system (Salesforce, HubSpot, Dynamics, etc.) with attribution data',
    inputSchema: {
      type: 'object',
      properties: {
        opportunity_ids: {
          type: 'array',
          items: { type: 'string' },
          description: 'Opportunity IDs to export (optional - exports all if not provided)',
        },
        format: {
          type: 'string',
          enum: ['salesforce', 'hubspot', 'dynamics', 'generic_json', 'generic_yaml'],
          description: 'CRM export format',
          default: 'generic_json',
        },
        dry_run: {
          type: 'boolean',
          description: 'If true, validate only without actual sync (default: true for safety)',
          default: true,
        },
      },
    },
  },
  {
    name: 'crm_attribution',
    description: 'Calculate revenue attribution breakdown across OEMs, partners, regions for opportunities',
    inputSchema: {
      type: 'object',
      properties: {
        opportunity_ids: {
          type: 'array',
          items: { type: 'string' },
          description: 'Opportunity IDs (optional - calculates for all if not provided)',
        },
      },
    },
  },
  {
    name: 'crm_validate',
    description: 'Validate an opportunity has all required fields for CRM export',
    inputSchema: {
      type: 'object',
      properties: {
        opportunity_id: {
          type: 'string',
          description: 'Opportunity ID to validate',
        },
      },
      required: ['opportunity_id'],
    },
  },
];

export async function handleCrmTool(name: string, args: any) {
  try {
    if (name === 'crm_export') {
      const response = await fetch(`${API_BASE}/v1/crm/export`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(args),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'CRM export failed');
      }

      const result = await response.json();
      return {
        content: [
          {
            type: 'text',
            text: `CRM Export ${result.dry_run ? '(DRY-RUN)' : 'COMPLETE'}:\n` +
                  `Total: ${result.total}\n` +
                  `Success: ${result.success_count}\n` +
                  `Errors: ${result.error_count}\n\n` +
                  JSON.stringify(result, null, 2),
          },
        ],
      };
    } else if (name === 'crm_attribution') {
      const response = await fetch(`${API_BASE}/v1/crm/attribution`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(args),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Attribution calculation failed');
      }

      const result = await response.json();
      return {
        content: [
          {
            type: 'text',
            text: `Revenue Attribution Calculated:\n` +
                  `Total Opportunities: ${result.total}\n\n` +
                  JSON.stringify(result.attributions, null, 2),
          },
        ],
      };
    } else if (name === 'crm_validate') {
      const response = await fetch(`${API_BASE}/v1/crm/validate/${args.opportunity_id}`);

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Validation failed');
      }

      const result = await response.json();
      return {
        content: [
          {
            type: 'text',
            text: result.valid
              ? `✓ Opportunity ${args.opportunity_id} is valid for CRM export`
              : `✗ Validation errors:\n${result.errors.join('\n')}`,
          },
        ],
      };
    }

    throw new Error(`Unknown CRM tool: ${name}`);
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    return {
      content: [
        {
          type: 'text',
          text: `Error: ${errorMessage}`,
        },
      ],
      isError: true,
    };
  }
}
