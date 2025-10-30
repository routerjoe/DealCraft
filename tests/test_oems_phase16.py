"""Tests for OEM Partner Intelligence - Phase 16."""

from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mcp.api.main import app
from mcp.core.oems import OEMPartner, OEMStore


@pytest.fixture
def temp_oems_file(tmp_path):
    """Create a temporary OEMs file for testing."""
    test_file = tmp_path / "test_oems.json"
    yield str(test_file)
    # Cleanup
    if test_file.exists():
        test_file.unlink()


@pytest.fixture
def oem_store(temp_oems_file):
    """Create an OEMStore instance for testing."""
    return OEMStore(storage_path=temp_oems_file)


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestOEMStore:
    """Test OEMStore functionality."""

    def test_load_create_store(self, temp_oems_file):
        """Test loading and creating a new store."""
        store = OEMStore(storage_path=temp_oems_file)
        assert store.partners == []
        assert Path(temp_oems_file).exists()

    def test_add_or_update_new(self, oem_store):
        """Test adding a new OEM partner."""
        partner = OEMPartner(oem_name="Dell Technologies", tier="Platinum", partner_poc="John Doe", notes="Primary hardware vendor")

        result = oem_store.add_or_update(partner)

        assert result.oem_name == "Dell Technologies"
        assert result.tier == "Platinum"
        assert result.partner_poc == "John Doe"
        assert len(oem_store.partners) == 1

    def test_add_or_update_existing(self, oem_store):
        """Test updating an existing OEM partner."""
        # Add initial partner
        partner1 = OEMPartner(oem_name="HP Inc", tier="Gold", partner_poc="Jane Smith", notes="Initial notes")
        oem_store.add_or_update(partner1)

        # Update the same partner
        partner2 = OEMPartner(oem_name="HP Inc", tier="Platinum", partner_poc="Jane Smith", notes="Updated notes")
        result = oem_store.add_or_update(partner2)

        assert result.tier == "Platinum"
        assert result.notes == "Updated notes"
        assert len(oem_store.partners) == 1

    def test_get_existing(self, oem_store):
        """Test retrieving an existing OEM partner."""
        partner = OEMPartner(oem_name="Cisco Systems", tier="Diamond", partner_poc="Bob Johnson", notes="Networking partner")
        oem_store.add_or_update(partner)

        result = oem_store.get("Cisco Systems")

        assert result is not None
        assert result.oem_name == "Cisco Systems"
        assert result.tier == "Diamond"

    def test_get_nonexistent(self, oem_store):
        """Test retrieving a non-existent OEM partner."""
        result = oem_store.get("Nonexistent OEM")
        assert result is None

    def test_get_all(self, oem_store):
        """Test retrieving all OEM partners."""
        partners = [
            OEMPartner(oem_name="Dell", tier="Platinum", partner_poc="Alice", notes="Note 1"),
            OEMPartner(oem_name="HP", tier="Gold", partner_poc="Bob", notes="Note 2"),
            OEMPartner(oem_name="Cisco", tier="Diamond", partner_poc="Charlie", notes="Note 3"),
        ]

        for p in partners:
            oem_store.add_or_update(p)

        all_partners = oem_store.get_all()
        assert len(all_partners) == 3
        assert all(isinstance(p, OEMPartner) for p in all_partners)

    def test_persistence(self, temp_oems_file):
        """Test that data persists across store instances."""
        # Create first store and add data
        store1 = OEMStore(storage_path=temp_oems_file)
        partner = OEMPartner(oem_name="Lenovo", tier="Silver", partner_poc="Eve Brown", notes="PC vendor")
        store1.add_or_update(partner)

        # Create second store and verify data persists
        store2 = OEMStore(storage_path=temp_oems_file)
        assert len(store2.partners) == 1
        assert store2.partners[0].oem_name == "Lenovo"

    def test_markdown_export_empty(self, oem_store):
        """Test markdown export with no partners."""
        markdown = oem_store.export_markdown()
        assert "# OEM Partners" in markdown
        assert "No OEM partners recorded" in markdown

    def test_markdown_export_format(self, oem_store):
        """Test markdown export format."""
        partner = OEMPartner(oem_name="Microsoft", tier="Platinum", partner_poc="David Lee", notes="Software licensing partner")
        oem_store.add_or_update(partner)

        markdown = oem_store.export_markdown()

        assert "# OEM Partners" in markdown
        assert "## OEM: Microsoft" in markdown
        assert "Tier: Platinum" in markdown
        assert "POC: David Lee" in markdown
        assert "Notes:" in markdown
        assert "Software licensing partner" in markdown
        assert "Updated:" in markdown

    def test_markdown_export_multiple_sorted(self, oem_store):
        """Test markdown export with multiple partners sorted by name."""
        partners = [
            OEMPartner(oem_name="Zebra", tier="Gold", partner_poc="Z Person", notes="Last"),
            OEMPartner(oem_name="Apple", tier="Platinum", partner_poc="A Person", notes="First"),
            OEMPartner(oem_name="Microsoft", tier="Diamond", partner_poc="M Person", notes="Middle"),
        ]

        for p in partners:
            oem_store.add_or_update(p)

        markdown = oem_store.export_markdown()

        # Check that partners appear in alphabetical order
        apple_pos = markdown.find("## OEM: Apple")
        microsoft_pos = markdown.find("## OEM: Microsoft")
        zebra_pos = markdown.find("## OEM: Zebra")

        assert apple_pos < microsoft_pos < zebra_pos


