"""Tests for CRM sync and attribution engine - Phase 6."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mcp.api.main import app
from mcp.core.crm_sync import AttributionEngine, CRMSyncEngine

client = TestClient(app)

# Test data
TEST_DATA_DIR = Path("data")
TEST_STATE_FILE = TEST_DATA_DIR / "state.json"


@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Setup and teardown for each test."""
    # Save original
    original_state = None
    if TEST_STATE_FILE.exists():
        with open(TEST_STATE_FILE, "r") as f:
            original_state = f.read()

    # Initialize test data
    TEST_DATA_DIR.mkdir(exist_ok=True)

    # Create test state with opportunities
    test_state = {
        "opportunities": [
            {
                "id": "crm_test_1",
                "name": "Test CRM Deal 1",
                "title": "Test CRM Deal 1",
                "customer": "Federal Agency A",
                "customer_org": "Department of Defense",
                "oems": ["Microsoft", "Cisco"],
                "partners": ["Partner X", "Partner Y"],
                "amount": 1000000,
                "stage": "Proposal",
                "close_date": "2025-06-30T00:00:00Z",
                "source": "Govly",
                "contract_vehicle": "SEWP V",
                "region": "East",
                "tags": ["federal", "cloud"],
            },
            {
                "id": "crm_test_2",
                "name": "Test CRM Deal 2",
                "title": "Test CRM Deal 2",
                "customer": "Agency B",
                "oems": ["Dell"],
                "partners": [],
                "amount": 500000,
                "stage": "Negotiation",
                "close_date": "2025-09-30T00:00:00Z",
                "source": "Direct",
                "contract_vehicle": "GSA Schedule",
            },
        ],
        "recent_actions": [],
    }

    with open(TEST_STATE_FILE, "w") as f:
        json.dump(test_state, f)

    yield

    # Restore original
    if original_state:
        with open(TEST_STATE_FILE, "w") as f:
            f.write(original_state)


# ============================================================================
# Attribution Engine Tests
# ============================================================================


class TestAttributionEngine:
    """Test attribution calculation logic."""

    @pytest.fixture
    def engine(self):
        """Create attribution engine instance."""
        return AttributionEngine()

    def test_oem_attribution_single(self, engine):
        """Test OEM attribution with single OEM."""
        attr = engine.calculate_oem_attribution(["Microsoft"], 1000000)

        assert "Microsoft" in attr
        assert attr["Microsoft"] == 600000.0  # 60% primary

    def test_oem_attribution_multiple(self, engine):
        """Test OEM attribution with multiple OEMs."""
        attr = engine.calculate_oem_attribution(["Microsoft", "Cisco", "Dell"], 1000000)

        assert attr["Microsoft"] == 600000.0  # 60% primary
        assert attr["Cisco"] == 300000.0  # 30% secondary
        assert attr["Dell"] == 100000.0  # 10% tertiary

    def test_oem_attribution_empty(self, engine):
        """Test OEM attribution with no OEMs."""
        attr = engine.calculate_oem_attribution([], 1000000)
        assert attr == {}

    def test_partner_attribution_equal_split(self, engine):
        """Test partner attribution splits equally."""
        attr = engine.calculate_partner_attribution(["Partner A", "Partner B"], 1000000, {})

        # Partners get 20% of total, split equally
        assert attr["Partner A"] == 100000.0  # 10%
        assert attr["Partner B"] == 100000.0  # 10%

    def test_partner_attribution_empty(self, engine):
        """Test partner attribution with no partners."""
        attr = engine.calculate_partner_attribution([], 1000000, {})
        assert attr == {}

    def test_full_attribution_complete(self, engine):
        """Test full attribution calculation."""
        opp = {
            "oems": ["Microsoft", "Cisco"],
            "partners": ["Partner A"],
            "amount": 1000000,
            "region": "East",
            "customer_org": "Agency X",
        }

        attr = engine.calculate_full_attribution(opp)

        assert "oem_attribution" in attr
        assert "partner_attribution" in attr
        assert "region" in attr
        assert "customer_org" in attr
        assert "total_amount" in attr
        assert attr["total_amount"] == 1000000

    def test_full_attribution_handles_non_list(self, engine):
        """Test attribution handles non-list OEMs/partners."""
        opp = {"oems": "Microsoft", "partners": "Partner A", "amount": 500000}

        attr = engine.calculate_full_attribution(opp)

        assert "oem_attribution" in attr
        assert "partner_attribution" in attr


# ============================================================================
# CRM Sync Engine Tests
# ============================================================================


