# Forecast Hub Engine - Technical Guide

**Version:** 1.5.0 (Phase 5)  
**Last Updated:** October 28, 2025

---

## Overview

The Forecast Hub Engine is Red River's intelligent opportunity forecasting system that combines multi-factor scoring with AI-driven analytics to predict win probability and revenue projections across fiscal years.

### Key Features

- **Multi-Factor Intelligent Scoring** - Weighted scoring based on OEM alignment, partner fit, contract vehicles, and more
- **Win Probability Modeling** - Statistical models incorporating stage probability and time decay
- **Confidence Intervals** - Statistical bounds for forecast accuracy
- **FY-Based Projections** - Automatic distribution across FY25, FY26, FY27
- **Export Capabilities** - Obsidian dashboard and CSV export
- **TUI Integration** - Real-time forecast viewing in terminal UI

---

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────┐
│                  Forecast Hub Engine                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │      Opportunity Scoring Engine                 │    │
│  │  - OEM Alignment                                │    │
│  │  - Partner Fit                                  │    │
│  │  - Contract Vehicle Priority                    │    │
│  │  - Govly Relevance                              │    │
│  │  - Deal Size Scoring                            │    │
│  └────────────────────────────────────────────────┘    │
│                          ↓                               │
│  ┌────────────────────────────────────────────────┐    │
│  │    Win Probability Calculator                   │    │
│  │  - Stage Multipliers                            │    │
│  │  - Time Decay Factors                           │    │
│  │  - Confidence Intervals                         │    │
│  └────────────────────────────────────────────────┘    │
│                          ↓                               │
│  ┌────────────────────────────────────────────────┐    │
│  │      FY Distribution Engine                     │    │
│  │  - FY25, FY26, FY27 Projections                │    │
│  │  - Revenue Allocation Logic                     │    │
│  └────────────────────────────────────────────────┘    │
│                          ↓                               │
│  ┌────────────────────────────────────────────────┐    │
│  │         Export & Visualization                  │    │
│  │  - Obsidian Dashboard                           │    │
│  │  - CSV Export                                   │    │
│  │  - TUI Panel                                    │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Intelligent Scoring System

### Scoring Components

The intelligent scoring system evaluates opportunities across five dimensions:

#### 1. OEM Alignment Score (Weight: 25%)

Measures strategic alignment with Red River's key OEM partnerships.

**Scoring Table:**

| OEM                    | Score |
|------------------------|-------|
| Microsoft              | 95    |
| Cisco                  | 92    |
| Dell                   | 90    |
| HPE                    | 88    |
| Palo Alto Networks     | 88    |
| VMware                 | 85    |
| Fortinet               | 85    |
| NetApp                 | 83    |
| AWS                    | 80    |
| Google                 | 75    |
| Oracle                 | 70    |
| IBM                    | 68    |
| Unknown OEM            | 50    |

**Logic:**
- Takes highest score when multiple OEMs are present
- Case-insensitive matching
- Partial name matching supported

#### 2. Partner Fit Score (Weight: 15%)

Evaluates partner ecosystem strength and OEM alignment.

**Scoring Logic:**
- Base score: 50 (no partners) or 60 (has partners)
- +5 per additional partner (max +20)
- +10 per partner-OEM alignment (max +20)
- Range: 0-100

#### 3. Contract Vehicle Score (Weight: 20%)

Ranks opportunities by contract vehicle priority.

**Scoring Table:**

| Contract Vehicle       | Score |
|------------------------|-------|
| SEWP V                 | 95    |
| NASA SOLUTIONS         | 92    |
| GSA Schedule           | 90    |
| DHS FirstSource II     | 88    |
| CIO-SP3                | 85    |
| Alliant 2              | 83    |
| 8(a) STARS II          | 80    |
| Direct                 | 60    |
| Unknown                | 50    |

#### 4. Govly Relevance Score (Weight: 10%)

Measures federal/government opportunity relevance.

**Scoring Logic:**
- Base: 50
- Source = "Govly": 85
- +10 per federal tag (max +30)
- Tags checked: "federal", "government", "agency", "DEPARTMENT-ALPHA", "civilian", "govly"

#### 5. Deal Size Score (Weight: 30%)

Logarithmic scoring based on deal value.

**Scoring Table:**

| Deal Size         | Score |
|-------------------|-------|
| < $10K            | 20    |
| $10K - $50K       | 40    |
| $50K - $100K      | 50    |
| $100K - $250K     | 60    |
| $250K - $500K     | 70    |
| $500K - $1M       | 80    |
| $1M - $5M         | 90    |
| $5M - $10M        | 95    |
| > $10M            | 100   |

### Win Probability Calculation

Win probability combines the weighted composite score with stage probability and time decay:

```
Win Probability = (Composite Score × Stage Multiplier × Time Decay) / 100
```

#### Stage Multipliers

| Stage          | Multiplier |
|----------------|-----------|
| Qualification  | 0.15      |
| Discovery      | 0.25      |
| Proposal       | 0.45      |
| Negotiation    | 0.75      |
| Closed Won     | 1.00      |
| Closed Lost    | 0.00      |
| Unknown        | 0.20      |

#### Time Decay Factors

| Days to Close  | Factor |
|----------------|--------|
| Overdue        | 0.50   |
| < 30 days      | 1.00   |
| 30-90 days     | 0.95   |
| 90-180 days    | 0.85   |
| 180-365 days   | 0.75   |
| > 365 days     | 0.60   |

