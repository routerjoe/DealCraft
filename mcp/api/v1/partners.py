from typing import Any, Dict, List

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/v1/partners", tags=["partners"])


class TierRecord(BaseModel):
    oem: str
    tier_global: str
    tier_redriver: str
    source: str
    notes: str | None = None


class SyncRequest(BaseModel):
    sources: List[str] = []
    dry_run: bool = True


@router.get("/tiers", response_model=List[TierRecord])
async def list_tiers() -> List[TierRecord]:
    # TODO: read from partners.db (or JSONL) once implemented
    return []


@router.post("/sync")
async def sync_tiers(req: SyncRequest) -> Dict[str, Any]:
    # TODO: wire to PartnerTierSync (dry_run default)
    return {"status": "not_implemented", "received": req.model_dump()}


@router.get("/export/obsidian")
async def export_obsidian() -> Dict[str, Any]:
    # TODO: regenerate 50 Dashboards/Partner_Tiers_Index.md via bases/dataview fallback
    return {"status": "not_implemented"}
