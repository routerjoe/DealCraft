"""Partner enrichment and strength scoring engine.

This module provides normalized partner strength scores (0-100 scale)
based on multiple factors including tier, OEM alignment, program diversity,
and relationship depth.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Strategic OEMs with their alignment weights
STRATEGIC_OEMS = {
    "Microsoft": 100,
    "Cisco": 95,
    "Dell": 90,
    "HPE": 88,
    "Lenovo": 85,
    "NetApp": 82,
    "VMware": 80,
    "Palo Alto": 78,
    "Fortinet": 75,
    "AWS": 95,
    "Google": 92,
    "Oracle": 85,
}

# Tier base weights
TIER_WEIGHTS = {
    "gold": 100,
    "silver": 75,
    "bronze": 50,
    "partner": 40,  # Generic partner designation
}


@dataclass
class PartnerScore:
    """Partner strength score with breakdown."""

    name: str
    strength_score: float  # 0-100 normalized score
    tier: str
    oem: str
    oem_count: int
    program_count: int
    capabilities: List[str]
    trend: str  # "rising", "stable", "declining"
    breakdown: Dict[str, float]
    metadata: Dict[str, Any]
    scored_at: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert score to dictionary."""
        return {
            "name": self.name,
            "strength_score": round(self.strength_score, 2),
            "tier": self.tier,
            "oem": self.oem,
            "oem_count": self.oem_count,
            "program_count": self.program_count,
            "capabilities": self.capabilities,
            "trend": self.trend,
            "breakdown": {k: round(v, 2) for k, v in self.breakdown.items()},
            "metadata": self.metadata,
            "scored_at": self.scored_at,
        }


