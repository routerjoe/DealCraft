"""
Webhook ingestion for Govly and Radar events.
Parses events into append-only opportunities list in state.json.
Auto-generates minimal opportunity.md with triage flag.
"""

import json
import logging
import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["webhooks"])

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
    x_request_id: str = Header(None),
) -> WebhookResponse:
    """
    Ingest Govly federal opportunity events.

    - Parses event into opportunity structure
    - Appends to state.json opportunities[]
    - Auto-generates minimal opportunity.md with triage: true
    - Returns opportunity_id for tracking

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
        opp_id = generate_opportunity_id("govly", payload.event_id)

        # Load current state
        state = load_state()

        # Create opportunity record
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
            "triage": True,
            "created_at": datetime.utcnow().isoformat(),
            "request_id": x_request_id,
        }

        # Append to opportunities list
        state["opportunities"].append(opportunity)

        # Save state
        save_state(state)

        # Generate minimal opportunity.md
        obsidian_dir = "obsidian/40 Projects/Opportunities/Triage"
        os.makedirs(obsidian_dir, exist_ok=True)
        md_path = os.path.join(obsidian_dir, f"{opp_id}.md")
        with open(md_path, "w") as f:
            f.write(create_minimal_opportunity_md(opp_id, payload.title, "Govly"))

        logger.info(f"Govly webhook ingested: {opp_id} (request_id: {x_request_id})")

        return WebhookResponse(
            status="success",
            opportunity_id=opp_id,
            message=f"Govly opportunity {opp_id} ingested and triaged",
        )

    except Exception as e:
        logger.error(f"Govly webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Radar Webhook Handler
# ============================================================================


@router.post("/radar/webhook", response_model=WebhookResponse)
async def radar_webhook(
    payload: RadarWebhookPayload,
    x_request_id: str = Header(None),
) -> WebhookResponse:
    """
    Ingest Radar contract modification events.

    - Parses event into opportunity structure
    - Appends to state.json opportunities[]
    - Auto-generates minimal opportunity.md with triage: true
    - Returns opportunity_id for tracking

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
        opp_id = generate_opportunity_id("radar", payload.radar_id)

        # Load current state
        state = load_state()

        # Create opportunity record
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
            "triage": True,
            "created_at": datetime.utcnow().isoformat(),
            "request_id": x_request_id,
        }

        # Append to opportunities list
        state["opportunities"].append(opportunity)

        # Save state
        save_state(state)

        # Generate minimal opportunity.md
        obsidian_dir = "obsidian/40 Projects/Opportunities/Triage"
        os.makedirs(obsidian_dir, exist_ok=True)
        md_path = os.path.join(obsidian_dir, f"{opp_id}.md")
        with open(md_path, "w") as f:
            f.write(create_minimal_opportunity_md(opp_id, opportunity["title"], "Radar"))

        logger.info(f"Radar webhook ingested: {opp_id} (request_id: {x_request_id})")

        return WebhookResponse(
            status="success",
            opportunity_id=opp_id,
            message=f"Radar opportunity {opp_id} ingested and triaged",
        )

    except Exception as e:
        logger.error(f"Radar webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
