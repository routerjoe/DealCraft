# Kilo Code Prompts — 2025-10-27 Project Setup & Scaffolding
**Date:** Tuesday, October 27 2025 EDT  
**Repo:** routerjoe/red-river-sales-automation  
**Context:** Red River Sales MCP (no Salesforce; consume Radar via emails only).  
**Tooling:** Kilo Code + Claude, Python 3.11+.

> Paste each prompt (one at a time) into **Kilo Code**. Each is self-contained and deliverable-focused.

---

## PROMPT 1 — Scaffold Core Project (API + Core + Tasks)
**Task:** Create project skeleton with FastAPI, JSON logging, request IDs, and Kilo aliases.

**Do:**
- Create folders: `/mcp/api`, `/mcp/core`, `/scripts`, `/tests`.
- Implement `FastAPI` app with middleware that adds `request_id` and measures `latency_ms`; set `X-Request-ID` response header.
- Add `.env.sample`, `logging.json`, `requirements.txt`, `kilo.yml`, and scripts (`dev.sh`, `test.sh`, `lint.sh`, `build.sh`).
- Add `/healthz` and `/v1/info` endpoints and unit tests.

**Constraints:**
- No secrets in code; use `.env`.
- JSON logs include: `request_id`, `latency_ms`, `method`, `path`, `status`.
- POSIX shell scripts; `chmod +x` them.
- Code lint-clean with `ruff`.

**Deliver:**
- New files per *File Plan* below
- Updated `README.md` (Quick start + Logging example)
- **Commit message (exact):**  
  `feat(scaffold): create /mcp/api and /mcp/core, add .env + JSON logging with request_id, and Kilo Code task aliases (dev/test/lint/build)`

**File Plan:**
```
mcp/
 ├─ api/
 │   └─ main.py                # FastAPI app + middleware + /healthz + /v1/info
 └─ core/
     ├─ config.py              # loads .env
     └─ logging.py             # configure + log_request()

scripts/
 ├─ dev.sh                     # uvicorn --reload
 ├─ test.sh                    # pytest -q
 ├─ lint.sh                    # ruff check .
 └─ build.sh                   # lint + tests

tests/test_health.py
.env.sample
logging.json
requirements.txt
kilo.yml
README.md
```

**Kilo tasks (`kilo.yml`):**
```yaml
tasks:
  run:dev: bash scripts/dev.sh
  run:test: bash scripts/test.sh
  run:lint: bash scripts/lint.sh
  run:build: bash scripts/build.sh
```

**Acceptance Criteria:**
- [ ] `kc run:test` passes
- [ ] `kc run:lint` passes
- [ ] `/healthz` & `/v1/info` return 200 via `kc run:dev`
- [ ] Logs show one JSON line per request with `request_id` & `latency_ms`

**Post-Run Commands:**
```bash
cp .env.sample .env
pip install -r requirements.txt
kc run:dev
kc run:test
kc run:lint
kc run:build
```

---

## PROMPT 2 — API for OEMs & Contracts (CRUD + File Store)
**Task:** Implement CRUD endpoints for OEMs and Contract Vehicles, backed by `data/state.json` with atomic read/write helpers.

**Do:**
- Create `mcp/core/store.py` with `read_json(path)`, `write_json(path, data)` (atomic write).
- Create `data/state.json` if missing with default structure:
  ```json
  {
    "oems": [],
    "contracts": [],
    "selected_ai": "gpt-5-thinking"
  }
  ```
- Add `mcp/api/v1/oems.py` routes:
  - `GET /v1/oems`
  - `POST /v1/oems` → body: `{"name": str, "authorized": bool, "threshold": int}`
  - `PATCH /v1/oems/{name}` → partial updates
  - `DELETE /v1/oems/{name}`
- Add `mcp/api/v1/contracts.py` routes:
  - `GET /v1/contracts`
  - `POST /v1/contracts` → `{"name": str, "supported": bool, "notes": str}`
  - `PATCH /v1/contracts/{name}`
  - `DELETE /v1/contracts/{name}`
- Wire routers in `mcp/api/main.py` under prefix `/v1`.

**Constraints:**
- Validate bodies with Pydantic models.
- Return 409 on duplicate names; 404 on missing records.
- Log `request_id` for every call.

