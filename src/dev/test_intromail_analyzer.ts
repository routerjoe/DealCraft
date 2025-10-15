import { handleIntromailTool } from '../tools/intromail/index.js';
import { resolve } from 'path';
import { existsSync } from 'fs';

async function main() {
  const csvPath = resolve(process.cwd(), 'samples', 'IntroMail', 'sample_input.csv');
  if (!existsSync(csvPath)) {
    console.error('[test_intromail_analyzer] Sample CSV not found at', csvPath);
    process.exit(1);
  }

  console.log('[test_intromail_analyzer] Running analyzer on', csvPath);
  const result = await handleIntromailTool('intromail_analyzer', {
    csv_path: csvPath
  });

  // MCP-style return object with content array
  if (result && Array.isArray((result as any).content)) {
    const text = (result as any).content[0]?.text ?? JSON.stringify(result);
    console.log(text);
  } else {
    console.log(JSON.stringify(result, null, 2));
  }
}

main().catch((err) => {
  console.error('[test_intromail_analyzer] Error:', err?.message || err);
  process.exit(1);
});