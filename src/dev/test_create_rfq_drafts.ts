import fs from 'fs';
import path from 'path';
import dotenv from 'dotenv';
import { createRfqDrafts } from '../tools/rfq/drafts.js';

function loadEnv() {
  const root = process.cwd();
  dotenv.config({ path: path.resolve(root, '.env') });
}

async function main() {
  try {
    loadEnv();

    const argPath = process.argv[2];
    const jsonPath = argPath
      ? path.resolve(argPath)
      : path.resolve(process.cwd(), 'red-river-rfq-email-drafts/sample_rfq.json');

    if (!fs.existsSync(jsonPath)) {
      console.error(`Sample payload not found at: ${jsonPath}`);
      process.exit(1);
    }

    const raw = fs.readFileSync(jsonPath, 'utf-8');
    const payload = JSON.parse(raw);

    console.log('Calling create_rfq_drafts with payload:', JSON.stringify(payload, null, 2));

    const result = await createRfqDrafts(payload);
    console.log('Tool result:', result);
    console.log('If Legacy Outlook is open, two drafts should now be in Drafts (OEM + Internal).');

  } catch (err: any) {
    console.error('Error:', err?.message || String(err));
    process.exit(1);
  }
}

main();