"""
Rate limiting tests.

Sprint 15: Production Hardening
Tests for rate limiting middleware functionality.
"""

import json
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mcp.api.main import app
from mcp.api.middleware import rate_limit

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


class TestRateLimitingGeneral:
    """Test rate limiting for GENERAL endpoints."""

    def test_general_endpoint_rate_limit(self, monkeypatch):
        """Test that GENERAL endpoints enforce 100 req/min limit."""
        # Fix time to a specific minute
        fixed_time = 1000000.0  # Some fixed epoch time
        monkeypatch.setattr(time, "time", lambda: fixed_time)

        # Clear any existing buckets
        rate_limit._buckets.clear()

        # Make 100 requests - should all succeed
        success_count = 0
        for i in range(100):
            response = client.get("/v1/info")
            if response.status_code == 200:
                success_count += 1

        assert success_count == 100, "First 100 requests should succeed"

        # 101st request should be rate limited
        response = client.get("/v1/info")
        assert response.status_code == 429
        data = response.json()
        assert data["error"] == "rate_limited"
        assert "GENERAL" in data["message"]
        assert data["limit"] == 100
        assert "retry_after" in data

    def test_rate_limit_window_reset(self, monkeypatch):
        """Test that rate limit resets after minute window."""
        # Start at minute 0
        fixed_time = [1000000.0]  # Use list to allow modification

        def mock_time():
            return fixed_time[0]

        monkeypatch.setattr(time, "time", mock_time)

        # Clear buckets
        rate_limit._buckets.clear()

        # Fill up the bucket (100 requests)
        for i in range(100):
            response = client.get("/v1/info")
            assert response.status_code == 200

        # Next request should fail
        response = client.get("/v1/info")
        assert response.status_code == 429

        # Advance time by 61 seconds (next minute)
        fixed_time[0] += 61

        # Should work again
        response = client.get("/v1/info")
        assert response.status_code == 200


class TestRateLimitingWebhooks:
    """Test rate limiting for WEBHOOK endpoints."""

    def test_webhook_endpoint_higher_limit(self, monkeypatch):
        """Test that WEBHOOK endpoints have 1000 req/min limit."""
        # Fix time
        fixed_time = 2000000.0
        monkeypatch.setattr(time, "time", lambda: fixed_time)

        # Clear buckets
        rate_limit._buckets.clear()

        # Make 200 requests to webhook - should all succeed (well under 1000 limit)
        success_count = 0
        for i in range(200):
            response = client.post(
                "/v1/govly/webhook",
                json={
                    "event_id": f"test_{i}",
                    "event_type": "opportunity",
                    "title": "Test Opportunity",
                    "estimated_amount": 100000,
                },
            )
            if response.status_code == 200:
                success_count += 1

        assert success_count == 200, "First 200 webhook requests should succeed"

        # Make 800 more to reach limit (total 1000)
        for i in range(800):
            response = client.post(
                "/v1/govly/webhook",
                json={
                    "event_id": f"test_{i + 200}",
                    "event_type": "opportunity",
                    "title": "Test Opportunity",
                    "estimated_amount": 100000,
                },
            )
            if response.status_code != 200:
                break
        else:
            # All 800 should succeed
            pass

        # 1001st request should be rate limited
        response = client.post(
            "/v1/govly/webhook",
            json={
                "event_id": "test_1001",
                "event_type": "opportunity",
                "title": "Test Opportunity",
                "estimated_amount": 100000,
            },
        )
        assert response.status_code == 429
        data = response.json()
        assert data["error"] == "rate_limited"
        assert "WEBHOOKS" in data["message"]
        assert data["limit"] == 1000


