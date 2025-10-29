"""
Contract Vehicle API Endpoints - Phase 8
Recommend and score contract vehicles for opportunities.
"""

from typing import Any, Dict, List

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from mcp.core.cv_recommender import cv_recommender
from mcp.core.store import read_json

router = APIRouter(prefix="/v1/cv", tags=["contract_vehicles"])

STATE_FILE = "data/state.json"


# ============================================================================
# Models
# ============================================================================


class CVRecommendRequest(BaseModel):
    """Request to get CV recommendations for an opportunity."""

    opportunity_id: str = Field(..., description="Opportunity ID")
    top_n: int = Field(default=3, description="Number of recommendations")


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/recommend", response_model=Dict[str, Any])
async def recommend_contract_vehicles(request: CVRecommendRequest, x_request_id: str = Header(default="unknown")) -> Dict[str, Any]:
    """
    Recommend contract vehicles for an opportunity.
    POST /v1/cv/recommend

    Returns:
    {
        "opportunity_id": "opp-123",
        "recommendations": [
            {
                "contract_vehicle": "SEWP V",
                "cv_score": 98.5,
                "reasoning": ["✓ Supports Microsoft", "✓ Active BPAs"],
                "has_bpa": true
            }
        ]
    }
    """
    try:
        # Load opportunity
        state = read_json(STATE_FILE)
        opportunities = state.get("opportunities", [])

        opp = next((o for o in opportunities if o.get("id") == request.opportunity_id), None)

        if not opp:
            raise HTTPException(
                status_code=404,
                detail=f"Opportunity {request.opportunity_id} not found",
            )

        # Get recommendations
        recommendations = cv_recommender.recommend_vehicles(opp, request.top_n)

        return {
            "request_id": x_request_id,
            "opportunity_id": request.opportunity_id,
            "recommendations": recommendations,
            "top_n": request.top_n,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vehicles", response_model=List[str])
async def get_available_vehicles() -> List[str]:
    """
    Get list of all available contract vehicles.
    GET /v1/cv/vehicles

    Returns:
    ["SEWP V", "NASA SOLUTIONS", "GSA Schedule", ...]
    """
    return cv_recommender.get_available_vehicles()


@router.get("/vehicles/{vehicle_name}", response_model=Dict[str, Any])
async def get_vehicle_details(vehicle_name: str) -> Dict[str, Any]:
    """
    Get details for a specific contract vehicle.
    GET /v1/cv/vehicles/SEWP%20V

    Returns vehicle capabilities, OEMs supported, etc.
    """
    try:
        if vehicle_name not in cv_recommender.CONTRACT_VEHICLES:
            raise HTTPException(status_code=404, detail=f"Contract vehicle '{vehicle_name}' not found")

        vehicle_data = cv_recommender.CONTRACT_VEHICLES[vehicle_name]

        return {
            "name": vehicle_name,
            "priority": vehicle_data["priority"],
            "oems_supported": vehicle_data["oems_supported"],
            "categories": vehicle_data["categories"],
            "has_active_bpas": vehicle_data["active_bpas"],
            "ceiling": vehicle_data.get("ceiling"),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
