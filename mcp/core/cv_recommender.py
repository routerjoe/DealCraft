"""
Contract Vehicle Recommender Engine - Phase 8

Analyzes opportunities and recommends optimal contract vehicles based on:
- OEM alignment
- Customer requirements
- Existing DealCraft contracts
- BPA availability
- Historical success rates

Now uses Entity Management System for contract vehicle data.
"""

from typing import Any, Dict, List, Tuple

from mcp.core.entities import contract_vehicle_store


class CVRecommender:
    """
    Contract Vehicle Recommendation Engine.

    Scores and recommends contract vehicles for opportunities
    based on multiple factors.
    """

    def __init__(self):
        """Initialize CV recommender with entity store."""
        self._cv_store = contract_vehicle_store

    # Legacy contract vehicle database for backward compatibility
    CONTRACT_VEHICLES = {
        "SEWP V": {
            "priority": 95,
            "oems_supported": [
                "Microsoft",
                "Cisco",
                "Dell",
                "HPE",
                "VMware",
                "NetApp",
            ],
            "categories": ["IT Hardware", "Software", "Cloud Services"],
            "active_bpas": True,
            "ceiling": 50000000000,  # $50B
        },
        "NASA SOLUTIONS": {
            "priority": 92,
            "oems_supported": ["Dell", "HPE", "Cisco", "Microsoft"],
            "categories": ["IT Hardware", "Professional Services"],
            "active_bpas": True,
            "ceiling": 20000000000,
        },
        "GSA Schedule": {
            "priority": 90,
            "oems_supported": ["Microsoft", "Cisco", "Dell", "HPE", "All OEMs"],
            "categories": ["All Categories"],
            "active_bpas": True,
            "ceiling": None,  # No ceiling
        },
        "DHS FirstSource II": {
            "priority": 88,
            "oems_supported": ["Cisco", "Palo Alto Networks", "Fortinet"],
            "categories": ["Cybersecurity", "Networking"],
            "active_bpas": True,
            "ceiling": 22000000000,
        },
        "CIO-SP3": {
            "priority": 85,
            "oems_supported": ["All OEMs"],
            "categories": ["IT Services", "Cloud", "Cybersecurity"],
            "active_bpas": False,
            "ceiling": 20000000000,
        },
        "Alliant 2": {
            "priority": 83,
            "oems_supported": ["All OEMs"],
            "categories": ["IT Services", "Professional Services"],
            "active_bpas": False,
            "ceiling": 65000000000,
        },
        "8(a) STARS II": {
            "priority": 80,
            "oems_supported": ["All OEMs"],
            "categories": ["IT Services", "Small Business"],
            "active_bpas": False,
            "ceiling": 15000000000,
        },
    }

    def calculate_cv_score(self, cv_name: str, opportunity: Dict[str, Any]) -> Tuple[float, List[str]]:
        """
        Calculate fit score for a contract vehicle.

        Args:
            cv_name: Contract vehicle name
            opportunity: Opportunity data

        Returns:
            Tuple of (score 0-100, list of reasons)
        """
        # Try entity store first
        cv_entity = self._cv_store.get_by_name(cv_name)

        if cv_entity:
            # Use entity store data
            score = cv_entity.priority_score
            reasons = []

            # Check OEM alignment
            oems = opportunity.get("oems", [])
            if not isinstance(oems, list):
                oems = [oems] if oems else []

            oem_matches = 0
            # Convert OEM names to lowercase IDs for matching
            cv_oem_ids = [oem_id.lower() for oem_id in cv_entity.oems_supported]

            # Check if this CV supports all major OEMs (12+)
            if len(cv_entity.oems_supported) >= 12:
                # Treat as "All OEMs" supported
                for oem in oems:
                    oem_matches += 1
                    reasons.append(f"✓ {cv_name} supports all OEMs")
                    break
            else:
                for oem in oems:
                    oem_lower = oem.lower()
                    # Check if any supported OEM matches
                    if any(oem_id in oem_lower or oem_lower in oem_id for oem_id in cv_oem_ids):
                        oem_matches += 1
                        reasons.append(f"✓ {cv_name} supports {oem}")

            # OEM alignment bonus
            if oem_matches > 0:
                score += min(oem_matches * 2, 5)  # +2 per match, max +5

            # BPA bonus
            if cv_entity.active_bpas > 0:
                score += 3
                reasons.append(f"✓ DealCraft has active BPAs on {cv_name}")

            # Check amount against ceiling
            amount = float(opportunity.get("amount", opportunity.get("est_amount", 0)))
            ceiling = cv_entity.ceiling_amount
            if ceiling and amount <= ceiling:
                reasons.append(f"✓ Deal size (${amount:,.0f}) within {cv_name} ceiling")
            elif ceiling and amount > ceiling:
                score -= 20
                reasons.append(f"⚠ Deal size (${amount:,.0f}) exceeds {cv_name} ceiling (${ceiling:,.0f})")

            return (min(score, 100.0), reasons)

        # Fallback to legacy data
        if cv_name not in self.CONTRACT_VEHICLES:
            return (50.0, ["Unknown contract vehicle"])

        cv_data = self.CONTRACT_VEHICLES[cv_name]
        score = cv_data["priority"]
        reasons = []

        # Check OEM alignment
        oems = opportunity.get("oems", [])
        if not isinstance(oems, list):
            oems = [oems] if oems else []

        oem_matches = 0
        for oem in oems:
            if "All OEMs" in cv_data["oems_supported"]:
                oem_matches += 1
                reasons.append(f"✓ {cv_name} supports all OEMs")
                break
            elif any(supported.lower() in oem.lower() or oem.lower() in supported.lower() for supported in cv_data["oems_supported"]):
                oem_matches += 1
                reasons.append(f"✓ {cv_name} supports {oem}")

        # OEM alignment bonus
        if oem_matches > 0:
            score += min(oem_matches * 2, 5)  # +2 per match, max +5

        # BPA bonus
        if cv_data["active_bpas"]:
            score += 3
            reasons.append(f"✓ DealCraft has active BPAs on {cv_name}")

        # Check amount against ceiling
        amount = float(opportunity.get("amount", opportunity.get("est_amount", 0)))
        ceiling = cv_data.get("ceiling")
        if ceiling and amount <= ceiling:
            reasons.append(f"✓ Deal size (${amount:,.0f}) within {cv_name} ceiling")
        elif ceiling and amount > ceiling:
            score -= 20
            reasons.append(f"⚠ Deal size (${amount:,.0f}) exceeds {cv_name} ceiling (${ceiling:,.0f})")

        return (min(score, 100.0), reasons)

    def recommend_vehicles(self, opportunity: Dict[str, Any], top_n: int = 3) -> List[Dict[str, Any]]:
        """
        Recommend contract vehicles for an opportunity.

        Args:
            opportunity: Opportunity data dictionary
            top_n: Number of top recommendations to return

        Returns:
            List of recommended CVs with scores and reasoning
        """
        recommendations = []

        # Use entity store if available
        cvs = self._cv_store.get_all(active_only=True)
        if cvs:
            for cv in cvs:
                score, reasons = self.calculate_cv_score(cv.name, opportunity)

                recommendations.append(
                    {
                        "contract_vehicle": cv.name,
                        "cv_score": score,
                        "priority": cv.priority_score,
                        "reasoning": reasons,
                        "has_bpa": cv.active_bpas > 0,
                    }
                )
        else:
            # Fallback to legacy data
            for cv_name in self.CONTRACT_VEHICLES.keys():
                score, reasons = self.calculate_cv_score(cv_name, opportunity)

                recommendations.append(
                    {
                        "contract_vehicle": cv_name,
                        "cv_score": score,
                        "priority": self.CONTRACT_VEHICLES[cv_name]["priority"],
                        "reasoning": reasons,
                        "has_bpa": self.CONTRACT_VEHICLES[cv_name]["active_bpas"],
                    }
                )

        # Sort by score (descending)
        recommendations.sort(key=lambda x: x["cv_score"], reverse=True)

        return recommendations[:top_n]

    def get_available_vehicles(self) -> List[str]:
        """Get list of all available contract vehicles."""
        # Use entity store if available
        cvs = self._cv_store.get_all(active_only=True)
        if cvs:
            return [cv.name for cv in cvs]
        # Fallback to legacy data
        return list(self.CONTRACT_VEHICLES.keys())


# Global recommender instance
cv_recommender = CVRecommender()
