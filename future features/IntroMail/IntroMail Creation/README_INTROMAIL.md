# IntroMail (MCP) — Outreach Draft Generator

**Date:** Saturday, October 11, 2025 (America/New_York)

Purpose
Create personalized Outlook Draft emails from a CSV with placeholders and optional attachments. Includes a universal Red River introduction template and inline fallback.

Contents
- src/tools/intromail.ts — MCP tool wrapper
- scripts/intromail.applescript — Draft creation logic (uses inline template fallback)
- templates/intro_email.txt — Universal Red River intro email (same text as inline fallback)
- prompts/kilo_intromail_prompt.md — Copy/paste prompt for Kilo Code
- .env.example — Defaults (subject, attachment)
- assets/linecards/placeholder.txt — Put your Line Card PDF here
- samples/sample_contacts.csv — CSV starter
