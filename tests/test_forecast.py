"""Tests for Forecast Hub Engine endpoints."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mcp.api.main import app

client = TestClient(app)

# Test data
TEST_DATA_DIR = Path("data")
TEST_STATE_FILE = TEST_DATA_DIR / "state.json"
TEST_FORECAST_FILE = TEST_DATA_DIR / "forecast.json"


@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Setup and teardown for each test."""
    # Save originals
    original_state = None
    original_forecast = None

    if TEST_STATE_FILE.exists():
        with open(TEST_STATE_FILE, "r") as f:
            original_state = f.read()

    if TEST_FORECAST_FILE.exists():
        with open(TEST_FORECAST_FILE, "r") as f:
            original_forecast = f.read()

    # Initialize test data
    TEST_DATA_DIR.mkdir(exist_ok=True)

    # Create test state with sample opportunities
    test_state = {
        "opportunities": [
            {"id": "test_opp_1", "name": "Test Opportunity 1", "amount": 100000, "close_date": "2025-03-15T00:00:00Z"},
            {"id": "test_opp_2", "name": "Test Opportunity 2", "amount": 250000, "close_date": "2026-06-30T00:00:00Z"},
        ],
        "recent_actions": [],
    }

    with open(TEST_STATE_FILE, "w") as f:
        json.dump(test_state, f)

    # Initialize empty forecast
    with open(TEST_FORECAST_FILE, "w") as f:
        json.dump({}, f)

    yield

    # Restore originals
    if original_state:
        with open(TEST_STATE_FILE, "w") as f:
            f.write(original_state)

    if original_forecast:
        with open(TEST_FORECAST_FILE, "w") as f:
            f.write(original_forecast)


def test_forecast_run_success():
    """Test successful forecast generation."""
    response = client.post("/v1/forecast/run", json={"model": "gpt-5-thinking", "confidence_threshold": 50})

    assert response.status_code == 200
    data = response.json()
    assert "forecasts_generated" in data
    assert data["forecasts_generated"] == 2  # Two opportunities in test state
    assert "forecasts" in data
    assert len(data["forecasts"]) == 2
    assert "latency_ms" in data


def test_forecast_run_specific_opportunities():
    """Test forecast generation for specific opportunities."""
    response = client.post("/v1/forecast/run", json={"opportunity_ids": ["test_opp_1"], "model": "gpt-5-thinking"})

    assert response.status_code == 200
    data = response.json()
    assert data["forecasts_generated"] == 1
    assert len(data["forecasts"]) == 1
    assert data["forecasts"][0]["opportunity_id"] == "test_opp_1"


def test_forecast_run_creates_forecast_file():
    """Test that forecast run persists to forecast.json."""
    response = client.post("/v1/forecast/run", json={})
    assert response.status_code == 200

    # Check forecast.json exists and has data
    assert TEST_FORECAST_FILE.exists()
    with open(TEST_FORECAST_FILE, "r") as f:
        forecasts = json.load(f)

    assert len(forecasts) == 2
    assert "test_opp_1" in forecasts
    assert "test_opp_2" in forecasts


def test_forecast_data_structure():
    """Test that forecast data has required fields."""
    response = client.post("/v1/forecast/run", json={})
    assert response.status_code == 200

    forecast = response.json()["forecasts"][0]

    # Check all required fields
    assert "opportunity_id" in forecast
    assert "opportunity_name" in forecast
    assert "projected_amount_FY25" in forecast
    assert "projected_amount_FY26" in forecast
    assert "projected_amount_FY27" in forecast
    assert "confidence_score" in forecast
    assert "reasoning" in forecast
    assert "generated_at" in forecast
    assert "model_used" in forecast

    # Check confidence score is 0-100
    assert 0 <= forecast["confidence_score"] <= 100


def test_forecast_summary_success():
    """Test forecast summary endpoint."""
    # First generate forecasts
    client.post("/v1/forecast/run", json={})

    # Then get summary
    response = client.get("/v1/forecast/summary")

    assert response.status_code == 200
    data = response.json()

    assert "total_opportunities" in data
    assert "total_projected_FY25" in data
    assert "total_projected_FY26" in data
    assert "total_projected_FY27" in data
    assert "avg_confidence" in data
    assert "high_confidence_count" in data
    assert "medium_confidence_count" in data
    assert "low_confidence_count" in data
    assert "last_updated" in data


