"""Contract Vehicle management endpoints."""

from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from mcp.core.store import read_json, write_json

router = APIRouter(prefix="/contracts", tags=["Contracts"])

# Path to state file
STATE_FILE = Path(__file__).parent.parent.parent.parent / "data" / "state.json"


class ContractCreate(BaseModel):
    """Schema for creating a Contract Vehicle."""

    name: str = Field(..., min_length=1, description="Contract name")
    supported: bool = Field(default=False, description="Whether contract is supported")
    notes: str = Field(default="", description="Additional notes")


class ContractUpdate(BaseModel):
    """Schema for updating a Contract (partial updates allowed)."""

    supported: Optional[bool] = Field(None, description="Whether contract is supported")
    notes: Optional[str] = Field(None, description="Additional notes")


class Contract(BaseModel):
    """Schema for Contract response."""

    name: str
    supported: bool
    notes: str


@router.get("", response_model=List[Contract])
async def list_contracts() -> List[Contract]:
    """List all Contract Vehicles."""
    state = read_json(str(STATE_FILE))
    return state.get("contracts", [])


@router.post("", response_model=Contract, status_code=status.HTTP_201_CREATED)
async def create_contract(contract: ContractCreate) -> Contract:
    """Create a new Contract Vehicle."""
    state = read_json(str(STATE_FILE))
    contracts = state.get("contracts", [])

    # Check for duplicate name
    if any(c["name"] == contract.name for c in contracts):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Contract with name '{contract.name}' already exists",
        )

    # Add new contract
    new_contract = contract.model_dump()
    contracts.append(new_contract)
    state["contracts"] = contracts

    # Save state
    write_json(str(STATE_FILE), state)

    return new_contract


@router.patch("/{name}", response_model=Contract)
async def update_contract(name: str, contract_update: ContractUpdate) -> Contract:
    """Update an existing Contract Vehicle (partial updates)."""
    state = read_json(str(STATE_FILE))
    contracts = state.get("contracts", [])

    # Find contract by name
    contract_index = None
    for i, c in enumerate(contracts):
        if c["name"] == name:
            contract_index = i
            break

    if contract_index is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Contract with name '{name}' not found")

    # Apply partial updates
    update_data = contract_update.model_dump(exclude_unset=True)
    contracts[contract_index].update(update_data)
    state["contracts"] = contracts

    # Save state
    write_json(str(STATE_FILE), state)

    return contracts[contract_index]


@router.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contract(name: str) -> None:
    """Delete a Contract Vehicle."""
    state = read_json(str(STATE_FILE))
    contracts = state.get("contracts", [])

    # Find and remove contract
    original_count = len(contracts)
    contracts = [c for c in contracts if c["name"] != name]

    if len(contracts) == original_count:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Contract with name '{name}' not found")

    state["contracts"] = contracts

    # Save state
    write_json(str(STATE_FILE), state)
