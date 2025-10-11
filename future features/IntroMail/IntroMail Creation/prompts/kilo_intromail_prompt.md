# Kilo Code Prompt — Add IntroMail Tool to MCP

Add a new MCP tool named `intromail:intros` that:
1) Accepts args: `csv_path` (required), `subject_template` (optional), `body_template_path` (optional), `attachment_path` (optional), `dry_run` (optional).
2) Reads `scripts/intromail.applescript`, prepends runtime config (csvPath, subjectTemplate, bodyTemplatePath, attachmentPath), and executes via `osascript`.
3) Creates Outlook **Drafts** only.
4) Uses the inline default email body if `body_template_path` is not provided; include `templates/intro_email.txt` as the canonical file template.
5) Returns JSON `{ ok, message }` on success.
6) Register with `registerTool(introMailTool)`.
