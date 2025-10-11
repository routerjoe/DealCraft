import { join, dirname } from 'path';
import { tmpdir } from 'os';
import { existsSync, mkdirSync } from 'fs';
import { getObsidianPath, getBaseDir } from '../../utils/env.js';

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
  const baseDir = getBaseDir();

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

  // Build candidate list (in priority order):
  // 1) Explicit env override
  // 2) targetDir-based (per-call sandbox)
  // 3) RED_RIVER_BASE_DIR/data default
  const candidates: string[] = [];
  if (process.env.STATE_PATH) candidates.push(process.env.STATE_PATH);
  if (targetDir) candidates.push(join(targetDir, '.fleeting_state.json'));
  candidates.push(join(baseDir, 'data', '.fleeting_state.json'));

  // Ensure parent dir is creatable; reject root-level or unwritable parents
  function ensureParent(p: string): boolean {
    try {
      const dir = dirname(p);
      if (dir === '/') return false; // never to root
      if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
      return true;
    } catch {
      return false;
    }
  }

  let STATE = '';
  for (const cand of candidates) {
    if (ensureParent(cand)) { STATE = cand; break; }
  }
  // Fallback: tmp dir that should always be writable
  if (!STATE) {
    const fallback = join(tmpdir(), 'redriver', '.fleeting_state.json');
    try { ensureParent(fallback); } catch {}
    STATE = fallback;
  }

  const REVIEW =
    process.env.REVIEW_QUEUE_PATH ||
    join(vault, '30 Hubs', '_Review Queue.md');

  return { DAILY, MEET, PEOPLE, HUB, TODO, STATE, REVIEW };
}