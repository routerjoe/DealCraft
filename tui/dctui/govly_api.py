"""
API bridge for Govly/Radar opportunities from state.json
"""

import json
from pathlib import Path
from typing import Any, Dict, List


def load_opportunities() -> List[Dict[str, Any]]:
    """Load opportunities from state.json"""
    state_file = Path(__file__).resolve().parents[2] / "data" / "state.json"

    if not state_file.exists():
        return []

    try:
        with open(state_file, "r") as f:
            state = json.load(f)
            return state.get("opportunities", [])
    except (json.JSONDecodeError, IOError):
        return []


def filter_by_source(opportunities: List[Dict[str, Any]], source: str) -> List[Dict[str, Any]]:
    """Filter opportunities by source (govly, radar, etc.)"""
    return [opp for opp in opportunities if opp.get("source", "").lower() == source.lower()]


def get_govly_opportunities() -> List[Dict[str, Any]]:
    """Get all Govly opportunities"""
    opps = load_opportunities()
    return filter_by_source(opps, "govly")


def get_radar_opportunities() -> List[Dict[str, Any]]:
    """Get all Radar opportunities"""
    opps = load_opportunities()
    return filter_by_source(opps, "radar")


def get_opportunity_stats() -> Dict[str, int]:
    """Get opportunity statistics by source"""
    opps = load_opportunities()

    stats = {
        "total": len(opps),
        "govly": len([o for o in opps if o.get("source") == "govly"]),
        "radar": len([o for o in opps if o.get("source") == "radar"]),
        "triage": len([o for o in opps if o.get("triage")]),
    }

    return stats
