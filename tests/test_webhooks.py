"""Tests for Govly and Radar webhook endpoints."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mcp.api.main import app

client = TestClient(app)

# Test data directory
TEST_DATA_DIR = Path("data")
TEST_STATE_FILE = TEST_DATA_DIR / "state.json"


@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Setup and teardown for each test."""
    # Save original state if exists
    original_state = None
    if TEST_STATE_FILE.exists():
        with open(TEST_STATE_FILE, "r") as f:
            original_state = f.read()

    # Initialize clean state
    TEST_DATA_DIR.mkdir(exist_ok=True)
    with open(TEST_STATE_FILE, "w") as f:
        json.dump({"opportunities": [], "recent_actions": []}, f)

    yield

    # Restore original state
    if original_state:
        with open(TEST_STATE_FILE, "w") as f:
            f.write(original_state)

    # Clean up test opportunity files (both Triage and FY directories)
    base_dir = Path("obsidian/40 Projects/Opportunities")
    for subdir in ["Triage", "FY2026"]:
        dir_path = base_dir / subdir
        if dir_path.exists():
            for file in dir_path.glob("govly_*.md"):
                file.unlink()
            for file in dir_path.glob("radar_*.md"):
                file.unlink()


def test_govly_webhook_success():
    """Test successful Govly webhook ingestion."""
    payload = {
        "event_id": "test_12345",
        "event_type": "opportunity",
        "title": "Test IT Services RFQ",
        "description": "Federal IT services contract",
        "estimated_amount": 500000,
        "agency": "Federal Agency A",
        "posted_date": "2025-10-28T00:00:00Z",
        "close_date": "2025-11-15T23:59:59Z",
        "source_url": "https://govly.example.com/opp/12345",
    }

    response = client.post("/v1/govly/webhook", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["opportunity_id"] == "govly_test_12345"
    assert "Govly opportunity" in data["message"]


def test_govly_webhook_creates_state_entry():
    """Test that Govly webhook creates opportunity in state.json."""
    payload = {
        "event_id": "state_test_456",
        "event_type": "opportunity",
        "title": "State Test Opportunity",
        "description": "Testing state creation",
        "estimated_amount": 250000,
        "agency": "DOD",
        "posted_date": "2025-10-28T00:00:00Z",
        "close_date": "2025-12-01T23:59:59Z",
        "source_url": "https://govly.example.com/opp/456",
    }

    response = client.post("/v1/govly/webhook", json=payload)
    assert response.status_code == 200

    # Check state.json
    with open(TEST_STATE_FILE, "r") as f:
        state = json.load(f)

    assert len(state["opportunities"]) == 1
    opp = state["opportunities"][0]
    assert opp["id"] == "govly_state_test_456"
    assert opp["title"] == "State Test Opportunity"
    assert opp["source"] == "govly"
    # FY routing: Dec 2025 close_date routes to FY2026, so triage=False
    assert opp["triage"] is False
    assert opp["fy"] == "FY2026"
    assert opp["estimated_amount"] == 250000


def test_govly_webhook_creates_markdown():
    """Test that Govly webhook creates opportunity markdown file."""
    payload = {
        "event_id": "md_test_789",
        "event_type": "opportunity",
        "title": "Markdown Test",
        "description": "Testing markdown creation",
        "estimated_amount": 100000,
        "agency": "NASA",
        "posted_date": "2025-10-28T00:00:00Z",
        "close_date": "2025-11-30T23:59:59Z",
        "source_url": "https://govly.example.com/opp/789",
    }

    response = client.post("/v1/govly/webhook", json=payload)
    assert response.status_code == 200

    # Check markdown file exists (Nov 2025 close_date routes to FY2026)
    md_path = Path("obsidian/40 Projects/Opportunities/FY2026/govly_md_test_789.md")
    assert md_path.exists()

    # Check content
    content = md_path.read_text()
    assert "id: govly_md_test_789" in content
    assert "title: Markdown Test" in content
    assert "source: Govly" in content
    assert "triage: true" in content


def test_radar_webhook_success():
    """Test successful Radar webhook ingestion."""
    payload = {
        "radar_id": "radar_test_111",
        "radar_type": "contract",
        "company_name": "Acme Corp",
        "contract_value": 1500000,
        "contract_date": "2025-10-28T00:00:00Z",
        "description": "Contract modification for IT services",
        "source_url": "https://radar.example.com/contract/111",
    }

    response = client.post("/v1/radar/webhook", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["opportunity_id"] == "radar_radar_test_111"
    assert "Radar opportunity" in data["message"]


def test_radar_webhook_creates_state_entry():
    """Test that Radar webhook creates opportunity in state.json."""
    payload = {
        "radar_id": "state_222",
        "radar_type": "modification",
        "company_name": "TechCorp",
        "contract_value": 750000,
        "contract_date": "2025-10-28T00:00:00Z",
        "description": "Contract modification",
        "source_url": "https://radar.example.com/contract/222",
    }

    response = client.post("/v1/radar/webhook", json=payload)
    assert response.status_code == 200

    # Check state.json
    with open(TEST_STATE_FILE, "r") as f:
        state = json.load(f)

    assert len(state["opportunities"]) == 1
    opp = state["opportunities"][0]
    assert opp["id"] == "radar_state_222"
    assert opp["title"] == "TechCorp - Modification"
    assert opp["source"] == "radar"
    # FY routing: Oct 2025 contract_date routes to FY2026, so triage=False
    assert opp["triage"] is False
    assert opp["fy"] == "FY2026"
    assert opp["estimated_amount"] == 750000


def test_radar_webhook_creates_markdown():
    """Test that Radar webhook creates opportunity markdown file."""
    payload = {
        "radar_id": "md_333",
        "radar_type": "contract",
        "company_name": "GlobalTech",
        "contract_value": 2000000,
        "contract_date": "2025-10-28T00:00:00Z",
        "description": "New contract award",
        "source_url": "https://radar.example.com/contract/333",
    }

    response = client.post("/v1/radar/webhook", json=payload)
    assert response.status_code == 200

    # Check markdown file exists (Oct 2025 contract_date routes to FY2026)
    md_path = Path("obsidian/40 Projects/Opportunities/FY2026/radar_md_333.md")
    assert md_path.exists()

    # Check content
    content = md_path.read_text()
    assert "id: radar_md_333" in content
    assert "title: GlobalTech - Contract" in content
    assert "source: Radar" in content
    assert "triage: true" in content


def test_govly_webhook_with_request_id():
    """Test that Govly webhook includes request_id in response headers."""
    payload = {"event_id": "reqid_test", "event_type": "opportunity", "title": "Request ID Test", "estimated_amount": 100000}

    response = client.post("/v1/govly/webhook", json=payload)

    assert response.status_code == 200
    assert "x-request-id" in response.headers
    assert "x-latency-ms" in response.headers


def test_radar_webhook_with_request_id():
    """Test that Radar webhook includes request_id in response headers."""
    payload = {"radar_id": "reqid_radar", "radar_type": "contract", "company_name": "Test Co", "contract_value": 100000}

    response = client.post("/v1/radar/webhook", json=payload)

    assert response.status_code == 200
    assert "x-request-id" in response.headers
    assert "x-latency-ms" in response.headers


def test_multiple_webhook_ingestions():
    """Test multiple webhook ingestions accumulate in state."""
    # First Govly
    govly_payload = {"event_id": "multi_1", "event_type": "opportunity", "title": "First Opportunity", "estimated_amount": 100000}
    client.post("/v1/govly/webhook", json=govly_payload)

    # Second Radar
    radar_payload = {"radar_id": "multi_2", "radar_type": "contract", "company_name": "Company", "contract_value": 200000}
    client.post("/v1/radar/webhook", json=radar_payload)

    # Check both are in state
    with open(TEST_STATE_FILE, "r") as f:
        state = json.load(f)

    assert len(state["opportunities"]) == 2
    assert any(o["id"] == "govly_multi_1" for o in state["opportunities"])
    assert any(o["id"] == "radar_multi_2" for o in state["opportunities"])
