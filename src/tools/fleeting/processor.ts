export type FleetingScope = 'today' | 'this-week' | 'this-month' | 'since-last-run' | 'range';

export interface FleetingOptions {
  scope: FleetingScope;
  range?: string;
  dryRun?: boolean;
  force?: boolean;
  targetDir?: string;
}

export interface Result {
  meetings_created: number;
  meetings_updated: number;
  contacts_created: number;
  contacts_updated: number;
  contacts_triaged: number;
  company_hubs_created: number;
  tasks_added: number;
  tasks_moved_to_completed: number;
  skipped_notes: number;
  processed_notes: number;
}

export interface FleetingSummary extends Result {
  scope: string;
  dryRun: boolean;
}

export async function runFleetingProcessor(options: FleetingOptions): Promise<FleetingSummary> {
  const { scope, range, dryRun = false } = options || ({} as FleetingOptions);
  const label = scope === 'range' && range ? `range ${range}` : scope;
  return {
    scope: label,
    dryRun,
    meetings_created: 0,
    meetings_updated: 0,
    contacts_created: 0,
    contacts_updated: 0,
    contacts_triaged: 0,
    company_hubs_created: 0,
    tasks_added: 0,
    tasks_moved_to_completed: 0,
    skipped_notes: 0,
    processed_notes: 0,
  };
}