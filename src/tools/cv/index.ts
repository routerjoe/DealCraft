import { Tool } from '@modelcontextprotocol/sdk/types.js';

const API_BASE = process.env.API_BASE_URL || 'http://localhost:8000';

export const cvTools: Tool[] = [
  {
    name: 'cv_recommend',
    description: 'Get intelligent contract vehicle recommendations for an opportunity based on OEM alignment, BPA availability, and deal size',
    inputSchema: {
      type: 'object',
      properties: {
        opportunity_id: {
          type: 'string',
          description: 'Opportunity ID to get CV recommendations for',
        },
        top_n: {
          type: 'number',
          description: 'Number of top recommendations to return',
          default: 3,
        },
      },
      required: ['opportunity_id'],
    },
  },
  {
    name: 'cv_list',
    description: 'List all available contract vehicles with their capabilities',
    inputSchema: {
      type: 'object',
      properties: {},
    },
  },
  {
    name: 'cv_details',
    description: 'Get detailed information about a specific contract vehicle',
    inputSchema: {
      type: 'object',
      properties: {
        vehicle_name: {
          type: 'string',
          description: 'Contract vehicle name (e.g., "SEWP V", "GSA Schedule")',
        },
      },
      required: ['vehicle_name'],
    },
  },
];

export async function handleCvTool(name: string, args: any) {
  try {
    if (name === 'cv_recommend') {
      const response = await fetch(`${API_BASE}/v1/cv/recommend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          opportunity_id: args.opportunity_id,
          top_n: args.top_n || 3,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'CV recommendation failed');
      }

      const result = await response.json();
      return {
        content: [
          {
            type: 'text',
            text: `Contract Vehicle Recommendations for ${result.opportunity_id}:\n\n` +
                  result.recommendations
                    .map((rec: any, idx: number) =>
                      `${idx + 1}. ${rec.contract_vehicle}\n` +
                      `   Score: ${rec.cv_score.toFixed(1)}/100\n` +
                      `   Priority: ${rec.priority}\n` +
                      `   Active BPAs: ${rec.has_bpa ? 'Yes' : 'No'}\n` +
                      `   Reasoning:\n${rec.reasoning.map((r: string) => `     ${r}`).join('\n')}`
                    )
                    .join('\n\n'),
          },
        ],
      };
    } else if (name === 'cv_list') {
      const response = await fetch(`${API_BASE}/v1/cv/vehicles`);

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to fetch vehicles');
      }

      const vehicles = await response.json();
      return {
        content: [
          {
            type: 'text',
            text: `Available Contract Vehicles:\n\n${vehicles.join('\n')}`,
          },
        ],
      };
    } else if (name === 'cv_details') {
      const encodedName = encodeURIComponent(args.vehicle_name);
      const response = await fetch(`${API_BASE}/v1/cv/vehicles/${encodedName}`);

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to fetch vehicle details');
      }

      const details = await response.json();
      return {
        content: [
          {
            type: 'text',
            text: `${details.name} Details:\n\n` +
                  `Priority Score: ${details.priority}\n` +
                  `Active BPAs: ${details.has_active_bpas ? 'Yes' : 'No'}\n` +
                  `Ceiling: ${details.ceiling ? `$${details.ceiling.toLocaleString()}` : 'No ceiling'}\n\n` +
                  `OEMs Supported:\n${details.oems_supported.map((o: string) => `  - ${o}`).join('\n')}\n\n` +
                  `Categories:\n${details.categories.map((c: string) => `  - ${c}`).join('\n')}`,
          },
        ],
      };
    }

    throw new Error(`Unknown CV tool: ${name}`);
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