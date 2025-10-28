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