class TestOEMEndpoints:
    """Test OEM API endpoints."""

    def test_get_all_empty(self, client):
        """Test GET /v1/oems/all returns successfully."""
        response = client.get("/v1/oems/all")
        assert response.status_code == 200
        # Note: May contain data from other tests due to shared store
        assert isinstance(response.json(), list)
        assert "x-request-id" in response.headers
        assert "x-latency-ms" in response.headers

    def test_add_oem(self, client):
        """Test POST /v1/oems/add to create a new partner."""
        data = {"oem_name": "Oracle", "tier": "Gold", "partner_poc": "Sarah Connor", "notes": "Database solutions"}

        response = client.post("/v1/oems/add", json=data)
        assert response.status_code == 201

        result = response.json()
        assert result["oem_name"] == "Oracle"
        assert result["tier"] == "Gold"
        assert result["partner_poc"] == "Sarah Connor"
        assert result["notes"] == "Database solutions"
        assert "updated_at" in result
        assert "x-request-id" in response.headers

    def test_add_oem_minimal(self, client):
        """Test POST /v1/oems/add with minimal data."""
        data = {"oem_name": "IBM", "tier": "Silver"}

        response = client.post("/v1/oems/add", json=data)
        assert response.status_code == 201

        result = response.json()
        assert result["oem_name"] == "IBM"
        assert result["tier"] == "Silver"
        assert result["partner_poc"] is None
        assert result["notes"] is None

    def test_get_oem_by_name(self, client):
        """Test GET /v1/oems/{name} to retrieve a specific partner."""
        # First add a partner
        data = {"oem_name": "VMware", "tier": "Platinum", "partner_poc": "Tom Anderson", "notes": "Virtualization expert"}
        client.post("/v1/oems/add", json=data)

        # Retrieve it
        response = client.get("/v1/oems/VMware")
        assert response.status_code == 200

        result = response.json()
        assert result["oem_name"] == "VMware"
        assert result["tier"] == "Platinum"

    def test_get_oem_not_found(self, client):
        """Test GET /v1/oems/{name} for non-existent partner."""
        response = client.get("/v1/oems/NonExistentOEM")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_export_obsidian(self, client):
        """Test GET /v1/oems/export/obsidian."""
        # Add a test partner
        data = {"oem_name": "NetApp", "tier": "Gold", "partner_poc": "Lisa Simpson", "notes": "Storage solutions provider"}
        client.post("/v1/oems/add", json=data)

        # Export markdown
        response = client.get("/v1/oems/export/obsidian")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"

        markdown = response.text
        assert "# OEM Partners" in markdown
        assert "## OEM: NetApp" in markdown
        assert "Tier: Gold" in markdown
        assert "POC: Lisa Simpson" in markdown
        assert "Storage solutions provider" in markdown

    def test_system_contracts_preserved(self, client):
        """Test that system contracts are preserved."""
        # Test x-request-id and x-latency-ms headers
        response = client.get("/v1/oems/all")
        assert "x-request-id" in response.headers
        assert "x-latency-ms" in response.headers

        # Test /v1/info includes new endpoints
        info_response = client.get("/v1/info")
        assert info_response.status_code == 200
        endpoints = info_response.json()["endpoints"]
        assert "/v1/oems/all" in endpoints
        assert "/v1/oems/add" in endpoints
        assert "/v1/oems/{name}" in endpoints
        assert "/v1/oems/export/obsidian" in endpoints

    def test_healthz_unchanged(self, client):
        """Test that healthz endpoint is unchanged."""
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestOEMDataModel:
    """Test OEMPartner data model."""

    def test_create_partner_full(self):
        """Test creating a partner with all fields."""
        partner = OEMPartner(oem_name="Adobe", tier="Platinum", partner_poc="John Smith", notes="Creative software partner")

        assert partner.oem_name == "Adobe"
        assert partner.tier == "Platinum"
        assert partner.partner_poc == "John Smith"
        assert partner.notes == "Creative software partner"
        assert isinstance(partner.updated_at, datetime)

    def test_create_partner_minimal(self):
        """Test creating a partner with minimal fields."""
        partner = OEMPartner(oem_name="SAP", tier="Gold")

        assert partner.oem_name == "SAP"
        assert partner.tier == "Gold"
        assert partner.partner_poc is None
        assert partner.notes is None
        assert isinstance(partner.updated_at, datetime)

    def test_partner_serialization(self):
        """Test partner serialization to JSON."""
        partner = OEMPartner(oem_name="Salesforce", tier="Diamond", partner_poc="Mary Johnson", notes="CRM platform")

        data = partner.model_dump(mode="json")
        assert data["oem_name"] == "Salesforce"
        assert "updated_at" in data