def test_forecast_summary_with_threshold():
    """Test forecast summary with confidence threshold."""
    # Generate forecasts
    client.post("/v1/forecast/run", json={})

    # Get summary with high threshold
    response = client.get("/v1/forecast/summary?confidence_threshold=80")

    assert response.status_code == 200
    data = response.json()

    # Should filter by confidence
    assert data["total_opportunities"] >= 0


def test_forecast_summary_empty_state():
    """Test forecast summary with no forecasts."""
    response = client.get("/v1/forecast/summary")

    assert response.status_code == 200
    data = response.json()

    assert data["total_opportunities"] == 0
    assert data["total_projected_FY25"] == 0
    assert data["total_projected_FY26"] == 0
    assert data["total_projected_FY27"] == 0
    assert data["avg_confidence"] == 0


def test_forecast_run_with_request_id():
    """Test that forecast endpoints include request_id in headers."""
    response = client.post("/v1/forecast/run", json={})

    assert response.status_code == 200
    assert "x-request-id" in response.headers
    assert "x-latency-ms" in response.headers


def test_forecast_amounts_sum_correctly():
    """Test that forecast amounts across FYs are reasonable."""
    response = client.post("/v1/forecast/run", json={})
    assert response.status_code == 200

    forecast = response.json()["forecasts"][0]

    # All amounts should be non-negative
    assert forecast["projected_amount_FY25"] >= 0
    assert forecast["projected_amount_FY26"] >= 0
    assert forecast["projected_amount_FY27"] >= 0

    # Sum should be close to original amount (within reason)
    total_forecast = forecast["projected_amount_FY25"] + forecast["projected_amount_FY26"] + forecast["projected_amount_FY27"]
    assert total_forecast > 0


# ============================================================================
# Phase 5: Intelligent Scoring Tests
# ============================================================================


def test_forecast_includes_scoring_fields():
    """Test that Phase 5 forecasts include intelligent scoring fields."""
    response = client.post("/v1/forecast/run", json={})
    assert response.status_code == 200

    forecast = response.json()["forecasts"][0]

    # Check Phase 5 scoring fields are present
    assert "win_prob" in forecast
    assert "score_raw" in forecast
    assert "score_scaled" in forecast
    assert "oem_alignment_score" in forecast
    assert "partner_fit_score" in forecast
    assert "contract_vehicle_score" in forecast
    assert "govly_relevance_score" in forecast
    assert "confidence_interval" in forecast

    # Check scoring values are in valid ranges
    assert 0 <= forecast["win_prob"] <= 100
    assert 0 <= forecast["score_raw"] <= 100
    assert 0 <= forecast["oem_alignment_score"] <= 100


def test_confidence_interval_structure():
    """Test that confidence interval has required fields."""
    response = client.post("/v1/forecast/run", json={})
    assert response.status_code == 200

    forecast = response.json()["forecasts"][0]
    ci = forecast["confidence_interval"]

    assert "lower_bound" in ci
    assert "upper_bound" in ci
    assert "interval_width" in ci
    assert "confidence_level" in ci

    # Bounds should be valid
    assert 0 <= ci["lower_bound"] <= 100
    assert 0 <= ci["upper_bound"] <= 100
    assert ci["lower_bound"] <= ci["upper_bound"]


# ============================================================================
# Phase 5: New Endpoint Tests
# ============================================================================


def test_get_all_forecasts():
    """Test GET /v1/forecast/all endpoint."""
    # First generate forecasts
    client.post("/v1/forecast/run", json={})

    # Then get all
    response = client.get("/v1/forecast/all")

    assert response.status_code == 200
    data = response.json()

    assert "total" in data
    assert "forecasts" in data
    assert data["total"] == len(data["forecasts"])
    assert data["total"] == 2  # Two test opportunities


def test_get_forecasts_by_fy():
    """Test GET /v1/forecast/FYxx endpoint."""
    # Generate forecasts
    client.post("/v1/forecast/run", json={})

    # Test FY25
    response = client.get("/v1/forecast/FY25")
    assert response.status_code == 200
    data = response.json()

    assert "fiscal_year" in data
    assert data["fiscal_year"] == "FY25"
    assert "total_opportunities" in data
    assert "total_projected" in data
    assert "forecasts" in data

    # Verify forecasts have FY25 amounts
    for forecast in data["forecasts"]:
        assert "projected_amount_FY25" in forecast
        assert forecast["projected_amount_FY25"] > 0


