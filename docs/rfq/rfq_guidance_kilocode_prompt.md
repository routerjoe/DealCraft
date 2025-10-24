# Kilo Code Build Prompt — RFQ Email “Guidance” Revamp (Red River Sales MCP)
**Date:** Friday, October 24 2025 EDT  
**Owner:** Joe Nolan (Red River)  
**Context:** Module lives under Red River Sales MCP → *1. RFQ Email* → *AI Guidance for Analyst*.

---

## 0) Setup & Constraints
- **Environment:** Python 3.11+, Textual or Prompt Toolkit–based TUI. No letter-only prompts; real buttons, menus, and hotkeys.
- **Repo Layout (target):**
  - `modules/guidance/guidance_ui.py` (TUI views)
  - `modules/guidance/oem_store.py` (CRUD + persistence)
  - `modules/guidance/contracts_store.py`
  - `modules/guidance/ai_runner.py` (model selector + timing/metrics)
  - `data/oem_authorizations.json`
  - `data/contracts_supported.json`
  - `logs/ai_guidance_results.jsonl`
  - `tests/test_guidance.py`
- **Persistence:** JSON files above. Create if missing.

---

## 1) Goal
Replace the broken “Guidance” screen with a **functional, clean, and reliable** interface that lets an analyst:
1. **Add/Edit OEMs** and toggle **Authorization** with numeric **Threshold**.
2. **Add/Edit Contract Vehicles** and toggle **Supported**, with free-text **Notes**.
3. **Choose an AI model** (ChatGPT-5, Claude 3.5 Sonnet, Gemini 1.5 Pro, Local/Kilo) and **run guidance** against the current RFQ email body to compare **speed** and **insight depth**.
4. Persist everything and log every AI run with latency and basic metrics.

---

## 2) UI Specification
### 2.1 Layout
- **Header Bar:** “RFQ Guidance · Active AI: <model> · Last Refresh: <timestamp>”
- **Top Buttons:** `[Add OEM] [Add Contract] [Toggle OEM] [Toggle Contract] [Run Guidance] [Refresh] [Back]`
- **Left Panel: OEM Authorization Table**
  - Columns: **OEM | Authorized | Threshold | Updated**
  - Sortable by OEM; Up/Down selects; Enter opens edit dialog.
- **Right Panel: Supported Contract Vehicles**
  - Columns: **Contract | Supported | Notes | Updated**
  - Enter opens edit dialog.
- **Bottom Status Bar:** Errors, saves, and “Run Guidance” results summary.

### 2.2 Interactions & Hotkeys
- Global: `Tab` cycles focus; `Esc` closes dialogs; `Ctrl+S` saves; `r` refresh; `q` back.
- OEM Panel:
  - `a` → Add OEM (modal: *OEM Name*, *Authorized* default **No**, *Threshold* default **5**).
  - `t` → Toggle Authorized on selected row.
  - `e` → Edit threshold (integer 1–10).
- Contract Panel:
  - `c` → Add Contract (modal: *Contract Name*, *Supported* default **Yes**, *Notes*).
  - `s` → Toggle Supported on selected row.
  - `n` → Edit Notes.
- AI Runner:
  - `m` → Model menu; `g` or `[Run Guidance]` → execute on active RFQ.
  - After run, show **latency (ms)**, **tokens (if available)**, **insight depth (1–10)**, and **key bullets**.

### 2.3 Visuals
- Use standard Textual widgets (Buttons, DataTable, Footer).  
- Color coding: Green = Authorized/Supported; Red = Not Authorized/Not Supported; Blue highlight for selection.

---

