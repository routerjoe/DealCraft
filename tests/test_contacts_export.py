"""Tests for contacts export endpoints."""

import csv
import io
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mcp.api.main import app

client = TestClient(app)

# Test data file path
STATE_FILE = Path("data/state.json")


@pytest.fixture(autouse=True)
def setup_contacts():
    """Set up test contacts in state file."""
    # Save original state
    original_state = None
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            original_state = json.load(f)

    # Create test contacts
    test_contacts = [
        {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-0100",
            "organization": "Acme Corp",
            "title": "Sales Manager",
        },
        {
            "name": "Jane Smith",
            "email": "jane.smith@techcorp.com",
            "phone": "+1-555-0200",
            "organization": "TechCorp",
            "title": "CTO",
        },
        {
            "name": "Bob Johnson",
            "email": "bjohnson@startup.io",
            "phone": "",
            "organization": "Startup Inc",
            "title": "",
        },
    ]

    # Write test state
    with open(STATE_FILE, "w") as f:
        json.dump({"contacts": test_contacts, "oems": [], "contracts": []}, f)

    yield

    # Restore original state
    if original_state:
        with open(STATE_FILE, "w") as f:
            json.dump(original_state, f)


def test_export_csv_success():
    """Test successful CSV export."""
    response = client.get("/v1/contacts/export.csv")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "Content-Disposition" in response.headers
    assert "contacts.csv" in response.headers["Content-Disposition"]
    assert "X-Request-ID" in response.headers


def test_export_csv_content():
    """Test CSV content format and data."""
    response = client.get("/v1/contacts/export.csv")

    assert response.status_code == 200

    # Parse CSV
    csv_content = response.text
    csv_reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(csv_reader)

    # Verify header
    assert csv_reader.fieldnames == ["Name", "Email", "Phone", "Organization", "Title"]

    # Verify data
    assert len(rows) == 3

    # Check first contact
    assert rows[0]["Name"] == "John Doe"
    assert rows[0]["Email"] == "john.doe@example.com"
    assert rows[0]["Phone"] == "+1-555-0100"
    assert rows[0]["Organization"] == "Acme Corp"
    assert rows[0]["Title"] == "Sales Manager"

    # Check second contact
    assert rows[1]["Name"] == "Jane Smith"
    assert rows[1]["Email"] == "jane.smith@techcorp.com"

    # Check third contact (with empty fields)
    assert rows[2]["Name"] == "Bob Johnson"
    assert rows[2]["Phone"] == ""
    assert rows[2]["Title"] == ""


def test_export_vcf_success():
    """Test successful vCard export."""
    response = client.get("/v1/contacts/export.vcf")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/vcard; charset=utf-8"
    assert "Content-Disposition" in response.headers
    assert "contacts.vcf" in response.headers["Content-Disposition"]
    assert "X-Request-ID" in response.headers


def test_export_vcf_content():
    """Test vCard content format and data."""
    response = client.get("/v1/contacts/export.vcf")

    assert response.status_code == 200

    vcf_content = response.text
    vcards = vcf_content.split("\n\n")

    # Should have 3 vCards
    assert len(vcards) == 3

    # Check first vCard
    first_vcard = vcards[0]
    assert "BEGIN:VCARD" in first_vcard
    assert "VERSION:3.0" in first_vcard
    assert "FN:John Doe" in first_vcard
    assert "N:Doe;John;;;" in first_vcard
    assert "EMAIL;TYPE=INTERNET:john.doe@example.com" in first_vcard
    assert "TEL;TYPE=WORK,VOICE:+1-555-0100" in first_vcard
    assert "ORG:Acme Corp" in first_vcard
    assert "TITLE:Sales Manager" in first_vcard
    assert "END:VCARD" in first_vcard


def test_export_vcf_name_parsing():
    """Test vCard name parsing for different formats."""
    response = client.get("/v1/contacts/export.vcf")
    vcf_content = response.text

    # Check various name formats
    # "John Doe" should become N:Doe;John;;;
    assert "N:Doe;John;;;" in vcf_content

    # "Jane Smith" should become N:Smith;Jane;;;
    assert "N:Smith;Jane;;;" in vcf_content

    # "Bob Johnson" should become N:Johnson;Bob;;;
    assert "N:Johnson;Bob;;;" in vcf_content


def test_export_csv_empty_contacts():
    """Test CSV export when no contacts exist."""
    # Clear contacts
    with open(STATE_FILE, "w") as f:
        json.dump({"oems": [], "contracts": []}, f)

    response = client.get("/v1/contacts/export.csv")

    assert response.status_code == 200

    # Should have header only
    csv_content = response.text
    lines = csv_content.strip().split("\n")
    assert len(lines) == 1
    assert lines[0] == "Name,Email,Phone,Organization,Title"


def test_export_vcf_empty_contacts():
    """Test vCard export when no contacts exist."""
    # Clear contacts
    with open(STATE_FILE, "w") as f:
        json.dump({"oems": [], "contracts": []}, f)

    response = client.get("/v1/contacts/export.vcf")

    assert response.status_code == 200
    assert response.text == ""


