"""Email ingestion endpoints for RFQ, Govly, and IntroMail."""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from mcp.core.store import read_json, write_json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/email", tags=["Email Ingestion"])

# File path for state storage
STATE_FILE = "data/state.json"


class RFQIngestRequest(BaseModel):
    """RFQ email ingestion request."""

    subject: str = Field(..., min_length=1, description="Email subject")
    body: str = Field(..., min_length=1, description="Email body")
    attachments: List[str] = Field(default_factory=list, description="Attachment filenames")
    received_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z", description="Timestamp when email was received")


class RFQIngestResponse(BaseModel):
    """RFQ ingestion response."""

    ingest_id: str
    received_at: str
    record_count: int


class GovlyIngestRequest(BaseModel):
    """Govly webhook ingestion request."""

    event: str = Field(..., min_length=1, description="Event type")
    payload: Dict[str, Any] = Field(..., description="Event payload")


class GovlyIngestResponse(BaseModel):
    """Govly ingestion response."""

    ingest_id: str
    received_at: str
    event: str
    record_count: int


class IntroMailIngestRequest(BaseModel):
    """IntroMail email ingestion request."""

    to: str = Field(..., min_length=1, description="Recipient email")
    from_email: str = Field(..., alias="from", min_length=1, description="Sender email")
    body: str = Field(..., min_length=1, description="Email body")
    tags: List[str] = Field(default_factory=list, description="Email tags")

    @field_validator("from_email")
    @classmethod
    def validate_from_email(cls, v: str) -> str:
        """Validate from email contains @."""
        if "@" not in v:
            raise ValueError("Invalid email format")
        return v

    @field_validator("to")
    @classmethod
    def validate_to_email(cls, v: str) -> str:
        """Validate to email contains @."""
        if "@" not in v:
            raise ValueError("Invalid email format")
        return v


class IntroMailIngestResponse(BaseModel):
    """IntroMail ingestion response."""

    ingest_id: str
    received_at: str
    record_count: int


@router.post("/rfq/ingest", response_model=RFQIngestResponse, status_code=201)
async def ingest_rfq(request: RFQIngestRequest) -> RFQIngestResponse:
    """
    Ingest an RFQ email.

    Stores the RFQ in state.json for processing.
    """
    try:
        # Generate ingest_id
        ingest_id = str(uuid.uuid4())

        # Read current state
        state = read_json(STATE_FILE)

        # Initialize rfqs list if not exists
        if "rfqs" not in state:
            state["rfqs"] = []

        # Create RFQ record
        rfq_record = {
            "ingest_id": ingest_id,
            "subject": request.subject,
            "body": request.body,
            "attachments": request.attachments,
            "received_at": request.received_at,
            "ingested_at": datetime.utcnow().isoformat() + "Z",
        }

        # Append to state
        state["rfqs"].append(rfq_record)

        # Write back to file
        write_json(STATE_FILE, state)

        logger.info(f"Ingested RFQ: {ingest_id}, total RFQs: {len(state['rfqs'])}")

        return RFQIngestResponse(
            ingest_id=ingest_id,
            received_at=rfq_record["received_at"],
            record_count=len(state["rfqs"]),
        )

    except Exception as e:
        logger.error(f"Failed to ingest RFQ: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.post("/govly/ingest", response_model=GovlyIngestResponse, status_code=201)
async def ingest_govly(request: GovlyIngestRequest) -> GovlyIngestResponse:
    """
    Ingest a Govly webhook event.

    Stores the event in state.json for processing.
    """
    try:
        # Generate ingest_id
        ingest_id = str(uuid.uuid4())
        received_at = datetime.utcnow().isoformat() + "Z"

        # Read current state
        state = read_json(STATE_FILE)

        # Initialize govly_events list if not exists
        if "govly_events" not in state:
            state["govly_events"] = []

        # Create Govly record
        govly_record = {
            "ingest_id": ingest_id,
            "event": request.event,
            "payload": request.payload,
            "received_at": received_at,
        }

        # Append to state
        state["govly_events"].append(govly_record)

        # Write back to file
        write_json(STATE_FILE, state)

        logger.info(f"Ingested Govly event: {ingest_id}, event: {request.event}, total events: {len(state['govly_events'])}")

        return GovlyIngestResponse(
            ingest_id=ingest_id,
            received_at=received_at,
            event=request.event,
            record_count=len(state["govly_events"]),
        )

    except Exception as e:
        logger.error(f"Failed to ingest Govly event: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.post("/intromail/ingest", response_model=IntroMailIngestResponse, status_code=201)
async def ingest_intromail(request: IntroMailIngestRequest) -> IntroMailIngestResponse:
    """
    Ingest an IntroMail email.

    Stores the email in state.json for processing.
    """
    try:
        # Generate ingest_id
        ingest_id = str(uuid.uuid4())
        received_at = datetime.utcnow().isoformat() + "Z"

        # Read current state
        state = read_json(STATE_FILE)

        # Initialize intromails list if not exists
        if "intromails" not in state:
            state["intromails"] = []

        # Create IntroMail record
        intromail_record = {
            "ingest_id": ingest_id,
            "to": request.to,
            "from": request.from_email,
            "body": request.body,
            "tags": request.tags,
            "received_at": received_at,
        }

        # Append to state
        state["intromails"].append(intromail_record)

        # Write back to file
        write_json(STATE_FILE, state)

        logger.info(f"Ingested IntroMail: {ingest_id}, total intromails: {len(state['intromails'])}")

        return IntroMailIngestResponse(
            ingest_id=ingest_id,
            received_at=received_at,
            record_count=len(state["intromails"]),
        )

    except Exception as e:
        logger.error(f"Failed to ingest IntroMail: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")