## 3) Data Models
### 3.1 `oem_authorizations.json`
```json
{
  "items": [
    {
      "oem": "Cisco",
      "authorized": true,
      "threshold": 5,
      "updated": "2025-10-24T13:00:00Z"
    }
  ]
}
```
### 3.2 `contracts_supported.json`
```json
{
  "items": [
    {
      "contract": "SEWP V",
      "supported": true,
      "notes": "Primary NASA GWAC for federal. Use Carahsoft/Immix as needed.",
      "updated": "2025-10-24T13:00:00Z"
    }
  ]
}
```
### 3.3 `logs/ai_guidance_results.jsonl`
- One JSON per line with fields:
```json
{
  "ts": "2025-10-24T13:05:06Z",
  "rfq_id": "548416",
  "model": "chatgpt-5",
  "latency_ms": 812,
  "token_in": 2048,
  "token_out": 512,
  "insight_depth": 8,
  "oem_hits": ["Cisco","NetApp"],
  "contract_hits": ["SEWP V","CHESS"],
  "summary": "RFQ aligns to NetOps; requires OEM auth for Cisco; vehicles: CHESS, SEWP.",
  "raw_excerpt": "…first 600 chars of model answer…"
}
```

---

## 4) AI Model Selector & Runner
### 4.1 Selector
- Provide dropdown with the following **display names → provider keys**:
  1. **ChatGPT‑5** → `"openai:gpt-5"`
  2. **Claude 3.5 Sonnet** → `"anthropic:claude-3-5-sonnet"`
  3. **Gemini 1.5 Pro** → `"google:gemini-1.5-pro"`
  4. **Kilo Local** → `"local:kilo-default"`
- Persist last-used model in `~/.mcp/guidance_prefs.json`.

### 4.2 Runner Behavior
- Input: **Active RFQ email text** (provided by parent screen via function argument) + **current OEM/Contract tables**.
- Build a **system prompt** (below) and call the selected model using existing MCP client utilities.
- Time the call; compute `insight_depth` by scoring presence of: OEM matches, contract mapping, compliance/security comments, and actionability.

### 4.3 System Prompt (to send to model)
> You are Red River’s RFQ Analyst. Analyze the pasted RFQ email.  
> 1) Identify relevant **OEMs** and whether we are **authorized**; flag gaps.  
> 2) Map to **Contract Vehicles** (SEWP, CHESS, 2GIT, ITES-3H/4H, etc.) with rationale.  
> 3) Call out **AFCENT/AETC/Federal** context, NetOps/Zero Trust/Cisco/Nutanix details.  
> 4) Provide **3–5 actionable steps** (registration needed, teaming, questions to CO).  
> 5) Output JSON with keys: `oem_hits[]`, `contract_hits[]`, `risks[]`, `actions[]`, `summary`.

---

## 5) Acceptance Criteria
- [ - ] All buttons and hotkeys work; no letter-only fake prompts.
- [ - ] Create/update/delete items persist immediately; files created if missing.
- [ - ] Model selector persists choice and shows in header.
- [ - ] “Run Guidance” logs a JSONL line, shows latency, and displays top bullets.
- [ - ] Tables never corrupt; graceful error handling with status bar messages.
- [ - ] Unit test `tests/test_guidance.py` covers CRUD and prompt assembly.

---

## 6) Implementation Notes
- Prefer **Textual**: `DataTable`, `Footer`, `ModalScreen` dialogs.
- Wrap file IO with locking to avoid concurrent writes.
- Add `--debug` flag to print model payloads (redact secrets).
- Reuse existing MCP RFQ email loader to pass `rfq_id`, `subject`, and `body`.

---

## 7) Deliverables
1. Working TUI module with the layout and hotkeys above.
2. JSON schemas initialized with sample values if files are missing.
3. Test file and a short README snippet in `modules/guidance/README.md`.

---

## 8) Nice-to-Haves (if quick)
- Import/export CSV for OEMs and Contracts.
- Inline filter text box for each table.
- Column sort persisting between sessions.

---

## 9) Hand-off
When done, open a PR titled: **“MCP: RFQ Guidance Revamp (TUI + AI Selector)”** with a short demo gif.