def test_export_csv_special_characters():
    """Test CSV export with special characters."""
    # Add contact with special characters
    special_contact = {
        "name": "Test, User",
        "email": "test@example.com",
        "phone": "(555) 123-4567",
        "organization": "Company, LLC",
        "title": "VP, Operations",
    }

    with open(STATE_FILE, "w") as f:
        json.dump({"contacts": [special_contact]}, f)

    response = client.get("/v1/contacts/export.csv")
    assert response.status_code == 200

    # Parse CSV
    csv_reader = csv.DictReader(io.StringIO(response.text))
    rows = list(csv_reader)

    assert len(rows) == 1
    # CSV module should handle quoting properly
    assert rows[0]["Name"] == "Test, User"
    assert rows[0]["Organization"] == "Company, LLC"
    assert rows[0]["Title"] == "VP, Operations"


def test_export_csv_newlines_in_fields():
    """Test CSV export with newlines in fields (should be sanitized)."""
    # Add contact with newlines
    contact_with_newlines = {
        "name": "Test\nUser",
        "email": "test@example.com",
        "phone": "555-1234",
        "organization": "Company\nLLC",
        "title": "Manager\nSales",
    }

    with open(STATE_FILE, "w") as f:
        json.dump({"contacts": [contact_with_newlines]}, f)

    response = client.get("/v1/contacts/export.csv")
    assert response.status_code == 200

    # Parse CSV
    csv_reader = csv.DictReader(io.StringIO(response.text))
    rows = list(csv_reader)

    # Newlines should be replaced with spaces
    assert rows[0]["Name"] == "Test User"
    assert rows[0]["Organization"] == "Company LLC"
    assert rows[0]["Title"] == "Manager Sales"


def test_export_vcf_optional_fields():
    """Test vCard export with optional fields missing."""
    # Add contact with minimal fields
    minimal_contact = {
        "name": "Minimal Contact",
        "email": "minimal@example.com",
        "phone": "",
        "organization": "",
        "title": "",
    }

    with open(STATE_FILE, "w") as f:
        json.dump({"contacts": [minimal_contact]}, f)

    response = client.get("/v1/contacts/export.vcf")
    assert response.status_code == 200

    vcf_content = response.text

    # Should have basic fields
    assert "FN:Minimal Contact" in vcf_content
    assert "EMAIL;TYPE=INTERNET:minimal@example.com" in vcf_content

    # Should not have empty optional fields (or they should be omitted)
    # TEL, ORG, TITLE should not appear if empty
    lines = vcf_content.split("\n")
    tel_lines = [line for line in lines if line.startswith("TEL")]
    org_lines = [line for line in lines if line.startswith("ORG:")]
    title_lines = [line for line in lines if line.startswith("TITLE:")]

    assert len(tel_lines) == 0
    assert len(org_lines) == 0
    assert len(title_lines) == 0


def test_export_vcf_single_name():
    """Test vCard export with single name (no space)."""
    # Add contact with single name
    single_name_contact = {
        "name": "Madonna",
        "email": "madonna@example.com",
        "phone": "",
        "organization": "",
        "title": "",
    }

    with open(STATE_FILE, "w") as f:
        json.dump({"contacts": [single_name_contact]}, f)

    response = client.get("/v1/contacts/export.vcf")
    assert response.status_code == 200

    vcf_content = response.text

    # Should handle single name
    assert "FN:Madonna" in vcf_content
    # N field: Last;First;Middle;Prefix;Suffix
    # With single name, it goes in First field
    assert "N:;Madonna;;;" in vcf_content


def test_csv_and_vcf_have_same_count():
    """Test that CSV and VCF exports have same number of contacts."""
    csv_response = client.get("/v1/contacts/export.csv")
    vcf_response = client.get("/v1/contacts/export.vcf")

    # Count CSV rows (excluding header)
    csv_rows = len(csv_response.text.strip().split("\n")) - 1

    # Count vCards
    vcards = [v for v in vcf_response.text.split("\n\n") if v.strip()]
    vcf_count = len(vcards)

    assert csv_rows == vcf_count == 3


def test_export_missing_state_file():
    """Test export when state file doesn't exist."""
    # Remove state file temporarily
    if STATE_FILE.exists():
        STATE_FILE.rename(STATE_FILE.with_suffix(".bak"))

    try:
        # CSV should return empty with headers
        csv_response = client.get("/v1/contacts/export.csv")
        assert csv_response.status_code == 200
        assert "Name,Email,Phone,Organization,Title" in csv_response.text

        # VCF should return empty
        vcf_response = client.get("/v1/contacts/export.vcf")
        assert vcf_response.status_code == 200
        assert vcf_response.text == ""
    finally:
        # Restore backup
        if STATE_FILE.with_suffix(".bak").exists():
            STATE_FILE.with_suffix(".bak").rename(STATE_FILE)