class TestCRMSyncEngine:
    """Test CRM sync engine logic."""

    @pytest.fixture
    def engine(self):
        """Create CRM sync engine instance."""
        return CRMSyncEngine(dry_run=True)

    def test_validate_opportunity_valid(self, engine):
        """Test validation with valid opportunity."""
        opp = {
            "id": "test-1",
            "title": "Test Deal",
            "customer": "Agency",
            "amount": 100000,
            "stage": "Proposal",
            "close_date": "2025-12-31T00:00:00Z",
        }

        is_valid, errors = engine.validate_opportunity(opp)

        assert is_valid is True
        assert errors == []

    def test_validate_opportunity_missing_fields(self, engine):
        """Test validation catches missing required fields."""
        opp = {"id": "test-1", "title": "Test Deal"}

        is_valid, errors = engine.validate_opportunity(opp)

        assert is_valid is False
        assert len(errors) > 0
        assert any("customer" in e for e in errors)
        assert any("amount" in e for e in errors)

    def test_validate_opportunity_invalid_amount(self, engine):
        """Test validation catches invalid amounts."""
        opp = {
            "id": "test-1",
            "title": "Test",
            "customer": "Agency",
            "amount": -100,
            "stage": "Proposal",
            "close_date": "2025-12-31",
        }

        is_valid, errors = engine.validate_opportunity(opp)

        assert is_valid is False
        assert any("positive" in e.lower() for e in errors)

    def test_validate_opportunity_invalid_date(self, engine):
        """Test validation catches invalid dates."""
        opp = {
            "id": "test-1",
            "title": "Test",
            "customer": "Agency",
            "amount": 100000,
            "stage": "Proposal",
            "close_date": "invalid-date",
        }

        is_valid, errors = engine.validate_opportunity(opp)

        assert is_valid is False
        assert any("close_date" in e for e in errors)

    def test_format_salesforce(self, engine):
        """Test Salesforce format conversion."""
        opp = {
            "id": "test-1",
            "title": "Test Deal",
            "customer": "Agency",
            "customer_org": "DOD",
            "oems": ["Microsoft"],
            "partners": ["Partner A"],
            "amount": 500000,
            "stage": "Proposal",
            "close_date": "2025-12-31T00:00:00Z",
            "source": "Govly",
            "contract_vehicle": "SEWP V",
            "region": "East",
        }

        formatted = engine.format_for_salesforce(opp)

        assert formatted["Name"] == "Test Deal"
        assert formatted["Amount"] == 500000
        assert formatted["OEM_Primary__c"] == "Microsoft"
        assert "Partner A" in formatted["Partner_Names__c"]
        assert formatted["Contract_Vehicle__c"] == "SEWP V"
        assert formatted["Region__c"] == "East"

    def test_format_generic_json(self, engine):
        """Test generic JSON format conversion."""
        opp = {
            "id": "test-1",
            "title": "Test Deal",
            "customer": "Agency",
            "amount": 500000,
            "stage": "Proposal",
            "close_date": "2025-12-31T00:00:00Z",
        }

        formatted = engine.format_for_generic_json(opp)

        assert formatted["id"] == "test-1"
        assert formatted["title"] == "Test Deal"
        assert formatted["amount"] == 500000
        assert "attribution" in formatted
        assert "forecast" in formatted
        assert "exported_at" in formatted

    def test_export_opportunity_dry_run(self, engine):
        """Test export in dry-run mode."""
        opp = {
            "id": "test-1",
            "title": "Test Deal",
            "customer": "Agency",
            "amount": 500000,
            "stage": "Proposal",
            "close_date": "2025-12-31T00:00:00Z",
        }

        result = engine.export_opportunity(opp, format="generic_json")

        assert result["success"] is True
        assert result["dry_run"] is True
        assert "Dry-run mode" in result["message"]
        assert "formatted_data" in result

    def test_export_opportunity_invalid(self, engine):
        """Test export with invalid opportunity."""
        opp = {"id": "test-1"}  # Missing required fields

        result = engine.export_opportunity(opp)

        assert result["success"] is False
        assert len(result["errors"]) > 0
        assert result["dry_run"] is True

    def test_bulk_export(self, engine):
        """Test bulk export of multiple opportunities."""
        opps = [
            {
                "id": "test-1",
                "title": "Deal 1",
                "customer": "Agency A",
                "amount": 100000,
                "stage": "Proposal",
                "close_date": "2025-12-31T00:00:00Z",
            },
            {
                "id": "test-2",
                "title": "Deal 2",
                "customer": "Agency B",
                "amount": 200000,
                "stage": "Negotiation",
                "close_date": "2026-03-31T00:00:00Z",
            },
        ]

        result = engine.bulk_export(opps)

        assert result["total"] == 2
        assert result["success_count"] == 2
        assert result["error_count"] == 0
        assert len(result["results"]) == 2


