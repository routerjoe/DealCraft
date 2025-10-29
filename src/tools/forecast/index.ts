import { Tool } from '@modelcontextprotocol/sdk/types.js';

const API_BASE = process.env.API_BASE_URL || 'http://localhost:8000';

export const forecastTools: Tool[] = [
  {
    name: 'forecast_run',
    description: 'Generate intelligent forecasts for opportunities with multi-factor scoring',
    inputSchema: {
      type: 'object',
      properties: {
        opportunity_ids: {
          type: 'array',
          items: { type: 'string' },
          description: 'Specific opportunity IDs to forecast (optional - forecasts all if not provided)',
        },
        model: {
          type: 'string',
          description: 'AI model to use',
          default: 'gpt-5-thinking',
        },
      },
    },
  },
  {
    name: 'forecast_all',
    description: 'Get all forecasts with intelligent scoring data',
    inputSchema: {
      type: 'object',
      properties: {},
    },
  },
  {
    name: 'forecast_top',
    description: 'Get top-ranked opportunities by win probability or other criteria',
    inputSchema: {
      type: 'object',
      properties: {
        limit: {
          type: 'number',
          description: 'Number of top deals to return',
          default: 20,
        },
        sort_by: {
          type: 'string',
          enum: ['win_prob', 'score_raw', 'projected_amount', 'FY25', 'FY26', 'FY27'],
          description: 'Sorting criteria',
          default: 'win_prob',
        },
      },
    },
  },
  {
    name: 'forecast_export_csv',
    description: 'Export forecasts to CSV file',
    inputSchema: {
      type: 'object',
      properties: {
        fiscal_year: {
          type: 'number',
          description: 'Specific fiscal year (25, 26, or 27) - exports all FYs if not provided',
        },
      },
    },
  },
  {
    name: 'forecast_export_obsidian',
    description: 'Export forecasts to Obsidian Forecast Dashboard with summary tables and top deals',
    inputSchema: {
      type: 'object',
      properties: {},
    },
  },
];

export async function handleForecastTool(name: string, args: any) {
  try {
    if (name === 'forecast_run') {
      const response = await fetch(`${API_BASE}/v1/forecast/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(args),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Forecast generation failed');
      }

      const result = await response.json();
      return {
        content: [
          {
            type: 'text',
            text: `Forecasts Generated: ${result.forecasts_generated}\n` +
                  `Latency: ${result.latency_ms}ms\n\n` +
                  `Sample forecast:\n${JSON.stringify(result.forecasts[0], null, 2)}`,
          },
        ],
      };
    } else if (name === 'forecast_all') {
      const response = await fetch(`${API_BASE}/v1/forecast/all`);

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to fetch forecasts');
      }

      const result = await response.json();
      return {
        content: [
          {
            type: 'text',
            text: `All Forecasts:\nTotal: ${result.total}\n\n` +
                  JSON.stringify(result.forecasts, null, 2),
          },
        ],
      };
    } else if (name === 'forecast_top') {
      const limit = args.limit || 20;
      const sort_by = args.sort_by || 'win_prob';
      const response = await fetch(
        `${API_BASE}/v1/forecast/top?limit=${limit}&sort_by=${sort_by}`
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to fetch top forecasts');
      }

      const result = await response.json();
      return {
        content: [
          {
            type: 'text',
            text: `Top ${result.top_deals.length} Deals (sorted by ${result.sort_criteria}):\n\n` +
                  result.top_deals
                    .map((deal: any, idx: number) =>
                      `${idx + 1}. ${deal.opportunity_name}\n` +
                      `   Win Prob: ${deal.win_prob}%\n` +
                      `   FY25: $${deal.projected_amount_FY25.toLocaleString()}\n` +
                      `   Scores: OEM:${deal.oem_alignment_score} Partner:${deal.partner_fit_score} CV:${deal.contract_vehicle_score}`
                    )
                    .join('\n\n'),
          },
        ],
      };
    } else if (name === 'forecast_export_csv') {
      const fy_param = args.fiscal_year ? `?fiscal_year=${args.fiscal_year}` : '';
      const response = await fetch(`${API_BASE}/v1/forecast/export/csv${fy_param}`);

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'CSV export failed');
      }

      const csvContent = await response.text();
      const lines = csvContent.split('\n');
      return {
        content: [
          {
            type: 'text',
            text: `CSV Export Complete:\n${lines.length} rows\n\nFirst 5 rows:\n${lines.slice(0, 5).join('\n')}`,
          },
        ],
      };
    } else if (name === 'forecast_export_obsidian') {
      const response = await fetch(`${API_BASE}/v1/forecast/export/obsidian`, {
        method: 'POST',
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Obsidian export failed');
      }

      const result = await response.json();
      return {
        content: [
          {
            type: 'text',
            text: `Obsidian Dashboard Updated:\n` +
                  `Path: ${result.path}\n` +
                  `Opportunities: ${result.opportunities_exported}\n` +
                  `FY25: $${result.total_FY25.toLocaleString()}\n` +
                  `FY26: $${result.total_FY26.toLocaleString()}\n` +
                  `FY27: $${result.total_FY27.toLocaleString()}`,
          },
        ],
      };
    }

    throw new Error(`Unknown forecast tool: ${name}`);
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