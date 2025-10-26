"""AI model and guidance endpoints."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from mcp.core.ai_router import generate_guidance, get_available_models, process_ai_request

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
    """
    List available AI models.

    Returns:
        List of available model names
    """
    models = get_available_models()
    return list(models.keys())


@router.get("/models/detailed")
async def list_models_detailed() -> Dict[str, Dict[str, str]]:
    """
    List available AI models with detailed information.

    Returns:
        Dictionary of model configurations with provider information
    """
    return get_available_models()


class AskRequest(BaseModel):
    """Request schema for unified AI ask endpoint."""

    query: str = Field(..., description="User's question or request", min_length=1)
    model: Optional[str] = Field(default=None, description="AI model to use (defaults to gpt-5-thinking)")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context data")


class AskResponse(BaseModel):
    """Response schema for unified AI ask endpoint."""

    answer: str = Field(..., description="AI-generated response")
    model: str = Field(..., description="Model used for generation")
    provider: str = Field(..., description="AI provider (openai, anthropic, gemini)")
    context_used: bool = Field(..., description="Whether context was provided")


@router.post("/ask", response_model=AskResponse)
async def ask_ai(request: AskRequest) -> AskResponse:
    """
    Unified AI endpoint for general queries.

    Supports multiple AI models (OpenAI, Anthropic, Gemini) and optional context.
    Request ID and latency are automatically logged via middleware.
    """
    # Process request using AI router
    result = process_ai_request(query=request.query, model=request.model, context=request.context)

    return AskResponse(**result)


@router.post("/guidance", response_model=GuidanceResponse)
async def get_guidance(request: GuidanceRequest) -> GuidanceResponse:
    """Generate AI guidance for an RFQ."""
    # Convert request to dict for processing
    payload = request.model_dump()

    # Generate guidance using AI router
    result = generate_guidance(payload)

    return GuidanceResponse(**result)
