import { runFleetingProcessor } from '../tools/fleeting/processor.js';
import { resolve } from 'path';

async function main() {
  const cwd = process.cwd();
  const samplesDir = resolve(cwd, 'samples/fleeting');
  const outBase = resolve(cwd, 'samples/fleeting/out');

  // Direct all outputs to samples/fleeting/out to avoid touching your real vault
  process.env.MEETING_NOTES_DIR = resolve(outBase, 'Meeting Notes');
  process.env.PEOPLE_DIR = resolve(outBase, 'People');
  process.env.HUB_DIR = resolve(outBase, '30 Hubs');
  process.env.TODO_LIST_PATH = resolve(outBase, 'To Do List.md');
  process.env.STATE_PATH = resolve(outBase, '.fleeting_state.json');
  process.env.REVIEW_QUEUE_PATH = resolve(outBase, '30 Hubs', '_Review Queue.md');

  const summary = await runFleetingProcessor({
    scope: 'range',
    range: '2025-10-01..2025-10-31',
    dryRun: false, // writes into samples/fleeting/out
    force: false,
    targetDir: samplesDir,
  });

  // Dev harness output
  console.log(JSON.stringify(summary, null, 2));
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});