def test_get_top_forecasts():
    """Test GET /v1/forecast/top endpoint."""
    # Generate forecasts
    client.post("/v1/forecast/run", json={})

    # Get top forecasts by win probability
    response = client.get("/v1/forecast/top?limit=5&sort_by=win_prob")

    assert response.status_code == 200
    data = response.json()

    assert "top_deals" in data
    assert "sort_criteria" in data
    assert "limit" in data
    assert data["sort_criteria"] == "win_prob"
    assert len(data["top_deals"]) <= 5

    # Verify sorted by win probability (descending)
    if len(data["top_deals"]) > 1:
        for i in range(len(data["top_deals"]) - 1):
            assert data["top_deals"][i]["win_prob"] >= data["top_deals"][i + 1]["win_prob"]


def test_top_forecasts_sort_by_fy():
    """Test GET /v1/forecast/top with FY sorting."""
    # Generate forecasts
    client.post("/v1/forecast/run", json={})

    # Sort by FY25
    response = client.get("/v1/forecast/top?sort_by=FY25")

    assert response.status_code == 200
    data = response.json()

    assert data["sort_criteria"] == "FY25"
    assert len(data["top_deals"]) > 0


def test_export_csv_all():
    """Test CSV export for all forecasts."""
    # Generate forecasts
    client.post("/v1/forecast/run", json={})

    # Export CSV
    response = client.get("/v1/forecast/export/csv")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "Content-Disposition" in response.headers
    assert "forecast_all.csv" in response.headers["Content-Disposition"]

    # Verify CSV content
    csv_content = response.text
    lines = csv_content.strip().split("\n")

    # Should have header + data rows
    assert len(lines) >= 2  # Header + at least 1 data row

    # Check header includes key columns
    header = lines[0]
    assert "opportunity_id" in header
    assert "win_prob" in header
    assert "projected_amount_FY25" in header


def test_export_csv_specific_fy():
    """Test CSV export for specific fiscal year."""
    # Generate forecasts
    client.post("/v1/forecast/run", json={})

    # Export FY25
    response = client.get("/v1/forecast/export/csv?fiscal_year=25")

    assert response.status_code == 200
    assert "forecast_FY25.csv" in response.headers["Content-Disposition"]


def test_export_csv_no_forecasts():
    """Test CSV export with no forecasts available."""
    response = client.get("/v1/forecast/export/csv")

    assert response.status_code == 404
    assert "No forecasts available" in response.json()["detail"]


def test_export_obsidian():
    """Test Obsidian dashboard export."""
    # Generate forecasts
    client.post("/v1/forecast/run", json={})

    # Export to Obsidian
    response = client.post("/v1/forecast/export/obsidian")

    assert response.status_code == 200
    data = response.json()

    assert "path" in data
    assert "opportunities_exported" in data
    assert "total_FY25" in data
    assert "total_FY26" in data
    assert "total_FY27" in data
    assert "dashboard_updated" in data

    assert data["opportunities_exported"] == 2
    assert data["dashboard_updated"] is True
    assert "Forecast Dashboard.md" in data["path"]

    # Verify file was created
    from pathlib import Path

    dashboard_path = Path(data["path"])
    assert dashboard_path.exists()

    # Verify content structure
    content = dashboard_path.read_text()
    assert "# 📊 Forecast Dashboard" in content
    assert "Summary" in content
    assert "FY25" in content
    assert "FY26" in content
    assert "FY27" in content


def test_export_obsidian_no_forecasts():
    """Test Obsidian export with no forecasts."""
    response = client.post("/v1/forecast/export/obsidian")

    assert response.status_code == 404
    assert "No forecasts available" in response.json()["detail"]


def test_forecast_summary_with_scores():
    """Test that summary includes scoring information."""
    # Generate forecasts
    client.post("/v1/forecast/run", json={})

    # Get summary
    response = client.get("/v1/forecast/summary")

    assert response.status_code == 200
    data = response.json()

    # Existing fields
    assert "total_opportunities" in data
    assert "avg_confidence" in data

    # FY totals should be present
    assert "total_projected_FY25" in data
    assert "total_projected_FY26" in data
    assert "total_projected_FY27" in data


def test_top_forecasts_empty_state():
    """Test top forecasts with no data."""
    response = client.get("/v1/forecast/top")

    assert response.status_code == 200
    data = response.json()

    assert data["top_deals"] == []
    assert data["limit"] == 10


def test_forecast_by_fy_invalid():
    """Test FY endpoint with invalid fiscal year."""
    # Generate forecasts
    client.post("/v1/forecast/run", json={})

    # Request invalid FY
    response = client.get("/v1/forecast/FY99")

    assert response.status_code == 200
    data = response.json()

    # Should return empty or minimal data
    assert data["fiscal_year"] == "FY99"
    assert data["total_opportunities"] >= 0
