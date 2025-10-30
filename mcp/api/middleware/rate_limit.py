"""
Rate limiting middleware for MCP API endpoints.

Implements token bucket rate limiting with per-route-group limits.
Uses in-memory storage (keyed by route group and minute window).
"""

import time
from typing import Dict, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

# Rate limits per minute for each route group
RATE_LIMITS = {
    "GENERAL": 100,
    "WEBHOOKS": 1000,  # High volume endpoints like /v1/govly/webhook, /v1/radar/webhook
    "AI": 20,  # AI endpoints like /v1/ai/*
}

# In-memory token bucket storage: {(group, minute): count}
_buckets: Dict[Tuple[str, int], int] = {}


def classify_path(path: str) -> str:
    """
    Classify request path into a rate limit group.

    Args:
        path: Request path (e.g., "/v1/ai/analyze")

    Returns:
        Group name: "WEBHOOKS", "AI", or "GENERAL"
    """
    if "/webhook" in path:
        return "WEBHOOKS"
    if path.startswith("/v1/ai/"):
        return "AI"
    return "GENERAL"


def get_current_minute() -> int:
    """Get current minute as integer (epoch seconds / 60)."""
    return int(time.time() / 60)


def check_rate_limit(group: str, current_minute: int) -> Tuple[bool, int]:
    """
    Check if request is within rate limit.

    Args:
        group: Rate limit group name
        current_minute: Current minute bucket

    Returns:
        Tuple of (allowed: bool, retry_after_seconds: int)
    """
    limit = RATE_LIMITS[group]
    key = (group, current_minute)

    # Get current count, default to 0
    count = _buckets.get(key, 0)

    if count >= limit:
        # Rate limit exceeded
        seconds_into_minute = int(time.time() % 60)
        retry_after = 60 - seconds_into_minute
        return False, retry_after

    # Increment counter
    _buckets[key] = count + 1

    # Clean up old buckets (older than 2 minutes)
    old_cutoff = current_minute - 2
    keys_to_delete = [k for k in _buckets if k[1] < old_cutoff]
    for k in keys_to_delete:
        del _buckets[k]

    return True, 0


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce rate limits on API endpoints.

    Rate limits are applied per route group per minute:
    - GENERAL: 100 req/min
    - WEBHOOKS: 1000 req/min
    - AI: 20 req/min
    """

    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        path = request.url.path

        # Classify the route
        group = classify_path(path)
        current_minute = get_current_minute()

        # Check rate limit
        allowed, retry_after = check_rate_limit(group, current_minute)

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limited",
                    "message": f"Rate limit exceeded for {group} endpoints",
                    "retry_after": retry_after,
                    "limit": RATE_LIMITS[group],
                },
                headers={"Retry-After": str(retry_after)},
            )

        # Process request normally
        response = await call_next(request)
        return response
