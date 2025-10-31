# Forecast API Endpoints

**Version:** 1.5.0 (Phase 5)  
**Base URL:** `http://localhost:8000`  
**Last Updated:** October 28, 2025

---

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
  - [POST /v1/forecast/run](#post-v1forecastrun)
  - [GET /v1/forecast/summary](#get-v1forecastsummary)
  - [GET /v1/forecast/all](#get-v1forecastall)
  - [GET /v1/forecast/FY{year}](#get-v1forecastfyyear)
  - [GET /v1/forecast/top](#get-v1forecasttop)
  - [GET /v1/forecast/export/csv](#get-v1forecastexportcsv)
  - [POST /v1/forecast/export/obsidian](#post-v1forecastexportobsidian)
- [Data Models](#data-models)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)

---

## Overview

The Forecast API provides intelligent forecasting and scoring for sales opportunities. Phase 5 introduces multi-factor scoring, confidence intervals, and enhanced export capabilities.

### Key Features

- **Intelligent Scoring**: Multi-dimensional opportunity evaluation
- **Win Probability**: Statistical models with confidence intervals
- **FY Projections**: Automatic distribution across FY25/26/27
- **Flexible Exports**: CSV and Obsidian dashboard formats
- **Query Options**: Sort, filter, and paginate results

---

## Authentication

All endpoints require the `X-Request-ID` header for request tracking:

```http
X-Request-ID: unique-request-id
```

If not provided, a default value of "unknown" will be used.

---

## Endpoints

### POST /v1/forecast/run

Generate forecasts for opportunities with intelligent scoring.

#### Request

**URL:** `/v1/forecast/run`  
**Method:** `POST`  
**Content-Type:** `application/json`

**Body Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `opportunity_ids` | array[string] | No | null | Specific opportunity IDs to forecast. If null, forecasts all opportunities. |
| `model` | string | No | "gpt-5-thinking" | AI model to use for forecasting |
| `confidence_threshold` | integer | No | 50 | Minimum confidence score (0-100) |

**Example Request:**

```bash
curl -X POST http://localhost:8000/v1/forecast/run \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: req-12345" \
  -d '{
    "opportunity_ids": ["opp-123", "opp-456"],
    "model": "gpt-5-thinking",
    "confidence_threshold": 50
  }'
```

#### Response

**Status:** `200 OK`

```json
{
  "request_id": "req-12345",
  "forecasts_generated": 2,
  "forecasts": [
    {
      "opportunity_id": "opp-123",
      "opportunity_name": "Agency Cloud Migration",
      "projected_amount_FY25": 800000.00,
      "projected_amount_FY26": 150000.00,
      "projected_amount_FY27": 50000.00,
      "confidence_score": 85,
      "reasoning": "High-confidence forecast based on close_date...",
      "generated_at": "2025-10-28T22:00:00Z",
      "model_used": "gpt-5-thinking",
      "win_prob": 72.5,
      "score_raw": 85.2,
      "score_scaled": 85.2,
      "oem_alignment_score": 95.0,
      "partner_fit_score": 75.0,
      "contract_vehicle_score": 95.0,
      "govly_relevance_score": 85.0,
      "confidence_interval": {
        "lower_bound": 52.5,
        "upper_bound": 92.5,
        "interval_width": 40.0,
        "confidence_level": 0.80
      }
    }
  ],
  "latency_ms": 245.67
}
```

---

### GET /v1/forecast/summary

Get summary statistics for all forecasts.

#### Request

**URL:** `/v1/forecast/summary?confidence_threshold=50`  
**Method:** `GET`

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `confidence_threshold` | integer | No | 50 | Minimum confidence score to include |

**Example Request:**

```bash
curl "http://localhost:8000/v1/forecast/summary?confidence_threshold=70" \
  -H "X-Request-ID: req-12346"
```

#### Response

**Status:** `200 OK`

```json
{
  "total_opportunities": 10,
  "total_projected_FY25": 5000000.00,
  "total_projected_FY26": 7500000.00,
  "total_projected_FY27": 2500000.00,
  "avg_confidence": 75.5,
  "high_confidence_count": 6,
  "medium_confidence_count": 3,
  "low_confidence_count": 1,
  "last_updated": "2025-10-28T22:00:00Z"
}
```

---

### GET /v1/forecast/all

Retrieve all forecasts.

#### Request

**URL:** `/v1/forecast/all`  
**Method:** `GET`

**Example Request:**

```bash
curl http://localhost:8000/v1/forecast/all \
  -H "X-Request-ID: req-12347"
```

#### Response

**Status:** `200 OK`

```json
{
  "request_id": "req-12347",
  "total": 10,
  "forecasts": [
    {
      "opportunity_id": "opp-123",
      "opportunity_name": "Agency Cloud Migration",
      "projected_amount_FY25": 800000.00,
      "projected_amount_FY26": 150000.00,
      "projected_amount_FY27": 50000.00,
      "win_prob": 72.5,
      "confidence_score": 85,
      "oem_alignment_score": 95.0,
      "partner_fit_score": 75.0,
      "contract_vehicle_score": 95.0,
      "govly_relevance_score": 85.0,
      "confidence_interval": {
        "lower_bound": 52.5,
        "upper_bound": 92.5,
        "interval_width": 40.0,
        "confidence_level": 0.80
      },
      "generated_at": "2025-10-28T22:00:00Z"
    }
  ]
}
```

---

### GET /v1/forecast/FY{year}

Get forecasts for a specific fiscal year.

#### Request

**URL:** `/v1/forecast/FY25` or `/v1/forecast/FY26` or `/v1/forecast/FY27`  
**Method:** `GET`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `year` | integer | Yes | Fiscal year (25, 26, or 27) |

**Example Request:**

```bash
curl http://localhost:8000/v1/forecast/FY25 \
  -H "X-Request-ID: req-12348"
```

#### Response

**Status:** `200 OK`

```json
{
  "request_id": "req-12348",
  "fiscal_year": "FY25",
  "total_opportunities": 8,
  "total_projected": 5000000.00,
  "forecasts": [
    {
      "opportunity_id": "opp-123",
      "opportunity_name": "Agency Cloud Migration",
      "projected_amount_FY25": 800000.00,
      "win_prob": 72.5,
      "confidence_score": 85,
      "generated_at": "2025-10-28T22:00:00Z"
    }
  ]
}
```

**Notes:**
- Only returns forecasts with non-zero amounts for the requested FY
- Sorted by projected amount (descending)

---

### GET /v1/forecast/top

Get top-ranked forecasts by various criteria.

#### Request

**URL:** `/v1/forecast/top?limit=10&sort_by=win_prob&fiscal_year=25`  
**Method:** `GET`

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | integer | No | 10 | Maximum number of results |
| `sort_by` | string | No | "win_prob" | Sort criteria (see options below) |
| `fiscal_year` | integer | No | null | Filter by fiscal year (25, 26, 27) |

**Sort Options:**
- `win_prob` - Win probability (highest first)
- `score_raw` - Raw composite score
- `projected_amount` - Total projected across all FYs
- `FY25` - FY25 projected amount
- `FY26` - FY26 projected amount
- `FY27` - FY27 projected amount

**Example Request:**

```bash
curl "http://localhost:8000/v1/forecast/top?limit=5&sort_by=win_prob" \
  -H "X-Request-ID: req-12349"
```

#### Response

**Status:** `200 OK`

```json
{
  "request_id": "req-12349",
  "top_deals": [
    {
      "opportunity_id": "opp-123",
      "opportunity_name": "Agency Cloud Migration",
      "projected_amount_FY25": 800000.00,
      "projected_amount_FY26": 150000.00,
      "projected_amount_FY27": 50000.00,
      "win_prob": 82.5,
      "score_raw": 89.2,
      "oem_alignment_score": 95.0,
      "partner_fit_score": 85.0,
      "contract_vehicle_score": 95.0,
      "generated_at": "2025-10-28T22:00:00Z"
    }
  ],
  "sort_criteria": "win_prob",
  "limit": 5,
  "total_available": 10
}
```

---

### GET /v1/forecast/export/csv

Export forecasts to CSV format.

#### Request

**URL:** `/v1/forecast/export/csv?fiscal_year=25`  
**Method:** `GET`

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `fiscal_year` | integer | No | null | Export specific FY (25, 26, 27). If omitted, exports all FYs. |

**Example Request:**

```bash
curl "http://localhost:8000/v1/forecast/export/csv?fiscal_year=25" \
  -H "X-Request-ID: req-12350" \
  -o forecast_FY25.csv
```

#### Response

**Status:** `200 OK`  
**Content-Type:** `text/csv`  
**Headers:**
- `Content-Disposition: attachment; filename=forecast_FY25.csv`
- `X-Request-ID: req-12350`

**CSV Structure (All FYs):**

```csv
opportunity_id,opportunity_name,projected_amount_FY25,projected_amount_FY26,projected_amount_FY27,total_projected,win_prob,confidence_score,oem_alignment_score,partner_fit_score,contract_vehicle_score,govly_relevance_score,confidence_interval_lower,confidence_interval_upper,generated_at,model_used
opp-123,Agency Cloud Migration,800000.00,150000.00,50000.00,1000000.00,72.5,85,95.0,75.0,95.0,85.0,52.5,92.5,2025-10-28T22:00:00Z,gpt-5-thinking
```

**CSV Structure (Single FY):**

```csv
opportunity_id,opportunity_name,projected_amount_FY25,win_prob,confidence_score,oem_alignment_score,partner_fit_score,contract_vehicle_score,govly_relevance_score,generated_at
opp-123,Agency Cloud Migration,800000.00,72.5,85,95.0,75.0,95.0,85.0,2025-10-28T22:00:00Z
```

**Error Response:**

**Status:** `404 Not Found`

```json
{
  "detail": "No forecasts available to export"
}
```

---

### POST /v1/forecast/export/obsidian

Export forecasts to Obsidian Forecast Dashboard.

#### Request

**URL:** `/v1/forecast/export/obsidian`  
**Method:** `POST`

**Example Request:**

```bash
curl -X POST http://localhost:8000/v1/forecast/export/obsidian \
  -H "X-Request-ID: req-12351"
```

#### Response

**Status:** `200 OK`

```json
{
  "request_id": "req-12351",
  "path": "obsidian/50 Dashboards/Forecast Dashboard.md",
  "opportunities_exported": 10,
  "total_FY25": 5000000.00,
  "total_FY26": 7500000.00,
  "total_FY27": 2500000.00,
  "dashboard_updated": true
}
```

**Notes:**
- Creates/updates: `obsidian/50 Dashboards/Forecast Dashboard.md`
- Dashboard includes:
  - Summary statistics
  - FY projections table
  - Top 20 opportunities by win probability
  - Confidence distribution
  - OEM heat map

**Error Response:**

**Status:** `404 Not Found`

```json
{
  "detail": "No forecasts available to export"
}
```

---

## Data Models

### ForecastData

Complete forecast data model with Phase 5 enhancements.

```typescript
{
  // Basic Information
  opportunity_id: string;
  opportunity_name: string;
  
  // FY Projections
  projected_amount_FY25: number;  // Float, 2 decimal places
  projected_amount_FY26: number;
  projected_amount_FY27: number;
  
  // Legacy Fields
  confidence_score: number;       // Integer 0-100
  reasoning: string;
  generated_at: string;           // ISO 8601 UTC
  model_used: string;
  
  // Phase 5: Intelligent Scoring
  win_prob: number;               // Float 0-100
  score_raw: number;              // Float 0-100
  score_scaled: number;           // Float 0-100
  oem_alignment_score: number;    // Float 0-100
  partner_fit_score: number;      // Float 0-100
  contract_vehicle_score: number; // Float 0-100
  govly_relevance_score: number;  // Float 0-100
  
  // Confidence Interval
  confidence_interval: {
    lower_bound: number;          // Float 0-100
    upper_bound: number;          // Float 0-100
    interval_width: number;       // Float
    confidence_level: number;     // Float (typically 0.80)
  }
}
```

### ForecastSummary

Aggregate statistics across all forecasts.

```typescript
{
  total_opportunities: number;
  total_projected_FY25: number;
  total_projected_FY26: number;
  total_projected_FY27: number;
  avg_confidence: number;
  high_confidence_count: number;    // >= 75%
  medium_confidence_count: number;  // 50-74%
  low_confidence_count: number;     // < 50%
  last_updated: string;             // ISO 8601 UTC
}
```

---

## Error Handling

### Standard Error Response

```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| `200` | Success |
| `201` | Created |
| `400` | Bad Request - Invalid parameters |
| `404` | Not Found - Resource doesn't exist |
| `500` | Internal Server Error |

### Common Errors

**404: No Forecasts Available**
```json
{
  "detail": "No forecasts available to export"
}
```

**500: Forecast Generation Failed**
```json
{
  "detail": "Failed to generate forecast: [specific error]"
}
```

---

## Rate Limiting

Currently, there are no rate limits on forecast endpoints. However, consider:

- Batch forecasting: Use `opportunity_ids` to process specific opportunities
- Caching: Forecasts are cached in `data/forecast.json`
- Performance: Expect ~500ms for 100 opportunities

---

## Best Practices

### 1. Request IDs

Always include unique request IDs for tracking:

```bash
curl -H "X-Request-ID: $(uuidgen)" ...
```

### 2. Incremental Updates

Update only changed opportunities:

```bash
curl -X POST http://localhost:8000/v1/forecast/run \
  -d '{"opportunity_ids": ["opp-new-1", "opp-updated-2"]}'
```

### 3. Regular Exports

Schedule regular exports for historical tracking:

```bash
# Daily export
0 9 * * * curl http://localhost:8000/v1/forecast/export/csv \
  -o "snapshots/forecast_$(date +%Y%m%d).csv"
```

### 4. Error Handling

Always check response status and handle errors:

```python
response = requests.post("http://localhost:8000/v1/forecast/run")
if response.status_code == 200:
    forecasts = response.json()["forecasts"]
else:
    print(f"Error: {response.json()['detail']}")
```

---

## Examples

### Python Client

```python
import requests

class ForecastClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def generate_forecasts(self, opportunity_ids=None):
        """Generate forecasts for opportunities."""
        response = requests.post(
            f"{self.base_url}/v1/forecast/run",
            json={"opportunity_ids": opportunity_ids}
        )
        response.raise_for_status()
        return response.json()
    
    def get_top_deals(self, limit=10, sort_by="win_prob"):
        """Get top-ranked deals."""
        response = requests.get(
            f"{self.base_url}/v1/forecast/top",
            params={"limit": limit, "sort_by": sort_by}
        )
        response.raise_for_status()
        return response.json()["top_deals"]
    
    def export_csv(self, fiscal_year=None):
        """Export forecasts to CSV."""
        params = {"fiscal_year": fiscal_year} if fiscal_year else {}
        response = requests.get(
            f"{self.base_url}/v1/forecast/export/csv",
            params=params
        )
        response.raise_for_status()
        return response.text

# Usage
client = ForecastClient()
forecasts = client.generate_forecasts()
top_deals = client.get_top_deals(limit=5)
csv_data = client.export_csv(fiscal_year=25)
```

### JavaScript Client

```javascript
class ForecastClient {
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  async generateForecasts(opportunityIds = null) {
    const response = await fetch(`${this.baseUrl}/v1/forecast/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ opportunity_ids: opportunityIds })
    });
    return response.json();
  }

  async getTopDeals(limit = 10, sortBy = 'win_prob') {
    const params = new URLSearchParams({ limit, sort_by: sortBy });
    const response = await fetch(`${this.baseUrl}/v1/forecast/top?${params}`);
    const data = await response.json();
    return data.top_deals;
  }

  async exportObsidian() {
    const response = await fetch(`${this.baseUrl}/v1/forecast/export/obsidian`, {
      method: 'POST'
    });
    return response.json();
  }
}

// Usage
const client = new ForecastClient();
const forecasts = await client.generateForecasts();
const topDeals = await client.getTopDeals(5);
const result = await client.exportObsidian();
```

---

## Changelog

### v1.5.0 (Phase 5) - October 28, 2025

**Added:**
- Intelligent multi-factor scoring system
- Win probability with confidence intervals
- GET `/v1/forecast/all` endpoint
- GET `/v1/forecast/FY{year}` endpoint
- GET `/v1/forecast/top` endpoint
- GET `/v1/forecast/export/csv` endpoint
- POST `/v1/forecast/export/obsidian` endpoint

**Enhanced:**
- ForecastData model with scoring fields
- Confidence interval calculations
- FY distribution logic

### v1.4.0 (Phase 4) - Previous

**Added:**
- POST `/v1/forecast/run` endpoint
- GET `/v1/forecast/summary` endpoint
- Basic forecast persistence

---

## Support

- **Documentation:** [`/docs/guides/forecast_engine.md`](../guides/forecast_engine.md)
- **Source Code:** [`mcp/api/v1/forecast.py`](../../mcp/api/v1/forecast.py)
- **Tests:** [`tests/test_forecast.py`](../../tests/test_forecast.py)