"""Partner Tier API Endpoints"""

import logging
import os
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from mcp.core.partners_sync import PartnerSyncError, PartnerTierSync

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/partners", tags=["partners"])


class TierRecord(BaseModel):
    name: str
    tier: str
    program: str
    oem: str
    poc: str | None = None
    notes: str | None = None
    updated_at: str
    created_at: str


class SyncRequest(BaseModel):
    dry_run: bool = True


@router.get("/tiers", response_model=List[TierRecord])
async def list_tiers(request: Request) -> List[TierRecord]:
    """
    Get all partner tier records from OEMStore.

    Returns:
        List of partner tier records
    """
    try:
        sync = PartnerTierSync(store_path="data/oems.json")
        records = sync._load_store()

        # Convert to TierRecord objects
        tier_records = [TierRecord(**record) for record in records]

        return tier_records
    except Exception as e:
        logger.error(f"Failed to list partner tiers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync")
async def sync_tiers(req: SyncRequest, request: Request) -> Dict[str, Any]:
    """
    Sync partner tier data from data/partners/ directory.

    Args:
        req: SyncRequest with dry_run flag

    Returns:
        Sync results with added, updated, unchanged counts
    """
    try:
        # Get VAULT_ROOT from environment
        vault_root = os.getenv("VAULT_ROOT")

        # Initialize sync
        sync = PartnerTierSync(vault_root=vault_root, store_path="data/oems.json")

        # Load sources from data/partners/
        records = sync.load_sources()

        if not records:
            return {
                "dry_run": req.dry_run,
                "added": [],
                "updated": [],
                "unchanged": [],
                "message": "No partner data files found in data/partners/",
            }

        # Validate records
        is_valid, errors = sync.validate(records)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Validation failed: {', '.join(errors)}")

        # Plan updates
        plan = sync.plan_updates(records)

        # Apply updates
        result = sync.apply_updates(plan, dry_run=req.dry_run)

        return {
            "dry_run": req.dry_run,
            "added": plan["added"],
            "updated": plan["updated"],
            "unchanged": plan["unchanged"],
            "applied": result["applied"],
        }
    except PartnerSyncError as e:
        logger.error(f"Partner sync error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to sync partner tiers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/obsidian")
async def export_obsidian(request: Request) -> Dict[str, Any]:
    """
    Export partner tier data to Obsidian markdown files.

    Writes per-OEM markdown files to <VAULT_ROOT>/30 Hubs/OEMs/

    Returns:
        Export results with files written count
    """
    try:
        # Get VAULT_ROOT from environment
        vault_root = os.getenv("VAULT_ROOT")

        if not vault_root:
            raise HTTPException(status_code=500, detail="VAULT_ROOT environment variable not set")

        # Initialize sync
        sync = PartnerTierSync(vault_root=vault_root, store_path="data/oems.json")

        # Export to Obsidian
        result = sync.export_obsidian()

        return result
    except PartnerSyncError as e:
        logger.error(f"Partner export error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to export to Obsidian: {e}")
        raise HTTPException(status_code=500, detail=str(e))
