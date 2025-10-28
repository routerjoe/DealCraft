# Phase 3 Overview — Integrations & Dashboard Enhancements

**Version:** v1.3.0  
**Release Date:** October 26, 2025  
**Sprint Window:** October 27 – November 10, 2025

---

## Executive Summary

Phase 3 delivers a comprehensive integration layer that unifies AI capabilities, enhances system observability, and provides intelligent dashboard views for sales pipeline management. The release introduces multi-model AI routing, automatic Federal Fiscal Year organization, and real-time monitoring—all while maintaining 100% backward compatibility.

### Key Metrics
- **Tests:** 71 passing (up from 67)
- **API Latency:** <3ms average (budget: 250ms)
- **Models Supported:** 6 (across 3 AI providers)
- **Dashboard Queries:** 10 Dataview blocks + 1 DataviewJS
- **Breaking Changes:** 0 (fully backward compatible)

---

## Component Overview

### 1. AI Router Enhancement

#### Purpose
Provide a unified interface for AI model interactions with automatic routing, validation, and fallback handling.

#### Key Features
- **Unified Endpoint:** `POST /v1/ai/ask`
  - Single interface for all AI queries
  - Model selection via request payload
  - Automatic model validation

- **Multi-Model Support:** 6 AI models across 3 providers
  ```
  OpenAI:
    ├─ gpt-5-thinking (default)
    └─ gpt-4-turbo
  
  Anthropic:
    ├─ claude-3.5
    └─ claude-3-opus
  
  Gemini:
    ├─ gemini-1.5-pro
    └─ gemini-1.5-flash
  ```

- **Smart Validation:** Invalid model names automatically fall back to `gpt-5-thinking`
- **Provider Metadata:** Detailed endpoint returns provider information

#### Request Example
```bash
curl -X POST http://localhost:8000/v1/ai/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Analyze this RFQ for compliance issues",
    "model": "claude-3.5",
    "context": {"rfq_id": "RFQ-2025-001"}
  }'
```

#### Response Example
```json
{
  "answer": "Analysis complete. No compliance issues found.",
  "model": "claude-3.5",
  "provider": "anthropic",
  "context_used": true
}
```

#### Implementation
- **Core Module:** `mcp/core/ai_router.py`
  - `select_model()` - Validates and selects AI model
  - `process_ai_request()` - Processes unified AI requests
  - `get_available_models()` - Returns model registry
  - `AVAILABLE_MODELS` - Dictionary of 6 models with metadata

- **API Endpoint:** `mcp/api/v1/ai.py`
  - `POST /v1/ai/ask` - Unified AI interface
  - `GET /v1/ai/models` - List model names
  - `GET /v1/ai/models/detailed` - Detailed model info

---

### 2. System Monitoring & Logging

#### Purpose
Provide real-time visibility into API usage, performance, and request patterns.

#### Key Features
- **Recent Actions Endpoint:** `GET /v1/system/recent-actions`
  - Returns last 10 API requests
  - Automatic rotation (oldest removed when >10)
  - Persistent storage in `data/state.json`

- **Automatic Logging Middleware**
  - Captures every API request (except `/healthz`)
  - Logs: request_id, timestamp, method, path, latency_ms, status_code, context
  - Atomic writes ensure data integrity

- **Request Tracking Headers**
  - `x-request-id`: UUID4 for distributed tracing
  - `x-latency-ms`: Request duration in milliseconds

#### Logged Data Structure
```json
{
  "request_id": "a1b2c3d4-e5f6-4789-a0b1-c2d3e4f5g6h7",
  "timestamp": "2025-10-26T15:30:45.123456+00:00",
  "method": "POST",
  "path": "/v1/ai/ask",
  "latency_ms": 2,
  "status_code": 200,
  "context": {"query": "sample=true"}
}
```

#### Use Cases
- **Performance Monitoring:** Track API latency trends
- **Debugging:** Trace requests via `x-request-id`
- **Usage Analytics:** Understand endpoint popularity
- **SLA Compliance:** Verify <250ms latency budget

