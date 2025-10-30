"""OEM Partner Intelligence endpoints - Phase 16."""

from typing import List

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from mcp.core.oems import OEMPartner, OEMStore

router = APIRouter(prefix="/oems", tags=["OEM Partner Intelligence"])

# Initialize global store
_store: OEMStore | None = None


def get_store() -> OEMStore:
    """Get or initialize the OEM store singleton."""
    global _store
    if _store is None:
        _store = OEMStore()
    return _store


class OEMPartnerCreate(BaseModel):
    """Schema for creating or updating an OEM partner."""

    oem_name: str = Field(..., min_length=1, description="OEM partner name")
    tier: str = Field(..., description="Partner tier level")
    partner_poc: str | None = Field(None, description="Partner point of contact")
    notes: str | None = Field(None, description="Additional notes about the partner")


class OEMPartnerResponse(BaseModel):
    """Schema for OEM partner response."""

    oem_name: str
    tier: str
    partner_poc: str | None
    notes: str | None
    updated_at: str  # ISO format string


@router.get("/all", response_model=List[OEMPartnerResponse])
async def get_all_oems(request: Request) -> List[OEMPartnerResponse]:
    """
    Get all OEM partners.

    Returns:
        List of all OEM partners with their details
    """
    store = get_store()
    partners = store.get_all()

    return [
        OEMPartnerResponse(oem_name=p.oem_name, tier=p.tier, partner_poc=p.partner_poc, notes=p.notes, updated_at=p.updated_at.isoformat())
        for p in partners
    ]


@router.post("/add", response_model=OEMPartnerResponse, status_code=status.HTTP_201_CREATED)
async def add_oem(data: OEMPartnerCreate, request: Request) -> OEMPartnerResponse:
    """
    Add or update an OEM partner.

    If an OEM partner with the same name exists, it will be updated.
    Otherwise, a new partner will be created.

    Args:
        data: OEM partner data

    Returns:
        The created or updated OEM partner
    """
    store = get_store()

    # Create OEMPartner instance
    partner = OEMPartner(oem_name=data.oem_name, tier=data.tier, partner_poc=data.partner_poc, notes=data.notes)

    # Add or update
    result = store.add_or_update(partner)

    return OEMPartnerResponse(
        oem_name=result.oem_name,
        tier=result.tier,
        partner_poc=result.partner_poc,
        notes=result.notes,
        updated_at=result.updated_at.isoformat(),
    )


@router.get("/{name}", response_model=OEMPartnerResponse)
async def get_oem(name: str, request: Request) -> OEMPartnerResponse:
    """
    Lookup an OEM partner by name.

    Args:
        name: OEM partner name

    Returns:
        OEM partner details

    Raises:
        HTTPException: 404 if partner not found
    """
    store = get_store()
    partner = store.get(name)

    if partner is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"OEM partner '{name}' not found")

    return OEMPartnerResponse(
        oem_name=partner.oem_name,
        tier=partner.tier,
        partner_poc=partner.partner_poc,
        notes=partner.notes,
        updated_at=partner.updated_at.isoformat(),
    )


@router.get("/export/obsidian", response_class=PlainTextResponse)
async def export_obsidian(request: Request) -> str:
    """
    Export all OEM partners as Obsidian-compatible markdown.

    Returns markdown text only (does not write to disk).
    Format for each partner:

    ## OEM: <oem_name>
    Tier: <tier>
    POC: <partner_poc>
    Updated: <updated_at>
    Notes:
    <notes>

    Returns:
        Markdown-formatted text of all OEM partners
    """
    store = get_store()
    return store.export_markdown()