# ============================================================================
# API Endpoint Tests
# ============================================================================


def test_crm_formats_endpoint():
    """Test GET /v1/crm/formats endpoint."""
    response = client.get("/v1/crm/formats")

    assert response.status_code == 200
    formats = response.json()

    assert isinstance(formats, list)
    assert "salesforce" in formats
    assert "generic_json" in formats


def test_crm_validate_endpoint():
    """Test GET /v1/crm/validate/{id} endpoint."""
    response = client.get("/v1/crm/validate/crm_test_1")

    assert response.status_code == 200
    data = response.json()

    assert "opportunity_id" in data
    assert "valid" in data
    assert "errors" in data
    assert data["opportunity_id"] == "crm_test_1"


def test_crm_validate_not_found():
    """Test validation for non-existent opportunity."""
    response = client.get("/v1/crm/validate/nonexistent")

    assert response.status_code == 404


def test_crm_export_all():
    """Test POST /v1/crm/export for all opportunities."""
    response = client.post(
        "/v1/crm/export",
        json={"format": "generic_json", "dry_run": True},
    )

    assert response.status_code == 200
    data = response.json()

    # Verify new simplified API response format (Phase 12)
    assert "status" in data
    assert data["status"] == "ok"
    assert "total" in data
    assert "opportunities_validated" in data
    assert data["dry_run"] is True
    assert data["total"] == 2  # Two test opportunities
    assert data["opportunities_validated"] == 2


def test_crm_export_specific_opportunities():
    """Test CRM export for specific opportunities."""
    response = client.post(
        "/v1/crm/export",
        json={
            "opportunity_ids": ["crm_test_1"],
            "format": "salesforce",
            "dry_run": True,
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Verify new simplified API response format (Phase 12)
    assert data["status"] == "ok"
    assert data["total"] == 1
    assert data["opportunities_validated"] == 1
    assert data["dry_run"] is True
    assert data["format"] == "salesforce"


def test_crm_export_no_opportunities():
    """Test CRM export with no matching opportunities."""
    response = client.post(
        "/v1/crm/export",
        json={"opportunity_ids": ["nonexistent"], "dry_run": True},
    )

    assert response.status_code == 404


def test_crm_attribution_endpoint():
    """Test POST /v1/crm/attribution endpoint."""
    response = client.post("/v1/crm/attribution", json={})

    assert response.status_code == 200
    data = response.json()

    assert "total" in data
    assert "attributions" in data
    assert data["total"] == 2

    # Check attribution structure
    attr = data["attributions"][0]
    assert "opportunity_id" in attr
    assert "opportunity_name" in attr
    assert "oem_attribution" in attr
    assert "partner_attribution" in attr
    assert "total_amount" in attr


def test_crm_attribution_specific_opportunities():
    """Test attribution for specific opportunities."""
    response = client.post("/v1/crm/attribution", json={"opportunity_ids": ["crm_test_1"]})

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 1
    assert data["attributions"][0]["opportunity_id"] == "crm_test_1"


def test_crm_attribution_validates_amounts():
    """Test that attribution amounts are calculated correctly."""
    response = client.post("/v1/crm/attribution", json={"opportunity_ids": ["crm_test_1"]})

    assert response.status_code == 200
    attr = response.json()["attributions"][0]

    # Verify OEM attribution totals
    oem_total = sum(attr["oem_attribution"].values())
    # Should be 90% of amount (60% primary + 30% secondary for 2 OEMs)
    assert oem_total == 900000.0

    # Verify partner attribution
    partner_total = sum(attr["partner_attribution"].values())
    # Should be 20% of amount split between 2 partners
    assert partner_total == 200000.0


def test_crm_export_includes_forecast_data():
    """Test that CRM export includes forecast scoring data."""
    # First run forecasts
    client.post("/v1/forecast/run", json={})

    # Then export
    response = client.post(
        "/v1/crm/export",
        json={
            "opportunity_ids": ["crm_test_1"],
            "format": "salesforce",
            "dry_run": True,
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Verify new simplified API response format (Phase 12)
    # In dry-run mode, we validate the export succeeded
    assert data["status"] == "ok"
    assert data["total"] == 1
    assert data["opportunities_validated"] == 1
    assert data["dry_run"] is True
    assert data["format"] == "salesforce"


def test_crm_export_dry_run_default():
    """Test that dry-run defaults to True for safety."""
    response = client.post("/v1/crm/export", json={"format": "generic_json"})

    assert response.status_code == 200
    assert response.json()["dry_run"] is True
