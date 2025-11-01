"""
Intelligent Opportunity Scoring Engine - Phase 5
Multi-factor scoring system for opportunities including:
- OEM alignment scoring
- Partner fit scoring
- Contract vehicle scoring
- Govly relevance scoring
- Win probability modeling
- Historical win-rate curves

Sprint 14: v2.1 Audited Bonuses & Guardrails
- Differentiated region bonuses based on historical win rates
- Tiered customer org bonuses (DoD, Civilian, Default)
- Scaled CV recommendation bonuses (single vs multiple)
- Maximum total bonus cap (15.0)
- Minimal feature store stub for future persistence
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

# ============================================================================
# v2.1 Audited Bonus Constants (Sprint 14)
# ============================================================================

# Region bonuses based on historical win rate analysis (FY23-FY25)
REGION_BONUS_AUDITED = {
    "East": 2.5,  # +0.5% (65% win rate vs 60% avg)
    "West": 2.0,  # No change (60% win rate = avg)
    "Central": 1.5,  # -0.5% (55% win rate vs 60% avg)
}

# Customer org bonuses tiered by strategic value
CUSTOMER_ORG_BONUS_AUDITED = {
    "DOD": 4.0,  # +1% (strategic account, 70% win rate)
    "Civilian": 3.0,  # No change (60% win rate)
    "Default": 2.0,  # For known orgs not in top tiers
}

# CV recommendation bonuses scaled by flexibility
CV_RECOMMENDATION_BONUS_AUDITED = {
    "single": 5.0,  # 1 CV recommended (validates fit)
    "multiple": 7.0,  # 2+ CVs (higher flexibility, 15% faster close)
}

# Guardrails: Maximum total bonus to prevent score inflation
MAX_TOTAL_BONUS = 15.0

# Score bounds
MIN_SCORE = 0.0
MAX_SCORE = 100.0
MIN_WIN_PROB = 0.0
MAX_WIN_PROB = 1.0

# ============================================================================
# Feature Store (In-Memory Stub for Sprint 14)
# ============================================================================

# In-memory feature store: {opportunity_id: features_dict}
# Production: persist to data/feature_store.jsonl
_feature_store: Dict[str, Dict[str, Any]] = {}

FEATURE_SCHEMA = {
    "opportunity_id": str,
    "oem_alignment": float,
    "partner_fit": float,
    "vehicle_score": float,
    "region_bonus": float,
    "org_bonus": float,
    "cv_bonus": float,
}


def save_features(opportunity_id: str, features: Dict[str, Any]) -> None:
    """
    Save features to in-memory feature store (stub).

    Args:
        opportunity_id: Unique opportunity identifier
        features: Feature dictionary to store
    """
    _feature_store[opportunity_id] = {
        "opportunity_id": opportunity_id,
        "scored_at": datetime.utcnow().isoformat() + "Z",
        **features,
    }


def get_features(opportunity_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve features from feature store.

    Args:
        opportunity_id: Unique opportunity identifier

    Returns:
        Feature dictionary or None if not found
    """
    return _feature_store.get(opportunity_id)


