"""
AI Account Plans Generation Engine - Sprint 12
Generates strategic account plans for federal customers (AFCENT, AETC)

Features:
- Pulls forecast data (scores, win_prob, FY projections)
- Integrates CV recommender for contract vehicle strategies
- Leverages OEM alignment scores from scoring engine
- Produces structured plans with executive summaries, strategies, and timelines
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

from mcp.core.cv_recommender import cv_recommender
from mcp.core.scoring import scorer


class AccountPlanGenerator:
    """
    Generates comprehensive AI-powered account plans for federal customers.

    Integrates:
    - Forecast data and scoring
    - Contract vehicle recommendations
    - OEM strategic positioning
    - Partner ecosystem strategies
    """

    # Supported customers
    SUPPORTED_CUSTOMERS = ["AFCENT", "AETC"]

    # Customer profiles with strategic context
    CUSTOMER_PROFILES = {
        "AFCENT": {
            "full_name": "Air Forces Central Command",
            "region": "CENTCOM AOR",
            "focus_areas": ["Cybersecurity", "Cloud Migration", "Network Modernization", "AI/ML"],
            "priority_oems": ["Cisco", "Palo Alto Networks", "Microsoft", "Dell"],
            "strategic_vehicles": ["SEWP V", "GSA Schedule", "DHS FirstSource II"],
            "budget_profile": "high",
        },
        "AETC": {
            "full_name": "Air Education and Training Command",
            "region": "CONUS Training Bases",
            "focus_areas": ["Training Infrastructure", "Collaboration Tools", "Data Center Modernization", "Storage"],
            "priority_oems": ["Microsoft", "Dell", "HPE", "NetApp"],
            "strategic_vehicles": ["SEWP V", "NASA SOLUTIONS", "GSA Schedule"],
            "budget_profile": "medium-high",
        },
    }

    def __init__(self):
        """Initialize the account plan generator."""
        self.forecast_file = Path("data/forecast.json")
        self.state_file = Path("data/state.json")

    def load_forecast_data(self) -> Dict[str, Any]:
        """Load forecast data from data/forecast.json."""
        if not self.forecast_file.exists():
            return {}
        try:
            with open(self.forecast_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def load_opportunities(self) -> List[Dict[str, Any]]:
        """Load opportunities from data/state.json."""
        if not self.state_file.exists():
            return []
        try:
            with open(self.state_file, "r") as f:
                state = json.load(f)
                return state.get("opportunities", [])
        except (json.JSONDecodeError, IOError):
            return []

    def filter_opportunities_by_customer(self, opportunities: List[Dict[str, Any]], customer: str) -> List[Dict[str, Any]]:
        """Filter opportunities relevant to the customer."""
        # Simple filtering by customer name or organization in opportunity data
        filtered = []
        customer_lower = customer.lower()

        for opp in opportunities:
            opp_customer = opp.get("customer", "").lower()
            opp_org = opp.get("customer_org", "").lower()
            opp_title = opp.get("title", opp.get("name", "")).lower()

            if customer_lower in opp_customer or customer_lower in opp_org or customer_lower in opp_title:
                filtered.append(opp)

        return filtered

    def generate_executive_summary(self, customer: str, opportunities: List[Dict[str, Any]], forecast_data: Dict[str, Any]) -> str:
        """Generate executive summary for the account plan."""
        profile = self.CUSTOMER_PROFILES.get(customer, {})

        # Calculate totals from opportunities
        total_opps = len(opportunities)
        total_value = sum(float(o.get("amount", o.get("est_amount", 0))) for o in opportunities)
        avg_win_prob = sum(float(o.get("win_prob", 0)) for o in opportunities) / max(total_opps, 1)

        # FY projections (if available in forecast)
        fy25_total = 0.0
        fy26_total = 0.0
        fy27_total = 0.0

        for opp in opportunities:
            opp_id = opp.get("id", "")
            if opp_id in forecast_data:
                forecast = forecast_data[opp_id]
                fy25_total += forecast.get("projected_amount_FY25", 0)
                fy26_total += forecast.get("projected_amount_FY26", 0)
                fy27_total += forecast.get("projected_amount_FY27", 0)

        region = profile.get("region", "the federal sector")
        full_name = profile.get("full_name", customer)
        summary = f"""
{full_name} represents a strategic opportunity for Red River Technology in {region}.

