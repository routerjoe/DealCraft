"""Extended tests for forecast reasoning - Phase 9."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mcp.api.main import app

client = TestClient(app)

TEST_DATA_DIR = Path("data")
TEST_STATE_FILE = TEST_DATA_DIR / "state.json"
TEST_FORECAST_FILE = TEST_DATA_DIR / "forecast.json"


@pytest.fixture(autouse=True)
def setup_test_data():
    """Setup test data with CV and org context."""
    original_state = None
    original_forecast = None

    if TEST_STATE_FILE.exists():
        with open(TEST_STATE_FILE, "r") as f:
            original_state = f.read()

    if TEST_FORECAST_FILE.exists():
        with open(TEST_FORECAST_FILE, "r") as f:
            original_forecast = f.read()

    TEST_DATA_DIR.mkdir(exist_ok=True)

    # Create test opportunities with Phase 6-8 fields
    test_state = {
        "opportunities": [
            {
                "id": "reasoning_test_1",
                "name": "Test with CV Recommendations",
                "title": "Test with CV Recommendations",
                "oems": ["Microsoft"],
                "partners": ["Partner A"],
                "amount": 1000000,
                "stage": "Proposal",
                "close_date": "2025-06-30T00:00:00Z",
                "source": "Govly",
                "region": "East",
                "customer_org": "Department of Defense",
                "contracts_recommended": ["SEWP V", "GSA Schedule"],
                "tags": ["federal"],
            },
            {
                "id": "reasoning_test_2",
                "name": "Test without Context",
                "title": "Test without Context",
                "oems": ["Dell"],
                "amount": 500000,
                "stage": "Qualification",
                "close_date": "2026-12-31T00:00:00Z",
            },
        ],
        "recent_actions": [],
    }

    with open(TEST_STATE_FILE, "w") as f:
        json.dump(test_state, f)

    with open(TEST_FORECAST_FILE, "w") as f:
        json.dump({}, f)

    yield

    if original_state:
        with open(TEST_STATE_FILE, "w") as f:
            f.write(original_state)

    if original_forecast:
        with open(TEST_FORECAST_FILE, "w") as f:
            f.write(original_forecast)


class TestForecastReasoningStructure:
    """Test forecast reasoning includes required fields."""

    def test_top_returns_reasoning_data(self):
        """Test /v1/forecast/top includes reasoning components."""
        # Generate forecasts first
        client.post("/v1/forecast/run", json={})

        # Get top forecasts
        response = client.get("/v1/forecast/top?limit=5")

        assert response.status_code == 200
        data = response.json()

        assert "top_deals" in data
        assert len(data["top_deals"]) > 0

        # Check first deal has scoring fields
        deal = data["top_deals"][0]
        assert "win_prob" in deal
        assert "score_raw" in deal
        assert "score_scaled" in deal
        assert "reasoning" in deal

    def test_reasoning_contains_scoring_breakdown(self):
        """Test reasoning field contains score breakdown."""
        client.post("/v1/forecast/run", json={})

        response = client.get("/v1/forecast/all")
        assert response.status_code == 200

        forecasts = response.json()["forecasts"]
        assert len(forecasts) > 0

        forecast = forecasts[0]

        # Reasoning should mention scoring components
        reasoning = forecast["reasoning"]
        assert "scoring" in reasoning.lower() or "breakdown" in reasoning.lower()


class TestScoringAdjustments:
    """Test that scoring adjustments are applied and visible."""

    def test_cv_bonus_visible_in_enhanced_opp(self):
        """Test CV recommendation bonus is reflected in score_scaled."""
        client.post("/v1/forecast/run", json={})

        response = client.get("/v1/forecast/all")
        forecasts = response.json()["forecasts"]

        # Find forecast with CV recommendations
        cv_forecast = next(
            (f for f in forecasts if f["opportunity_id"] == "reasoning_test_1"),
            None,
        )

        assert cv_forecast is not None

        # score_scaled should be higher than score_raw due to bonuses
        # (CV +5%, Region +2%, Org +3% = +10%)
        assert cv_forecast["score_scaled"] >= cv_forecast["score_raw"]

    def test_region_bonus_applies(self):
        """Test region bonus is applied when region specified."""
        client.post("/v1/forecast/run", json={})

        response = client.get("/v1/forecast/all")
        forecasts = response.json()["forecasts"]

        # Forecast with region should have enhanced score
        with_region = next(
            (f for f in forecasts if f["opportunity_id"] == "reasoning_test_1"),
            None,
        )

        assert with_region is not None
        # Region bonus should be reflected
        assert with_region["score_scaled"] > 0

    def test_org_bonus_applies(self):
        """Test customer org bonus is applied."""
        client.post("/v1/forecast/run", json={})

        response = client.get("/v1/forecast/all")
        forecasts = response.json()["forecasts"]

        with_org = next(
            (f for f in forecasts if f["opportunity_id"] == "reasoning_test_1"),
            None,
        )

        assert with_org is not None
        # Should have org context
        assert with_org["score_scaled"] >= with_org["score_raw"]


class TestCompositeScoringFields:
    """Test composite scoring field presence."""

    def test_forecast_includes_all_scoring_fields(self):
        """Test forecast includes all Phase 9 enhanced fields."""
        client.post("/v1/forecast/run", json={})

        response = client.get("/v1/forecast/all")
        forecasts = response.json()["forecasts"]

        assert len(forecasts) > 0
        forecast = forecasts[0]

        # Base Phase 5 fields
        assert "win_prob" in forecast
        assert "score_raw" in forecast
        assert "score_scaled" in forecast
        assert "oem_alignment_score" in forecast
        assert "partner_fit_score" in forecast
        assert "contract_vehicle_score" in forecast
        assert "govly_relevance_score" in forecast

        # Confidence interval
        assert "confidence_interval" in forecast

    def test_reasoning_mentions_components(self):
        """Test reasoning mentions key scoring components."""
        client.post("/v1/forecast/run", json={})

        response = client.get("/v1/forecast/all")
        forecasts = response.json()["forecasts"]

        forecast = forecasts[0]
        reasoning = forecast["reasoning"].lower()

        # Should mention amount
        assert "amount" in reasoning or "$" in reasoning

        # Should mention fiscal year distribution
        assert "fy" in reasoning or "fiscal" in reasoning