def test_integration_full_workflow(client):
    """Test complete workflow from add to export."""
    # Add multiple partners with unique names for this test
    partners = [
        {"oem_name": "Integration Test Red Hat", "tier": "Platinum", "partner_poc": "Alice", "notes": "Open source"},
        {"oem_name": "Integration Test AWS", "tier": "Diamond", "partner_poc": "Bob", "notes": "Cloud services"},
        {"oem_name": "Integration Test Google", "tier": "Platinum", "partner_poc": "Charlie", "notes": "Cloud platform"},
    ]

    for p in partners:
        response = client.post("/v1/oems/add", json=p)
        assert response.status_code == 201

    # Get all partners (may include data from other tests)
    response = client.get("/v1/oems/all")
    assert response.status_code == 200
    all_partners = response.json()
    # Verify our test partners are in the results
    test_names = {p["oem_name"] for p in partners}
    returned_names = {p["oem_name"] for p in all_partners}
    assert test_names.issubset(returned_names), "Not all test partners found in results"

    # Get specific partner
    response = client.get("/v1/oems/Integration%20Test%20AWS")
    assert response.status_code == 200
    assert response.json()["tier"] == "Diamond"

    # Export markdown
    response = client.get("/v1/oems/export/obsidian")
    assert response.status_code == 200
    markdown = response.text
    assert "## OEM: Integration Test AWS" in markdown
    assert "## OEM: Integration Test Google" in markdown
    assert "## OEM: Integration Test Red Hat" in markdown
