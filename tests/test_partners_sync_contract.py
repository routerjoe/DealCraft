"""Tests for partner tier sync functionality"""

import json
import os

import pytest
from httpx import AsyncClient

from mcp.api.main import app
from mcp.core.partners_sync import PartnerTierRecord, PartnerTierSync


@pytest.fixture
def temp_partners_dir(tmp_path):
    """Create temporary partners directory with test data"""
    partners_dir = tmp_path / "data" / "partners"
    partners_dir.mkdir(parents=True)

    # Create test CSV
    csv_file = partners_dir / "partners_test.csv"
    csv_file.write_text(
        "name,tier,program,oem,poc,notes\n"
        "Red River Technology,Gold,Cisco PTP,Cisco,John Doe,Test partner\n"
        "Tech Solutions,Platinum,Nutanix Elevate,Nutanix,Jane Smith,Premium tier\n"
    )

    # Create test JSON
    json_file = partners_dir / "partners_test.json"
    json_data = {
        "partners": [
            {
                "name": "Cloud Partners Inc",
                "tier": "Silver",
                "program": "AWS Partner Network",
                "oem": "AWS",
                "poc": "Bob Johnson",
                "notes": "Cloud specialist",
            }
        ]
    }
    json_file.write_text(json.dumps(json_data, indent=2))

    return partners_dir


@pytest.fixture
def temp_store(tmp_path):
    """Create temporary OEM store"""
    store_path = tmp_path / "data" / "oems.json"
    store_path.parent.mkdir(parents=True, exist_ok=True)

    # Create empty store
    store_path.write_text("[]")

    return store_path


@pytest.fixture
def temp_vault(tmp_path):
    """Create temporary Obsidian vault"""
    vault_path = tmp_path / "vault"
    vault_path.mkdir()
    return vault_path


def test_partner_tier_record():
    """Test PartnerTierRecord normalization"""
    record = PartnerTierRecord(
        name="  Test Partner  ", tier="platinum", program="Test Program", oem="cisco", poc="Test POC", notes="Test notes"
    )

    assert record.name == "Test Partner"
    assert record.tier == "Platinum"
    assert record.oem == "Cisco"
    assert record.poc == "Test POC"


def test_load_csv(temp_partners_dir, tmp_path):
    """Test loading partner data from CSV"""
    # Change to temp directory
    original_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        sync = PartnerTierSync(store_path=str(tmp_path / "data" / "oems.json"))
        records = sync.load_sources()

        assert len(records) == 3  # 2 from CSV + 1 from JSON
        assert any(r.name == "Red River Technology" for r in records)
        assert any(r.name == "Cloud Partners Inc" for r in records)
    finally:
        os.chdir(original_cwd)


def test_validate_records():
    """Test record validation"""
    sync = PartnerTierSync()

    # Valid records
    valid_records = [PartnerTierRecord(name="Test", tier="Gold", program="Test Program", oem="Cisco")]
    is_valid, errors = sync.validate(valid_records)
    assert is_valid
    assert len(errors) == 0

    # Invalid records
    invalid_records = [PartnerTierRecord(name="", tier="Gold", program="Test Program", oem="Cisco")]
    is_valid, errors = sync.validate(invalid_records)
    assert not is_valid
    assert len(errors) > 0


def test_plan_updates(temp_store, tmp_path):
    """Test diff computation"""
    # Create store with existing data
    existing_data = [
        {
            "name": "Existing Partner",
            "tier": "Gold",
            "program": "Test Program",
            "oem": "Cisco",
            "poc": None,
            "notes": None,
            "updated_at": "2025-01-01T00:00:00Z",
            "created_at": "2025-01-01T00:00:00Z",
        }
    ]
    temp_store.write_text(json.dumps(existing_data))

    sync = PartnerTierSync(store_path=str(temp_store))

    # New and updated records
    records = [
        PartnerTierRecord(
            name="Existing Partner",
            tier="Platinum",  # Updated
            program="Test Program",
            oem="Cisco",
        ),
        PartnerTierRecord(name="New Partner", tier="Silver", program="New Program", oem="Nutanix"),
    ]

    plan = sync.plan_updates(records)

    assert len(plan["added"]) == 1
    assert len(plan["updated"]) == 1
    assert plan["added"][0]["name"] == "New Partner"
    assert plan["updated"][0]["name"] == "Existing Partner"