class OpportunityScorer:
    """
    Intelligent scoring engine for opportunities.

    Calculates multi-dimensional scores to predict win probability
    and business value alignment.
    """

    # OEM alignment scores (based on DealCraft's strategic partnerships)
    OEM_ALIGNMENT_SCORES = {
        "Microsoft": 95,
        "Cisco": 92,
        "Dell": 90,
        "HPE": 88,
        "VMware": 85,
        "NetApp": 83,
        "Palo Alto Networks": 88,
        "Fortinet": 85,
        "AWS": 80,
        "Google": 75,
        "Oracle": 70,
        "IBM": 68,
        "Default": 50,
    }

    # Contract vehicle priority scores
    CONTRACT_VEHICLE_SCORES = {
        "GSA Schedule": 90,
        "SEWP V": 95,
        "NASA SOLUTIONS": 92,
        "DHS FirstSource II": 88,
        "CIO-SP3": 85,
        "Alliant 2": 83,
        "8(a) STARS II": 80,
        "Direct": 60,
        "Default": 50,
    }

    # Stage multipliers for win probability
    STAGE_MULTIPLIERS = {
        "Qualification": 0.15,
        "Discovery": 0.25,
        "Proposal": 0.45,
        "Negotiation": 0.75,
        "Closed Won": 1.0,
        "Closed Lost": 0.0,
        "Default": 0.20,
    }

    def __init__(self):
        """Initialize the scoring engine."""
        self.historical_win_rates = {}  # Will be populated from historical data

    def calculate_oem_alignment_score(self, oems: List[str]) -> float:
        """
        Calculate OEM alignment score based on strategic partnerships.

        Args:
            oems: List of OEM names associated with the opportunity

        Returns:
            Score from 0-100
        """
        if not oems:
            return self.OEM_ALIGNMENT_SCORES["Default"]

        scores = []
        for oem in oems:
            # Fuzzy matching - check if any known OEM is in the string
            matched_score = None
            for known_oem, score in self.OEM_ALIGNMENT_SCORES.items():
                if known_oem.lower() in oem.lower() or oem.lower() in known_oem.lower():
                    matched_score = score
                    break

            scores.append(matched_score if matched_score else self.OEM_ALIGNMENT_SCORES["Default"])

        # Return highest OEM score (best alignment)
        return max(scores)

    def calculate_contract_vehicle_score(self, vehicle: str) -> float:
        """
        Calculate contract vehicle score based on DealCraft's vehicle priorities.

        Args:
            vehicle: Contract vehicle name

        Returns:
            Score from 0-100
        """
        if not vehicle:
            return self.CONTRACT_VEHICLE_SCORES["Default"]

        # Check for exact or partial matches
        for known_vehicle, score in self.CONTRACT_VEHICLE_SCORES.items():
            if known_vehicle.lower() in vehicle.lower() or vehicle.lower() in known_vehicle.lower():
                return score

        return self.CONTRACT_VEHICLE_SCORES["Default"]

    def calculate_partner_fit_score(self, partners: List[str], oems: List[str]) -> float:
        """
        Calculate partner fit score based on partner-OEM alignment.

        Args:
            partners: List of partners involved
            oems: List of OEMs involved

        Returns:
            Score from 0-100
        """
        if not partners:
            return 50.0  # Neutral score if no partners

        # Base score starts at 60 for having partners
        score = 60.0

        # Bonus for multiple partners (ecosystem strength)
        if len(partners) > 1:
            score += min(len(partners) * 5, 20)  # Max +20 for multiple partners

        # Bonus if partners align with OEMs (assumes named partnerships)
        alignment_bonus = 0
        for partner in partners:
            for oem in oems:
                if oem.lower() in partner.lower() or partner.lower() in oem.lower():
                    alignment_bonus += 10

        score += min(alignment_bonus, 20)  # Max +20 for alignment

        return min(score, 100.0)

    def calculate_govly_relevance_score(self, tags: List[str], source: str) -> float:
        """
        Calculate Govly relevance score based on opportunity metadata.

        Args:
            tags: List of tags associated with the opportunity
            source: Source of the opportunity (e.g., "Govly", "Direct", etc.)

        Returns:
            Score from 0-100
        """
        score = 50.0  # Base score

        # High score if explicitly from Govly
        if source and "govly" in source.lower():
            score = 85.0

        # Check tags for government/federal indicators
        gov_keywords = ["federal", "government", "agency", "dod", "civilian", "govly"]
        if tags:
            matching_tags = sum(1 for tag in tags for keyword in gov_keywords if keyword in tag.lower())
            score += min(matching_tags * 10, 30)  # Max +30 for gov tags

        return min(score, 100.0)

    def calculate_amount_score(self, amount: float) -> float:
        """
        Calculate score based on deal size (larger deals get higher scores).

        Args:
            amount: Deal amount in USD

        Returns:
            Score from 0-100
        """
        if amount <= 0:
            return 0.0

        # Logarithmic scale for deal size
        # $10K = 40, $100K = 60, $1M = 80, $10M = 95, $100M = 100
        if amount < 10000:
            return 20.0
        elif amount < 50000:
            return 40.0
        elif amount < 100000:
            return 50.0
        elif amount < 250000:
            return 60.0
        elif amount < 500000:
            return 70.0
        elif amount < 1000000:
            return 80.0
        elif amount < 5000000:
            return 90.0
        elif amount < 10000000:
            return 95.0
        else:
            return 100.0

    def calculate_stage_probability(self, stage: str) -> float:
        """
        Calculate win probability based on opportunity stage.

        Args:
            stage: Current opportunity stage

        Returns:
            Probability from 0.0 to 1.0
        """
        for known_stage, multiplier in self.STAGE_MULTIPLIERS.items():
            if known_stage.lower() in stage.lower():
                return multiplier

        return self.STAGE_MULTIPLIERS["Default"]

    def calculate_time_decay_factor(self, close_date: str) -> float:
        """
        Calculate time decay factor (closer dates = higher urgency).

        Args:
            close_date: Expected close date (ISO format)

        Returns:
            Factor from 0.5 to 1.0
        """
        try:
            close_dt = datetime.fromisoformat(close_date.replace("Z", "+00:00"))
            now = datetime.now(close_dt.tzinfo)
            days_until_close = (close_dt - now).days

            if days_until_close < 0:
                return 0.5  # Past due - lower urgency
            elif days_until_close < 30:
                return 1.0  # Urgent - closing soon
            elif days_until_close < 90:
                return 0.95
            elif days_until_close < 180:
                return 0.85
            elif days_until_close < 365:
                return 0.75
            else:
                return 0.6  # Far future - lower urgency
        except (ValueError, AttributeError):
            return 0.75  # Default if date is invalid

    def calculate_composite_score(self, opportunity: Dict[str, Any], include_reasoning: bool = False) -> Dict[str, Any]:
        """
        Calculate comprehensive multi-factor score for an opportunity.

        Phase 9: Enhanced with Phase 6-8 factors (CRM, CV, attribution)

        Args:
            opportunity: Opportunity data dictionary
            include_reasoning: If True, include detailed score reasoning

        Returns:
            Dictionary containing all scores and final win probability
        """
        # Extract relevant fields
        oems = opportunity.get("oems", [])
        if not isinstance(oems, list):
            oems = [oems] if oems else []

        partners = opportunity.get("partners", [])
        if not isinstance(partners, list):
            partners = [partners] if partners else []

        tags = opportunity.get("tags", [])
        if not isinstance(tags, list):
            tags = []

        amount_value = opportunity.get("amount", opportunity.get("est_amount", 0))
        amount = float(amount_value) if amount_value is not None else 0.0
        stage = opportunity.get("stage", "Unknown")
        close_date = opportunity.get("close_date", opportunity.get("est_close", ""))
        source = opportunity.get("source", "")
        vehicle = opportunity.get("contract_vehicle", "")

        # Phase 6-8: Additional context
        region = opportunity.get("region", "")
        customer_org = opportunity.get("customer_org", "")
        contracts_recommended = opportunity.get("contracts_recommended", [])

        # Calculate individual scores
        oem_score = self.calculate_oem_alignment_score(oems)
        partner_score = self.calculate_partner_fit_score(partners, oems)
        vehicle_score = self.calculate_contract_vehicle_score(vehicle)
        govly_score = self.calculate_govly_relevance_score(tags, source)
        amount_score = self.calculate_amount_score(amount)
        stage_prob = self.calculate_stage_probability(stage)
        time_factor = self.calculate_time_decay_factor(close_date)

        # Sprint 14 v2.1: Apply audited bonuses with guardrails
        # Region bonus (audited based on historical win rates)
        region_bonus = 0.0
        if region in REGION_BONUS_AUDITED:
            region_bonus = REGION_BONUS_AUDITED[region]

        # Customer org bonus (tiered by strategic value)
        org_bonus = 0.0
        if customer_org:
            # Check for DOD/Civilian keywords
            customer_org_upper = customer_org.upper()
            if "DOD" in customer_org_upper or "DEFENSE" in customer_org_upper:
                org_bonus = CUSTOMER_ORG_BONUS_AUDITED["DOD"]
            elif "CIVIL" in customer_org_upper or "Federal Agency A" in customer_org_upper:
                org_bonus = CUSTOMER_ORG_BONUS_AUDITED["Civilian"]
            else:
                org_bonus = CUSTOMER_ORG_BONUS_AUDITED["Default"]

        # CV recommendation bonus (scaled by count)
        cv_bonus = 0.0
        if contracts_recommended and len(contracts_recommended) > 0:
            if len(contracts_recommended) == 1:
                cv_bonus = CV_RECOMMENDATION_BONUS_AUDITED["single"]
            else:  # 2+ CVs
                cv_bonus = CV_RECOMMENDATION_BONUS_AUDITED["multiple"]

        # Calculate weighted composite score (0-100)
        weights = {
            "oem_alignment": 0.25,
            "partner_fit": 0.15,
            "vehicle": 0.20,
            "govly_relevance": 0.10,
            "amount": 0.30,
        }

        raw_score = (
            oem_score * weights["oem_alignment"]
            + partner_score * weights["partner_fit"]
            + vehicle_score * weights["vehicle"]
            + govly_score * weights["govly_relevance"]
            + amount_score * weights["amount"]
        )

        # Sprint 14 v2.1: Apply guardrails
        # Cap total bonuses to prevent score inflation
        total_bonuses = region_bonus + org_bonus + cv_bonus

        # If bonuses exceeded cap, scale them proportionally
        if total_bonuses > MAX_TOTAL_BONUS:
            scale_factor = MAX_TOTAL_BONUS / total_bonuses
            region_bonus *= scale_factor
            org_bonus *= scale_factor
            cv_bonus *= scale_factor

        # Apply bonuses and cap final score
        enhanced_score = min(raw_score + region_bonus + org_bonus + cv_bonus, MAX_SCORE)

        # Apply stage probability and time decay to get final win probability
        win_probability = enhanced_score * stage_prob * time_factor / 100.0

        # Scale win probability to 0-100 and apply bounds
        win_prob_scaled = min(max(win_probability * 100, MIN_WIN_PROB * 100), MAX_SCORE)

        # Build score reasoning (Phase 9)
        score_reasoning = []
        if include_reasoning:
            score_reasoning.append(
                f"Base Score: {raw_score:.1f}% (OEM:{oem_score:.0f} Partner:{partner_score:.0f} Vehicle:{vehicle_score:.0f})"
            )
            if region_bonus > 0:
                score_reasoning.append(f"+ Region Bonus: {region_bonus:.0f}% ({region})")
            if org_bonus > 0:
                score_reasoning.append(f"+ Customer Org Bonus: {org_bonus:.0f}%")
            if cv_bonus > 0:
                score_reasoning.append(f"+ CV Recommended Bonus: {cv_bonus:.0f}% ({len(contracts_recommended)} vehicles)")
            score_reasoning.append(f"= Enhanced Score: {enhanced_score:.1f}%")
            score_reasoning.append(f"× Stage Probability: {stage_prob*100:.0f}% ({stage})")
            score_reasoning.append(f"× Time Decay: {time_factor:.2f}")
            score_reasoning.append(f"= Win Probability: {win_prob_scaled:.1f}%")

        result = {
            "score_raw": round(raw_score, 2),
            "score_scaled": round(enhanced_score, 2),  # Enhanced with bonuses
            "win_prob": round(win_prob_scaled, 2),
            "oem_alignment_score": round(oem_score, 2),
            "partner_fit_score": round(partner_score, 2),
            "contract_vehicle_score": round(vehicle_score, 2),
            "govly_relevance_score": round(govly_score, 2),
            "amount_score": round(amount_score, 2),
            "stage_probability": round(stage_prob * 100, 2),
            "time_decay_factor": round(time_factor, 2),
            # Phase 9: Enhanced factors
            "region_bonus": round(region_bonus, 2),
            "customer_org_bonus": round(org_bonus, 2),
            "cv_recommendation_bonus": round(cv_bonus, 2),
            "total_bonuses_applied": round(region_bonus + org_bonus + cv_bonus, 2),
            "weights_used": weights,
            "scoring_model": "multi_factor_v2.1_audited",  # Sprint 14: v2.1
            "scored_at": datetime.utcnow().isoformat() + "Z",
        }

        if include_reasoning:
            result["score_reasoning"] = score_reasoning

        # Sprint 14: Save to feature store (in-memory stub)
        opp_id = opportunity.get("id", f"temp_{datetime.utcnow().timestamp()}")
        save_features(
            opp_id,
            {
                "oem_alignment": oem_score,
                "partner_fit": partner_score,
                "vehicle_score": vehicle_score,
                "region_bonus": region_bonus,
                "org_bonus": org_bonus,
                "cv_bonus": cv_bonus,
                "raw_score": raw_score,
                "enhanced_score": enhanced_score,
                "win_probability": win_prob_scaled,
            },
        )

        return result

    def calculate_confidence_interval(self, win_prob: float, amount: float, stage: str) -> Dict[str, float]:
        """
        Calculate confidence interval for forecast.

        Args:
            win_prob: Win probability (0-100)
            amount: Deal amount
            stage: Current stage

        Returns:
            Dictionary with lower, upper bounds and interval width
        """
        # Base interval width depends on stage
        stage_variance = {
            "Qualification": 0.40,
            "Discovery": 0.35,
            "Proposal": 0.25,
            "Negotiation": 0.15,
            "Default": 0.30,
        }

        variance = stage_variance.get(stage, stage_variance["Default"])

        # Adjust variance based on deal size (larger deals = more uncertainty)
        if amount > 5000000:
            variance *= 1.3
        elif amount > 1000000:
            variance *= 1.15

        lower_bound = max(0, win_prob - (variance * 100))
        upper_bound = min(100, win_prob + (variance * 100))

        return {
            "lower_bound": round(lower_bound, 2),
            "upper_bound": round(upper_bound, 2),
            "interval_width": round(upper_bound - lower_bound, 2),
            "confidence_level": 0.80,  # 80% confidence interval
        }


# Global scorer instance
scorer = OpportunityScorer()
