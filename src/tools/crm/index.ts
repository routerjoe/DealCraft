import { Tool } from '@modelcontextprotocol/sdk/types.js';

export const crmTools: Tool[] = [
  {
    name: 'crm_create_opportunity',
    description: 'Create an opportunity note in Obsidian vault',
    inputSchema: {
      type: 'object',
      properties: {
        title: {
          type: 'string',
          description: 'Opportunity title',
        },
        customer: {
          type: 'string',
          description: 'Customer name',
        },
      },
      required: ['title'],
    },
  },
];

export async function handleCrmTool(name: string, args: any) {
  // Stub implementation - will build out later
  return {
    content: [
      {
        type: 'text',
        text: `CRM tool "${name}" not yet implemented. Coming soon!`,
      },
    ],
  };
}
