import { Tool } from '@modelcontextprotocol/sdk/types.js';

export const salesTools: Tool[] = [
  {
    name: 'sales_calculate_margin',
    description: 'Calculate profit margin from cost and sell price',
    inputSchema: {
      type: 'object',
      properties: {
        cost: {
          type: 'number',
          description: 'Cost price',
        },
        sell_price: {
          type: 'number',
          description: 'Sell price',
        },
      },
      required: ['cost', 'sell_price'],
    },
  },
];

export async function handleSalesTool(name: string, args: any) {
  // Stub implementation - will build out later
  return {
    content: [
      {
        type: 'text',
        text: `Sales tool "${name}" not yet implemented. Coming soon!`,
      },
    ],
  };
}
