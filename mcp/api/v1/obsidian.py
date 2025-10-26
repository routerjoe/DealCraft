"""Obsidian note generation endpoints."""

import logging
from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from pydantic import BaseModel, Field

router = APIRouter(prefix="/obsidian", tags=["Obsidian"])

logger = logging.getLogger(__name__)

# Template directory
TEMPLATE_DIR = Path(__file__).parent.parent.parent.parent / "templates" / "obsidian"
OBSIDIAN_BASE_DIR = Path("obsidian")


class OpportunityRequest(BaseModel):
    """Request to create an Obsidian opportunity note."""

    id: str = Field(..., min_length=1, description="Opportunity ID")
    title: str = Field(..., min_length=1, description="Opportunity title")
    customer: str = Field(..., min_length=1, description="Customer name")
    oem: str = Field(..., min_length=1, description="OEM/vendor name")
    amount: float = Field(..., gt=0, description="Opportunity amount")
    stage: str = Field(..., min_length=1, description="Sales stage")
    close_date: str = Field(..., min_length=1, description="Expected close date")
    source: str = Field(..., min_length=1, description="Lead source")
    tags: List[str] = Field(default_factory=lambda: ["opportunity", "30-hub"], description="Note tags")


class OpportunityResponse(BaseModel):
    """Response after creating opportunity note."""

    path: str = Field(..., description="Path to created note")
    created: bool = Field(..., description="Whether the note was created successfully")


@router.post("/opportunity", response_model=OpportunityResponse, status_code=201)
async def create_opportunity_note(request: OpportunityRequest) -> OpportunityResponse:
    """
    Create an Obsidian opportunity note in the 30 Hub directory.

    Generates a formatted markdown note from the opportunity template.
    """
    try:
        # Set up Jinja2 environment
        env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))

        # Load template
        try:
            template = env.get_template("opportunity.md.j2")
        except TemplateNotFound:
            logger.error(f"Template not found at {TEMPLATE_DIR}/opportunity.md.j2")
            raise HTTPException(status_code=500, detail="Opportunity template not found")

        # Prepare template variables
        created_timestamp = datetime.utcnow().isoformat() + "Z"
        template_vars = {
            "id": request.id,
            "title": request.title,
            "customer": request.customer,
            "oem": request.oem,
            "amount": request.amount,
            "stage": request.stage,
            "close_date": request.close_date,
            "source": request.source,
            "tags": request.tags,
            "created": created_timestamp,
        }

        # Render template
        content = template.render(**template_vars)

        # Determine output path
        opportunities_dir = OBSIDIAN_BASE_DIR / "30 Hub" / "Opportunities"
        opportunities_dir.mkdir(parents=True, exist_ok=True)

        # Create filename: <id> - <title>.md
        safe_title = request.title.replace("/", "-").replace("\\", "-")
        filename = f"{request.id} - {safe_title}.md"
        file_path = opportunities_dir / filename

        # Write file atomically
        temp_path = file_path.with_suffix(".tmp")
        temp_path.write_text(content, encoding="utf-8")
        temp_path.replace(file_path)

        logger.info(f"Created opportunity note: {file_path}")

        return OpportunityResponse(
            path=str(file_path),
            created=True,
        )

    except Exception as e:
        logger.error(f"Failed to create opportunity note: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create note: {str(e)}")
