# Changelog

All notable changes to the Red River Sales MCP API will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

**See also:** Detailed release notes are available in [`docs/releases/`](docs/releases/)

## [v1.4.0] - 2025-10-28

Phase 4: Forecast & Govly Automation Batch - See full release notes: [docs/releases/v1.4.0.md](docs/releases/v1.4.0.md)

### Added

#### Forecast Hub Engine
- `POST /v1/forecast/run` - Generate multi-year forecasts for FY25, FY26, FY27
- `GET /v1/forecast/summary` - Aggregate forecast analytics with confidence tiers
- Forecast fields: `projected_amount_FY25`, `projected_amount_FY26`, `projected_amount_FY27`, `confidence_score (0-100)`
- Persistent storage in `data/forecast.json` with atomic writes
- Derived fields automatically added to opportunity notes in `state.json`

#### Webhook Ingestion
- `POST /v1/govly/webhook` - Ingest federal opportunity events from Govly
- `POST /v1/radar/webhook` - Ingest contract modifications from Radar
- Append-only persistence to `state.json → opportunities[]`
- Auto-generates minimal `opportunity.md` files with `triage: true` flag
- Request ID and latency tracking for all webhook calls

#### Metrics & Latency Monitor
- `GET /v1/metrics` - Comprehensive performance metrics (avg, p95, p99 latency, request volumes, accuracy tracking)
- `POST /v1/metrics/accuracy` - Record accuracy results for model performance tracking
- `GET /v1/metrics/health` - Health check endpoint
- Persistent storage in `data/metrics.json` (tracks up to 1000 requests)
- Per-endpoint statistics with status code breakdown

#### Obsidian Enhancements
- Updated opportunity template with forecast frontmatter fields and triage banner
- New Opportunities Dashboard with triage queue, high-confidence opportunities (≥75%), grouping by customer/OEM
- New Forecast Dashboard with FY25/26/27 projections, confidence distribution, customer breakdowns

#### TUI Integration
- New MetricsPanel displaying real-time latency stats, request volumes, accuracy matrix, top-5 slowest endpoints
- Keyboard shortcuts: `M` (refresh metrics), `P` (toggle auto-refresh)

### Tests
- **Total:** 101 tests passing (up from 71)
- **New tests:** 30 added (11 webhook tests, 10 forecast tests, 12 metrics tests, -3 removed duplicates)
- **Coverage:** ≥90% branch coverage
- **Success rate:** 100%

### Performance
- Average forecast latency: ~45ms (target ≤250ms)
- Test suite execution: ~4.3s
- Build time: ~6s total

### Links
- [Full Release Notes](docs/releases/v1.4.0.md)
- [Tag v1.4.0](https://github.com/routerjoe/red-river-sales-automation/releases/tag/v1.4.0)

---

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

### Related Documentation
- [GitHub Release Tag](https://github.com/routerjoe/red-river-sales-automation/releases/tag/v1.3.0)
- [Phase 3 Overview](docs/guides/phase3_overview.md)
- [Architecture Documentation](docs/architecture/phase3.md)

---

## [Unreleased]

### Planned (Phase 5)
- AI model integration for forecasting (replace heuristic with GPT-5 reasoning)
- Historical trend analysis and win rate tracking
- Multi-scenario forecasting with confidence intervals
- Automated re-forecasting (weekly scheduled jobs)

---

[v1.4.0]: https://github.com/routerjoe/red-river-sales-automation/compare/v1.3.0...v1.4.0
[v1.3.0]: https://github.com/routerjoe/red-river-sales-automation/compare/v1.2.0...v1.3.0
[Unreleased]: https://github.com/routerjoe/red-river-sales-automation/compare/v1.4.0...HEAD