"""Tests for health check and info endpoints."""

from fastapi.testclient import TestClient

from mcp.api.main import app

client = TestClient(app)


def test_health_check():
    """Test the /healthz endpoint returns healthy status."""
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_health_check_has_request_id():
    """Test that health check response includes X-Request-ID header."""
    response = client.get("/healthz")
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"]  # Not empty


def test_api_info():
    """Test the /v1/info endpoint returns API information."""
    response = client.get("/v1/info")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "environment" in data
    assert data["name"] == "Red River Sales MCP API"
    assert data["version"] == "1.10.0"


def test_api_info_has_request_id():
    """Test that API info response includes X-Request-ID header."""
    response = client.get("/v1/info")
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"]  # Not empty


def test_404_endpoint():
    """Test that non-existent endpoints return 404."""
    response = client.get("/nonexistent")
    assert response.status_code == 404
