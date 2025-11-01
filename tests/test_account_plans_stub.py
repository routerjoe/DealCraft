"""
Tests for AI Account Plans API implementation.

Sprint 12: AI Account Plans
Tests real account plan generation for Customer Alpha and Customer Beta with forecast integration.
"""

import pytest
from fastapi.testclient import TestClient

from mcp.api.main import app

client = TestClient(app)


class TestAccountPlansEndpoints:
    """Test that account plans endpoints are mounted and functional."""

    def test_generate_endpoint_exists(self):
        """Test that generate endpoint returns 200 for valid request."""
        response = client.post(
            "/v1/account-plans/generate",
            json={
                "customer": "Customer Alpha",
                "oem_partners": ["Cisco"],
                "fiscal_year": "FY26",
                "format": "json",
            },
        )
        assert response.status_code == 200

    def test_formats_endpoint_exists(self):
        """Test that formats endpoint returns 200."""
        response = client.get("/v1/account-plans/formats")
        assert response.status_code == 200


class TestAccountPlansRealImplementation:
    """Test real account plan generation."""

    def test_generate_returns_success(self):
        """Test that generate endpoint returns success status."""
        response = client.post(
            "/v1/account-plans/generate",
            json={
                "customer": "Customer Alpha",
                "oem_partners": ["Cisco", "Nutanix"],
                "fiscal_year": "FY26",
                "format": "json",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "Customer Alpha Command" in data["message"]
        assert data["plan_id"] is not None
        assert data["preview"] is not None

    def test_generate_plan_structure(self):
        """Test that generated plan has required structure."""
        response = client.post(
            "/v1/account-plans/generate",
            json={
                "customer": "Customer Alpha",
                "oem_partners": ["Cisco"],
                "fiscal_year": "FY26",
                "format": "json",
            },
        )

        assert response.status_code == 200
        data = response.json()
        preview = data["preview"]

        # Check required keys
        assert "customer" in preview
        assert "executive_summary" in preview
        assert "goals_kpis" in preview
        assert "oem_strategy" in preview
        assert "contract_vehicle_strategy" in preview
        assert "partner_stack" in preview
        assert "outreach_plan" in preview
        assert "risks_mitigations" in preview
        assert "checkpoints_30_60_90" in preview
        assert "sources_used" in preview
        assert "reasoning" in preview

    def test_customer_beta_plan_contains_customer_data(self):
        """Test that Customer Beta plan includes customer-specific data."""
        response = client.post(
            "/v1/account-plans/generate",
            json={
                "customer": "Customer Beta",
                "oem_partners": ["NetApp", "Red Hat"],
                "fiscal_year": "FY26",
                "format": "json",
            },
        )

        assert response.status_code == 200
        data = response.json()
        preview = data["preview"]
        assert preview["customer"] == "Customer Beta"
        assert "Customer Beta Command" in preview["customer_full_name"]

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
                "customer": "Customer Alpha",
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
                "customer": "Customer Alpha",
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
                "customer": "Customer Alpha",
                "oem_partners": ["Cisco"],
                "fiscal_year": "FY26",
                "format": "markdown",
                "focus_areas": ["security", "cloud"],
            },
        )
        assert response.status_code == 200

    def test_unknown_customer_returns_400(self):
        """Test that unknown customer returns 400 with helpful hint."""
        response = client.post(
            "/v1/account-plans/generate",
            json={
                "customer": "UNKNOWN_ORG",
                "oem_partners": ["Cisco"],
                "fiscal_year": "FY26",
                "format": "json",
            },
        )
        assert response.status_code == 400
        assert "Unsupported customer" in response.json()["detail"]
        assert "Customer Alpha" in response.json()["detail"] or "Customer Beta" in response.json()["detail"]


class TestAccountPlansHeaders:
    """Test response header presence."""

    def test_generate_includes_request_id(self):
        """Test that generate response includes x-request-id header."""
        response = client.post(
            "/v1/account-plans/generate",
            json={
                "customer": "Customer Alpha",
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

    def test_customer_alpha_plan_generation(self):
        """Test Customer Alpha account plan generation."""
        response = client.post(
            "/v1/account-plans/generate",
            json={
                "customer": "Customer Alpha",
                "oem_partners": ["Cisco", "Nutanix"],
                "fiscal_year": "FY26",
                "format": "markdown",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["preview"]["customer"] == "Customer Alpha"

    def test_customer_beta_plan_generation(self):
        """Test Customer Beta account plan generation."""
        response = client.post(
            "/v1/account-plans/generate",
            json={
                "customer": "Customer Beta",
                "oem_partners": ["NetApp", "Red Hat"],
                "fiscal_year": "FY26",
                "format": "markdown",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["preview"]["customer"] == "Customer Beta"


class TestAccountPlansOEMPartners:
    """Test OEM partner handling."""

    def test_cisco_partner(self):
        """Test Cisco as OEM partner."""
        response = client.post(
            "/v1/account-plans/generate",
            json={
                "customer": "Customer Alpha",
                "oem_partners": ["Cisco"],
                "fiscal_year": "FY26",
                "format": "json",
            },
        )
        assert response.status_code == 200
        data = response.json()
        # Check that OEM strategy includes Cisco
        assert "oem_strategy" in data["preview"]
        assert any(s["oem"] == "Cisco" for s in data["preview"]["oem_strategy"])

    def test_multiple_partners(self):
        """Test multiple OEM partners."""
        partners = ["Cisco", "Nutanix", "NetApp", "Red Hat"]
        response = client.post(
            "/v1/account-plans/generate",
            json={
                "customer": "Customer Alpha",
                "oem_partners": partners,
                "fiscal_year": "FY26",
                "format": "json",
            },
        )
        assert response.status_code == 200
        data = response.json()
        # Check that plan was generated successfully with OEM strategies
        assert "oem_strategy" in data["preview"]
        assert len(data["preview"]["oem_strategy"]) >= 1


class TestAccountPlansFormats:
    """Test output format handling."""

    def test_markdown_format(self):
        """Test markdown format selection."""
        response = client.post(
            "/v1/account-plans/generate",
            json={
                "customer": "Customer Alpha",
                "oem_partners": ["Cisco"],
                "fiscal_year": "FY26",
                "format": "markdown",
            },
        )
        assert response.status_code == 200
        data = response.json()
        # Markdown format returns full plan with note
        assert data["status"] == "success"
        assert data["preview"] is not None

    def test_pdf_format(self):
        """Test PDF format selection returns PDF file."""
        response = client.post(
            "/v1/account-plans/generate",
            json={
                "customer": "Customer Alpha",
                "oem_partners": ["Cisco"],
                "fiscal_year": "FY26",
                "format": "pdf",
            },
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        # Verify PDF content
        assert len(response.content) > 1000
        assert response.content.startswith(b"%PDF-")

    def test_json_format(self):
        """Test JSON format selection."""
        response = client.post(
            "/v1/account-plans/generate",
            json={
                "customer": "Customer Alpha",
                "oem_partners": ["Cisco"],
                "fiscal_year": "FY26",
                "format": "json",
            },
        )
        assert response.status_code == 200
        data = response.json()
        # JSON format returns full plan structure
        assert data["status"] == "success"
        assert "executive_summary" in data["preview"]

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
