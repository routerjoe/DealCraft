# Changelog

All notable changes to the Red River Sales MCP API will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v1.3.0] - 2025-10-26

### Added

#### AI Router Enhancement
- **New endpoint:** `POST /v1/ai/ask` - Unified AI query interface
- **Multi-model support:** 6 AI models across 3 providers
  - OpenAI: `gpt-5-thinking`, `gpt-4-turbo`
  - Anthropic: `claude-3.5`, `claude-3-opus`
  - Gemini: `gemini-1.5-pro`, `gemini-1.5-flash`
- **Enhanced endpoint:** `GET /v1/ai/models/detailed` - Returns provider information
- New functions: `get_available_models()`, `process_ai_request()`, improved `select_model()` validation

#### System Logging & Monitoring
- **New endpoint:** `GET /v1/system/recent-actions` - Last 10 API requests with metadata
- **Automatic action logging** via middleware with rotation (max 10 entries)
- Persistent storage in `data/state.json`
- Logged fields: `request_id`, `timestamp`, `method`, `path`, `latency_ms`, `status_code`, `context`

#### Request Tracking
- All responses now include `x-request-id` header (UUID4)
- All responses now include `x-latency-ms` header
- Average latency: <3ms (budget: 250ms)

#### Federal Fiscal Year Routing
- **New function:** `get_federal_fy()` - Routes opportunities to correct FY folder
- **Base directory changed:** `obsidian/40 Projects/Opportunities/<FYxx|Triage>`
- Automatic routing based on close_date:
  - FY25: Oct 2024 - Sep 2025
  - FY26: Oct 2025 - Sep 2026
  - Triage: Invalid/missing dates

#### Dashboard-Friendly YAML Aliases
- Added non-breaking aliases to Obsidian opportunity notes:
  - `est_amount` (numeric alias for amount)
  - `est_close` (date string alias for close_date)
  - `oems` (list format of oem)
  - `partners` (empty list default)
  - `contract_vehicle` (empty string default)
- All original YAML keys preserved for backward compatibility

#### Obsidian Dataview Dashboard
- **New file:** `obsidian/50 Dashboards/Opportunities Dashboard.md`
- 10 comprehensive Dataview query blocks:
  1. Pipeline by Stage (aggregated totals)
  2. Upcoming Closes (90-day rolling window)
  3. By Federal Fiscal Year
  4. Top Opportunities (>$500K)
  5. By OEM/Vendor breakdown
  6. By Customer breakdown
  7. Triage Queue monitoring
  8. By Source tracking
  9. Recent Activity (30 days)
  10. Summary Stats (DataviewJS)
- All queries use fallback syntax: `(amount ?? est_amount)`
- All queries filter: `WHERE type = "opportunity"`

### Changed
- Obsidian opportunity base directory: `obsidian/30 Hub/Opportunities` → `obsidian/40 Projects/Opportunities/<FYxx|Triage>`
- AI models endpoint now returns 6 models (previously 3)

### Tests
- **Total:** 71 tests passing (up from 67)
- **New tests:** 4 added for FY routing and YAML aliases
  - `test_fy_routing_fy25`
  - `test_fy_routing_fy26`
  - `test_yaml_aliases_present`
  - `test_yaml_aliases_oems_list`
- **Success rate:** 100%

### Files Modified
- **New:** `mcp/api/v1/system.py`, `logs/phase3_test.log`
- **Modified:** `mcp/core/ai_router.py`, `mcp/api/v1/ai.py`, `mcp/api/main.py`, `mcp/api/v1/obsidian.py`, test suites

### Non-Breaking Changes
- All changes are backward compatible
- Original YAML keys preserved in Obsidian notes
- Existing endpoints maintain same behavior
- New endpoints additive only

### Performance
- API response times: <3ms average
- Test suite execution: ~3s
- Build time: <6s total

### Links
- [Tag v1.3.0](https://github.com/routerjoe/red-river-sales-automation/releases/tag/v1.3.0)
- [Sprint Summary](obsidian/60%20Projects/MCP%20(Red%20River%20Sales%20Automation)/90_KiloCode_Sprint/summaries/2025-10-26-phase3-integration-summary.md)

---

## [Unreleased]

### Planned (Phase 4)
- Forecast Hub automation (AI predictions across FY24–FY26)
- Radar Parser & Govly webhook automation
- Metrics & feedback loop for latency/accuracy tracking

---

[v1.3.0]: https://github.com/routerjoe/red-river-sales-automation/compare/v1.2.0...v1.3.0
[Unreleased]: https://github.com/routerjoe/red-river-sales-automation/compare/v1.3.0...HEAD