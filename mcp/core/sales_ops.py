"""Sales operations automation helpers (Sprint 19).

Provides helper functions for enriching forecasts with partner context,
calculating attributions, and preparing CRM exports.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def enrich_forecast_with_partners(forecast_data: Dict[str, Any], partner_scores: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Enrich forecast data with partner intelligence context.

    Args:
        forecast_data: Forecast result dictionary
        partner_scores: List of partner score dictionaries

    Returns:
        Enriched forecast with partner context
    """
    enriched = forecast_data.copy()

    # Extract partner names from opportunities
    partner_names = set()
    for opp in forecast_data.get("opportunities", []):
        partners = opp.get("partner_attribution", [])
        if isinstance(partners, list):
            partner_names.update(partners)

    # Find matching partner scores
    partner_context = []
    for name in partner_names:
        for score in partner_scores:
            if score["name"] == name:
                partner_context.append(
                    {
                        "name": score["name"],
                        "strength_score": score["strength_score"],
                        "tier": score["tier"],
                        "capabilities": score.get("capabilities", []),
                    }
                )
                break

    # Add partner context to enriched data
    enriched["partner_context"] = {
        "engaged_partners": len(partner_context),
        "partners": partner_context,
        "avg_partner_strength": round(
            sum(p["strength_score"] for p in partner_context) / len(partner_context),
            2,
        )
        if partner_context
        else 0.0,
    }

    return enriched


