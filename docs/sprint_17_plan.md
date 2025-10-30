# Sprint 17 — Partner Tier Ingestion & Sync
Date: Thursday, October 30 2025 EDT
Status: Seed (docs + stubs + tests)

## Objective
Ingest partner tier data (Cisco, Nutanix, NetApp, Red Hat, etc.) from structured sources and sync into:
- OEM Hubs (YAML keys: tier_global, tier_redriver)
- partners.db (SQLite) via existing Partners Base
- Obsidian dashboards (`50 Dashboards/Partner_Tiers_Index.md`)
- API exposure for tier lookups and Obsidian export

## Scope
1) Parsers: CSV/JSONL/Markdown partner tier sheets
2) Validation: Ensure schema compliance (Unified YAML Schema)
3) Sync: Update OEM hubs + partners.db (idempotent)
4) API: 
   - GET /v1/partners/tiers
   - POST /v1/partners/sync (dry_run default true)
   - GET /v1/partners/export/obsidian
5) Obsidian: Rebuild Partner_Tiers_Index.md via bases or Dataview fallback
6) Security: No secrets stored; only read from configured vault path

## Acceptance Criteria
- Endpoints exist & respond (200) with contract models
- Dry-run shows diffs of proposed updates
- After real run, OEM Hubs updated and `80 Reference/bases/partners.db` rebuilt
- Dashboard reflects updated tiers

## Out of Scope
- Partner portal scraping
- Auth flows for OEM portals

## Checklist
- [ ] Implement parser + sync stubs
- [ ] Contract tests green (xfail removed when implemented)
- [ ] API endpoints wired, headers present (x-request-id, x-latency-ms)
- [ ] Obsidian dashboard updated programmatically
- [ ] Docs updated (how-to + troubleshooting)
