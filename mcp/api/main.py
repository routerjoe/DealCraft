"""Red River Sales MCP API - FastAPI application."""

import time
import uuid
from typing import Dict

from fastapi import FastAPI, Request

from mcp.api.v1 import ai, contacts, contracts, oems
from mcp.core.config import config
from mcp.core.logging import log_request

# Create FastAPI app
app = FastAPI(
    title="Red River Sales MCP API",
    description="Model Context Protocol API for Red River Sales Automation",
    version="1.0.0",
)

# Include v1 routers
app.include_router(oems.router, prefix="/v1")
app.include_router(contracts.router, prefix="/v1")
app.include_router(ai.router, prefix="/v1")
app.include_router(contacts.router, prefix="/v1")


@app.middleware("http")
async def request_tracking_middleware(request: Request, call_next):
    """Add request_id and measure latency for all requests."""
    # Generate unique request ID
    request_id = str(uuid.uuid4())

    # Add request_id to request state for access in routes
    request.state.request_id = request_id

    # Measure request latency
    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Calculate latency in milliseconds
    latency_ms = round((time.time() - start_time) * 1000, 2)

    # Add X-Request-ID header to response
    response.headers["X-Request-ID"] = request_id

    # Log the request
    log_request(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        latency_ms=latency_ms,
    )

    return response


@app.get("/healthz", tags=["Health"])
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/v1/info", tags=["Info"])
async def api_info() -> Dict[str, str]:
    """API information endpoint."""
    return {
        "name": "Red River Sales MCP API",
        "version": "1.0.0",
        "environment": config.environment,
    }
