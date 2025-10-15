import fs from 'node:fs';
import path from 'node:path';
import { handleIntromailTool } from '../tools/intromail/index.js';

const home = process.env.HOME || process.env.USERPROFILE || '.';
const inbox = process.env.INTROMAIL_INBOX_DIR || path.join(home, 'RedRiver', 'campaigns', 'inbox');

if (!fs.existsSync(inbox)) fs.mkdirSync(inbox, { recursive: true });

console.log('[IntroMail] Watching inbox:', inbox);

const debounceTimers = new Map<string, NodeJS.Timeout>();

fs.watch(inbox, { persistent: true }, (eventType, filename) => {
  if (!filename || !filename.toLowerCase().endsWith('.csv')) return;
  const full = path.join(inbox, filename);

  if (debounceTimers.has(full)) {
    clearTimeout(debounceTimers.get(full)!);
  }
  const timer = setTimeout(async () => {
    debounceTimers.delete(full);
    if (!fs.existsSync(full)) return;
    try {
      console.log('[IntroMail] Detected CSV:', full, '→ running analyzer...');
      const res = await handleIntromailTool('intromail_analyzer', { csv_path: full });
      const text = (res as any)?.content?.[0]?.text ?? JSON.stringify(res);
      console.log('[IntroMail] Analyzer result:', text);
    } catch (e: any) {
      console.error('[IntroMail] Analyzer failed:', e?.message || String(e));
    }
  }, 750);
  debounceTimers.set(full, timer);
});