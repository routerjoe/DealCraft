"""
Tests for Account Plans PDF Export - Phase 12

Validates:
- PDF generation for supported customers
- PDF response format (content-type, headers)
- Error handling for unsupported customers
"""

from fastapi.testclient import TestClient

from mcp.api.main import app

client = TestClient(app)


def test_account_plan_pdf_afcent():
    """Test PDF export for AFCENT customer."""
    response = client.post(
        "/v1/account-plans/generate",
        json={"customer": "AFCENT", "oem_partners": ["Cisco", "Microsoft"], "fiscal_year": "FY26", "format": "pdf"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"

    # Verify PDF content is non-empty
    pdf_content = response.content
    assert len(pdf_content) > 1000  # PDFs should be at least 1KB

    # Verify PDF magic bytes
    assert pdf_content.startswith(b"%PDF-")

    # Verify custom headers
    assert "x-request-id" in response.headers
    assert "x-latency-ms" in response.headers

    # Verify filename in Content-Disposition
    assert "content-disposition" in response.headers
    assert "account_plan_afcent" in response.headers["content-disposition"]
    assert ".pdf" in response.headers["content-disposition"]


def test_account_plan_pdf_aetc():
    """Test PDF export for AETC customer."""
    response = client.post(
        "/v1/account-plans/generate", json={"customer": "AETC", "oem_partners": ["Dell", "HPE"], "fiscal_year": "FY26", "format": "pdf"}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"

    # Verify PDF content
    pdf_content = response.content
    assert len(pdf_content) > 1000
    assert pdf_content.startswith(b"%PDF-")

    # Verify filename contains customer name
    assert "aetc" in response.headers["content-disposition"].lower()


def test_account_plan_pdf_unknown_customer():
    """Test PDF export with unknown customer returns 400."""
    response = client.post(
        "/v1/account-plans/generate",
        json={"customer": "UnknownCustomer", "oem_partners": ["Cisco"], "fiscal_year": "FY26", "format": "pdf"},
    )

    assert response.status_code == 400
    assert "detail" in response.json()
    assert "unsupported customer" in response.json()["detail"].lower()


def test_account_plan_json_format_still_works():
    """Test that JSON format still works after PDF implementation."""
    response = client.post(
        "/v1/account-plans/generate", json={"customer": "AFCENT", "oem_partners": ["Cisco"], "fiscal_year": "FY26", "format": "json"}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"

    data = response.json()
    assert data["status"] == "success"
    assert "preview" in data
    assert "customer" in data["preview"]


def test_account_plan_markdown_format_still_works():
    """Test that markdown format still works after PDF implementation."""
    response = client.post(
        "/v1/account-plans/generate", json={"customer": "AETC", "oem_partners": ["Microsoft"], "fiscal_year": "FY26", "format": "markdown"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "preview" in data


def test_account_plan_pdf_with_minimal_data():
    """Test PDF generation works even with minimal opportunity data."""
    # This tests the fallback to sample data when no real opportunities exist
    response = client.post(
        "/v1/account-plans/generate", json={"customer": "AFCENT", "oem_partners": ["Cisco"], "fiscal_year": "FY26", "format": "pdf"}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"

    # Should still generate a valid PDF
    pdf_content = response.content
    assert len(pdf_content) > 1000
    assert pdf_content.startswith(b"%PDF-")
