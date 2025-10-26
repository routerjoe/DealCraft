"""OEM management endpoints."""

from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from mcp.core.store import read_json, write_json

router = APIRouter(prefix="/oems", tags=["OEMs"])

# Path to state file
STATE_FILE = Path(__file__).parent.parent.parent.parent / "data" / "state.json"


class OEMCreate(BaseModel):
    """Schema for creating an OEM."""

    name: str = Field(..., min_length=1, description="OEM name")
    authorized: bool = Field(default=False, description="Whether OEM is authorized")
    threshold: int = Field(default=0, ge=0, description="Threshold value")


class OEMUpdate(BaseModel):
    """Schema for updating an OEM (partial updates allowed)."""

    authorized: Optional[bool] = Field(None, description="Whether OEM is authorized")
    threshold: Optional[int] = Field(None, ge=0, description="Threshold value")


class OEM(BaseModel):
    """Schema for OEM response."""

    name: str
    authorized: bool
    threshold: int


@router.get("", response_model=List[OEM])
async def list_oems() -> List[OEM]:
    """List all OEMs."""
    state = read_json(str(STATE_FILE))
    return state.get("oems", [])


@router.post("", response_model=OEM, status_code=status.HTTP_201_CREATED)
async def create_oem(oem: OEMCreate) -> OEM:
    """Create a new OEM."""
    state = read_json(str(STATE_FILE))
    oems = state.get("oems", [])

    # Check for duplicate name
    if any(o["name"] == oem.name for o in oems):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"OEM with name '{oem.name}' already exists",
        )

    # Add new OEM
    new_oem = oem.model_dump()
    oems.append(new_oem)
    state["oems"] = oems

    # Save state
    write_json(str(STATE_FILE), state)

    return new_oem


@router.patch("/{name}", response_model=OEM)
async def update_oem(name: str, oem_update: OEMUpdate) -> OEM:
    """Update an existing OEM (partial updates)."""
    state = read_json(str(STATE_FILE))
    oems = state.get("oems", [])

    # Find OEM by name
    oem_index = None
    for i, o in enumerate(oems):
        if o["name"] == name:
            oem_index = i
            break

    if oem_index is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"OEM with name '{name}' not found")

    # Apply partial updates
    update_data = oem_update.model_dump(exclude_unset=True)
    oems[oem_index].update(update_data)
    state["oems"] = oems

    # Save state
    write_json(str(STATE_FILE), state)

    return oems[oem_index]


@router.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_oem(name: str) -> None:
    """Delete an OEM."""
    state = read_json(str(STATE_FILE))
    oems = state.get("oems", [])

    # Find and remove OEM
    original_count = len(oems)
    oems = [o for o in oems if o["name"] != name]

    if len(oems) == original_count:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"OEM with name '{name}' not found")

    state["oems"] = oems

    # Save state
    write_json(str(STATE_FILE), state)
