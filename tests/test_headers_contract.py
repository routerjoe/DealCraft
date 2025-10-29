"""
Contract tests for response headers across all endpoints.

Sprint 15: Production Hardening
Validates that all endpoints include x-request-id and x-latency-ms headers.
"""

import re

import pytest
from fastapi.testclient import TestClient

from mcp.api.main import app

client = TestClient(app)


class TestRequiredHeaders:
    """Test that required headers are present on all endpoints."""

    def test_healthz_has_headers(self):
        """Test health endpoint includes required headers."""
        response = client.get("/healthz")
        assert response.status_code == 200

        # Convert to lowercase for case-insensitive check
        headers = {k.lower(): v for k, v in response.headers.items()}
        assert "x-request-id" in headers
        assert "x-latency-ms" in headers

    def test_info_has_headers(self):
        """Test info endpoint includes required headers."""
        response = client.get("/v1/info")
        assert response.status_code == 200

        headers = {k.lower(): v for k, v in response.headers.items()}
        assert "x-request-id" in headers
        assert "x-latency-ms" in headers

    def test_forecast_summary_has_headers(self):
        """Test forecast summary includes required headers."""
        response = client.get("/v1/forecast/summary")

        headers = {k.lower(): v for k, v in response.headers.items()}
        assert "x-request-id" in headers
        assert "x-latency-ms" in headers

    def test_metrics_has_headers(self):
        """Test metrics endpoint includes required headers."""
        response = client.get("/v1/metrics")

        headers = {k.lower(): v for k, v in response.headers.items()}
        assert "x-request-id" in headers
        assert "x-latency-ms" in headers

    def test_system_recent_actions_has_headers(self):
        """Test recent actions endpoint includes required headers."""
        response = client.get("/v1/system/recent-actions")

        headers = {k.lower(): v for k, v in response.headers.items()}
        assert "x-request-id" in headers
        assert "x-latency-ms" in headers


class TestHeaderFormats:
    """Test header value formats."""

    def test_request_id_is_uuid(self):
        """Test that x-request-id is a valid UUID."""
        response = client.get("/healthz")
        headers = {k.lower(): v for k, v in response.headers.items()}

        request_id = headers.get("x-request-id")
        assert request_id is not None

        # UUID v4 format: 8-4-4-4-12 hex characters
        uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        assert re.match(uuid_pattern, request_id, re.IGNORECASE)

    def test_latency_is_numeric(self):
        """Test that x-latency-ms is a numeric value."""
        response = client.get("/healthz")
        headers = {k.lower(): v for k, v in response.headers.items()}

        latency = headers.get("x-latency-ms")
        assert latency is not None

        # Should be parseable as integer
        latency_int = int(latency)
        assert latency_int >= 0

    def test_latency_is_reasonable(self):
        """Test that latency values are reasonable."""
        response = client.get("/healthz")
        headers = {k.lower(): v for k, v in response.headers.items()}

        latency = int(headers["x-latency-ms"])

        # Should be less than 10 seconds (10000ms)
        assert latency < 10000
        # Should be non-negative (0ms is valid for very fast requests)
        assert latency >= 0


class TestHeadersOnPOSTEndpoints:
    """Test headers on POST endpoints."""

    def test_obsidian_opportunity_has_headers(self):
        """Test opportunity creation includes headers."""
        response = client.post(
            "/v1/obsidian/opportunity",
            json={
                "id": "test_header_001",
                "title": "Test Opportunity",
                "customer": "Test Customer",
                "oem": "Cisco",
                "amount": 100000,
                "stage": "Discovery",
                "close_date": "2025-12-31",
                "source": "Test",
            },
        )

        headers = {k.lower(): v for k, v in response.headers.items()}
        assert "x-request-id" in headers
        assert "x-latency-ms" in headers

    def test_webhook_has_headers(self):
        """Test webhook endpoints include headers."""
        response = client.post(
            "/v1/govly/webhook",
            json={
                "event_id": "header_test_001",
                "event_type": "opportunity",
                "title": "Header Test",
                "estimated_amount": 50000,
            },
        )

        headers = {k.lower(): v for k, v in response.headers.items()}
        assert "x-request-id" in headers
        assert "x-latency-ms" in headers


class TestHeaderConsistency:
    """Test header consistency across requests."""

    def test_different_requests_have_different_ids(self):
        """Test that each request gets a unique request ID."""
        response1 = client.get("/healthz")
        response2 = client.get("/healthz")

        headers1 = {k.lower(): v for k, v in response1.headers.items()}
        headers2 = {k.lower(): v for k, v in response2.headers.items()}

        id1 = headers1["x-request-id"]
        id2 = headers2["x-request-id"]

        # Should be different UUIDs
        assert id1 != id2

    def test_all_endpoints_use_same_middleware(self):
        """Test that all endpoints use the same header middleware."""
        endpoints = [
            "/healthz",
            "/v1/info",
            "/v1/forecast/summary",
            "/v1/metrics",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            headers = {k.lower(): v for k, v in response.headers.items()}

            # All should have both headers
            assert "x-request-id" in headers, f"{endpoint} missing x-request-id"
            assert "x-latency-ms" in headers, f"{endpoint} missing x-latency-ms"


class TestErrorResponseHeaders:
    """Test headers on error responses."""

    def test_404_has_headers(self):
        """Test that 404 responses include headers."""
        response = client.get("/v1/nonexistent/endpoint")
        assert response.status_code == 404

        headers = {k.lower(): v for k, v in response.headers.items()}
        assert "x-request-id" in headers
        assert "x-latency-ms" in headers

    def test_422_validation_error_has_headers(self):
        """Test that validation errors include headers."""
        response = client.post("/v1/obsidian/opportunity", json={"invalid": "payload"})
        assert response.status_code == 422

        headers = {k.lower(): v for k, v in response.headers.items()}
        assert "x-request-id" in headers
        assert "x-latency-ms" in headers


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