#### Implementation
- **Core Module:** `mcp/api/main.py`
  - `log_action_to_state()` - Persists action log
  - Middleware: `add_request_id_and_latency()` - Auto-logging

- **API Endpoint:** `mcp/api/v1/system.py`
  - `GET /v1/system/recent-actions` - Retrieves logs

- **Storage:** `data/state.json`
  - `recent_actions` array (max 10 entries)
  - Atomic writes via `mcp/core/store.py`

---

### 3. Federal Fiscal Year Routing

#### Purpose
Automatically organize opportunities by Federal Fiscal Year for better pipeline management and reporting.

#### Key Concept
Federal FY runs from **October 1 (Year N-1)** to **September 30 (Year N)**:
- **FY25:** Oct 1, 2024 → Sep 30, 2025
- **FY26:** Oct 1, 2025 → Sep 30, 2026

#### Routing Logic
```python
def get_federal_fy(close_date_str: str) -> str:
    date = parse(close_date_str)  # YYYY-MM-DD
    
    if date.month >= 10:  # Oct-Dec
        return f"FY{(date.year + 1) % 100:02d}"
    else:  # Jan-Sep
        return f"FY{date.year % 100:02d}"
```

#### Directory Structure
```
obsidian/40 Projects/Opportunities/
├── FY24/
│   ├── OPP-001 - Legacy Migration.md
│   └── OPP-002 - Server Refresh.md
├── FY25/
│   ├── OPP-010 - Cloud Strategy.md
│   └── OPP-011 - Security Upgrade.md
├── FY26/
│   ├── OPP-020 - AI Implementation.md
│   └── OPP-021 - Network Overhaul.md
└── Triage/
    └── OPP-999 - Invalid Date.md
```

#### Examples
| Close Date | Fiscal Year | Folder |
|------------|-------------|--------|
| 2024-11-15 | FY25 | `/FY25/` |
| 2025-06-30 | FY25 | `/FY25/` |
| 2025-10-01 | FY26 | `/FY26/` |
| 2026-03-15 | FY26 | `/FY26/` |
| Invalid | N/A | `/Triage/` |

#### Implementation
- **Core Function:** `mcp/api/v1/obsidian.py`
  - `get_federal_fy()` - FY calculation logic
  - `create_opportunity_note()` - Routes to correct folder

---

### 4. Dashboard-Friendly YAML Aliases

#### Purpose
Enable Obsidian Dataview queries to work with multiple field naming conventions without breaking existing notes.

#### Design Principle
**Non-Breaking Addition:** Original fields preserved, aliases added alongside.

#### Alias Mapping
| Original Key | Alias Key | Format | Purpose |
|--------------|-----------|--------|---------|
| `amount` | `est_amount` | Numeric | Dashboard aggregations |
| `close_date` | `est_close` | Date string | Date filtering |
| `oem` | `oems` | List `[oem]` | Multi-vendor support |
| N/A | `partners` | List `[]` | Future partner tracking |
| N/A | `contract_vehicle` | String `""` | Contract type field |

#### YAML Example
```yaml
---
id: OPP-2025-001
title: "Federal IT Modernization"
customer: DoD Agency X
oem: Dell Technologies
amount: 250000.0
stage: Qualification
close_date: 2025-06-30
source: RFQ
type: opportunity

# Dashboard-friendly aliases (non-breaking)
est_amount: 250000.0
est_close: 2025-06-30
oems:
  - Dell Technologies
partners: []
contract_vehicle: ""

tags:
  - opportunity
  - 30-hub
---
```

#### Dataview Query Pattern
```dataview
TABLE
  (amount ?? est_amount) AS Amount,
  (close_date ?? est_close) AS "Close Date",
  (oems ?? [oem]) AS OEMs
FROM "40 Projects/Opportunities"
WHERE type = "opportunity"
```

The `??` operator provides fallback:
1. Try `amount` first (original field)
2. Fall back to `est_amount` if missing
3. Ensures queries work with old and new notes

---

### 5. Obsidian Dataview Dashboard

#### Purpose
Provide real-time, queryable views of the sales pipeline with minimal manual updates.

