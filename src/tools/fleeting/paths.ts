import { join } from 'path';
import { getObsidianPath } from '../../utils/env.js';

export interface FleetingPaths {
  DAILY: string;
  MEET: string;
  PEOPLE: string;
  HUB: string;
  TODO: string;
  STATE: string;
  REVIEW: string;
}

/**
 * Resolve all paths used by the Fleeting Notes processor.
 * Defaults follow the v7 prompt guide and fall back to the Obsidian vault path.
 * targetDir, if provided, overrides DAILY_NOTES_DIR for ad-hoc runs.
 */
export function getFleetingPaths(targetDir?: string): FleetingPaths {
  const vault = getObsidianPath();

  const DAILY =
    targetDir ||
    process.env.DAILY_NOTES_DIR ||
    join(vault, '00 Inbox', 'Daily Notes');

  const MEET =
    process.env.MEETING_NOTES_DIR ||
    join(vault, '10 Literature', 'Meeting Notes');

  const PEOPLE =
    process.env.PEOPLE_DIR ||
    join(vault, '30 Hubs', 'People');

  const HUB =
    process.env.HUB_DIR ||
    join(vault, '30 Hubs');

  const TODO =
    process.env.TODO_LIST_PATH ||
    join(DAILY, 'To Do List.md');

  const STATE =
    process.env.STATE_PATH ||
    join(process.cwd(), '.fleeting_state.json');

  const REVIEW =
    process.env.REVIEW_QUEUE_PATH ||
    join(vault, '30 Hubs', '_Review Queue.md');

  return { DAILY, MEET, PEOPLE, HUB, TODO, STATE, REVIEW };
}