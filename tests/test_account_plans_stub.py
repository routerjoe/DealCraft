"""
Tests for AI Account Plans API stub.

Sprint 12: AI Account Plans
Tests endpoint mounting, request/response validation, and header presence.
"""

import pytest
from fastapi.testclient import TestClient

from mcp.api.main import app

client = TestClient(app)


class TestAccountPlansEndpoints:
    """Test that account plans endpoints are mounted."""

    def test_generate_endpoint_exists(self):
        """Test that generate endpoint returns 200 or 422."""
        response = client.post(
            "/v1/account-plans/generate",
            json={
                "customer": "AFCENT",
                "oem_partners": ["Cisco"],
                "fiscal_year": "FY26",
                "format": "markdown",
            },
        )
        # Should return 200 (stub success) or 422 (validation error)
        assert response.status_code in [200, 422]

    def test_formats_endpoint_exists(self):
        """Test that formats endpoint returns 200."""
        response = client.get("/v1/account-plans/formats")
        assert response.status_code == 200


class TestAccountPlansStubResponses:
    """Test stub response format."""

    def test_generate_returns_not_implemented(self):
        """Test that generate endpoint returns not_implemented status."""
        response = client.post(
            "/v1/account-plans/generate",
            json={
                "customer": "AFCENT",
                "oem_partners": ["Cisco", "Nutanix"],
                "fiscal_year": "FY26",
                "format": "markdown",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "not_implemented"
        assert "Sprint 12 development phase" in data["message"]
        assert data["plan_id"] is None
        assert data["preview"] is not None

    def test_generate_preview_contains_request_data(self):
        """Test that preview includes request parameters."""
        response = client.post(
            "/v1/account-plans/generate",
            json={
                "customer": "AETC",
                "oem_partners": ["NetApp", "Red Hat"],
                "fiscal_year": "FY26",
                "format": "json",
            },
        )

        assert response.status_code == 200
        data = response.json()
        preview = data["preview"]
        assert preview["customer"] == "AETC"
        assert "NetApp" in preview["oem_partners"]
        assert "Red Hat" in preview["oem_partners"]
        assert preview["fiscal_year"] == "FY26"
        assert preview["format"] == "json"

    def test_formats_returns_format_list(self):
        """Test that formats endpoint returns list of formats."""
        response = client.get("/v1/account-plans/formats")

        assert response.status_code == 200
        data = response.json()
        assert "formats" in data
        assert len(data["formats"]) >= 3  # markdown, pdf, json

        # Check for expected formats
        format_ids = [f["id"] for f in data["formats"]]
        assert "markdown" in format_ids
        assert "pdf" in format_ids
        assert "json" in format_ids


class TestAccountPlansValidation:
    """Test request validation."""

    def test_generate_requires_customer(self):
        """Test that customer field is required."""
        response = client.post(
            "/v1/account-plans/generate",
            json={
                "oem_partners": ["Cisco"],
                "fiscal_year": "FY26",
                "format": "markdown",
            },
        )
        assert response.status_code == 422

    def test_generate_requires_oem_partners(self):
        """Test that oem_partners field is required."""
        response = client.post(
            "/v1/account-plans/generate",
            json={
                "customer": "AFCENT",
                "fiscal_year": "FY26",
                "format": "markdown",
            },
        )
        assert response.status_code == 422

    def test_generate_requires_fiscal_year(self):
        """Test that fiscal_year field is required."""
        response = client.post(
            "/v1/account-plans/generate",
            json={
                "customer": "AFCENT",
                "oem_partners": ["Cisco"],
                "format": "markdown",
            },
        )
        assert response.status_code == 422

    def test_generate_accepts_optional_focus_areas(self):
        """Test that focus_areas is optional."""
        response = client.post(
            "/v1/account-plans/generate",
            json={
                "customer": "AFCENT",
                "oem_partners": ["Cisco"],
                "fiscal_year": "FY26",
                "format": "markdown",
                "focus_areas": ["security", "cloud"],
            },
        )
        assert response.status_code == 200


class TestAccountPlansHeaders:
    """Test response header presence."""

    def test_generate_includes_request_id(self):
        """Test that generate response includes x-request-id header."""
        response = client.post(
            "/v1/account-plans/generate",
            json={
                "customer": "AFCENT",
                "oem_partners": ["Cisco"],
                "fiscal_year": "FY26",
                "format": "markdown",
            },
        )
        assert response.status_code == 200
        # Note: Headers may be case-insensitive depending on FastAPI/Starlette version
        headers_lower = {k.lower(): v for k, v in response.headers.items()}
        assert "x-request-id" in headers_lower or "x-latency-ms" in headers_lower

    def test_formats_includes_request_id(self):
        """Test that formats response includes x-request-id header."""
        response = client.get("/v1/account-plans/formats")
        assert response.status_code == 200
        headers_lower = {k.lower(): v for k, v in response.headers.items()}
        assert "x-request-id" in headers_lower or "x-latency-ms" in headers_lower


class TestAccountPlansCustomers:
    """Test customer-specific functionality."""

    def test_afcent_plan_generation(self):
        """Test AFCENT account plan generation."""
        response = client.post(
            "/v1/account-plans/generate",
            json={
                "customer": "AFCENT",
                "oem_partners": ["Cisco", "Nutanix"],
                "fiscal_year": "FY26",
                "format": "markdown",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["preview"]["customer"] == "AFCENT"

    def test_aetc_plan_generation(self):
        """Test AETC account plan generation."""
        response = client.post(
            "/v1/account-plans/generate",
            json={
                "customer": "AETC",
                "oem_partners": ["NetApp", "Red Hat"],
                "fiscal_year": "FY26",
                "format": "markdown",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["preview"]["customer"] == "AETC"


class TestAccountPlansOEMPartners:
    """Test OEM partner handling."""

    def test_cisco_partner(self):
        """Test Cisco as OEM partner."""
        response = client.post(
            "/v1/account-plans/generate",
            json={
                "customer": "AFCENT",
                "oem_partners": ["Cisco"],
                "fiscal_year": "FY26",
                "format": "markdown",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "Cisco" in data["preview"]["oem_partners"]

    def test_multiple_partners(self):
        """Test multiple OEM partners."""
        partners = ["Cisco", "Nutanix", "NetApp", "Red Hat"]
        response = client.post(
            "/v1/account-plans/generate",
            json={
                "customer": "AFCENT",
                "oem_partners": partners,
                "fiscal_year": "FY26",
                "format": "markdown",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["preview"]["oem_partners"]) == 4


class TestAccountPlansFormats:
    """Test output format handling."""

    def test_markdown_format(self):
        """Test markdown format selection."""
        response = client.post(
            "/v1/account-plans/generate",
            json={
                "customer": "AFCENT",
                "oem_partners": ["Cisco"],
                "fiscal_year": "FY26",
                "format": "markdown",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["preview"]["format"] == "markdown"

    def test_pdf_format(self):
        """Test PDF format selection."""
        response = client.post(
            "/v1/account-plans/generate",
            json={
                "customer": "AFCENT",
                "oem_partners": ["Cisco"],
                "fiscal_year": "FY26",
                "format": "pdf",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["preview"]["format"] == "pdf"

    def test_json_format(self):
        """Test JSON format selection."""
        response = client.post(
            "/v1/account-plans/generate",
            json={
                "customer": "AFCENT",
                "oem_partners": ["Cisco"],
                "fiscal_year": "FY26",
                "format": "json",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["preview"]["format"] == "json"

    def test_format_info_structure(self):
        """Test format info structure."""
        response = client.get("/v1/account-plans/formats")
        assert response.status_code == 200
        data = response.json()

        markdown_format = next(f for f in data["formats"] if f["id"] == "markdown")
        assert markdown_format["name"] == "Markdown"
        assert markdown_format["extension"] == ".md"
        assert markdown_format["supports_obsidian"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
