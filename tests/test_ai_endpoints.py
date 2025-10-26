"""Tests for AI endpoints."""

from fastapi.testclient import TestClient

from mcp.api.main import app

client = TestClient(app)


def test_list_models():
    """Test GET /v1/ai/models returns expected model list."""
    response = client.get("/v1/ai/models")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 6  # Updated to match expanded model list
    assert "gpt-5-thinking" in data
    assert "gpt-4-turbo" in data
    assert "claude-3.5" in data
    assert "claude-3-opus" in data
    assert "gemini-1.5-pro" in data
    assert "gemini-1.5-flash" in data


def test_guidance_minimal():
    """Test POST /v1/ai/guidance with minimal payload."""
    payload = {"rfq_text": "Sample RFQ for testing"}
    response = client.post("/v1/ai/guidance", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "summary" in data
    assert "actions" in data
    assert "risks" in data

    # Verify types
    assert isinstance(data["summary"], str)
    assert isinstance(data["actions"], list)
    assert isinstance(data["risks"], list)


def test_guidance_with_oems_and_contracts():
    """Test POST /v1/ai/guidance with full payload."""
    payload = {
        "oems": [{"name": "Dell", "authorized": True}, {"name": "HP", "authorized": False}],
        "contracts": [
            {"name": "GSA Schedule", "supported": True},
            {"name": "NASPO", "supported": False},
        ],
        "rfq_text": "RFQ for servers and storage",
        "model": "claude-3.5",
    }
    response = client.post("/v1/ai/guidance", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "summary" in data
    assert "actions" in data
    assert "risks" in data

    # Verify content mentions the model and counts
    assert "claude-3.5" in data["summary"]
    assert "1 authorized OEMs" in data["summary"]
    assert "1 supported contract" in data["summary"]


def test_guidance_default_model():
    """Test POST /v1/ai/guidance uses default model when not specified."""
    payload = {"rfq_text": "Default model test"}
    response = client.post("/v1/ai/guidance", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Should use default gpt-5-thinking
    assert "gpt-5-thinking" in data["summary"]


def test_guidance_has_request_id():
    """Test that guidance endpoint includes X-Request-ID header."""
    payload = {"rfq_text": "Test"}
    response = client.post("/v1/ai/guidance", json=payload)
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"]


def test_models_has_request_id():
    """Test that models endpoint includes X-Request-ID header."""
    response = client.get("/v1/ai/models")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"]
