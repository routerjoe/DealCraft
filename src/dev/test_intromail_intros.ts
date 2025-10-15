import { handleIntromailTool } from '../tools/intromail/index.js';
import { resolve } from 'path';
import { existsSync } from 'fs';

async function main() {
  const csvPath = resolve(process.cwd(), 'samples', 'IntroMail', 'sample_input.csv');
  const bodyTemplatePath = resolve(process.cwd(), 'templates', 'intro_email.txt');

  if (!existsSync(csvPath)) {
    console.error('[test_intromail_intros] Sample CSV not found at', csvPath);
    process.exit(1);
  }
  if (!existsSync(bodyTemplatePath)) {
    console.error('[test_intromail_intros] Body template not found at', bodyTemplatePath);
    process.exit(1);
  }

  console.log('[test_intromail_intros] Dry-run generating Outlook drafts from', csvPath);
  const result = await handleIntromailTool('intromail_intros', {
    csv_path: csvPath,
    subject_template: process.env.INTROMAIL_SUBJECT_DEFAULT || 'Intro — Red River + {{company}}',
    body_template_path: bodyTemplatePath,
    attachment_path: process.env.INTROMAIL_ATTACHMENT_DEFAULT || '',
    dry_run: true
  });

  if (result && Array.isArray((result as any).content)) {
    const text = (result as any).content[0]?.text ?? JSON.stringify(result);
    console.log(text);
  } else {
    console.log(JSON.stringify(result, null, 2));
  }
}

main().catch((err) => {
  console.error('[test_intromail_intros] Error:', err?.message || err);
  process.exit(1);
});