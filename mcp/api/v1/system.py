"""System monitoring and logging endpoints."""

import logging
from typing import List

from fastapi import APIRouter
from pydantic import BaseModel, Field

from mcp.core.store import read_json

router = APIRouter(prefix="/system", tags=["System"])

logger = logging.getLogger(__name__)

# File path for state storage
STATE_FILE = "data/state.json"


class ActionLog(BaseModel):
    """Action log entry."""

    request_id: str = Field(..., description="Unique request identifier")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    method: str = Field(..., description="HTTP method")
    path: str = Field(..., description="Request path")
    latency_ms: int = Field(..., description="Request latency in milliseconds")
    status_code: int = Field(..., description="HTTP status code")
    context: dict = Field(default_factory=dict, description="Additional context")


@router.get("/recent-actions", response_model=List[ActionLog])
async def get_recent_actions() -> List[ActionLog]:
    """
    Get the last 10 actions/requests.

    Returns a list of recent API requests with timing and metadata.
    The list is maintained in data/state.json with automatic rotation.
    """
    try:
        # Read state from storage
        state = read_json(STATE_FILE)
        actions_data = state.get("recent_actions", [])

        # Convert to ActionLog objects
        actions = [ActionLog(**action) for action in actions_data]

        logger.info(f"Retrieved {len(actions)} recent actions")
        return actions

    except FileNotFoundError:
        logger.warning("State file not found, returning empty list")
        return []
    except Exception as e:
        logger.error(f"Failed to retrieve recent actions: {str(e)}")
        return []