def calculate_partner_attribution(opportunity: Dict[str, Any], partners: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate partner attribution for an opportunity.

    Partner pool: 20% of deal value, split evenly among engaged partners.
    OEM attribution: 60/30/10% split maintained.

    Args:
        opportunity: Opportunity dictionary
        partners: List of engaged partner dictionaries

    Returns:
        Attribution breakdown
    """
    deal_value = opportunity.get("amount", 0)
    partner_names = opportunity.get("partner_attribution", [])

    if not partner_names or not partners:
        return {
            "partner_pool": 0.0,
            "partner_split": {},
            "oem_attribution": {},
        }

    # Partner pool: 20% of deal value
    partner_pool = deal_value * 0.20

    # Even split among partners
    partner_split = {}
    if partner_names:
        per_partner = partner_pool / len(partner_names)
        for name in partner_names:
            partner_split[name] = round(per_partner, 2)

    # OEM attribution (60/30/10%)
    oem_list = opportunity.get("oem_attribution", [])
    oem_attribution = {}
    if oem_list:
        if len(oem_list) >= 1:
            oem_attribution[oem_list[0]] = round(deal_value * 0.60, 2)
        if len(oem_list) >= 2:
            oem_attribution[oem_list[1]] = round(deal_value * 0.30, 2)
        if len(oem_list) >= 3:
            oem_attribution[oem_list[2]] = round(deal_value * 0.10, 2)

    return {
        "partner_pool": round(partner_pool, 2),
        "partner_split": partner_split,
        "oem_attribution": oem_attribution,
        "metadata": {
            "deal_value": deal_value,
            "partners_engaged": len(partner_names),
            "oems_engaged": len(oem_list),
        },
    }


def summarize_account_context(
    account_name: str, opportunities: List[Dict[str, Any]], partner_scores: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Summarize account context with partner intelligence.

    Args:
        account_name: Account/customer name
        opportunities: List of opportunities for this account
        partner_scores: List of partner score dictionaries

    Returns:
        Account summary with partner context
    """
    if not opportunities:
        return {
            "account_name": account_name,
            "total_pipeline": 0.0,
            "opportunity_count": 0,
            "engaged_partners": [],
            "partner_strength_avg": 0.0,
        }

    # Calculate totals
    total_pipeline = sum(opp.get("amount", 0) for opp in opportunities)

    # Collect engaged partners
    partner_names = set()
    for opp in opportunities:
        partners = opp.get("partner_attribution", [])
        if isinstance(partners, list):
            partner_names.update(partners)

    # Get partner strength scores
    partner_strengths = []
    engaged_partners = []
    for name in partner_names:
        for score in partner_scores:
            if score["name"] == name:
                partner_strengths.append(score["strength_score"])
                engaged_partners.append(
                    {
                        "name": score["name"],
                        "tier": score["tier"],
                        "strength_score": score["strength_score"],
                    }
                )
                break

    avg_strength = round(sum(partner_strengths) / len(partner_strengths), 2) if partner_strengths else 0.0

    return {
        "account_name": account_name,
        "total_pipeline": round(total_pipeline, 2),
        "opportunity_count": len(opportunities),
        "engaged_partners": engaged_partners,
        "partner_strength_avg": avg_strength,
        "top_opportunities": sorted(opportunities, key=lambda x: x.get("amount", 0), reverse=True)[:5],
    }


def prepare_crm_export_payload(opportunities: List[Dict[str, Any]], attribution_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Prepare CRM export payload with attribution.

    Args:
        opportunities: List of opportunity dictionaries
        attribution_data: List of attribution dictionaries

    Returns:
        CRM export payload
    """
    # Build attribution lookup
    attribution_map = {}
    for attr in attribution_data:
        opp_id = attr.get("opportunity_id")
        if opp_id:
            attribution_map[opp_id] = attr

    # Prepare opportunities with attribution
    export_opportunities = []
    for opp in opportunities:
        opp_id = opp.get("id", opp.get("name"))
        attribution = attribution_map.get(opp_id, {})

        export_opp = opp.copy()
        export_opp["attribution"] = attribution

        # Add CRM-specific fields
        export_opp["crm_amount"] = opp.get("amount", 0)
        export_opp["crm_stage"] = opp.get("stage", "Unknown")
        export_opp["crm_close_date"] = opp.get("close_date")

        export_opportunities.append(export_opp)

    return {
        "opportunities": export_opportunities,
        "summary": {
            "total_opportunities": len(export_opportunities),
            "total_pipeline": round(sum(o.get("amount", 0) for o in opportunities), 2),
            "with_attribution": sum(1 for o in export_opportunities if o.get("attribution")),
        },
    }


def inject_partner_context_to_reasoning(reasoning: str, partner_context: Dict[str, Any]) -> str:
    """Inject partner context into forecast reasoning string.

    Args:
        reasoning: Original reasoning string
        partner_context: Partner context dictionary

    Returns:
        Enhanced reasoning string
    """
    if not partner_context or not partner_context.get("partners"):
        return reasoning

    partners = partner_context["partners"]
    avg_strength = partner_context.get("avg_partner_strength", 0)

    partner_summary = f"\n\nPartner Context: {len(partners)} engaged partners "
    partner_summary += f"(avg strength: {avg_strength:.1f}/100). "

    # List top partners
    top_partners = sorted(partners, key=lambda x: x["strength_score"], reverse=True)[:3]
    if top_partners:
        partner_names = [f"{p['name']} ({p['tier']})" for p in top_partners]
        partner_summary += f"Key partners: {', '.join(partner_names)}."

    return reasoning + partner_summary


def calculate_partner_coverage_score(opportunity: Dict[str, Any], partner_scores: List[Dict[str, Any]]) -> float:
    """Calculate a coverage score based on partner engagement.

    Higher score indicates better partner coverage for the opportunity.

    Args:
        opportunity: Opportunity dictionary
        partner_scores: List of partner score dictionaries

    Returns:
        Coverage score (0-100)
    """
    partner_names = opportunity.get("partner_attribution", [])
    if not partner_names:
        return 0.0

    # Find partner scores
    engaged_scores = []
    for name in partner_names:
        for score in partner_scores:
            if score["name"] == name:
                engaged_scores.append(score["strength_score"])
                break

    if not engaged_scores:
        return 0.0

    # Calculate coverage: average strength with bonus for multiple partners
    avg_strength = sum(engaged_scores) / len(engaged_scores)
    coverage_bonus = min(len(engaged_scores) * 5, 20)  # Up to 20 point bonus

    return min(100.0, avg_strength + coverage_bonus)


def get_partner_recommendations(opportunity: Dict[str, Any], partner_scores: List[Dict[str, Any]], limit: int = 3) -> List[Dict[str, Any]]:
    """Recommend partners for an opportunity based on OEM and capabilities.

    Args:
        opportunity: Opportunity dictionary
        partner_scores: List of partner score dictionaries
        limit: Number of recommendations to return

    Returns:
        List of recommended partner dictionaries
    """
    oem = opportunity.get("oem")
    if not oem:
        return []

    # Filter partners by OEM
    matching_partners = [p for p in partner_scores if p.get("oem") == oem]

    # Sort by strength score
    matching_partners.sort(key=lambda x: x["strength_score"], reverse=True)

    # Return top N
    recommendations = []
    for partner in matching_partners[:limit]:
        recommendations.append(
            {
                "name": partner["name"],
                "tier": partner["tier"],
                "strength_score": partner["strength_score"],
                "capabilities": partner.get("capabilities", []),
                "reason": f"Strong {partner['tier']} partner for {oem}",
            }
        )

    return recommendations
