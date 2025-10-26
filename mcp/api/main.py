import os
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Routers
try:
    from mcp.api.v1.oems import router as oems_router
except Exception:
    oems_router = None

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


app = FastAPI(title="Red River Sales MCP API", version="1.0.0")


# Middleware: add request_id + latency_ms to every response
@app.middleware("http")
async def add_request_id_and_latency(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start = time.perf_counter()
    response = await call_next(request)
    latency_ms = int((time.perf_counter() - start) * 1000)
    response.headers["x-request-id"] = request_id
    response.headers["x-latency-ms"] = str(latency_ms)
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
            "version": "1.0.0",
            "environment": environment,
            "endpoints": [
                "/v1/oems",
                "/v1/contracts",
                "/v1/ai/models",
                "/v1/ai/guidance",
                "/v1/email/rfq/ingest",
                "/v1/email/govly/ingest",
                "/v1/email/intromail/ingest",
                "/v1/obsidian/opportunity",
                "/v1/contacts/export.csv",
                "/v1/contacts/export.vcf",
            ],
        },
        headers={"x-request-id": request.headers.get("x-request-id", "")},
    )


# Mount routers if present
if oems_router is not None:
    app.include_router(oems_router, prefix="/v1", tags=["oems"])
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