Our analysis identifies {total_opps} active opportunities with a combined value of \
${total_value:,.0f} and an average win probability of {avg_win_prob:.1f}%.

**Fiscal Year Projections:**
- FY25: ${fy25_total:,.0f}
- FY26: ${fy26_total:,.0f}
- FY27: ${fy27_total:,.0f}

**Strategic Focus Areas:** {', '.join(profile.get('focus_areas', ['Modernization', 'Security']))}

**Key Success Factors:**
1. Strong OEM alignment with {', '.join(profile.get('priority_oems', [])[:3])}
2. Proven contract vehicle experience on {', '.join(profile.get('strategic_vehicles', [])[:2])}
3. Established partner ecosystem for end-to-end delivery
4. Federal sector expertise and active clearances

This plan outlines our strategic approach to maximize capture and delivery success.
""".strip()

        return summary

    def generate_goals_kpis(self, customer: str, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate goals and KPIs."""
        total_value = sum(float(o.get("amount", o.get("est_amount", 0))) for o in opportunities)
        high_prob_opps = [o for o in opportunities if float(o.get("win_prob", 0)) >= 70]

        return [
            {
                "goal": f"Capture ${total_value * 0.6:,.0f} in contract awards",
                "kpi": "Win rate ≥ 60% on qualified opportunities",
                "target_date": (datetime.now() + timedelta(days=180)).strftime("%Y-%m-%d"),
            },
            {
                "goal": f"Close {len(high_prob_opps)} high-probability opportunities",
                "kpi": "Average win probability ≥ 75% on active pipeline",
                "target_date": (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d"),
            },
            {
                "goal": "Establish strategic OEM relationships",
                "kpi": "Execute 2+ OEM joint marketing campaigns",
                "target_date": (datetime.now() + timedelta(days=120)).strftime("%Y-%m-%d"),
            },
            {
                "goal": "Build partner ecosystem",
                "kpi": "Onboard 3+ qualified partners for teaming",
                "target_date": (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d"),
            },
        ]

    def generate_oem_strategy(self, customer: str, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate OEM positioning strategy."""
        profile = self.CUSTOMER_PROFILES.get(customer, {})
        priority_oems = profile.get("priority_oems", ["Microsoft", "Cisco", "Dell"])

        # Analyze OEM presence in opportunities
        oem_presence = {}
        for opp in opportunities:
            oems = opp.get("oems", [])
            if not isinstance(oems, list):
                oems = [oems] if oems else []
            for oem in oems:
                oem_presence[oem] = oem_presence.get(oem, 0) + 1

        strategies = []
        for oem in priority_oems[:4]:  # Top 4 OEMs
            oem_score = scorer.calculate_oem_alignment_score([oem])
            opp_count = oem_presence.get(oem, 0)

            strategies.append(
                {
                    "oem": oem,
                    "alignment_score": oem_score,
                    "opportunities_count": opp_count,
                    "positioning": self._get_oem_positioning(oem, customer),
                    "action_items": self._get_oem_action_items(oem, customer),
                }
            )

        return strategies

    def _get_oem_positioning(self, oem: str, customer: str) -> str:
        """Get OEM-specific positioning statement."""
        positions = {
            "Microsoft": (
                f"Position Microsoft cloud solutions (Azure Gov, M365) " f"for {customer}'s digital transformation and collaboration needs."
            ),
            "Cisco": f"Lead with Cisco's networking and security portfolio for {customer}'s infrastructure modernization.",
            "Dell": (
                f"Leverage Dell's end-to-end infrastructure solutions " f"for {customer}'s data center and edge computing requirements."
            ),
            "HPE": f"Position HPE's hybrid cloud and AI platforms for {customer}'s workload modernization initiatives.",
            "NetApp": (f"Focus on NetApp's data management and storage solutions " f"for {customer}'s data-intensive applications."),
            "Palo Alto Networks": (
                f"Emphasize Palo Alto Networks' advanced threat protection " f"for {customer}'s zero-trust security strategy."
            ),
        }
        return positions.get(oem, f"Position {oem} solutions aligned with {customer}'s strategic priorities.")

    def _get_oem_action_items(self, oem: str, customer: str) -> List[str]:
        """Get OEM-specific action items."""
        return [
            f"Schedule executive briefing with {oem} and {customer} leadership",
            f"Develop joint {oem} solution roadmap aligned with {customer} priorities",
            f"Execute co-marketing campaign highlighting {oem} federal success stories",
        ]

    def generate_contract_vehicle_strategy(self, customer: str, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate contract vehicle strategy with CV recommender integration."""
        profile = self.CUSTOMER_PROFILES.get(customer, {})
        strategic_vehicles = profile.get("strategic_vehicles", ["SEWP V", "GSA Schedule"])

        cv_strategies = []

        # Get recommendations for each strategic vehicle
        for vehicle in strategic_vehicles:
            # Calculate aggregate score across opportunities
            vehicle_score = scorer.calculate_contract_vehicle_score(vehicle)

            # Count opportunities that would benefit from this vehicle
            relevant_opps = 0
            for opp in opportunities:
                cv_recs = cv_recommender.recommend_vehicles(opp, top_n=3)
                if any(rec["contract_vehicle"] == vehicle for rec in cv_recs):
                    relevant_opps += 1

            cv_strategies.append(
                {
                    "vehicle": vehicle,
                    "priority_score": vehicle_score,
                    "applicable_opportunities": relevant_opps,
                    "rationale": self._get_cv_rationale(vehicle, customer),
                    "action_items": self._get_cv_action_items(vehicle),
                }
            )

        # Sort by priority score
        cv_strategies.sort(key=lambda x: x["priority_score"], reverse=True)

        return cv_strategies

    def _get_cv_rationale(self, vehicle: str, customer: str) -> str:
        """Get contract vehicle rationale."""
        rationales = {
            "SEWP V": (f"SEWP V provides best value for {customer}'s IT hardware and software " f"procurements with streamlined ordering."),
            "GSA Schedule": f"GSA Schedule offers flexibility and broad OEM coverage for {customer}'s diverse requirements.",
            "NASA SOLUTIONS": (
                f"NASA SOLUTIONS enables efficient procurement of IT infrastructure " f"and professional services for {customer}."
            ),
            "DHS FirstSource II": (f"DHS FirstSource II optimizes cybersecurity and networking " f"solution delivery for {customer}."),
        }
        return rationales.get(vehicle, f"{vehicle} provides strategic procurement advantages for {customer}.")

    def _get_cv_action_items(self, vehicle: str) -> List[str]:
        """Get contract vehicle action items."""
        return [
            f"Verify current {vehicle} contract status and ceiling availability",
            f"Align upcoming opportunities with {vehicle} procurement processes",
            f"Prepare {vehicle}-specific proposal templates and past performance",
        ]

    def generate_partner_stack(self, customer: str, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate partner ecosystem strategy."""
        # Analyze partner involvement in opportunities
        partner_presence = {}
        for opp in opportunities:
            partners = opp.get("partners", [])
            if not isinstance(partners, list):
                partners = [partners] if partners else []
            for partner in partners:
                if partner:
                    partner_presence[partner] = partner_presence.get(partner, 0) + 1

        # Build partner stack
        partner_stack = []
        for partner, count in sorted(partner_presence.items(), key=lambda x: x[1], reverse=True)[:5]:
            partner_stack.append(
                {
                    "partner": partner,
                    "opportunities_count": count,
                    "role": "Prime" if count >= 2 else "Subcontractor",
                    "capabilities": ["Solution Integration", "Professional Services", "Managed Services"],
                    "action_items": [
                        f"Establish teaming agreement with {partner}",
                        f"Define roles and responsibilities for {partner} engagement",
                        "Schedule quarterly business reviews",
                    ],
                }
            )

        # Add strategic partners if not present
        if len(partner_stack) < 3:
            partner_stack.append(
                {
                    "partner": "Strategic Partner TBD",
                    "opportunities_count": 0,
                    "role": "Subcontractor",
                    "capabilities": ["Specialized Services", "OEM Integration"],
                    "action_items": [
                        "Identify and qualify additional teaming partners",
                        "Conduct capability assessments",
                        "Execute partnership agreements",
                    ],
                }
            )

        return partner_stack

    def generate_outreach_plan(self, customer: str) -> List[Dict[str, Any]]:
        """Generate customer outreach and engagement plan."""
        today = datetime.now()

        return [
            {
                "step": 1,
                "activity": "Executive Relationship Mapping",
                "owner": "Account Executive",
                "due_date": (today + timedelta(days=14)).strftime("%Y-%m-%d"),
                "description": f"Map key stakeholders and decision-makers within {customer}",
            },
            {
                "step": 2,
                "activity": "Customer Needs Assessment",
                "owner": "Solutions Architect",
                "due_date": (today + timedelta(days=30)).strftime("%Y-%m-%d"),
                "description": "Conduct discovery sessions to understand requirements and pain points",
            },
            {
                "step": 3,
                "activity": "OEM Partner Engagement",
                "owner": "Partner Manager",
                "due_date": (today + timedelta(days=45)).strftime("%Y-%m-%d"),
                "description": "Coordinate OEM executive briefings and solution demonstrations",
            },
            {
                "step": 4,
                "activity": "Proposal Development",
                "owner": "Capture Manager",
                "due_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
                "description": "Develop and submit proposals for prioritized opportunities",
            },
            {
                "step": 5,
                "activity": "Contract Award & Transition",
                "owner": "Program Manager",
                "due_date": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
                "description": "Execute contract transition and onboarding activities",
            },
        ]

    def generate_risks_mitigations(self, customer: str, opportunities: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Generate risk assessment and mitigation strategies."""
        return [
            {
                "risk": "Competitive pressure from incumbents",
                "impact": "High",
                "likelihood": "Medium",
                "mitigation": (
                    "Differentiate with superior technical approach and past performance. "
                    "Leverage OEM partnerships for competitive advantage."
                ),
            },
            {
                "risk": "Budget constraints or continuing resolutions",
                "impact": "High",
                "likelihood": "Medium",
                "mitigation": (
                    "Provide flexible contract structures and phased implementation options. "
                    "Maintain pipeline diversity across fiscal years."
                ),
            },
            {
                "risk": "Technical evaluation criteria misalignment",
                "impact": "Medium",
                "likelihood": "Low",
                "mitigation": (
                    "Engage early in requirements development phase. " "Conduct regular capability briefings with customer technical teams."
                ),
            },
            {
                "risk": "Partner performance or availability",
                "impact": "Medium",
                "likelihood": "Low",
                "mitigation": (
                    "Establish multiple qualified teaming partners. " "Conduct regular partner capability assessments and business reviews."
                ),
            },
        ]

    def generate_checkpoints(self, customer: str) -> Dict[str, List[str]]:
        """Generate 30-60-90 day checkpoints."""
        return {
            "30_days": [
                f"Complete stakeholder mapping for {customer}",
                "Execute 2+ customer discovery sessions",
                "Establish OEM partner engagement cadence",
                "Identify top 3 near-term capture opportunities",
            ],
            "60_days": [
                "Submit 1+ proposals for qualified opportunities",
                "Conduct executive briefing with customer leadership",
                "Finalize teaming agreements with strategic partners",
                "Achieve 70%+ pipeline qualification rate",
            ],
            "90_days": [
                "Secure 1+ contract awards",
                "Expand relationship to additional stakeholder groups",
                "Execute joint OEM marketing campaign",
                "Achieve $1M+ in booked revenue",
            ],
        }

    def generate_account_plan(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive AI-powered account plan.

        Args:
            input_data: Dictionary containing:
                - customer: Customer name (AFCENT, AETC)
                - oem_partners: List of OEM partners (optional, for filtering)
                - fiscal_year: Fiscal year (optional)
                - focus_areas: Focus areas (optional)

        Returns:
            Structured account plan dictionary
        """
        customer = input_data.get("customer", "").upper()

        # Validate customer
        if customer not in self.SUPPORTED_CUSTOMERS:
            raise ValueError(
                f"Unsupported customer: {customer}. "
                f"Supported customers: {', '.join(self.SUPPORTED_CUSTOMERS)}. "
                f"Hint: This feature currently supports AFCENT and AETC."
            )

        # Load data
        forecast_data = self.load_forecast_data()
        all_opportunities = self.load_opportunities()

        # Filter opportunities for this customer
        opportunities = self.filter_opportunities_by_customer(all_opportunities, customer)

        # If no opportunities, create sample data for planning purposes
        if not opportunities:
            opportunities = [
                {
                    "id": "sample-1",
                    "title": f"Sample opportunity for {customer}",
                    "amount": 500000,
                    "win_prob": 65,
                    "oems": self.CUSTOMER_PROFILES[customer]["priority_oems"],
                    "partners": [],
                }
            ]

        # Generate plan components
        executive_summary = self.generate_executive_summary(customer, opportunities, forecast_data)
        goals_kpis = self.generate_goals_kpis(customer, opportunities)
        oem_strategy = self.generate_oem_strategy(customer, opportunities)
        cv_strategy = self.generate_contract_vehicle_strategy(customer, opportunities)
        partner_stack = self.generate_partner_stack(customer, opportunities)
        outreach_plan = self.generate_outreach_plan(customer)
        risks_mitigations = self.generate_risks_mitigations(customer, opportunities)
        checkpoints = self.generate_checkpoints(customer)

        # Collect sources used
        sources_used = [
            "Forecast Engine (FY projections and win probabilities)",
            "CV Recommender (contract vehicle recommendations)",
            "Scoring Engine (OEM alignment and opportunity prioritization)",
            "Opportunity Pipeline (active and qualified opportunities)",
        ]

        # Build reasoning
        reasoning = f"""
This account plan was generated using AI analysis of:
- {len(opportunities)} opportunities totaling ${sum(float(o.get('amount', o.get('est_amount', 0))) for o in opportunities):,.0f}
- {len(forecast_data)} forecast records with multi-factor scoring
- {len(oem_strategy)} strategic OEM partnerships
- {len(cv_strategy)} contract vehicle recommendations

The plan integrates Red River's established capabilities, OEM partnerships, and contract vehicle positions
to maximize capture probability and delivery success for {self.CUSTOMER_PROFILES[customer]['full_name']}.
""".strip()

        # Assemble final plan
        plan = {
            "customer": customer,
            "customer_full_name": self.CUSTOMER_PROFILES[customer]["full_name"],
            "executive_summary": executive_summary,
            "goals_kpis": goals_kpis,
            "oem_strategy": oem_strategy,
            "contract_vehicle_strategy": cv_strategy,
            "partner_stack": partner_stack,
            "outreach_plan": outreach_plan,
            "risks_mitigations": risks_mitigations,
            "checkpoints_30_60_90": checkpoints,
            "sources_used": sources_used,
            "reasoning": reasoning,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "opportunities_analyzed": len(opportunities),
        }

        return plan


# Global generator instance
account_plan_generator = AccountPlanGenerator()