class PartnerEnricher:
    """Partner enrichment and scoring engine."""

    def __init__(self, strategic_oems: Optional[Dict[str, int]] = None):
        """Initialize enricher with optional custom OEM weights.

        Args:
            strategic_oems: Optional custom OEM alignment weights
        """
        self.strategic_oems = strategic_oems or STRATEGIC_OEMS

    def calculate_tier_score(self, tier: str) -> float:
        """Calculate base score from tier.

        Args:
            tier: Partner tier (gold, silver, bronze, etc.)

        Returns:
            Tier score (0-100)
        """
        tier_lower = tier.lower()
        return float(TIER_WEIGHTS.get(tier_lower, 30))

    def calculate_oem_alignment_score(self, oem: str) -> float:
        """Calculate OEM strategic alignment score.

        Args:
            oem: OEM name

        Returns:
            OEM alignment score (0-100)
        """
        return float(self.strategic_oems.get(oem, 50))

    def calculate_program_diversity_score(self, program_count: int) -> float:
        """Calculate score based on program diversity.

        More programs = higher score, with diminishing returns.

        Args:
            program_count: Number of programs

        Returns:
            Diversity score (0-20)
        """
        if program_count <= 0:
            return 0.0
        elif program_count == 1:
            return 5.0
        elif program_count == 2:
            return 10.0
        elif program_count == 3:
            return 15.0
        else:
            return 20.0

    def calculate_relationship_bonus(self, has_poc: bool, has_notes: bool, note_length: int = 0) -> float:
        """Calculate bonus for relationship depth.

        Args:
            has_poc: Whether POC is assigned
            has_notes: Whether notes exist
            note_length: Length of notes

        Returns:
            Relationship bonus (0-10)
        """
        bonus = 0.0

        if has_poc:
            bonus += 5.0

        if has_notes:
            bonus += 2.0
            # Additional bonus for detailed notes
            if note_length > 100:
                bonus += 3.0
            elif note_length > 50:
                bonus += 1.5

        return min(bonus, 10.0)

    def infer_capabilities(self, partner_data: Dict[str, Any]) -> List[str]:
        """Infer partner capabilities from available data.

        Args:
            partner_data: Partner record dictionary

        Returns:
            List of capability tags
        """
        capabilities = []

        # Infer from OEM
        oem = partner_data.get("oem", "").lower()
        if "microsoft" in oem or "azure" in oem:
            capabilities.append("cloud")
        if "cisco" in oem or "palo alto" in oem or "fortinet" in oem:
            capabilities.append("security")
        if "dell" in oem or "hpe" in oem or "lenovo" in oem:
            capabilities.append("hardware")
        if "vmware" in oem:
            capabilities.append("virtualization")
        if "netapp" in oem:
            capabilities.append("storage")

        # Infer from program
        program = partner_data.get("program", "").lower()
        if "cloud" in program:
            capabilities.append("cloud")
        if "security" in program:
            capabilities.append("security")
        if "data" in program or "storage" in program:
            capabilities.append("storage")

        # Infer from notes
        notes = partner_data.get("notes", "").lower()
        if notes:
            if "cloud" in notes or "azure" in notes or "aws" in notes:
                capabilities.append("cloud")
            if "security" in notes or "cybersecurity" in notes:
                capabilities.append("security")
            if "ai" in notes or "machine learning" in notes:
                capabilities.append("ai")
            if "network" in notes:
                capabilities.append("networking")

        # Remove duplicates
        return list(set(capabilities))

    def determine_trend(self, partner_data: Dict[str, Any]) -> str:
        """Determine partner trend based on available data.

        Args:
            partner_data: Partner record dictionary

        Returns:
            Trend indicator: "rising", "stable", "declining"
        """
        # For now, simple logic based on tier and recent activity
        tier = partner_data.get("tier", "").lower()
        updated_at = partner_data.get("updated_at")
        created_at = partner_data.get("created_at")

        # Check if recently updated
        if updated_at and created_at:
            try:
                updated = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                days_diff = (updated - created).days

                # If updated within 90 days of creation, likely rising
                if days_diff < 90 and tier == "gold":
                    return "rising"
                elif days_diff < 90:
                    return "stable"
            except Exception:
                pass

        # Gold tier is generally stable or rising
        if tier == "gold":
            return "stable"
        elif tier == "silver":
            return "stable"
        else:
            return "stable"

    def calculate_strength_score(self, partner_data: Dict[str, Any]) -> PartnerScore:
        """Calculate comprehensive strength score for a partner.

        Scoring formula:
        base_score = tier_weight * 0.6 + oem_alignment * 0.3 + diversity * 0.1
        final_score = min(100, base_score + relationship_bonus)

        Args:
            partner_data: Partner record dictionary

        Returns:
            PartnerScore object with complete breakdown
        """
        name = partner_data["name"]
        tier = partner_data["tier"]
        oem = partner_data["oem"]
        poc = partner_data.get("poc")
        notes = partner_data.get("notes", "")

        # Calculate component scores
        tier_score = self.calculate_tier_score(tier)
        oem_score = self.calculate_oem_alignment_score(oem)

        # Estimate program count (would be better with actual data)
        program_count = 1  # Default assumption
        diversity_score = self.calculate_program_diversity_score(program_count)

        # Calculate relationship bonus
        relationship_bonus = self.calculate_relationship_bonus(has_poc=bool(poc), has_notes=bool(notes), note_length=len(notes))

        # Weighted combination
        base_score = tier_score * 0.6 + oem_score * 0.3 + diversity_score * 0.5
        final_score = min(100.0, base_score + relationship_bonus)

        # Infer capabilities and trend
        capabilities = self.infer_capabilities(partner_data)
        trend = self.determine_trend(partner_data)

        # Build breakdown
        breakdown = {
            "tier_score": tier_score,
            "oem_alignment_score": oem_score,
            "program_diversity_score": diversity_score,
            "relationship_bonus": relationship_bonus,
            "base_score": base_score,
        }

        return PartnerScore(
            name=name,
            strength_score=final_score,
            tier=tier,
            oem=oem,
            oem_count=1,  # Would need aggregation logic for multiple OEMs
            program_count=program_count,
            capabilities=capabilities,
            trend=trend,
            breakdown=breakdown,
            metadata={
                "has_poc": bool(poc),
                "has_notes": bool(notes),
                "notes_length": len(notes),
            },
            scored_at=datetime.now(timezone.utc).isoformat(),
        )

    def enrich_partners(self, partner_records: List[Dict[str, Any]]) -> List[PartnerScore]:
        """Enrich multiple partner records with scores.

        Args:
            partner_records: List of partner dictionaries

        Returns:
            List of PartnerScore objects
        """
        scores = []

        for record in partner_records:
            try:
                score = self.calculate_strength_score(record)
                scores.append(score)
            except Exception as e:
                logger.error(f"Failed to score partner {record.get('name', 'unknown')}: {e}")

        # Sort by strength score descending
        scores.sort(key=lambda x: x.strength_score, reverse=True)

        logger.info(f"Enriched {len(scores)} partners with strength scores")
        return scores

    def get_top_partners(self, scores: List[PartnerScore], limit: int = 20) -> List[PartnerScore]:
        """Get top N partners by strength score.

        Args:
            scores: List of PartnerScore objects
            limit: Number of top partners to return

        Returns:
            Top N partners
        """
        return sorted(scores, key=lambda x: x.strength_score, reverse=True)[:limit]

    def get_partners_by_capability(self, scores: List[PartnerScore], capability: str) -> List[PartnerScore]:
        """Filter partners by capability.

        Args:
            scores: List of PartnerScore objects
            capability: Capability to filter by

        Returns:
            Partners with specified capability
        """
        return [s for s in scores if capability.lower() in [c.lower() for c in s.capabilities]]

    def get_partners_by_oem(self, scores: List[PartnerScore], oem: str) -> List[PartnerScore]:
        """Filter partners by OEM.

        Args:
            scores: List of PartnerScore objects
            oem: OEM name

        Returns:
            Partners for specified OEM
        """
        return [s for s in scores if s.oem.lower() == oem.lower()]

    def get_score_distribution(self, scores: List[PartnerScore]) -> Dict[str, int]:
        """Get distribution of partners across score ranges.

        Args:
            scores: List of PartnerScore objects

        Returns:
            Dictionary mapping score range to count
        """
        distribution = {
            "90-100": 0,
            "80-89": 0,
            "70-79": 0,
            "60-69": 0,
            "50-59": 0,
            "below-50": 0,
        }

        for score in scores:
            s = score.strength_score
            if s >= 90:
                distribution["90-100"] += 1
            elif s >= 80:
                distribution["80-89"] += 1
            elif s >= 70:
                distribution["70-79"] += 1
            elif s >= 60:
                distribution["60-69"] += 1
            elif s >= 50:
                distribution["50-59"] += 1
            else:
                distribution["below-50"] += 1

        return distribution
