"""Tests for Obsidian note generation endpoints."""

import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mcp.api.main import app

client = TestClient(app)

# Test directory
OBSIDIAN_DIR = Path("obsidian")


@pytest.fixture(autouse=True)
def cleanup_obsidian_dir():
    """Clean up obsidian directory before and after each test."""
    # Clean up before test
    if OBSIDIAN_DIR.exists():
        shutil.rmtree(OBSIDIAN_DIR)

    yield

    # Clean up after test
    if OBSIDIAN_DIR.exists():
        shutil.rmtree(OBSIDIAN_DIR)


def test_create_opportunity_note():
    """Test creating an opportunity note."""
    response = client.post(
        "/v1/obsidian/opportunity",
        json={
            "id": "OPP-001",
            "title": "Federal IT Modernization",
            "customer": "DoD Agency X",
            "oem": "Dell Technologies",
            "amount": 250000.00,
            "stage": "Qualification",
            "close_date": "2025-03-31",
            "source": "RFQ",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["created"] is True
    assert "OPP-001 - Federal IT Modernization.md" in data["path"]
    assert "X-Request-ID" in response.headers

    # Verify file exists
    file_path = Path(data["path"])
    assert file_path.exists()


def test_opportunity_note_content():
    """Test that opportunity note has correct content and structure."""
    response = client.post(
        "/v1/obsidian/opportunity",
        json={
            "id": "OPP-002",
            "title": "Cloud Migration Project",
            "customer": "State Agency Y",
            "oem": "AWS",
            "amount": 500000.00,
            "stage": "Proposal",
            "close_date": "2025-06-30",
            "source": "Govly",
            "tags": ["cloud", "migration", "30-hub"],
        },
    )

    assert response.status_code == 201
    file_path = Path(response.json()["path"])

    # Read and verify content
    content = file_path.read_text(encoding="utf-8")

    # Check YAML frontmatter
    assert "---" in content
    assert "tags:" in content
    assert "- cloud" in content
    assert "- migration" in content
    assert "- 30-hub" in content
    assert "type: opportunity" in content
    assert "id: OPP-002" in content
    assert "customer: State Agency Y" in content
    assert "oem: AWS" in content
    assert "amount: 500000.0" in content
    assert "stage: Proposal" in content
    assert "close_date: 2025-06-30" in content
    assert "source: Govly" in content

    # Check content sections
    assert "# Cloud Migration Project" in content
    assert "## Summary" in content
    assert "**Customer:** State Agency Y" in content
    assert "**OEM:** AWS" in content
    assert "**Amount:** $500000.0" in content
    assert "**Stage:** Proposal" in content
    assert "**Expected Close:** 2025-06-30" in content
    assert "**Source:** Govly" in content
    assert "## Scope" in content
    assert "## OEM Details" in content
    assert "## Next Actions" in content
    assert "## Notes" in content


def test_opportunity_note_file_path():
    """Test that opportunity note is created at correct path."""
    response = client.post(
        "/v1/obsidian/opportunity",
        json={
            "id": "OPP-003",
            "title": "Security Upgrade",
            "customer": "Local Gov",
            "oem": "Cisco",
            "amount": 150000.00,
            "stage": "Discovery",
            "close_date": "2025-04-15",
            "source": "Partner Referral",
        },
    )

    assert response.status_code == 201
    file_path = Path(response.json()["path"])

    # Verify path structure
    assert file_path.parent.name == "Opportunities"
    assert file_path.parent.parent.name == "30 Hub"
    assert file_path.parent.parent.parent.name == "obsidian"
    assert file_path.name == "OPP-003 - Security Upgrade.md"


def test_opportunity_invalid_amount():
    """Test creating opportunity with invalid amount."""
    response = client.post(
        "/v1/obsidian/opportunity",
        json={
            "id": "OPP-004",
            "title": "Test",
            "customer": "Test Customer",
            "oem": "Test OEM",
            "amount": -1000.00,  # Invalid negative amount
            "stage": "Test",
            "close_date": "2025-12-31",
            "source": "Test",
        },
    )

    assert response.status_code == 422


def test_opportunity_missing_required_field():
    """Test creating opportunity with missing required field."""
    response = client.post(
        "/v1/obsidian/opportunity",
        json={
            "id": "OPP-005",
            "title": "Test",
            "customer": "Test Customer",
            # Missing oem
            "amount": 100000.00,
            "stage": "Test",
            "close_date": "2025-12-31",
            "source": "Test",
        },
    )

    assert response.status_code == 422


def test_opportunity_empty_string_validation():
    """Test that empty strings are rejected."""
    response = client.post(
        "/v1/obsidian/opportunity",
        json={
            "id": "",  # Empty ID
            "title": "Test",
            "customer": "Test Customer",
            "oem": "Test OEM",
            "amount": 100000.00,
            "stage": "Test",
            "close_date": "2025-12-31",
            "source": "Test",
        },
    )

    assert response.status_code == 422


def test_opportunity_special_characters_in_title():
    """Test that special characters in title are handled correctly."""
    response = client.post(
        "/v1/obsidian/opportunity",
        json={
            "id": "OPP-006",
            "title": "Project / with \\ slashes",
            "customer": "Test Customer",
            "oem": "Test OEM",
            "amount": 100000.00,
            "stage": "Test",
            "close_date": "2025-12-31",
            "source": "Test",
        },
    )

    assert response.status_code == 201
    file_path = Path(response.json()["path"])

    # Verify slashes are replaced with dashes
    assert file_path.name == "OPP-006 - Project - with - slashes.md"
    assert file_path.exists()


def test_opportunity_default_tags():
    """Test that default tags are applied when not provided."""
    response = client.post(
        "/v1/obsidian/opportunity",
        json={
            "id": "OPP-007",
            "title": "Default Tags Test",
            "customer": "Test Customer",
            "oem": "Test OEM",
            "amount": 100000.00,
            "stage": "Test",
            "close_date": "2025-12-31",
            "source": "Test",
        },
    )

    assert response.status_code == 201
    file_path = Path(response.json()["path"])
    content = file_path.read_text(encoding="utf-8")

    # Check default tags
    assert "- opportunity" in content
    assert "- 30-hub" in content


def test_multiple_opportunities():
    """Test creating multiple opportunity notes."""
    # Create first opportunity
    response1 = client.post(
        "/v1/obsidian/opportunity",
        json={
            "id": "OPP-008",
            "title": "First Opportunity",
            "customer": "Customer A",
            "oem": "OEM A",
            "amount": 100000.00,
            "stage": "Qualification",
            "close_date": "2025-03-31",
            "source": "RFQ",
        },
    )
    assert response1.status_code == 201
    path1 = Path(response1.json()["path"])
    assert path1.exists()

    # Create second opportunity
    response2 = client.post(
        "/v1/obsidian/opportunity",
        json={
            "id": "OPP-009",
            "title": "Second Opportunity",
            "customer": "Customer B",
            "oem": "OEM B",
            "amount": 200000.00,
            "stage": "Proposal",
            "close_date": "2025-04-30",
            "source": "Partner",
        },
    )
    assert response2.status_code == 201
    path2 = Path(response2.json()["path"])
    assert path2.exists()

    # Verify both files exist
    assert path1.exists()
    assert path2.exists()
    assert path1 != path2
