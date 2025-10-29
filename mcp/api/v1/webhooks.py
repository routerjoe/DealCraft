"""
Webhook ingestion for Govly and Radar events.
Parses events into append-only opportunities list in state.json.
Auto-generates minimal opportunity.md with triage flag.

Sprint 10: Added HMAC-SHA256 signature verification, replay protection,
FY routing, and dry-run support.
"""

import hashlib
import hmac
import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, Optional, Tuple

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["webhooks"])

# ============================================================================
# Replay Protection Cache
# ============================================================================

# In-memory nonce cache: {(source, event_id): timestamp}
# Entries expire after 5 minutes
_nonce_cache: Dict[Tuple[str, str], float] = {}
NONCE_TTL_SECONDS = 300  # 5 minutes


def _cleanup_nonce_cache() -> None:
    """Remove expired entries from nonce cache."""
    current_time = time.time()
    expired = [k for k, v in _nonce_cache.items() if current_time - v > NONCE_TTL_SECONDS]
    for key in expired:
        del _nonce_cache[key]


def _check_replay(source: str, event_id: str) -> bool:
    """
    Check if event has been seen before (replay attack).

    Returns True if replay detected, False if new event.
    """
    _cleanup_nonce_cache()
    key = (source, event_id)
    if key in _nonce_cache:
        return True
    _nonce_cache[key] = time.time()
    return False


# ============================================================================
# Signature Verification
# ============================================================================


def _verify_signature(
    secret: str,
    signature_header: Optional[str],
    body: bytes,
    secret_v2: Optional[str] = None,
) -> bool:
    """
    Verify HMAC-SHA256 signature.

    Supports dual-key rotation: tries primary secret, then fallback secret_v2.

    Args:
        secret: Primary webhook secret
        signature_header: X-Govly-Signature or X-Radar-Signature header value
        body: Raw request body bytes
        secret_v2: Optional fallback secret for rotation

    Returns:
        True if signature is valid, False otherwise
    """
    if not signature_header:
        return False

    # Extract hex digest from "sha256=<digest>" format
    if not signature_header.startswith("sha256="):
        return False

    received_signature = signature_header[7:]  # Remove "sha256=" prefix

    # Try primary secret
    calculated = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    if hmac.compare_digest(calculated, received_signature):
        return True

    # Try fallback secret if provided (for rotation)
    if secret_v2:
        calculated_v2 = hmac.new(secret_v2.encode("utf-8"), body, hashlib.sha256).hexdigest()
        if hmac.compare_digest(calculated_v2, received_signature):
            logger.info("Webhook authenticated with fallback secret (rotation in progress)")
            return True

    return False


# ============================================================================
# FY Routing Logic
# ============================================================================


def _calculate_fy(close_date: Optional[str]) -> Optional[str]:
    """
    Calculate Federal Fiscal Year from close date.

    Federal FY runs Oct 1 (N-1) to Sep 30 (N).

    Args:
        close_date: ISO 8601 date string or None

    Returns:
        "FY26", "FY27", etc., or None if invalid date
    """
    if not close_date:
        return None

    try:
        dt = datetime.fromisoformat(close_date.replace("Z", "+00:00"))
        if dt.month >= 10:  # Oct, Nov, Dec
            return f"FY{dt.year + 1}"
        else:  # Jan-Sep
            return f"FY{dt.year}"
    except (ValueError, AttributeError):
        return None


def _get_opportunity_path(fy: Optional[str], opp_id: str) -> str:
    """
    Get Obsidian file path for opportunity based on FY routing.

    Args:
        fy: Federal fiscal year (e.g., "FY26") or None
        opp_id: Opportunity ID

    Returns:
        File path relative to project root
    """
    base = "obsidian/40 Projects/Opportunities"
    if fy:
        return os.path.join(base, fy, f"{opp_id}.md")
    else:
        return os.path.join(base, "Triage", f"{opp_id}.md")


# ============================================================================
# Data Models
# ============================================================================


class GovlyWebhookPayload(BaseModel):
    """Govly event webhook payload."""

    event_id: str = Field(..., description="Unique event identifier")
    event_type: str = Field(..., description="Event type (e.g., 'opportunity', 'update')")
    title: str = Field(..., description="Opportunity title")
    description: Optional[str] = Field(None, description="Opportunity description")
    estimated_amount: Optional[float] = Field(None, description="Estimated contract amount")
    agency: Optional[str] = Field(None, description="Federal agency name")
    posted_date: Optional[str] = Field(None, description="ISO 8601 date posted")
    close_date: Optional[str] = Field(None, description="ISO 8601 close date")
    source_url: Optional[str] = Field(None, description="Source URL")


class RadarWebhookPayload(BaseModel):
    """Radar event webhook payload."""

    radar_id: str = Field(..., description="Unique radar identifier")
    radar_type: str = Field(..., description="Radar type (e.g., 'contract', 'modification')")
    company_name: str = Field(..., description="Company name")
    contract_value: Optional[float] = Field(None, description="Contract value")
    contract_date: Optional[str] = Field(None, description="ISO 8601 contract date")
    description: Optional[str] = Field(None, description="Contract description")
    source_url: Optional[str] = Field(None, description="Source URL")