def test_apply_updates_dry_run(temp_store, tmp_path):
    """Test dry run doesn't write"""
    sync = PartnerTierSync(store_path=str(temp_store))

    records = [PartnerTierRecord(name="Test Partner", tier="Gold", program="Test Program", oem="Cisco")]

    plan = sync.plan_updates(records)
    result = sync.apply_updates(plan, dry_run=True)

    assert result["dry_run"] is True
    assert result["applied"] is False

    # Store should still be empty
    store_data = json.loads(temp_store.read_text())
    assert len(store_data) == 0


def test_apply_updates_write(temp_store, tmp_path):
    """Test actual write"""
    sync = PartnerTierSync(store_path=str(temp_store))

    records = [PartnerTierRecord(name="Test Partner", tier="Gold", program="Test Program", oem="Cisco")]

    plan = sync.plan_updates(records)
    result = sync.apply_updates(plan, dry_run=False)

    assert result["dry_run"] is False
    assert result["applied"] is True

    # Store should have the record
    store_data = json.loads(temp_store.read_text())
    assert len(store_data) == 1
    assert store_data[0]["name"] == "Test Partner"


def test_export_obsidian(temp_store, temp_vault, tmp_path):
    """Test Obsidian markdown export"""
    # Create store with data
    test_data = [
        {
            "name": "Partner 1",
            "tier": "Gold",
            "program": "Cisco PTP",
            "oem": "Cisco",
            "poc": "John Doe",
            "notes": "Test notes",
            "updated_at": "2025-01-01T00:00:00Z",
            "created_at": "2025-01-01T00:00:00Z",
        },
        {
            "name": "Partner 2",
            "tier": "Platinum",
            "program": "Nutanix Elevate",
            "oem": "Nutanix",
            "poc": None,
            "notes": None,
            "updated_at": "2025-01-01T00:00:00Z",
            "created_at": "2025-01-01T00:00:00Z",
        },
    ]
    temp_store.write_text(json.dumps(test_data))

    sync = PartnerTierSync(vault_root=temp_vault, store_path=str(temp_store))
    result = sync.export_obsidian()

    assert result["status"] == "success"
    assert result["oems_count"] == 2
    assert len(result["files_written"]) == 2

    # Check files were created
    oems_dir = temp_vault / "30 Hubs" / "OEMs"
    assert oems_dir.exists()
    assert (oems_dir / "Cisco.md").exists()
    assert (oems_dir / "Nutanix.md").exists()

    # Check content
    cisco_content = (oems_dir / "Cisco.md").read_text()
    assert "Partner 1" in cisco_content
    assert "Gold" in cisco_content
    assert "John Doe" in cisco_content


@pytest.mark.asyncio
async def test_partners_endpoints_contract():
    """Test API endpoints basic contract"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Test /tiers endpoint
        r1 = await ac.get("/v1/partners/tiers")
        assert r1.status_code == 200
        assert isinstance(r1.json(), list)
        assert "x-request-id" in r1.headers
        assert "x-latency-ms" in r1.headers

        # Test /sync endpoint
        r2 = await ac.post("/v1/partners/sync", json={"dry_run": True})
        assert r2.status_code == 200
        body = r2.json()
        assert "dry_run" in body
        assert "added" in body
        assert "updated" in body
        assert "unchanged" in body
        assert "x-request-id" in r2.headers
        assert "x-latency-ms" in r2.headers

        # Test /export/obsidian endpoint (will fail without VAULT_ROOT but should return proper error)
        r3 = await ac.get("/v1/partners/export/obsidian")
        # Either success or proper error response
        assert r3.status_code in [200, 500]
        assert "x-request-id" in r3.headers
        assert "x-latency-ms" in r3.headers
