"""
AI Account Plans API - Implementation
Sprint 12: AI Account Plans (AFCENT/AETC Focus)

Generates strategic account plans for federal customers using AI analysis.
Integrates forecast data, CV recommendations, and OEM strategies.
"""

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from mcp.core.account_plans import account_plan_generator, render_plan_to_pdf

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/account-plans", tags=["account-plans"])


# ============================================================================
# Data Models
# ============================================================================


class AccountPlanRequest(BaseModel):
    """Request model for generating an account plan."""

    customer: str = Field(..., description="Customer name (e.g., AFCENT, AETC)")
    oem_partners: List[str] = Field(..., description="OEM partners (e.g., Cisco, Nutanix, NetApp, Red Hat)")
    fiscal_year: str = Field(..., description="Fiscal year (e.g., FY26)")
    focus_areas: Optional[List[str]] = Field(None, description="Focus areas (e.g., modernization, security, cloud)")
    format: str = Field("markdown", description="Output format: markdown, pdf, json")
    options: Optional[dict] = Field(None, description="Additional generation options")


class AccountPlanResponse(BaseModel):
    """Response model for account plan generation."""

    status: str = Field(..., description="Status: success, error, not_implemented")
    message: str = Field(..., description="Response message")
    plan_id: Optional[str] = Field(None, description="Generated plan ID")
    preview: Optional[dict] = Field(None, description="Plan preview data")


class FormatInfo(BaseModel):
    """Information about an output format."""

    id: str = Field(..., description="Format identifier")
    name: str = Field(..., description="Format display name")
    extension: str = Field(..., description="File extension")
    supports_obsidian: bool = Field(..., description="Whether format supports Obsidian export")


class FormatsResponse(BaseModel):
    """Response model for formats listing."""

    status: str = Field(..., description="Status: success, not_implemented")
    message: str = Field(..., description="Response message")
    formats: List[FormatInfo] = Field(..., description="Available output formats")


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/generate", response_model=AccountPlanResponse)
async def generate_account_plan(
    request: AccountPlanRequest,
    x_request_id: str = Header(None),
) -> AccountPlanResponse:
    """
    Generate AI-powered account plan for a federal customer.

    Analyzes forecast and opportunity data to generate strategic recommendations
    including OEM partner positioning, contract vehicle strategies, and execution timelines.

    **Example Request:**
    ```json
    {
      "customer": "AFCENT",
      "oem_partners": ["Cisco", "Nutanix"],
      "fiscal_year": "FY26",
      "focus_areas": ["modernization", "security"],
      "format": "json"
    }
    ```

    **Supported Customers:** AFCENT, AETC

    **OEM Partners:** Cisco, Nutanix, NetApp, Red Hat, Microsoft, Dell, HPE, Palo Alto Networks

    **Focus Areas:** modernization, security, cloud, networking, storage

    **Formats:** json, markdown (pdf not yet implemented)
    """
    start_time = datetime.utcnow()
    logger.info(f"Account plan generation requested: {request.customer} + {request.oem_partners} (request_id: {x_request_id})")

    try:
        # Prepare input data for generator
        input_data = {
            "customer": request.customer,
            "oem_partners": request.oem_partners,
            "fiscal_year": request.fiscal_year,
            "focus_areas": request.focus_areas,
        }

        # Generate plan
        plan = account_plan_generator.generate_account_plan(input_data)

        # Generate plan ID
        plan_id = f"plan-{request.customer.lower()}-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

        # Format response based on requested format
        if request.format == "pdf":
            # Generate PDF and return as streaming response
            pdf_bytes = render_plan_to_pdf(plan)

            latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.info(f"Account plan PDF generated successfully: {plan_id} (latency: {latency_ms:.2f}ms)")

            # Generate filename
            customer_slug = request.customer.lower().replace(" ", "_")
            date_str = datetime.utcnow().strftime("%Y%m%d")
            filename = f"account_plan_{customer_slug}_{date_str}.pdf"

            return StreamingResponse(
                iter([pdf_bytes]),
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"',
                    "X-Request-Id": x_request_id or "unknown",
                    "X-Latency-Ms": str(int(latency_ms)),
                },
            )
        elif request.format == "json":
            preview = plan
        elif request.format == "markdown":
            # Return JSON with note about markdown export
            preview = {
                **plan,
                "note": "Markdown export available. Full plan returned as JSON structure.",
            }
        else:
            preview = plan

        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.info(f"Account plan generated successfully: {plan_id} (latency: {latency_ms:.2f}ms)")

        return AccountPlanResponse(
            status="success",
            message=f"Account plan generated for {plan['customer_full_name']}",
            plan_id=plan_id,
            preview=preview,
        )

    except ValueError as e:
        # Handle unsupported customer or validation errors
        logger.warning(f"Account plan validation error: {str(e)} (request_id: {x_request_id})")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Account plan generation failed: {str(e)} (request_id: {x_request_id})", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate account plan: {str(e)}")


@router.get("/formats", response_model=FormatsResponse)
async def list_formats(
    x_request_id: str = Header(None),
) -> FormatsResponse:
    """
    List available output formats for account plans.

    **Available Formats:**
    - **Markdown:** Obsidian-compatible, editable
    - **PDF:** Print-ready, professional (not yet implemented)
    - **JSON:** Machine-readable, API integration
    """
    logger.info(f"Formats list requested (request_id: {x_request_id})")

    return FormatsResponse(
        status="success",
        message="Available output formats for account plans",
        formats=[
            FormatInfo(
                id="markdown",
                name="Markdown",
                extension=".md",
                supports_obsidian=True,
            ),
            FormatInfo(
                id="pdf",
                name="PDF Document",
                extension=".pdf",
                supports_obsidian=False,
            ),
            FormatInfo(
                id="json",
                name="JSON Data",
                extension=".json",
                supports_obsidian=False,
            ),
        ],
    )