---

## Confidence Intervals

Statistical confidence bounds are calculated for each forecast to represent uncertainty.

### Calculation Method

```python
variance = base_variance × stage_factor × amount_factor

lower_bound = max(0, win_prob - variance × 100)
upper_bound = min(100, win_prob + variance × 100)
```

### Variance Factors

**By Stage:**
- Qualification: 0.40 (±40%)
- Discovery: 0.35 (±35%)
- Proposal: 0.25 (±25%)
- Negotiation: 0.15 (±15%)

**By Deal Size:**
- > $5M: × 1.3
- $1M - $5M: × 1.15
- < $1M: × 1.0

**Confidence Level:** 80%

### Example

For a $2M deal in Proposal stage with 75% win probability:
- Base variance: 0.25
- Amount multiplier: 1.15
- Adjusted variance: 0.2875
- Lower bound: 75 - 28.75 = 46.25%
- Upper bound: 75 + 28.75 = 100% (capped)

---

## FY Distribution

Opportunities are distributed across fiscal years based on close date.

### Federal Fiscal Year Definition

- **FY25:** October 1, 2024 - September 30, 2025
- **FY26:** October 1, 2025 - September 30, 2026
- **FY27:** October 1, 2026 - September 30, 2027

### Distribution Logic

**Close Date in FY25:**
- FY25: 80% of amount
- FY26: 15% of amount
- FY27: 5% of amount

**Close Date in FY26:**
- FY25: 10% of amount
- FY26: 75% of amount
- FY27: 15% of amount

**Close Date in FY27:**
- FY25: 5% of amount
- FY26: 20% of amount
- FY27: 75% of amount

---

## Usage Examples

### Generate Forecasts

```bash
curl -X POST http://localhost:8000/v1/forecast/run \
  -H "Content-Type: application/json" \
  -d '{
    "opportunity_ids": ["opp-123"],
    "model": "gpt-5-thinking",
    "confidence_threshold": 50
  }'
```

### Get All Forecasts

```bash
curl http://localhost:8000/v1/forecast/all
```

### Get Top Opportunities

```bash
curl "http://localhost:8000/v1/forecast/top?limit=10&sort_by=win_prob"
```

### Export to CSV

```bash
curl "http://localhost:8000/v1/forecast/export/csv?fiscal_year=25" \
  -o forecast_FY25.csv
```

### Export to Obsidian

```bash
curl -X POST http://localhost:8000/v1/forecast/export/obsidian
```

---

## Data Model

### ForecastData Schema

```json
{
  "opportunity_id": "opp-123",
  "opportunity_name": "Agency Cloud Migration",
  "projected_amount_FY25": 800000.00,
  "projected_amount_FY26": 150000.00,
  "projected_amount_FY27": 50000.00,
  "confidence_score": 85,
  "reasoning": "High-confidence forecast based on...",
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
```

---

## Best Practices

### 1. Regular Forecast Updates

Run forecasts weekly or when opportunity data changes:

```bash
# Weekly cron job
0 9 * * 1 curl -X POST http://localhost:8000/v1/forecast/run
```

### 2. Monitor Confidence Intervals

Wide confidence intervals indicate high uncertainty:
- Interval > 40%: High uncertainty - gather more information
- Interval 20-40%: Moderate uncertainty - normal
- Interval < 20%: Low uncertainty - high confidence

### 3. Use Appropriate Sort Criteria

- **win_prob**: Best for prioritization
- **FY25/FY26/FY27**: For fiscal planning
- **projected_amount**: For revenue targets

### 4. Export Regular Snapshots

```bash
# Daily snapshot
curl "http://localhost:8000/v1/forecast/export/csv" \
  -o "snapshots/forecast_$(date +%Y%m%d).csv"
```

---

## Performance Considerations

### Computation Cost

- **Single Opportunity:** ~5ms
- **Batch (100 opportunities):** ~500ms
- **Full Forecast Run:** < 2 seconds

### Caching Strategy

Forecasts are cached in `data/forecast.json`:
- Atomic writes prevent corruption
- No database required
- Fast read access

### Scaling

For > 1000 opportunities:
1. Use batch processing with `opportunity_ids`
2. Implement pagination for `/top` endpoint
3. Consider moving to database storage

---

## Troubleshooting

### Issue: Low Win Probabilities

**Causes:**
- Early stage (Qualification/Discovery)
- Unknown/low-priority OEM
- No contract vehicle specified
- Far future close date

**Solutions:**
- Verify opportunity data completeness
- Update OEM mapping if needed
- Add contract vehicle information

### Issue: Wide Confidence Intervals

**Causes:**
- Early stage deals
- Very large deal size (> $5M)
- Limited historical data

**Solutions:**
- Normal for early-stage deals
- Gather more qualification data
- Update stage as deal progresses

---

## Future Enhancements

### Planned for Phase 6

- Historical win-rate learning
- Customer-specific scoring
- Region-based adjustments
- Technology domain analysis
- ML-based probability models

---

## References

- API Documentation: [`/docs/api/forecast_endpoints.md`](../api/forecast_endpoints.md)
- Code: [`mcp/api/v1/forecast.py`](../../mcp/api/v1/forecast.py)
- Scoring Engine: [`mcp/core/scoring.py`](../../mcp/core/scoring.py)
- Tests: [`tests/test_forecast.py`](../../tests/test_forecast.py), [`tests/test_scoring.py`](../../tests/test_scoring.py)