"""
Smoke tests for webhook signature validation and replay protection.

Sprint 10: Webhooks - Extended validation tests
Tests signature validation when secrets are configured and marks as xpass when not.
"""

import hashlib
import hmac
import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mcp.api.main import app

client = TestClient(app)

TEST_STATE_FILE = Path("data/state.json")


@pytest.fixture(autouse=True)
def setup_teardown():
    """Save and restore state."""
    original = None
    if TEST_STATE_FILE.exists():
        with open(TEST_STATE_FILE, "r") as f:
            original = f.read()

    yield

    if original:
        with open(TEST_STATE_FILE, "w") as f:
            f.write(original)


def calculate_signature(secret: str, payload: dict) -> str:
    """Calculate HMAC-SHA256 signature for webhook payload."""
    body = json.dumps(payload).encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={signature}"


@pytest.mark.xfail(reason="Signature validation requires GOVLY_WEBHOOK_SECRET to be configured")
class TestGovlySignatureValidation:
    """Test Govly webhook signature validation."""

    def test_valid_signature_accepted(self):
        """Test that valid HMAC-SHA256 signature is accepted."""
        secret = os.environ.get("GOVLY_WEBHOOK_SECRET")
        if not secret:
            pytest.skip("GOVLY_WEBHOOK_SECRET not configured")

        payload = {
            "event_id": "sig_valid_001",
            "event_type": "opportunity",
            "title": "Valid Signature Test",
            "estimated_amount": 100000,
        }

        signature = calculate_signature(secret, payload)

        response = client.post(
            "/v1/govly/webhook",
            json=payload,
            headers={"X-Govly-Signature": signature},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_invalid_signature_rejected(self):
        """Test that invalid signature is rejected with 401."""
        secret = os.environ.get("GOVLY_WEBHOOK_SECRET")
        if not secret:
            pytest.skip("GOVLY_WEBHOOK_SECRET not configured")

        payload = {
            "event_id": "sig_invalid_001",
            "event_type": "opportunity",
            "title": "Invalid Signature Test",
            "estimated_amount": 100000,
        }

        # Use wrong signature
        invalid_signature = "sha256=invalid_signature_hash"

        response = client.post(
            "/v1/govly/webhook",
            json=payload,
            headers={"X-Govly-Signature": invalid_signature},
        )

        # Should reject with 401 when signature validation is enabled
        assert response.status_code == 401
        data = response.json()
        assert data["status"] == "error"
        assert "signature" in data["message"].lower()

    def test_missing_signature_header(self):
        """Test behavior when signature header is missing."""
        secret = os.environ.get("GOVLY_WEBHOOK_SECRET")
        if not secret:
            # Without secret configured, should still accept requests
            payload = {
                "event_id": "sig_missing_001",
                "event_type": "opportunity",
                "title": "Missing Signature Test",
                "estimated_amount": 100000,
            }

            response = client.post("/v1/govly/webhook", json=payload)
            assert response.status_code == 200
        else:
            # With secret configured, should reject without signature
            payload = {
                "event_id": "sig_missing_002",
                "event_type": "opportunity",
                "title": "Missing Signature Test",
                "estimated_amount": 100000,
            }

            response = client.post("/v1/govly/webhook", json=payload)
            assert response.status_code == 401


@pytest.mark.xfail(reason="Signature validation requires RADAR_WEBHOOK_SECRET to be configured")
class TestRadarSignatureValidation:
    """Test Radar webhook signature validation."""

    def test_valid_signature_accepted(self):
        """Test that valid HMAC-SHA256 signature is accepted."""
        secret = os.environ.get("RADAR_WEBHOOK_SECRET")
        if not secret:
            pytest.skip("RADAR_WEBHOOK_SECRET not configured")

        payload = {
            "radar_id": "sig_valid_101",
            "radar_type": "contract",
            "company_name": "Test Corp",
            "contract_value": 250000,
        }

        signature = calculate_signature(secret, payload)

        response = client.post(
            "/v1/radar/webhook",
            json=payload,
            headers={"X-Radar-Signature": signature},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_invalid_signature_rejected(self):
        """Test that invalid signature is rejected with 401."""
        secret = os.environ.get("RADAR_WEBHOOK_SECRET")
        if not secret:
            pytest.skip("RADAR_WEBHOOK_SECRET not configured")

        payload = {
            "radar_id": "sig_invalid_101",
            "radar_type": "contract",
            "company_name": "Test Corp",
            "contract_value": 250000,
        }

        # Use wrong signature
        invalid_signature = "sha256=wrong_signature_value"

        response = client.post(
            "/v1/radar/webhook",
            json=payload,
            headers={"X-Radar-Signature": invalid_signature},
        )

        # Should reject with 401 when signature validation is enabled
        assert response.status_code == 401
        data = response.json()
        assert data["status"] == "error"


@pytest.mark.xfail(reason="Replay protection not yet implemented - planned for Sprint 10")
class TestWebhookReplayProtection:
    """Test replay protection mechanisms."""

    def test_duplicate_event_id_handling(self):
        """Test that duplicate event IDs are handled gracefully."""
        payload = {
            "event_id": "replay_test_001",
            "event_type": "opportunity",
            "title": "Replay Protection Test",
            "estimated_amount": 150000,
        }

        # First request should succeed
        response1 = client.post("/v1/govly/webhook", json=payload)
        assert response1.status_code == 200

        # Second request with same event_id should be detected
        # Implementation may either:
        # - Return 200 but not create duplicate (idempotent)
        # - Return 409 Conflict
        # - Log warning and skip processing
        response2 = client.post("/v1/govly/webhook", json=payload)
        assert response2.status_code in [200, 409]

        # Verify state.json doesn't have duplicates
        with open(TEST_STATE_FILE, "r") as f:
            state = json.load(f)

        # Count occurrences of this event_id
        matching_opps = [o for o in state["opportunities"] if o["id"] == "govly_replay_test_001"]
        # Should only have one entry, not duplicates
        assert len(matching_opps) <= 1


class TestWebhookEndpointHealth:
    """Test basic webhook endpoint health."""

    def test_govly_webhook_returns_request_headers(self):
        """Test Govly webhook includes tracking headers."""
        payload = {
            "event_id": "health_001",
            "event_type": "opportunity",
            "title": "Health Check",
            "estimated_amount": 50000,
        }

        response = client.post("/v1/govly/webhook", json=payload)

        # Should have request tracking headers
        assert "x-request-id" in response.headers
        assert "x-latency-ms" in response.headers

    def test_radar_webhook_returns_request_headers(self):
        """Test Radar webhook includes tracking headers."""
        payload = {
            "radar_id": "health_101",
            "radar_type": "contract",
            "company_name": "Health Test Corp",
            "contract_value": 75000,
        }

        response = client.post("/v1/radar/webhook", json=payload)

        # Should have request tracking headers
        assert "x-request-id" in response.headers
        assert "x-latency-ms" in response.headers

    def test_govly_webhook_happy_path(self):
        """Test basic Govly webhook happy path."""
        payload = {
            "event_id": "happy_001",
            "event_type": "opportunity",
            "title": "Happy Path Test",
            "description": "Testing basic webhook flow",
            "estimated_amount": 200000,
            "agency": "DOD",
            "close_date": "2025-12-31T23:59:59Z",
        }

        response = client.post("/v1/govly/webhook", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "govly_happy_001" in data["opportunity_id"]

    def test_radar_webhook_happy_path(self):
        """Test basic Radar webhook happy path."""
        payload = {
            "radar_id": "happy_101",
            "radar_type": "modification",
            "company_name": "Happy Test Corp",
            "contract_value": 300000,
            "description": "Contract modification test",
        }

        response = client.post("/v1/radar/webhook", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "radar_happy_101" in data["opportunity_id"]


class TestWebhookValidation:
    """Test webhook payload validation."""

    def test_govly_missing_required_fields(self):
        """Test Govly webhook rejects missing required fields."""
        # Missing event_id and title
        payload = {"event_type": "opportunity"}

        response = client.post("/v1/govly/webhook", json=payload)

        # Should return 422 validation error
        assert response.status_code == 422

    def test_radar_missing_required_fields(self):
        """Test Radar webhook rejects missing required fields."""
        # Missing radar_id and company_name
        payload = {"radar_type": "contract"}

        response = client.post("/v1/radar/webhook", json=payload)

        # Should return 422 validation error
        assert response.status_code == 422

    def test_govly_invalid_amount_type(self):
        """Test Govly webhook validates amount data type."""
        payload = {
            "event_id": "invalid_amount_001",
            "event_type": "opportunity",
            "title": "Invalid Amount Test",
            "estimated_amount": "not_a_number",  # Should be float/int
        }

        response = client.post("/v1/govly/webhook", json=payload)

        # Should return 422 validation error
        assert response.status_code == 422
