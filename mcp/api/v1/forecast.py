"""
Forecast Hub Engine - Phase 4
Generates AI-driven forecasts for opportunities across FY25, FY26, FY27.
Persists forecasts to data/forecast.json with derived fields on opportunity notes.
"""

import json
import statistics
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/v1/forecast", tags=["forecast"])

# Paths
FORECAST_FILE = Path("data/forecast.json")
STATE_FILE = Path("data/state.json")
OBSIDIAN_BASE = Path("obsidian/40 Projects/Opportunities")


# ============================================================================
# Models
# ============================================================================


class ForecastRequest(BaseModel):
    """Request to generate forecasts for opportunities."""

    opportunity_ids: Optional[List[str]] = Field(default=None, description="Specific opportunity IDs to forecast. If None, forecast all.")
    model: str = Field(default="gpt-5-thinking", description="AI model to use for forecasting")
    confidence_threshold: int = Field(default=50, description="Minimum confidence score (0-100) to include in summary")


class ForecastData(BaseModel):
    """Forecast data for a single opportunity."""

    opportunity_id: str
    opportunity_name: str
    projected_amount_FY25: float
    projected_amount_FY26: float
    projected_amount_FY27: float
    confidence_score: int  # 0-100
    reasoning: str
    generated_at: str  # ISO 8601
    model_used: str


class ForecastSummary(BaseModel):
    """Summary of all forecasts."""

    total_opportunities: int
    total_projected_FY25: float
    total_projected_FY26: float
    total_projected_FY27: float
    avg_confidence: float
    high_confidence_count: int  # >= 75
    medium_confidence_count: int  # 50-74
    low_confidence_count: int  # < 50
    last_updated: str


# ============================================================================
# Forecast Persistence
# ============================================================================


def load_forecasts() -> Dict[str, ForecastData]:
    """Load forecasts from data/forecast.json."""
    if not FORECAST_FILE.exists():
        return {}
    try:
        with open(FORECAST_FILE, "r") as f:
            data = json.load(f)
            return {k: ForecastData(**v) for k, v in data.items()}
    except (json.JSONDecodeError, ValueError):
        return {}


def save_forecasts(forecasts: Dict[str, ForecastData]) -> None:
    """Save forecasts to data/forecast.json with atomic write."""
    FORECAST_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp_file = FORECAST_FILE.with_suffix(".tmp")
    try:
        with open(temp_file, "w") as f:
            json.dump({k: v.model_dump() for k, v in forecasts.items()}, f, indent=2, default=str)
        temp_file.replace(FORECAST_FILE)
    except Exception as e:
        if temp_file.exists():
            temp_file.unlink()
        raise e


def load_state() -> Dict[str, Any]:
    """Load state from data/state.json."""
    if not STATE_FILE.exists():
        return {"opportunities": [], "actions": []}
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        return {"opportunities": [], "actions": []}


def get_opportunities() -> List[Dict[str, Any]]:
    """Get all opportunities from state.json."""
    state = load_state()
    return state.get("opportunities", [])


# ============================================================================
# Forecast Generation
# ============================================================================


