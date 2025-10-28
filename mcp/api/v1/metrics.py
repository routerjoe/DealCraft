"""
Metrics & Latency Monitor
Tracks API performance, request volume, and accuracy metrics.
"""

import json
import logging
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/metrics", tags=["metrics"])

METRICS_FILE = Path("data/metrics.json")


def load_metrics() -> Dict[str, Any]:
    """Load metrics from persistent storage."""
    if not METRICS_FILE.exists():
        return {
            "requests": [],
            "accuracy": {"correct": 0, "incorrect": 0, "unknown": 0},
            "created_at": datetime.utcnow().isoformat(),
        }
    try:
        with open(METRICS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {
            "requests": [],
            "accuracy": {"correct": 0, "incorrect": 0, "unknown": 0},
            "created_at": datetime.utcnow().isoformat(),
        }


def save_metrics(metrics: Dict[str, Any]) -> None:
    """Save metrics to persistent storage with atomic write."""
    METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp_file = METRICS_FILE.with_suffix(".tmp")
    try:
        with open(temp_file, "w") as f:
            json.dump(metrics, f, indent=2)
        temp_file.replace(METRICS_FILE)
    except IOError as e:
        logger.error(f"Failed to save metrics: {e}")


def record_request(endpoint: str, latency_ms: float, status_code: int) -> None:
    """Record a request for metrics tracking."""
    metrics = load_metrics()
    metrics["requests"].append(
        {
            "endpoint": endpoint,
            "latency_ms": latency_ms,
            "status_code": status_code,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )
    # Keep only last 1000 requests
    if len(metrics["requests"]) > 1000:
        metrics["requests"] = metrics["requests"][-1000:]
    save_metrics(metrics)


def record_accuracy(result: str) -> None:
    """Record accuracy result: 'correct', 'incorrect', or 'unknown'."""
    if result not in ["correct", "incorrect", "unknown"]:
        logger.warning(f"Invalid accuracy result: {result}")
        return
    metrics = load_metrics()
    metrics["accuracy"][result] = metrics["accuracy"].get(result, 0) + 1
    save_metrics(metrics)


def get_latency_stats(requests: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate latency statistics."""
    if not requests:
        return {"avg_latency_ms": 0.0, "p95_latency_ms": 0.0, "p99_latency_ms": 0.0}

    latencies = [r["latency_ms"] for r in requests]
    sorted_latencies = sorted(latencies)

    return {
        "avg_latency_ms": round(statistics.mean(latencies), 2),
        "p95_latency_ms": round(sorted_latencies[int(len(sorted_latencies) * 0.95)], 2),
        "p99_latency_ms": round(sorted_latencies[int(len(sorted_latencies) * 0.99)], 2),
        "min_latency_ms": round(min(latencies), 2),
        "max_latency_ms": round(max(latencies), 2),
    }


@router.get("")
async def get_metrics() -> Dict[str, Any]:
    """
    Get comprehensive metrics including latency, request volume, and accuracy.

    Returns:
        - avg_latency_ms: Average latency across all requests
        - p95_latency_ms: 95th percentile latency
        - p99_latency_ms: 99th percentile latency
        - request_volume_last_7d: Number of requests in last 7 days
        - request_volume_total: Total requests recorded
        - accuracy_confusion: Accuracy tracking (correct, incorrect, unknown)
        - endpoints: Per-endpoint statistics
    """
    metrics = load_metrics()

    # Filter requests from last 7 days
    now = datetime.utcnow()
    seven_days_ago = now - timedelta(days=7)
    recent_requests = [r for r in metrics["requests"] if datetime.fromisoformat(r["timestamp"]) >= seven_days_ago]

    # Calculate per-endpoint stats
    endpoint_stats = {}
    for req in metrics["requests"]:
        endpoint = req["endpoint"]
        if endpoint not in endpoint_stats:
            endpoint_stats[endpoint] = []
        endpoint_stats[endpoint].append(req)

    endpoints = {
        endpoint: {
            **get_latency_stats(reqs),
            "request_count": len(reqs),
            "status_codes": {str(r["status_code"]): sum(1 for x in reqs if x["status_code"] == r["status_code"]) for r in reqs},
        }
        for endpoint, reqs in endpoint_stats.items()
    }

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "latency": get_latency_stats(metrics["requests"]),
        "request_volume_last_7d": len(recent_requests),
        "request_volume_total": len(metrics["requests"]),
        "accuracy_confusion": metrics["accuracy"],
        "endpoints": endpoints,
    }


@router.post("/accuracy")
async def record_accuracy_result(result: str) -> Dict[str, str]:
    """
    Record an accuracy result for tracking model/prediction performance.

    Args:
        result: One of 'correct', 'incorrect', or 'unknown'

    Returns:
        Confirmation message
    """
    if result not in ["correct", "incorrect", "unknown"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid result. Must be one of: correct, incorrect, unknown",
        )

    record_accuracy(result)
    logger.info(f"Recorded accuracy result: {result}")

    return {"status": "recorded", "result": result}


@router.get("/health")
async def metrics_health() -> Dict[str, str]:
    """Health check for metrics system."""
    try:
        metrics = load_metrics()
        return {
            "status": "healthy",
            "requests_tracked": str(len(metrics["requests"])),
            "accuracy_total": str(sum(metrics["accuracy"].values())),
        }
    except Exception as e:
        logger.error(f"Metrics health check failed: {e}")
        raise HTTPException(status_code=500, detail="Metrics system unhealthy")