#### Location
`obsidian/50 Dashboards/Opportunities Dashboard.md`

#### Dashboard Sections

##### 1. Pipeline by Stage
Groups opportunities by sales stage with total estimated values.

```dataview
TABLE WITHOUT ID stage AS Stage,
sum(number(amount ?? est_amount)) AS EstTotal,
length(rows) AS Count,
rows.file.link AS Opportunities
FROM "40 Projects/Opportunities"
WHERE type = "opportunity"
GROUP BY stage
SORT EstTotal DESC
```

##### 2. Upcoming Closes (Next 90 Days)
Rolling 90-day window of opportunities closing soon.

```dataview
TABLE WITHOUT ID
file.link AS Opportunity,
customer AS Customer,
(oems ?? [oem]) AS OEMs,
(amount ?? est_amount) AS "Est. Amount",
(close_date ?? est_close) AS "Close Date"
FROM "40 Projects/Opportunities"
WHERE type = "opportunity"
AND date(close_date ?? est_close) <= date(today) + dur(90 days)
SORT (close_date ?? est_close) ASC
```

##### 3. By Federal Fiscal Year
Aggregates pipeline by FY folder.

```dataview
TABLE WITHOUT ID
file.folder AS "Fiscal Year",
sum(number(amount ?? est_amount)) AS "Total Pipeline",
length(rows) AS "Opportunity Count"
FROM "40 Projects/Opportunities"
GROUP BY file.folder
SORT file.folder DESC
```

##### 4. Top Opportunities (>$500K)
Highlights high-value deals requiring executive attention.

##### 5. By OEM/Vendor
Pipeline breakdown by vendor for partner management.

##### 6. By Customer
Pipeline breakdown by customer for account planning.

##### 7. Triage Queue
Opportunities with invalid dates needing review.

##### 8. By Source
Shows where opportunities are originating (RFQ, Govly, Partner, etc.).

##### 9. Recent Activity (Last 30 Days)
Recently created or modified opportunities.

##### 10. Summary Stats (DataviewJS)
JavaScript-powered summary with totals, averages, and stage breakdowns.

```javascript
const opportunities = dv.pages('"40 Projects/Opportunities"')
    .where(p => p.type === "opportunity");

const totalPipeline = opportunities
    .map(p => Number(p.amount ?? p.est_amount ?? 0))
    .reduce((a, b) => a + b, 0);

dv.paragraph(`**Total Pipeline:** $${totalPipeline.toLocaleString()}`);
```

---

## Integration Flow

### Opportunity Creation Flow
```
1. API Request
   ↓
2. Validate Input (Pydantic)
   ↓
3. Calculate Federal FY
   │  ├─ Parse close_date
   │  ├─ Determine FY (25, 26, etc.)
   │  └─ Route to folder
   ↓
4. Generate Markdown
   │  ├─ YAML frontmatter (original keys)
   │  ├─ YAML aliases (dashboard keys)
   │  └─ Markdown body
   ↓
5. Write to Disk
   │  Path: obsidian/40 Projects/Opportunities/FY25/OPP-001.md
   ↓
6. Dataview Auto-Updates
   └─ Dashboard queries re-execute on file change
```

### AI Request Flow
```
1. Client Request
   ↓
2. Middleware: Assign request_id
   ↓
3. Route to /v1/ai/ask
   ↓
4. Validate Model
   │  ├─ Check AVAILABLE_MODELS
   │  └─ Fallback to default if invalid
   ↓
5. Process Request
   │  ├─ Call process_ai_request()
   │  └─ Generate response
   ↓
6. Middleware: Calculate latency_ms
   ↓
7. Middleware: Log to state.json
   ↓
8. Return Response
   └─ Headers: x-request-id, x-latency-ms
```

---

## Testing Strategy

### Test Coverage
- **71 total tests** (up from 67)
- **100% pass rate**
- **<5 seconds** execution time

### New Tests (Phase 3)
1. `test_fy_routing_fy25` - Validates FY25 routing logic
2. `test_fy_routing_fy26` - Validates FY26 routing logic
3. `test_yaml_aliases_present` - Verifies all alias fields exist
4. `test_yaml_aliases_oems_list` - Validates list format for oems

