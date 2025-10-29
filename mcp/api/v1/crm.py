"""
CRM API Endpoints - Phase 6
Export opportunities to CRM systems with attribution tracking.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from mcp.core.crm_sync import attribution_engine, crm_sync_engine
from mcp.core.store import read_json

router = APIRouter(prefix="/v1/crm", tags=["crm"])

STATE_FILE = "data/state.json"


# ============================================================================
# Models
# ============================================================================


class CRMExportRequest(BaseModel):
    """Request to export opportunities to CRM."""

    opportunity_ids: Optional[List[str]] = Field(default=None, description="Specific IDs to export. If None, export all.")
    format: str = Field(
        default="generic_json",
        description="CRM format (salesforce, hubspot, generic_json, generic_yaml)",
    )
    dry_run: bool = Field(default=True, description="If True, validate only without actual sync")


class AttributionRequest(BaseModel):
    """Request to calculate attribution for opportunities."""

    opportunity_ids: Optional[List[str]] = Field(default=None, description="Specific IDs. If None, calculate for all.")


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/export", response_model=Dict[str, Any])
async def export_to_crm(request: CRMExportRequest, x_request_id: str = Header(default="unknown")) -> Dict[str, Any]:
    """
    Export opportunities to CRM system.
    POST /v1/crm/export

    Request body:
    {
        "opportunity_ids": ["opp-1", "opp-2"],  # optional
        "format": "salesforce",
        "dry_run": true
    }

    Returns:
    {
        "request_id": "uuid",
        "total": 10,
        "success_count": 8,
        "error_count": 2,
        "dry_run": true,
        "results": [...]
    }
    """
    try:
        # Load opportunities from state
        state = read_json(STATE_FILE)
        opportunities = state.get("opportunities", [])

        # Filter by IDs if provided
        if request.opportunity_ids:
            opportunities = [o for o in opportunities if o.get("id") in request.opportunity_ids]

        if not opportunities:
            raise HTTPException(status_code=404, detail="No opportunities found for export")

        # Set dry-run mode
        crm_sync_engine.dry_run = request.dry_run

        # Bulk export
        result = crm_sync_engine.bulk_export(opportunities, request.format)

        result["request_id"] = x_request_id

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/attribution", response_model=Dict[str, Any])
async def calculate_attribution(request: AttributionRequest, x_request_id: str = Header(default="unknown")) -> Dict[str, Any]:
    """
    Calculate attribution for opportunities.
    POST /v1/crm/attribution

    Request body:
    {
        "opportunity_ids": ["opp-1", "opp-2"]  # optional
    }

    Returns:
    {
        "request_id": "uuid",
        "total": 10,
        "attributions": [
            {
                "opportunity_id": "opp-1",
                "opportunity_name": "Deal Name",
                "oem_attribution": {"Microsoft": 600000, "Cisco": 300000},
                "partner_attribution": {"Partner A": 100000},
                "region": "East",
                "customer_org": "Agency X"
            }
        ]
    }
    """
    try:
        # Load opportunities
        state = read_json(STATE_FILE)
        opportunities = state.get("opportunities", [])

        # Filter by IDs if provided
        if request.opportunity_ids:
            opportunities = [o for o in opportunities if o.get("id") in request.opportunity_ids]

        if not opportunities:
            raise HTTPException(status_code=404, detail="No opportunities found for attribution")

        # Calculate attributions
        attributions = []
        for opp in opportunities:
            attr = attribution_engine.calculate_full_attribution(opp)
            attr["opportunity_id"] = opp.get("id", "unknown")
            attr["opportunity_name"] = opp.get("name", opp.get("title", "Unknown"))
            attributions.append(attr)

        return {
            "request_id": x_request_id,
            "total": len(attributions),
            "attributions": attributions,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/formats", response_model=List[str])
async def get_supported_formats() -> List[str]:
    """
    Get list of supported CRM export formats.
    GET /v1/crm/formats

    Returns:
    ["salesforce", "hubspot", "dynamics", "generic_json", "generic_yaml"]
    """
    from mcp.core.crm_sync import CRM_FORMATS

    return CRM_FORMATS


@router.get("/validate/{opportunity_id}", response_model=Dict[str, Any])
async def validate_opportunity_for_crm(opportunity_id: str, x_request_id: str = Header(default="unknown")) -> Dict[str, Any]:
    """
    Validate a specific opportunity for CRM export.
    GET /v1/crm/validate/opp-123

    Returns:
    {
        "opportunity_id": "opp-123",
        "valid": true,
        "errors": []
    }
    """
    try:
        # Load opportunity
        state = read_json(STATE_FILE)
        opportunities = state.get("opportunities", [])

        opp = next((o for o in opportunities if o.get("id") == opportunity_id), None)

        if not opp:
            raise HTTPException(status_code=404, detail=f"Opportunity {opportunity_id} not found")

        # Validate
        is_valid, errors = crm_sync_engine.validate_opportunity(opp)

        return {
            "request_id": x_request_id,
            "opportunity_id": opportunity_id,
            "valid": is_valid,
            "errors": errors,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