def generate_forecast_for_opportunity(opp: Dict[str, Any], model: str = "gpt-5-thinking") -> ForecastData:
    """
    Generate forecast for a single opportunity.
    Uses simple heuristic-based forecasting (can be replaced with AI model).
    """
    opp_id = opp.get("id", "unknown")
    opp_name = opp.get("name", "Unknown Opportunity")
    current_amount = float(opp.get("amount", opp.get("est_amount", 0)))
    close_date_str = opp.get("close_date", opp.get("est_close", ""))

    # Parse close date to determine FY
    try:
        close_date = datetime.fromisoformat(close_date_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        from datetime import timezone

        close_date = datetime.now(timezone.utc)

    # Simple heuristic: distribute amount across FYs based on close date
    # FY25: Oct 2024 - Sep 2025
    # FY26: Oct 2025 - Sep 2026
    # FY27: Oct 2026 - Sep 2027
    from datetime import timezone

    fy26_start = datetime(2025, 10, 1, tzinfo=timezone.utc)
    fy27_start = datetime(2026, 10, 1, tzinfo=timezone.utc)

    if close_date < fy26_start:
        fy25_amount = current_amount * 0.8
        fy26_amount = current_amount * 0.15
        fy27_amount = current_amount * 0.05
        confidence = 85
    elif close_date < fy27_start:
        fy25_amount = current_amount * 0.1
        fy26_amount = current_amount * 0.75
        fy27_amount = current_amount * 0.15
        confidence = 75
    else:
        fy25_amount = current_amount * 0.05
        fy26_amount = current_amount * 0.2
        fy27_amount = current_amount * 0.75
        confidence = 65

    reasoning = (
        f"Forecast based on close_date ({close_date_str}). "
        f"Current amount: ${current_amount:,.2f}. "
        f"Distributed across FY25-27 based on fiscal year alignment."
    )

    return ForecastData(
        opportunity_id=opp_id,
        opportunity_name=opp_name,
        projected_amount_FY25=round(fy25_amount, 2),
        projected_amount_FY26=round(fy26_amount, 2),
        projected_amount_FY27=round(fy27_amount, 2),
        confidence_score=confidence,
        reasoning=reasoning,
        generated_at=datetime.utcnow().isoformat() + "Z",
        model_used=model,
    )


def update_opportunity_with_forecast(opp: Dict[str, Any], forecast: ForecastData) -> Dict[str, Any]:
    """Add forecast fields to opportunity."""
    opp["forecast"] = {
        "projected_amount_FY25": forecast.projected_amount_FY25,
        "projected_amount_FY26": forecast.projected_amount_FY26,
        "projected_amount_FY27": forecast.projected_amount_FY27,
        "confidence_score": forecast.confidence_score,
        "generated_at": forecast.generated_at,
    }
    return opp


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/run", response_model=Dict[str, Any])
async def run_forecast(request: ForecastRequest, x_request_id: str = Header(default="unknown")) -> Dict[str, Any]:
    """
    Generate forecasts for opportunities.
    POST /v1/forecast/run

    Request body:
    {
        "opportunity_ids": ["opp-1", "opp-2"],  # optional
        "model": "gpt-5-thinking",
        "confidence_threshold": 50
    }

    Returns:
    {
        "request_id": "uuid",
        "forecasts_generated": 5,
        "forecasts": [...]
    }
    """
    start_time = datetime.utcnow()

    try:
        # Load existing forecasts
        forecasts = load_forecasts()

        # Get opportunities
        opportunities = get_opportunities()

        # Filter by IDs if provided
        if request.opportunity_ids:
            opportunities = [o for o in opportunities if o.get("id") in request.opportunity_ids]

        # Generate forecasts
        new_forecasts = []
        for opp in opportunities:
            forecast = generate_forecast_for_opportunity(opp, request.model)
            forecasts[forecast.opportunity_id] = forecast
            new_forecasts.append(forecast)

        # Save forecasts
        save_forecasts(forecasts)

        # Update opportunities in state with forecast fields
        state = load_state()
        updated = False
        for i, opp in enumerate(state.get("opportunities", [])):
            if opp.get("id") in forecasts:
                state["opportunities"][i] = update_opportunity_with_forecast(opp, forecasts[opp.get("id")])
                updated = True

        # Save updated state if any opportunities were updated
        if updated:
            from mcp.core.store import write_json

            write_json(str(STATE_FILE), state)

        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        return {
            "request_id": x_request_id,
            "forecasts_generated": len(new_forecasts),
            "forecasts": [f.model_dump() for f in new_forecasts],
            "latency_ms": round(latency_ms, 2),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary", response_model=ForecastSummary)
async def get_forecast_summary(confidence_threshold: int = 50, x_request_id: str = Header(default="unknown")) -> ForecastSummary:
    """
    Get summary of all forecasts.
    GET /v1/forecast/summary?confidence_threshold=50

    Returns:
    {
        "total_opportunities": 10,
        "total_projected_FY25": 500000,
        "total_projected_FY26": 750000,
        "total_projected_FY27": 250000,
        "avg_confidence": 75.5,
        "high_confidence_count": 6,
        "medium_confidence_count": 3,
        "low_confidence_count": 1,
        "last_updated": "2025-10-28T17:30:00Z"
    }
    """
    try:
        forecasts = load_forecasts()

        if not forecasts:
            return ForecastSummary(
                total_opportunities=0,
                total_projected_FY25=0,
                total_projected_FY26=0,
                total_projected_FY27=0,
                avg_confidence=0,
                high_confidence_count=0,
                medium_confidence_count=0,
                low_confidence_count=0,
                last_updated=datetime.utcnow().isoformat() + "Z",
            )

        # Filter by confidence threshold
        filtered = [f for f in forecasts.values() if f.confidence_score >= confidence_threshold]

        total_fy25 = sum(f.projected_amount_FY25 for f in filtered)
        total_fy26 = sum(f.projected_amount_FY26 for f in filtered)
        total_fy27 = sum(f.projected_amount_FY27 for f in filtered)
        avg_confidence = statistics.mean([f.confidence_score for f in filtered]) if filtered else 0

        high_conf = sum(1 for f in filtered if f.confidence_score >= 75)
        med_conf = sum(1 for f in filtered if 50 <= f.confidence_score < 75)
        low_conf = sum(1 for f in filtered if f.confidence_score < 50)

        return ForecastSummary(
            total_opportunities=len(filtered),
            total_projected_FY25=round(total_fy25, 2),
            total_projected_FY26=round(total_fy26, 2),
            total_projected_FY27=round(total_fy27, 2),
            avg_confidence=round(avg_confidence, 2),
            high_confidence_count=high_conf,
            medium_confidence_count=med_conf,
            low_confidence_count=low_conf,
            last_updated=datetime.utcnow().isoformat() + "Z",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