### Test Categories
- **AI Endpoints (6 tests):** Model selection, guidance generation
- **Obsidian Integration (13 tests):** FY routing, YAML generation, aliases
- **System Monitoring (future):** Recent actions, logging rotation
- **Contacts Export (13 tests):** CSV/VCF generation
- **Contracts & OEMs (20 tests):** CRUD operations
- **Email Ingestion (14 tests):** RFQ, Govly, IntroMail
- **Health & Info (5 tests):** Health checks, API info

---

## Performance Benchmarks

### API Response Times
| Endpoint | Avg Latency | Max Observed | Budget |
|----------|-------------|--------------|--------|
| `/v1/ai/ask` | 2-3ms | 5ms | 250ms |
| `/v1/ai/models` | <1ms | 1ms | 250ms |
| `/v1/system/recent-actions` | 1-2ms | 3ms | 250ms |
| `/v1/obsidian/opportunity` | 2-3ms | 5ms | 250ms |

**All endpoints comfortably under 250ms budget**

### Test Suite Performance
- **Execution Time:** ~3 seconds
- **Tests:** 71
- **Avg per test:** ~42ms

### Build Process
- **Lint:** <1 second
- **Format:** <1 second
- **Tests:** ~3 seconds
- **Total:** <6 seconds

---

## Migration Guide

### For Existing Deployments

#### 1. No Action Required
Phase 3 is **100% backward compatible**. Existing functionality continues to work without changes.

#### 2. Optional: Migrate Opportunities
If you want FY routing for existing opportunities:

```bash
# Example migration script (not included)
for file in obsidian/30\ Hub/Opportunities/*.md; do
  close_date=$(grep "close_date:" "$file" | cut -d' ' -f2)
  fy=$(python -c "from mcp.api.v1.obsidian import get_federal_fy; print(get_federal_fy('$close_date'))")
  mkdir -p "obsidian/40 Projects/Opportunities/$fy"
  mv "$file" "obsidian/40 Projects/Opportunities/$fy/"
done
```

#### 3. Optional: Add Dashboard
Copy `obsidian/50 Dashboards/Opportunities Dashboard.md` to your Obsidian vault and customize queries.

---

## Future Enhancements (Phase 4)

### Planned Features
1. **Forecast Hub**
   - AI-powered pipeline predictions
   - Win probability scoring
   - FY revenue forecasting

2. **Radar Parser**
   - Automated opportunity detection
   - Competitive intelligence gathering
   - Real-time market monitoring

3. **Govly Webhook Integration**
   - Real-time opportunity ingestion
   - Automatic RFQ creation
   - Notification system

4. **Metrics Dashboard**
   - Latency trend analysis
   - Model accuracy tracking
   - Usage analytics
   - Cost optimization

---

## Troubleshooting

### Common Issues

#### 1. Opportunities Not Appearing in Dashboard
**Symptom:** New opportunities don't show in Dataview queries

**Solutions:**
- Verify `type: opportunity` in YAML frontmatter
- Check file is in `40 Projects/Opportunities/` tree
- Restart Obsidian to refresh Dataview index

#### 2. FY Routing to Triage
**Symptom:** Opportunities always route to Triage folder

**Solutions:**
- Verify `close_date` format is `YYYY-MM-DD`
- Check date is not empty or null
- Validate date string in API request

#### 3. AI Model Not Found
**Symptom:** Model selection fails with error

**Solutions:**
- Check model name against `/v1/ai/models` endpoint
- Verify spelling (case-sensitive)
- System will auto-fallback to `gpt-5-thinking`

---

## Support & Resources

### Documentation
- **CHANGELOG:** Version history and release notes
- **Architecture Diagram:** System component overview
- **API Documentation:** Interactive docs at `/docs`
- **Sprint Summary:** Detailed Phase 3 notes

### Contact
For questions or issues, contact the Red River Sales Automation team.

---

**Phase 3 Status:** ✅ Complete  
**Production Ready:** Yes  
**Breaking Changes:** None  
**Recommended Action:** Deploy immediately