**Deliver:**
- New modules: `mcp/core/store.py`, `mcp/api/v1/oems.py`, `mcp/api/v1/contracts.py`
- Unit tests: `tests/test_oems.py`, `tests/test_contracts.py`
- Small README section documenting endpoints.

**Acceptance Criteria:**
- [ ] CRUD happy paths covered in tests
- [ ] `kc run:test` green
- [ ] Idempotent POST rejection (409 duplicates) verified

---

## PROMPT 3 — AI Stubs (Models List + Guidance Skeleton)
**Task:** Add AI endpoints the TUI will call; keep logic stubbed initially.

**Do:**
- Create `mcp/api/v1/ai.py` with:
  - `GET /v1/ai/models` → `["gpt-5-thinking","claude-3.5","gemini-1.5-pro"]`
  - `POST /v1/ai/guidance` → accepts:
    ```json
    {
      "oems": [{"name": "...","authorized": true}],
      "contracts": [{"name": "...","supported": true}],
      "rfq_text": "...",
      "model": "gpt-5-thinking"
    }
    ```
    Return shape:
    ```json
    {
      "summary": "...",
      "actions": ["...","..."],
      "risks": ["..."]
    }
    ```
- Add `mcp/core/ai_router.py` with `select_model(name)` and `generate_guidance(payload)` returning a static stub; load model name from request body or default.

**Constraints:**
- No API keys or provider SDK calls yet.
- Log `request_id` and measure `latency_ms` via existing middleware.

**Deliver:**
- `mcp/api/v1/ai.py`, `mcp/core/ai_router.py`
- Tests: `tests/test_ai_endpoints.py` (`GET /v1/ai/models`, minimal `POST /v1/ai/guidance`)

**Acceptance Criteria:**
- [ ] Models list returns expected values
- [ ] Guidance endpoint returns JSON with `summary`, `actions`, `risks`
- [ ] Tests pass: `kc run:test`

---

## PROMPT 4 — TUI Revamp Scaffold (Textual)
**Task:** Build a **Textual** TUI with three panels and key bindings; wire to API.

**Do:**
- Create `tui/app.py`, `tui/panels/oems.py`, `tui/panels/contracts.py`, `tui/panels/ai.py`, `tui/theme.py`.
- Panels:
  1) **OEM Authorization** — table `[OEM, Authorized, Threshold]`  
     Keys: `A` Add, `T` Toggle, `↑/↓` Threshold +/- , `D` Delete, `R` Refresh
  2) **Contract Vehicles** — table `[Contract, Supported, Notes]`  
     Keys: `C` Add, `S` Toggle, `E` Edit Notes, `X` Delete, `R` Refresh
  3) **AI Guidance** — text pane with `G` Generate, `I` Switch Model
- Async HTTP client (`httpx`) for `/v1` endpoints.
- Add Kilo alias: `run:tui: python -m tui.app`
- Create `README_TUI.md` (keymap + quickstart).

**Constraints:**
- Non-blocking UI; handle failures with toast/banner; include last `request_id` in footer.
- Keep styles minimal and accessible (Red River light theme).

**Deliver:**
- New `tui/` package + alias in `kilo.yml`
- Screenshots TODO placeholders in `README_TUI.md`

**Acceptance Criteria:**
- [ ] OEM and Contract CRUD work from TUI
- [ ] AI panel shows stubbed guidance response
- [ ] Model switch cycles `/v1/ai/models`

---

## PROMPT 5 — Quality Guardrails & Docs
**Task:** Finalize DX: lint, tests, runbook updates, and logging example.

**Do:**
- Ensure `ruff` clean.
- Ensure all tests pass locally.
- Add **RUNBOOK.md**: setup, commands, env vars, endpoints, TUI usage, troubleshooting.
- Add logging example JSON to README.
- Add `.env.sample` notes (no secrets).

**Deliver / Commit message:**
```
docs(runbook): add RUNBOOK and TUI usage; update logging example and .env notes
```

**Acceptance Criteria:**
- [ ] `kc run:test` and `kc run:lint` pass
- [ ] README + RUNBOOK accurately reflect current behavior

---

## Global Constraints
- No secrets in code or tests.
- JSON logs on every API call with `request_id` & `latency_ms`.
- Idempotent scripts; safe to re-run.

## Quick Verify (after each prompt)
```bash
cp .env.sample .env
pip install -r requirements.txt
kc run:test
kc run:lint
kc run:dev        # /healthz
kc run:tui        # after Prompt 4
```
