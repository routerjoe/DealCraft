import logging
import os
import time
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from mcp.api.middleware.rate_limit import RateLimitMiddleware
from mcp.core.log_filters import install_redacting_filter
from mcp.core.store import read_json, write_json

# Install redacting filter on root logger to protect all logs
install_redacting_filter()

logger = logging.getLogger(__name__)

# File path for state storage
STATE_FILE = "data/state.json"

# Routers
try:
    from mcp.api.v1.oems import router as oems_router
except Exception:
    oems_router = None

try:
    from mcp.api.v1.oems_ex import router as oems_ex_router
except Exception:
    oems_ex_router = None

try:
    from mcp.api.v1.contracts import router as contracts_router
except Exception:
    contracts_router = None

try:
    from mcp.api.v1.ai import router as ai_router
except Exception:
    ai_router = None

try:
    from mcp.api.v1.email import router as email_router
except Exception:
    email_router = None

try:
    from mcp.api.v1.obsidian import router as obsidian_router
except Exception:
    obsidian_router = None

try:
    from mcp.api.v1.contacts import router as contacts_router
except Exception:
    contacts_router = None

try:
    from mcp.api.v1.system import router as system_router
except Exception:
    system_router = None

try:
    from mcp.api.v1.forecast import router as forecast_router
except Exception:
    forecast_router = None

try:
    from mcp.api.v1.webhooks import router as webhooks_router
except Exception:
    webhooks_router = None

try:
    from mcp.api.v1.metrics import router as metrics_router
except Exception:
    metrics_router = None

try:
    from mcp.api.v1.crm import router as crm_router
except Exception:
    crm_router = None

try:
    from mcp.api.v1.cv import router as cv_router
except Exception:
    cv_router = None

try:
    from mcp.api.v1.account_plans import router as account_plans_router
except Exception:
    account_plans_router = None

try:
    from mcp.api.v1.partners import router as partners_router
except Exception:
    partners_router = None

try:
    from mcp.api.v1.partners_intel import router as partners_intel_router
except Exception:
    partners_intel_router = None


app = FastAPI(title="Red River Sales MCP API", version="2.0.0-rc2")

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)


def log_action_to_state(
    request_id: str,
    method: str,
    path: str,
    latency_ms: int,
    status_code: int,
    context: dict = None,
):
    """
    Log an action to state.json with automatic rotation (max 10 entries).

    Args:
        request_id: Unique request identifier
        method: HTTP method
        path: Request path
        latency_ms: Request latency in milliseconds
        status_code: HTTP status code
        context: Additional context (optional)
    """
    try:
        # Read current state
        try:
            state = read_json(STATE_FILE)
        except FileNotFoundError:
            state = {}

        # Get existing actions or initialize
        recent_actions = state.get("recent_actions", [])

        # Create new action entry
        action = {
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "method": method,
            "path": path,
            "latency_ms": latency_ms,
            "status_code": status_code,
            "context": context or {},
        }

        # Add to beginning of list
        recent_actions.insert(0, action)

        # Keep only last 10 entries (rotation)
        recent_actions = recent_actions[:10]

        # Update state
        state["recent_actions"] = recent_actions

        # Write back to storage
        write_json(STATE_FILE, state)

    except Exception as e:
        logger.error(f"Failed to log action to state: {str(e)}")


