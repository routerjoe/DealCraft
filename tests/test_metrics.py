"""Tests for Metrics & Latency Monitor endpoints."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mcp.api.main import app

client = TestClient(app)

# Test data
TEST_DATA_DIR = Path("data")
TEST_METRICS_FILE = TEST_DATA_DIR / "metrics.json"


@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Setup and teardown for each test."""
    # Save original
    original_metrics = None
    if TEST_METRICS_FILE.exists():
        with open(TEST_METRICS_FILE, "r") as f:
            original_metrics = f.read()

    # Initialize test metrics
    TEST_DATA_DIR.mkdir(exist_ok=True)
    test_metrics = {
        "requests": [
            {"endpoint": "/v1/forecast/run", "latency_ms": 45.2, "status_code": 200, "timestamp": "2025-10-28T12:00:00"},
            {"endpoint": "/v1/forecast/summary", "latency_ms": 12.5, "status_code": 200, "timestamp": "2025-10-28T12:01:00"},
            {"endpoint": "/v1/govly/webhook", "latency_ms": 150.0, "status_code": 200, "timestamp": "2025-10-28T12:02:00"},
        ],
        "accuracy": {"correct": 85, "incorrect": 10, "unknown": 5},
        "created_at": "2025-10-21T00:00:00",
    }

    with open(TEST_METRICS_FILE, "w") as f:
        json.dump(test_metrics, f)

    yield

    # Restore original
    if original_metrics:
        with open(TEST_METRICS_FILE, "w") as f:
            f.write(original_metrics)
    elif TEST_METRICS_FILE.exists():
        TEST_METRICS_FILE.unlink()


def test_metrics_endpoint_success():
    """Test successful metrics retrieval."""
    response = client.get("/v1/metrics")

    assert response.status_code == 200
    data = response.json()

    assert "timestamp" in data
    assert "latency" in data
    assert "request_volume_last_7d" in data
    assert "request_volume_total" in data
    assert "accuracy_confusion" in data
    assert "endpoints" in data


def test_metrics_latency_stats():
    """Test that metrics include latency statistics."""
    response = client.get("/v1/metrics")

    assert response.status_code == 200
    latency = response.json()["latency"]

    assert "avg_latency_ms" in latency
    assert "p95_latency_ms" in latency
    assert "p99_latency_ms" in latency
    assert "min_latency_ms" in latency
    assert "max_latency_ms" in latency

    # Check values are reasonable
    assert latency["avg_latency_ms"] > 0
    assert latency["p95_latency_ms"] >= latency["avg_latency_ms"]
    assert latency["max_latency_ms"] >= latency["min_latency_ms"]


def test_metrics_accuracy_confusion():
    """Test that metrics include accuracy confusion matrix."""
    response = client.get("/v1/metrics")

    assert response.status_code == 200
    accuracy = response.json()["accuracy_confusion"]

    assert "correct" in accuracy
    assert "incorrect" in accuracy
    assert "unknown" in accuracy

    # Check values from test data
    assert accuracy["correct"] == 85
    assert accuracy["incorrect"] == 10
    assert accuracy["unknown"] == 5


def test_metrics_request_volume():
    """Test that metrics track request volume."""
    response = client.get("/v1/metrics")

    assert response.status_code == 200
    data = response.json()

    assert data["request_volume_total"] == 3  # From test data
    assert data["request_volume_last_7d"] >= 0


def test_metrics_per_endpoint_stats():
    """Test that metrics include per-endpoint statistics."""
    response = client.get("/v1/metrics")

    assert response.status_code == 200
    endpoints = response.json()["endpoints"]

    assert isinstance(endpoints, dict)

    # Check that endpoints have stats
    for endpoint, stats in endpoints.items():
        assert "avg_latency_ms" in stats
        assert "request_count" in stats
        assert "status_codes" in stats


def test_record_accuracy_correct():
    """Test recording correct accuracy result."""
    response = client.post("/v1/metrics/accuracy?result=correct")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "recorded"
    assert data["result"] == "correct"


def test_record_accuracy_incorrect():
    """Test recording incorrect accuracy result."""
    response = client.post("/v1/metrics/accuracy?result=incorrect")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "recorded"
    assert data["result"] == "incorrect"


def test_record_accuracy_unknown():
    """Test recording unknown accuracy result."""
    response = client.post("/v1/metrics/accuracy?result=unknown")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "recorded"
    assert data["result"] == "unknown"


def test_record_accuracy_invalid():
    """Test that invalid accuracy results are rejected."""
    response = client.post("/v1/metrics/accuracy?result=invalid")

    assert response.status_code == 400


def test_metrics_health_check():
    """Test metrics health check endpoint."""
    response = client.get("/v1/metrics/health")

    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert data["status"] == "healthy"
    assert "requests_tracked" in data
    assert "accuracy_total" in data


def test_metrics_with_request_id():
    """Test that metrics endpoint includes request_id in headers."""
    response = client.get("/v1/metrics")

    assert response.status_code == 200
    assert "x-request-id" in response.headers
    assert "x-latency-ms" in response.headers


def test_metrics_empty_state():
    """Test metrics endpoint with empty metrics file."""
    # Clear metrics file
    with open(TEST_METRICS_FILE, "w") as f:
        json.dump({"requests": [], "accuracy": {"correct": 0, "incorrect": 0, "unknown": 0}, "created_at": "2025-10-28T00:00:00"}, f)

    response = client.get("/v1/metrics")

    assert response.status_code == 200
    data = response.json()

    assert data["request_volume_total"] == 0
    assert data["accuracy_confusion"]["correct"] == 0
