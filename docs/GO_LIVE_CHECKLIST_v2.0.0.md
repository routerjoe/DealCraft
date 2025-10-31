# DealCraft v2.0.0 — Go‑Live Checklist
_Date: Friday, October 31 2025 _

## Context
- Release target: **v2.0.0 (promote from v2.0.0-rc2)**
- Scope: Obsidian paths (Projects → Opportunities), Account Plan **PDF export**, CRM **dry‑run safety gate**.
- Federal context retained (SEWP, CHESS, Cisco, Nutanix), customer examples generic.

---

## 1) Pre‑Flight (Local)
- [ ] Ensure repo is clean on **main**: `git status` → clean
- [ ] Confirm version: `curl -s http://localhost:8000/v1/info | jq '.version'` → `"2.0.0-rc2"` (pre-promotion)
- [ ] Run tests: `pytest -q` → all green
- [ ] Verify headers: `curl -i http://localhost:8000/healthz | sed -n '1,20p'` → `x-request-id`, `x-latency-ms` present

## 2) Obsidian Paths
- [ ] Env: `echo $VAULT_ROOT` points at the **DealCraft** vault root
- [ ] Structure exists (create if needed):
  - [ ] `<VAULT_ROOT>/40 Projects/`
  - [ ] `<VAULT_ROOT>/40 Projects/Opportunities/`
- [ ] Smoke export (dry-run OK): `curl -s 'http://localhost:8000/v1/obsidian/sync/summary' | jq`

## 3) Account Plan PDF (Phase 12)
- [ ] Generate (dry-run JSON/MD first):  
  `curl -s -X POST http://localhost:8000/v1/account-plans/generate -H 'Content-Type: application/json' -d '{"customer":"Customer Alpha","format":"json"}' | jq`
- [ ] Generate **PDF**:  
  `curl -s -X POST http://localhost:8000/v1/account-plans/generate -H 'Content-Type: application/json' -d '{"customer":"Customer Alpha","format":"pdf"}' | jq`
- [ ] Confirm file saved (path from API response): `ls -lh <returned_path>`
- [ ] Visual QA: headers, tables, multi-page flow

## 4) CRM Write‑Safety
- [ ] Default safety: `curl -s -X POST http://localhost:8000/v1/crm/export -H 'Content-Type: application/json' -d '{"system":"salesforce"}' | jq` → should indicate **dry_run=true**.
- [ ] Destructive guard: only mutate with explicit `dry_run=false` and a targeted payload. Example (do **NOT** run in prod until approved):  
  `curl -s -X POST http://localhost:8000/v1/crm/export -H 'Content-Type: application/json' -d '{"system":"salesforce","dry_run":false,"records":[{"id":"TEST","amount":100}]}' | jq`

## 5) Slack + Govly (optional day‑2)
- [ ] Slack app bot token & signing secret present in `.env` (no secrets committed)
- [ ] Slash commands respond: `/rr recent`, `/rr forecast top 5`
- [ ] Govly webhook secret set; test with signed payload (if allowed)

## 6) Promotion: rc → GA
- [ ] Tag & release:  
  - [ ] `git tag -a v2.0.0 -m "DealCraft 2.0.0 — GA"`  
  - [ ] `git push origin v2.0.0`
- [ ] GitHub Release notes: summarize features; link to `docs/releases/v2.0.0-rc2.md` and Wiki
- [ ] (If using **dealcraft** public repo) ensure README and Wiki show **2.0.0**

## 7) Post‑Deploy Validation
- [ ] `curl -s http://<prod-host>/v1/info | jq '{name:.name, version:.version}'` → `"DealCraft API", "2.0.0"`
- [ ] Forecast top endpoint returns data and reasoning
- [ ] Obsidian export produces files under `40 Projects/Opportunities`
- [ ] Rate‑limit middleware behaves (429 on deliberate hammering for /v1/ai/*)
- [ ] Logs redact secrets (no `sk-`, `xoxb-`, emails)

## 8) Rollback Plan
- [ ] If needed, roll back to `v1.10.0` (git tag)  
  Commands: `git checkout v1.10.0 && uvicorn mcp.api.main:app` (or redeploy by tag)

## 9) Comms & Docs
- [ ] Update `CHANGELOG.md` → add **2.0.0 (GA)** section
- [ ] Update Wiki “Home” to point to 2.0.0 guides
- [ ] Capture before/after screenshots for internal enablement deck

---

## Appendix — FYI Commands
```bash
# Headers on any endpoint
curl -i http://localhost:8000/v1/forecast/top | sed -n '1,20p'

# List endpoints count
curl -s http://localhost:8000/v1/info | jq '{version, total_endpoints:(.endpoints|length)}'
```