# Middleware: add request_id + latency_ms to every response and log actions
@app.middleware("http")
async def add_request_id_and_latency(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start = time.perf_counter()

    # Process request
    response = await call_next(request)

    # Calculate latency
    latency_ms = int((time.perf_counter() - start) * 1000)

    # Add headers
    response.headers["x-request-id"] = request_id
    response.headers["x-latency-ms"] = str(latency_ms)

    # Log action (skip health checks and static routes)
    if not request.url.path.startswith("/healthz"):
        log_action_to_state(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            latency_ms=latency_ms,
            status_code=response.status_code,
            context={"query": str(request.url.query)} if request.url.query else {},
        )

    return response


# Health
@app.get("/healthz")
async def healthz(_: Request):
    # Tests expect exactly {"status":"healthy"}
    return {"status": "healthy"}


# Info
@app.get("/v1/info")
async def api_info(request: Request):
    environment = os.getenv("ENVIRONMENT", os.getenv("APP_ENV", "dev"))
    return JSONResponse(
        content={
            "name": "Red River Sales MCP API",
            "version": "2.0.0-rc2",
            "environment": environment,
            "endpoints": [
                "/healthz",
                "/v1/info",
                "/v1/oems",
                "/v1/oems/all",
                "/v1/oems/add",
                "/v1/oems/{name}",
                "/v1/oems/export/obsidian",
                "/v1/contracts",
                "/v1/contracts/{name}",
                "/v1/ai/models",
                "/v1/ai/models/detailed",
                "/v1/ai/guidance",
                "/v1/ai/ask",
                "/v1/email/rfq/ingest",
                "/v1/email/govly/ingest",
                "/v1/email/intromail/ingest",
                "/v1/obsidian/opportunity",
                "/v1/obsidian/sync/summary",
                "/v1/contacts/export.csv",
                "/v1/contacts/export.vcf",
                "/v1/system/recent-actions",
                "/v1/forecast/run",
                "/v1/forecast/summary",
                "/v1/forecast/all",
                "/v1/forecast/top",
                "/v1/forecast/FY{fiscal_year}",
                "/v1/forecast/export/csv",
                "/v1/forecast/export/obsidian",
                "/v1/crm/export",
                "/v1/crm/attribution",
                "/v1/crm/formats",
                "/v1/crm/validate/{opportunity_id}",
                "/v1/cv/recommend",
                "/v1/cv/vehicles",
                "/v1/cv/vehicles/{vehicle_name}",
                "/v1/govly/webhook",
                "/v1/radar/webhook",
                "/v1/metrics",
                "/v1/metrics/accuracy",
                "/v1/metrics/health",
                "/v1/account-plans/formats",
                "/v1/account-plans/generate",
                "/v1/partners/tiers",
                "/v1/partners/sync",
                "/v1/partners/export/obsidian",
                "/v1/partners/intel/scores",
                "/v1/partners/intel/graph",
                "/v1/partners/intel/enrich",
                "/v1/partners/intel/export/obsidian",
            ],
        },
        headers={"x-request-id": request.headers.get("x-request-id", "")},
    )


# Mount routers if present
if oems_router is not None:
    app.include_router(oems_router, prefix="/v1", tags=["oems"])
if oems_ex_router is not None:
    app.include_router(oems_ex_router, prefix="/v1", tags=["oems_ex"])
if contracts_router is not None:
    app.include_router(contracts_router, prefix="/v1", tags=["contracts"])
if ai_router is not None:
    app.include_router(ai_router, prefix="/v1", tags=["ai"])
if email_router is not None:
    app.include_router(email_router, prefix="/v1", tags=["email"])
if obsidian_router is not None:
    app.include_router(obsidian_router)  # already includes prefix="/v1" internally
if contacts_router is not None:
    app.include_router(contacts_router, prefix="/v1", tags=["contacts"])
if system_router is not None:
    app.include_router(system_router, prefix="/v1", tags=["system"])
if forecast_router is not None:
    app.include_router(forecast_router, tags=["forecast"])
if webhooks_router is not None:
    app.include_router(webhooks_router, tags=["webhooks"])
if metrics_router is not None:
    app.include_router(metrics_router, tags=["metrics"])
if crm_router is not None:
    app.include_router(crm_router, tags=["crm"])
if cv_router is not None:
    app.include_router(cv_router, tags=["contract_vehicles"])
if account_plans_router is not None:
    app.include_router(account_plans_router, tags=["account_plans"])
if partners_router is not None:
    app.include_router(partners_router, tags=["partners"])
if partners_intel_router is not None:
    app.include_router(partners_intel_router, tags=["partners_intel"])
