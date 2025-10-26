"""AI model and guidance endpoints."""

from typing import List

from fastapi import APIRouter
from pydantic import BaseModel, Field

from mcp.core.ai_router import generate_guidance

router = APIRouter(prefix="/ai", tags=["AI"])


class OEMInput(BaseModel):
    """OEM input for guidance request."""

    name: str
    authorized: bool


class ContractInput(BaseModel):
    """Contract input for guidance request."""

    name: str
    supported: bool


class GuidanceRequest(BaseModel):
    """Request schema for AI guidance."""

    oems: List[OEMInput] = Field(default_factory=list, description="List of OEMs")
    contracts: List[ContractInput] = Field(default_factory=list, description="List of contracts")
    rfq_text: str = Field(..., description="RFQ text to analyze")
    model: str = Field(default="gpt-5-thinking", description="AI model to use")


class GuidanceResponse(BaseModel):
    """Response schema for AI guidance."""

    summary: str = Field(..., description="Summary of analysis")
    actions: List[str] = Field(..., description="Recommended actions")
    risks: List[str] = Field(..., description="Identified risks")


@router.get("/models", response_model=List[str])
async def list_models() -> List[str]:
    """List available AI models."""
    return ["gpt-5-thinking", "claude-3.5", "gemini-1.5-pro"]


@router.post("/guidance", response_model=GuidanceResponse)
async def get_guidance(request: GuidanceRequest) -> GuidanceResponse:
    """Generate AI guidance for an RFQ."""
    # Convert request to dict for processing
    payload = request.model_dump()

    # Generate guidance using AI router
    result = generate_guidance(payload)

    return GuidanceResponse(**result)
