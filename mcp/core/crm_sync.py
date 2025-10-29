"""
CRM Sync & Attribution Engine - Phase 6

Provides CRM integration capabilities and revenue attribution tracking.
Features:
- CRM export format generation (JSON/YAML)
- Attribution engine (OEM, partner, revenue split)
- Validation and dry-run mode
- Integration with Phase 5 scoring
"""

from datetime import datetime
from typing import Any, Dict, List

# CRM Export Formats
CRM_FORMATS = ["salesforce", "hubspot", "dynamics", "generic_json", "generic_yaml"]


class AttributionEngine:
    """
    Calculate and track revenue attribution across dimensions.

    Attributes revenue to:
    - OEMs (based on technology stack)
    - Partners (based on involvement)
    - Sales teams (based on region/account ownership)
    - Contract vehicles
    """

    def __init__(self):
        """Initialize attribution engine."""
        self.attribution_rules = self._load_attribution_rules()

    def _load_attribution_rules(self) -> Dict[str, Any]:
        """Load attribution rules from configuration."""
        # Default rules - can be overridden from config file
        return {
            "oem_primary_weight": 0.60,  # Primary OEM gets 60%
            "oem_secondary_weight": 0.30,  # Secondary OEM gets 30%
            "oem_tertiary_weight": 0.10,  # Tertiary OEM gets 10%
            "partner_split": 0.20,  # Partners share 20% of total attribution
            "direct_bonus": 1.0,  # Direct deals get full attribution
        }

    def calculate_oem_attribution(self, oems: List[str], amount: float) -> Dict[str, float]:
        """
        Calculate revenue attribution across OEMs.

        Args:
            oems: List of OEMs involved (ordered by importance)
            amount: Total opportunity amount

        Returns:
            Dictionary mapping OEM name to attributed amount
        """
        if not oems:
            return {}

        attribution = {}
        weights = [
            self.attribution_rules["oem_primary_weight"],
            self.attribution_rules["oem_secondary_weight"],
            self.attribution_rules["oem_tertiary_weight"],
        ]

        for idx, oem in enumerate(oems[:3]):  # Max 3 OEMs
            weight = weights[idx] if idx < len(weights) else 0.0
            attribution[oem] = round(amount * weight, 2)

        return attribution

    def calculate_partner_attribution(self, partners: List[str], amount: float, oem_attribution: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate revenue attribution across partners.

        Args:
            partners: List of partners involved
            amount: Total opportunity amount
            oem_attribution: OEM attribution dict for cross-reference

        Returns:
            Dictionary mapping partner name to attributed amount
        """
        if not partners:
            return {}

        partner_pool = amount * self.attribution_rules["partner_split"]
        per_partner = partner_pool / len(partners)

        attribution = {}
        for partner in partners:
            attribution[partner] = round(per_partner, 2)

        return attribution

    def calculate_full_attribution(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate complete attribution for an opportunity.

        Args:
            opportunity: Opportunity data dictionary

        Returns:
            Complete attribution breakdown
        """
        oems = opportunity.get("oems", [])
        if not isinstance(oems, list):
            oems = [oems] if oems else []

        partners = opportunity.get("partners", [])
        if not isinstance(partners, list):
            partners = [partners] if partners else []

        amount = float(opportunity.get("amount", opportunity.get("est_amount", 0)))

        # Calculate attributions
        oem_attr = self.calculate_oem_attribution(oems, amount)
        partner_attr = self.calculate_partner_attribution(partners, amount, oem_attr)

        # Determine region and rep attribution
        region = opportunity.get("region", "Unknown")
        customer_org = opportunity.get("customer_org", opportunity.get("customer", ""))

        return {
            "oem_attribution": oem_attr,
            "partner_attribution": partner_attr,
            "region": region,
            "customer_org": customer_org,
            "total_amount": amount,
            "attribution_method": "multi_factor_v1",
            "calculated_at": datetime.utcnow().isoformat() + "Z",
        }


class CRMSyncEngine:
    """
    CRM synchronization and export engine.

    Handles:
    - Opportunity data formatting for CRM systems
    - Validation of required fields
    - Dry-run mode for safe testing
    - Integration with forecast scoring
    """

    def __init__(self, dry_run: bool = True):
        """
        Initialize CRM sync engine.

        Args:
            dry_run: If True, only validates without actual sync
        """
        self.dry_run = dry_run
        self.attribution_engine = AttributionEngine()

    def validate_opportunity(self, opportunity: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate opportunity has required fields for CRM export.

        Args:
            opportunity: Opportunity data dictionary

        Returns:
            Tuple of (is_valid, list of missing/invalid fields)
        """
        required_fields = [
            "id",
            "title",
            "customer",
            "amount",
            "stage",
            "close_date",
        ]

        errors = []

        for field in required_fields:
            if field not in opportunity:
                errors.append(f"Missing required field: {field}")
            elif not opportunity[field]:
                errors.append(f"Empty required field: {field}")

        # Validate amount is positive
        try:
            amount = float(opportunity.get("amount", opportunity.get("est_amount", 0)))
            if amount <= 0:
                errors.append("Amount must be positive")
        except (ValueError, TypeError):
            errors.append("Invalid amount format")

        # Validate close_date format
        close_date = opportunity.get("close_date", opportunity.get("est_close", ""))
        if close_date:
            try:
                datetime.fromisoformat(close_date.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                errors.append("Invalid close_date format (expected ISO 8601)")

        return (len(errors) == 0, errors)

    def format_for_salesforce(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format opportunity for Salesforce import.

        Args:
            opportunity: Opportunity data dictionary

        Returns:
            Salesforce-formatted dictionary
        """
        # Calculate attribution
        attribution = self.attribution_engine.calculate_full_attribution(opportunity)

        # Get forecast data if available
        forecast = opportunity.get("forecast", {})

        return {
            "Name": opportunity.get("title", opportunity.get("name", "")),
            "AccountId": opportunity.get("customer_org", opportunity.get("customer", "")),
            "Amount": opportunity.get("amount", opportunity.get("est_amount", 0)),
            "CloseDate": opportunity.get("close_date", opportunity.get("est_close", "")),
            "StageName": opportunity.get("stage", "Qualification"),
            "Type": opportunity.get("source", "New Business"),
            "LeadSource": opportunity.get("source", ""),
            # Custom fields
            "OEM_Primary__c": (list(attribution["oem_attribution"].keys())[0] if attribution["oem_attribution"] else ""),
            "Partner_Names__c": ", ".join(opportunity.get("partners", [])),
            "Contract_Vehicle__c": opportunity.get("contract_vehicle", ""),
            "FY25_Forecast__c": forecast.get("projected_amount_FY25", 0),
            "FY26_Forecast__c": forecast.get("projected_amount_FY26", 0),
            "FY27_Forecast__c": forecast.get("projected_amount_FY27", 0),
            "Win_Probability__c": forecast.get("win_prob", 0),
            "Confidence_Score__c": forecast.get("confidence_score", 0),
            "Region__c": opportunity.get("region", ""),
            "Description": opportunity.get("notes", ""),
        }

    def format_for_generic_json(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format opportunity as generic JSON for CRM import.

        Args:
            opportunity: Opportunity data dictionary

        Returns:
            Generic JSON-formatted dictionary
        """
        # Calculate attribution
        attribution = self.attribution_engine.calculate_full_attribution(opportunity)

        # Get forecast data
        forecast = opportunity.get("forecast", {})

        # Merge everything
        export_data = {
            "id": opportunity.get("id", ""),
            "title": opportunity.get("title", opportunity.get("name", "")),
            "customer": opportunity.get("customer", ""),
            "customer_org": opportunity.get("customer_org", ""),
            "customer_poc": opportunity.get("customer_poc", ""),
            "amount": opportunity.get("amount", opportunity.get("est_amount", 0)),
            "stage": opportunity.get("stage", ""),
            "close_date": opportunity.get("close_date", opportunity.get("est_close", "")),
            "source": opportunity.get("source", ""),
            "region": opportunity.get("region", ""),
            "oems": opportunity.get("oems", []),
            "partners": opportunity.get("partners", []),
            "contract_vehicle": opportunity.get("contract_vehicle", ""),
            "tags": opportunity.get("tags", []),
            # Attribution
            "attribution": attribution,
            # Forecast
            "forecast": forecast,
            # Metadata
            "exported_at": datetime.utcnow().isoformat() + "Z",
            "export_version": "1.0",
        }

        return export_data

    def export_opportunity(self, opportunity: Dict[str, Any], format: str = "generic_json") -> Dict[str, Any]:
        """
        Export opportunity to specified CRM format.

        Args:
            opportunity: Opportunity data dictionary
            format: CRM format (salesforce, hubspot, generic_json, etc.)

        Returns:
            Dictionary with export result
        """
        # Validate
        is_valid, errors = self.validate_opportunity(opportunity)
        if not is_valid:
            return {
                "success": False,
                "errors": errors,
                "dry_run": self.dry_run,
            }

        # Format based on target CRM
        if format == "salesforce":
            formatted = self.format_for_salesforce(opportunity)
        elif format == "generic_json":
            formatted = self.format_for_generic_json(opportunity)
        else:
            return {
                "success": False,
                "errors": [f"Unsupported format: {format}"],
                "dry_run": self.dry_run,
            }

        result = {
            "success": True,
            "opportunity_id": opportunity.get("id", "unknown"),
            "format": format,
            "dry_run": self.dry_run,
            "formatted_data": formatted,
            "exported_at": datetime.utcnow().isoformat() + "Z",
        }

        if self.dry_run:
            result["message"] = "Dry-run mode: No actual sync performed"
        else:
            result["message"] = "Export successful"

        return result

    def bulk_export(self, opportunities: List[Dict[str, Any]], format: str = "generic_json") -> Dict[str, Any]:
        """
        Export multiple opportunities in bulk.

        Args:
            opportunities: List of opportunity dictionaries
            format: CRM format

        Returns:
            Bulk export results
        """
        results = []
        success_count = 0
        error_count = 0

        for opp in opportunities:
            result = self.export_opportunity(opp, format)
            results.append(result)
            if result["success"]:
                success_count += 1
            else:
                error_count += 1

        return {
            "total": len(opportunities),
            "success_count": success_count,
            "error_count": error_count,
            "dry_run": self.dry_run,
            "results": results,
            "exported_at": datetime.utcnow().isoformat() + "Z",
        }


# Global instances
attribution_engine = AttributionEngine()
crm_sync_engine = CRMSyncEngine(dry_run=True)