class WebhookResponse(BaseModel):
    """Standard webhook response."""

    status: str = Field(..., description="Status: 'success' or 'error'")
    opportunity_id: Optional[str] = Field(None, description="Created opportunity ID")
    message: str = Field(..., description="Response message")
    dry_run: Optional[bool] = Field(None, description="Whether this was a dry-run request")
    fy_route: Optional[str] = Field(None, description="Federal Fiscal Year routing")


class ReplayErrorResponse(BaseModel):
    """Replay detection error response."""

    error: str = Field(default="replay_detected", description="Error type")
    message: str = Field(..., description="Error message")
    opportunity_id: Optional[str] = Field(None, description="Duplicate opportunity ID")


# ============================================================================
# State Management
# ============================================================================


def load_state() -> dict:
    """Load state.json with fallback to empty structure."""
    state_file = "data/state.json"
    if os.path.exists(state_file):
        try:
            with open(state_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load state.json: {e}")
    return {"opportunities": [], "recent_actions": []}


def save_state(state: dict) -> None:
    """Atomically save state.json."""
    state_file = "data/state.json"
    os.makedirs(os.path.dirname(state_file), exist_ok=True)
    temp_file = f"{state_file}.tmp"
    try:
        with open(temp_file, "w") as f:
            json.dump(state, f, indent=2)
        os.replace(temp_file, state_file)
    except IOError as e:
        logger.error(f"Failed to save state.json: {e}")
        raise


def generate_opportunity_id(source: str, external_id: str) -> str:
    """Generate unique opportunity ID from source and external ID."""
    return f"{source}_{external_id}".lower().replace(" ", "_")


def create_minimal_opportunity_md(opp_id: str, title: str, source: str) -> str:
    """Generate minimal opportunity.md content."""
    timestamp = datetime.utcnow().isoformat()
    return f"""---
id: {opp_id}
title: {title}
source: {source}
triage: true
created_at: {timestamp}
status: triage
---

# {title}

**Source:** {source}
**Status:** Triage
**Created:** {timestamp}

## Summary

Auto-ingested from {source} webhook. Awaiting manual review and enrichment.

## Next Steps

1. Review opportunity details
2. Validate estimated amount and close date
3. Assign to appropriate FY folder
4. Update triage flag to false when ready
"""


# ============================================================================
# Govly Webhook Handler
# ============================================================================


@router.post("/govly/webhook", response_model=WebhookResponse)
async def govly_webhook(
    payload: GovlyWebhookPayload,
    x_govly_signature: Optional[str] = Header(None, alias="X-Govly-Signature"),
    x_request_id: str = Header(None),
    dry_run: bool = Query(False, description="Dry-run mode (no writes)"),
) -> WebhookResponse:
    """
    Ingest Govly federal opportunity events.

    Sprint 10 Features:
    - HMAC-SHA256 signature verification (X-Govly-Signature header)
    - Replay protection (5-minute nonce cache)
    - Federal FY routing based on close_date
    - Dry-run mode support (query param: ?dry_run=true)

    **Payload Example:**
    ```json
    {
      "event_id": "govly_12345",
      "event_type": "opportunity",
      "title": "IT Services RFQ",
      "description": "Federal IT services contract",
      "estimated_amount": 500000,
      "agency": "GSA",
      "posted_date": "2025-10-28T00:00:00Z",
      "close_date": "2025-11-15T23:59:59Z",
      "source_url": "https://govly.example.com/opp/12345"
    }
    ```
    """
    try:
        # 1. Signature verification (if secret configured)
        govly_secret = os.environ.get("GOVLY_WEBHOOK_SECRET")
        govly_secret_v2 = os.environ.get("GOVLY_SECRET_V2")

        if govly_secret:
            # Reconstruct request body for signature verification
            body = json.dumps(payload.dict()).encode("utf-8")

            if not _verify_signature(govly_secret, x_govly_signature, body, govly_secret_v2):
                logger.warning(f"Invalid Govly webhook signature for event {payload.event_id}")
                raise HTTPException(
                    status_code=401,
                    detail={"status": "error", "message": "Invalid webhook signature"},
                )

        opp_id = generate_opportunity_id("govly", payload.event_id)

        # 2. Replay protection
        if _check_replay("govly", payload.event_id):
            logger.warning(f"Replay detected for Govly event: {payload.event_id}")
            raise HTTPException(
                status_code=409,
                detail={"error": "replay_detected", "message": f"Event {payload.event_id} already processed"},
            )

        # 3. Calculate FY routing
        fy = _calculate_fy(payload.close_date)

        # 4. Dry-run mode: preview actions without writing
        if dry_run:
            logger.info(f"Dry-run: Govly webhook {opp_id} (FY: {fy or 'Triage'})")
            return WebhookResponse(
                status="success",
                opportunity_id=opp_id,
                message=f"Dry-run: Govly opportunity {opp_id} would be ingested",
                dry_run=True,
                fy_route=fy or "Triage",
            )

        # 5. Load current state
        state = load_state()

        # 6. Create opportunity record
        opportunity = {
            "id": opp_id,
            "title": payload.title,
            "source": "govly",
            "source_id": payload.event_id,
            "description": payload.description,
            "estimated_amount": payload.estimated_amount,
            "agency": payload.agency,
            "posted_date": payload.posted_date,
            "close_date": payload.close_date,
            "source_url": payload.source_url,
            "triage": fy is None,  # Triage if no FY routing
            "fy": fy,
            "created_at": datetime.utcnow().isoformat(),
            "request_id": x_request_id,
        }

        # 7. Append to opportunities list
        state["opportunities"].append(opportunity)

        # 8. Save state
        save_state(state)

        # 9. Generate minimal opportunity.md with FY routing
        md_path = _get_opportunity_path(fy, opp_id)
        os.makedirs(os.path.dirname(md_path), exist_ok=True)
        with open(md_path, "w") as f:
            f.write(create_minimal_opportunity_md(opp_id, payload.title, "Govly"))

        logger.info(f"Govly webhook ingested: {opp_id} (FY: {fy or 'Triage'}, request_id: {x_request_id})")

        return WebhookResponse(
            status="success",
            opportunity_id=opp_id,
            message=f"Govly opportunity {opp_id} ingested and triaged",
            fy_route=fy,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Govly webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Radar Webhook Handler
# ============================================================================


@router.post("/radar/webhook", response_model=WebhookResponse)
async def radar_webhook(
    payload: RadarWebhookPayload,
    x_radar_signature: Optional[str] = Header(None, alias="X-Radar-Signature"),
    x_request_id: str = Header(None),
    dry_run: bool = Query(False, description="Dry-run mode (no writes)"),
) -> WebhookResponse:
    """
    Ingest Radar contract modification events.

    Sprint 10 Features:
    - HMAC-SHA256 signature verification (X-Radar-Signature header)
    - Replay protection (5-minute nonce cache)
    - Federal FY routing based on contract_date
    - Dry-run mode support (query param: ?dry_run=true)

    **Payload Example:**
    ```json
    {
      "radar_id": "radar_67890",
      "radar_type": "contract",
      "company_name": "Acme Corp",
      "contract_value": 1500000,
      "contract_date": "2025-10-28T00:00:00Z",
      "description": "Contract modification for IT services",
      "source_url": "https://radar.example.com/contract/67890"
    }
    ```
    """
    try:
        # 1. Signature verification (if secret configured)
        radar_secret = os.environ.get("RADAR_WEBHOOK_SECRET")

        if radar_secret:
            # Reconstruct request body for signature verification
            body = json.dumps(payload.dict()).encode("utf-8")

            if not _verify_signature(radar_secret, x_radar_signature, body):
                logger.warning(f"Invalid Radar webhook signature for event {payload.radar_id}")
                raise HTTPException(
                    status_code=401,
                    detail={"status": "error", "message": "Invalid webhook signature"},
                )

        opp_id = generate_opportunity_id("radar", payload.radar_id)

        # 2. Replay protection
        if _check_replay("radar", payload.radar_id):
            logger.warning(f"Replay detected for Radar event: {payload.radar_id}")
            raise HTTPException(
                status_code=409,
                detail={"error": "replay_detected", "message": f"Event {payload.radar_id} already processed"},
            )

        # 3. Calculate FY routing (use contract_date for Radar)
        fy = _calculate_fy(payload.contract_date)

        # 4. Dry-run mode: preview actions without writing
        if dry_run:
            logger.info(f"Dry-run: Radar webhook {opp_id} (FY: {fy or 'Triage'})")
            return WebhookResponse(
                status="success",
                opportunity_id=opp_id,
                message=f"Dry-run: Radar opportunity {opp_id} would be ingested",
                dry_run=True,
                fy_route=fy or "Triage",
            )

        # 5. Load current state
        state = load_state()

        # 6. Create opportunity record
        opportunity = {
            "id": opp_id,
            "title": f"{payload.company_name} - {payload.radar_type.title()}",
            "source": "radar",
            "source_id": payload.radar_id,
            "description": payload.description,
            "estimated_amount": payload.contract_value,
            "company_name": payload.company_name,
            "contract_date": payload.contract_date,
            "source_url": payload.source_url,
            "triage": fy is None,  # Triage if no FY routing
            "fy": fy,
            "created_at": datetime.utcnow().isoformat(),
            "request_id": x_request_id,
        }

        # 7. Append to opportunities list
        state["opportunities"].append(opportunity)

        # 8. Save state
        save_state(state)

        # 9. Generate minimal opportunity.md with FY routing
        md_path = _get_opportunity_path(fy, opp_id)
        os.makedirs(os.path.dirname(md_path), exist_ok=True)
        with open(md_path, "w") as f:
            f.write(create_minimal_opportunity_md(opp_id, opportunity["title"], "Radar"))

        logger.info(f"Radar webhook ingested: {opp_id} (FY: {fy or 'Triage'}, request_id: {x_request_id})")

        return WebhookResponse(
            status="success",
            opportunity_id=opp_id,
            message=f"Radar opportunity {opp_id} ingested and triaged",
            fy_route=fy,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Radar webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