class TestRateLimitingAI:
    """Test rate limiting for AI endpoints."""

    def test_ai_endpoint_lower_limit(self, monkeypatch):
        """Test that AI endpoints have 20 req/min limit."""
        # Fix time
        fixed_time = 3000000.0
        monkeypatch.setattr(time, "time", lambda: fixed_time)

        # Clear buckets
        rate_limit._buckets.clear()

        # Make 20 requests - should all succeed
        success_count = 0
        for i in range(20):
            response = client.post(
                "/v1/ai/ask",
                json={"question": f"Test question {i}", "model": "gpt-4-turbo"},
            )
            # AI endpoint may return 422 if validation fails, but shouldn't rate limit
            if response.status_code in [200, 422]:
                success_count += 1

        assert success_count == 20, "First 20 AI requests should not be rate limited"

        # 21st request should be rate limited
        response = client.post(
            "/v1/ai/ask",
            json={"question": "Test question 21", "model": "gpt-4-turbo"},
        )
        assert response.status_code == 429
        data = response.json()
        assert data["error"] == "rate_limited"
        assert "AI" in data["message"]
        assert data["limit"] == 20


class TestRateLimitClassification:
    """Test route classification logic."""

    def test_classify_webhook_routes(self):
        """Test that webhook routes are classified correctly."""
        assert rate_limit.classify_path("/v1/govly/webhook") == "WEBHOOKS"
        assert rate_limit.classify_path("/v1/radar/webhook") == "WEBHOOKS"
        assert rate_limit.classify_path("/webhook/test") == "WEBHOOKS"

    def test_classify_ai_routes(self):
        """Test that AI routes are classified correctly."""
        assert rate_limit.classify_path("/v1/ai/ask") == "AI"
        assert rate_limit.classify_path("/v1/ai/models") == "AI"
        assert rate_limit.classify_path("/v1/ai/guidance") == "AI"

    def test_classify_general_routes(self):
        """Test that general routes are classified correctly."""
        assert rate_limit.classify_path("/v1/info") == "GENERAL"
        assert rate_limit.classify_path("/v1/oems") == "GENERAL"
        assert rate_limit.classify_path("/v1/contracts") == "GENERAL"
        assert rate_limit.classify_path("/healthz") == "GENERAL"


class TestRateLimitResponse:
    """Test rate limit response format."""

    def test_rate_limit_response_format(self, monkeypatch):
        """Test that rate limit response has correct format."""
        # Fix time
        fixed_time = 4000000.0
        monkeypatch.setattr(time, "time", lambda: fixed_time)

        # Clear buckets
        rate_limit._buckets.clear()

        # Exhaust GENERAL limit
        for i in range(100):
            client.get("/v1/info")

        # Get rate limited response
        response = client.get("/v1/info")
        assert response.status_code == 429

        # Check response structure
        data = response.json()
        assert "error" in data
        assert data["error"] == "rate_limited"
        assert "message" in data
        assert "retry_after" in data
        assert "limit" in data

        # Check headers
        assert "Retry-After" in response.headers
        retry_after = int(response.headers["Retry-After"])
        assert 0 < retry_after <= 60


class TestRateLimitBucketCleanup:
    """Test that old buckets are cleaned up."""

    def test_bucket_cleanup(self, monkeypatch):
        """Test that buckets older than 2 minutes are cleaned up."""
        # Start at minute 1000
        fixed_time = [60000.0]  # Minute 1000

        def mock_time():
            return fixed_time[0]

        monkeypatch.setattr(time, "time", mock_time)

        # Clear buckets
        rate_limit._buckets.clear()

        # Make a request at minute 1000
        client.get("/v1/info")
        assert len(rate_limit._buckets) == 1

        # Advance to minute 1003 (3 minutes later)
        fixed_time[0] = 60000.0 + (3 * 60)

        # Make another request - should clean up old bucket
        client.get("/v1/info")

        # Should only have current minute's bucket
        current_minute = int(fixed_time[0] / 60)
        buckets = [k for k in rate_limit._buckets.keys()]
        assert len(buckets) <= 2  # Current minute + maybe one more
        assert all(k[1] >= current_minute - 2 for k in buckets)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
