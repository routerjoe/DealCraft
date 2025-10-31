"""Partner Intelligence API Endpoints (Sprint 18)."""

import logging
import os
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from mcp.core.enrich_partners import PartnerEnricher
from mcp.core.partner_graph import build_partner_graph
from mcp.core.partners_sync import PartnerTierSync

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/partners/intel", tags=["partners_intel"])


class ExportRequest(BaseModel):
    """Request model for Obsidian export."""

    dry_run: bool = True


@router.get("/scores")
async def get_partner_scores(request: Request) -> Dict[str, Any]:
    """Get partner strength scores.

    Returns normalized strength scores (0-100) for all partners
    with breakdown of scoring components.

    Returns:
        Dictionary containing partner scores and summary statistics
    """
    try:
        # Load partner data
        sync = PartnerTierSync(store_path="data/oems.json")
        records = sync._load_store()

        if not records:
            return {
                "scores": [],
                "summary": {
                    "total_partners": 0,
                    "avg_score": 0.0,
                    "distribution": {},
                },
            }

        # Enrich with scores
        enricher = PartnerEnricher()
        scores = enricher.enrich_partners(records)

        # Calculate summary statistics
        avg_score = sum(s.strength_score for s in scores) / len(scores) if scores else 0.0
        distribution = enricher.get_score_distribution(scores)

        return {
            "scores": [s.to_dict() for s in scores],
            "summary": {
                "total_partners": len(scores),
                "avg_score": round(avg_score, 2),
                "distribution": distribution,
            },
        }
    except Exception as e:
        logger.error(f"Failed to get partner scores: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graph")
async def get_partner_graph(request: Request) -> Dict[str, Any]:
    """Get partner relationship graph.

    Returns graph structure with nodes (partners) and edges (relationships)
    in adjacency list format with analytics.

    Returns:
        Graph structure with nodes, edges, and statistics
    """
    try:
        # Load partner data
        sync = PartnerTierSync(store_path="data/oems.json")
        records = sync._load_store()

        if not records:
            return {
                "nodes": {},
                "edges": [],
                "adjacency_list": {},
                "statistics": {
                    "total_nodes": 0,
                    "total_edges": 0,
                    "oem_distribution": {},
                    "tier_distribution": {},
                    "components": 0,
                },
            }

        # Build graph
        graph = build_partner_graph(records)

        return graph.to_dict()
    except Exception as e:
        logger.error(f"Failed to build partner graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/enrich")
async def enrich_partners(request: Request) -> Dict[str, Any]:
    """Enrich partner data with intelligence insights.

    Combines scoring, capabilities, trends, and relationship data
    into comprehensive partner intelligence profiles.

    Returns:
        Enriched partner data with insights
    """
    try:
        # Load partner data
        sync = PartnerTierSync(store_path="data/oems.json")
        records = sync._load_store()

        if not records:
            return {
                "partners": [],
                "insights": {
                    "top_partners": [],
                    "capabilities_map": {},
                    "oem_coverage": {},
                },
            }

        # Enrich with scores
        enricher = PartnerEnricher()
        scores = enricher.enrich_partners(records)

        # Get top partners
        top_partners = enricher.get_top_partners(scores, limit=10)

        # Build capabilities map
        capabilities_map: Dict[str, List[str]] = {}
        for score in scores:
            for cap in score.capabilities:
                if cap not in capabilities_map:
                    capabilities_map[cap] = []
                capabilities_map[cap].append(score.name)

        # Build OEM coverage map
        oem_coverage: Dict[str, int] = {}
        for score in scores:
            oem_coverage[score.oem] = oem_coverage.get(score.oem, 0) + 1

        return {
            "partners": [s.to_dict() for s in scores],
            "insights": {
                "top_partners": [s.to_dict() for s in top_partners],
                "capabilities_map": capabilities_map,
                "oem_coverage": oem_coverage,
            },
        }
    except Exception as e:
        logger.error(f"Failed to enrich partners: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export/obsidian")
async def export_to_obsidian(req: ExportRequest, request: Request) -> Dict[str, Any]:
    """Export partner intelligence to Obsidian markdown files.

    Writes enriched partner data to <VAULT_ROOT>/30 Hubs/OEMs/
    with strength scores, capabilities, and relationship graphs.

    Args:
        req: ExportRequest with dry_run flag

    Returns:
        Export results with files written
    """
    try:
        vault_root = os.getenv("VAULT_ROOT")
        if not vault_root:
            raise HTTPException(status_code=500, detail="VAULT_ROOT not configured")

        # Load partner data
        sync = PartnerTierSync(vault_root=vault_root, store_path="data/oems.json")
        records = sync._load_store()

        if not records:
            return {
                "dry_run": req.dry_run,
                "files_written": 0,
                "message": "No partner data to export",
            }

        # Enrich with scores
        enricher = PartnerEnricher()
        scores = enricher.enrich_partners(records)

        # Group by OEM for export
        oem_partners: Dict[str, List[Any]] = {}
        for score in scores:
            if score.oem not in oem_partners:
                oem_partners[score.oem] = []
            oem_partners[score.oem].append(score)

        if req.dry_run:
            return {
                "dry_run": True,
                "files_to_write": len(oem_partners),
                "oems": list(oem_partners.keys()),
                "message": "Dry run - no files written",
            }

        # Export using existing sync mechanism
        result = sync.export_obsidian()

        # Add enrichment metadata
        result["enrichment"] = {
            "total_partners_scored": len(scores),
            "avg_strength_score": round(sum(s.strength_score for s in scores) / len(scores), 2) if scores else 0.0,
            "oems_exported": len(oem_partners),
        }

        return result
    except Exception as e:
        logger.error(f"Failed to export to Obsidian: {e}")
        raise HTTPException(status_code=500, detail=str(e))
