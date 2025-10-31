"""Unified vault export handling (Sprint 20).

Centralized export logic for all entity types with improved formatting
and atomic file writes.
"""

import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from config.obsidian_paths import get_vault_path

logger = logging.getLogger(__name__)


class VaultExporter:
    """Unified vault export handler."""

    def __init__(self, vault_root: str):
        """Initialize exporter with vault root path.

        Args:
            vault_root: Path to Obsidian vault root
        """
        self.vault_root = Path(vault_root)

    def export_partner(self, partner_data: Dict[str, Any], score_data: Optional[Dict[str, Any]] = None) -> Path:
        """Export partner to Obsidian markdown.

        Args:
            partner_data: Partner record dictionary
            score_data: Optional partner score data

        Returns:
            Path to created file
        """
        # Determine path
        partners_dir = get_vault_path("partners", str(self.vault_root))
        oem = partner_data.get("oem", "Unknown")
        filename = f"{oem} Partners.md"
        filepath = partners_dir / filename

        # Build frontmatter
        frontmatter = {
            "type": "partner",
            "oem": oem,
            "updated": datetime.now(timezone.utc).isoformat(),
        }

        if score_data:
            frontmatter["strength_score"] = score_data.get("strength_score", 0)
            frontmatter["tier"] = score_data.get("tier", "")

        # Build content
        content = self._build_frontmatter(frontmatter)
        content += f"\n# {oem} Partners\n\n"

        # Partner details table
        content += "## Partner Details\n\n"
        content += "| Partner | Tier | Program | POC | Strength Score |\n"
        content += "|---------|------|---------|-----|----------------|\n"

        if score_data:
            name = partner_data.get("name", "")
            tier = partner_data.get("tier", "")
            program = partner_data.get("program", "")
            poc = partner_data.get("poc", "-")
            score = score_data.get("strength_score", 0)
            content += f"| {name} | {tier} | {program} | {poc} | {score:.1f} |\n"
        else:
            name = partner_data.get("name", "")
            tier = partner_data.get("tier", "")
            program = partner_data.get("program", "")
            poc = partner_data.get("poc", "-")
            content += f"| {name} | {tier} | {program} | {poc} | - |\n"

        content += "\n"

        # Capabilities section
        if score_data and score_data.get("capabilities"):
            content += "## Capabilities\n\n"
            for cap in score_data["capabilities"]:
                content += f"- {cap}\n"
            content += "\n"

        # Notes section
        notes = partner_data.get("notes")
        if notes:
            content += "## Notes\n\n"
            content += f"{notes}\n\n"

        # Write file atomically
        self._write_file_atomic(filepath, content)

        return filepath

    def export_opportunity(self, opportunity: Dict[str, Any]) -> Path:
        """Export opportunity to Obsidian markdown.

        Args:
            opportunity: Opportunity dictionary

        Returns:
            Path to created file
        """
        # Determine path based on FY
        opps_dir = get_vault_path("opportunities", str(self.vault_root))
        name = opportunity.get("name", "Unknown")
        filename = f"{name}.md"

        # Determine FY subfolder
        close_date = opportunity.get("close_date")
        if close_date:
            try:
                # Simple FY logic (Oct-Sep fiscal year)
                year = int(close_date[:4])
                month = int(close_date[5:7])
                fy = year + 1 if month >= 10 else year
                fy_short = str(fy)[-2:]
                filepath = opps_dir / f"FY{fy_short}" / filename
            except Exception:
                filepath = opps_dir / "Triage" / filename
        else:
            filepath = opps_dir / "Triage" / filename

        # Build frontmatter
        frontmatter = {
            "type": "opportunity",
            "amount": opportunity.get("amount", 0),
            "close_date": close_date,
            "stage": opportunity.get("stage", ""),
            "oem": opportunity.get("oem", ""),
            "updated": datetime.now(timezone.utc).isoformat(),
        }

        # Add forecast fields if present
        if "win_prob" in opportunity:
            frontmatter["win_prob"] = opportunity["win_prob"]
        if "score_raw" in opportunity:
            frontmatter["score_raw"] = opportunity["score_raw"]

        # Build content
        content = self._build_frontmatter(frontmatter)
        content += f"\n# {name}\n\n"

        # Details section
        content += "## Details\n\n"
        content += f"- **Amount**: ${opportunity.get('amount', 0):,.2f}\n"
        content += f"- **Stage**: {opportunity.get('stage', 'Unknown')}\n"
        content += f"- **Close Date**: {close_date or 'TBD'}\n"
        content += f"- **OEM**: {opportunity.get('oem', 'Unknown')}\n"

        if "customer" in opportunity:
            content += f"- **Customer**: {opportunity['customer']}\n"

        content += "\n"

        # Partner attribution
        partners = opportunity.get("partner_attribution", [])
        if partners:
            content += "## Partner Attribution\n\n"
            for partner in partners:
                content += f"- [[{partner}]]\n"
            content += "\n"

        # Write file atomically
        self._write_file_atomic(filepath, content)

        return filepath

    def export_forecast_dashboard(self, forecast_data: Dict[str, Any]) -> Path:
        """Export forecast dashboard to Obsidian.

        Args:
            forecast_data: Forecast summary data

        Returns:
            Path to created file
        """
        dashboards_dir = get_vault_path("dashboards", str(self.vault_root))
        filepath = dashboards_dir / "Forecast Dashboard.md"

        # Build frontmatter
        frontmatter = {
            "type": "dashboard",
            "category": "forecast",
            "updated": datetime.now(timezone.utc).isoformat(),
        }

        # Build content
        content = self._build_frontmatter(frontmatter)
        content += "\n# Forecast Dashboard\n\n"

        # Summary section
        summary = forecast_data.get("summary", {})
        content += "## Summary\n\n"
        content += f"- **Total Opportunities**: {summary.get('total_opportunities', 0)}\n"
        content += f"- **Total Pipeline**: ${summary.get('total_projected_amount', 0):,.2f}\n"
        content += f"- **Avg Win Probability**: {summary.get('avg_win_probability', 0):.1f}%\n"
        content += "\n"

        # FY projections
        content += "## FY Projections\n\n"
        content += "| Fiscal Year | Projected Amount | Opportunity Count |\n"
        content += "|-------------|------------------|-------------------|\n"

        fy_breakdown = forecast_data.get("fiscal_year_breakdown", {})
        for fy, data in sorted(fy_breakdown.items()):
            amount = data.get("total_amount", 0)
            count = data.get("count", 0)
            content += f"| {fy} | ${amount:,.2f} | {count} |\n"

        content += "\n"

        # Top opportunities
        opportunities = forecast_data.get("opportunities", [])
        if opportunities:
            content += "## Top Opportunities\n\n"
            content += "| Opportunity | Amount | Win Prob | Score |\n"
            content += "|-------------|--------|----------|-------|\n"

            top_opps = sorted(opportunities, key=lambda x: x.get("win_prob", 0), reverse=True)[:20]
            for opp in top_opps:
                name = opp.get("name", "Unknown")
                amount = opp.get("amount", 0)
                win_prob = opp.get("win_prob", 0)
                score = opp.get("score_raw", 0)
                content += f"| [[{name}]] | ${amount:,.0f} | {win_prob:.1f}% | {score:.1f} |\n"

            content += "\n"

        # Write file atomically
        self._write_file_atomic(filepath, content)

        return filepath

    def _build_frontmatter(self, data: Dict[str, Any]) -> str:
        """Build YAML frontmatter block.

        Args:
            data: Dictionary of frontmatter fields

        Returns:
            Formatted frontmatter string
        """
        yaml_lines = ["---"]
        for key, value in data.items():
            if isinstance(value, str):
                yaml_lines.append(f'{key}: "{value}"')
            elif isinstance(value, list):
                yaml_lines.append(f"{key}:")
                for item in value:
                    yaml_lines.append(f"  - {item}")
            else:
                yaml_lines.append(f"{key}: {value}")
        yaml_lines.append("---")
        return "\n".join(yaml_lines)

    def _write_file_atomic(self, filepath: Path, content: str) -> None:
        """Write file atomically with backup.

        Args:
            filepath: Target file path
            content: File content
        """
        # Ensure directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Backup existing file
        if filepath.exists():
            backup_path = filepath.with_suffix(f".bak.{int(datetime.now().timestamp())}")
            shutil.copy2(filepath, backup_path)

        # Write to temp file first
        temp_path = filepath.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(content)

        # Atomic rename
        temp_path.replace(filepath)

        logger.info(f"Exported to {filepath}")


def preview_sync_operations(vault_root: str, entity_type: str) -> Dict[str, Any]:
    """Preview what files would be created/updated during sync.

    Args:
        vault_root: Path to Obsidian vault root
        entity_type: Type of entities to preview (partners, opportunities, forecasts)

    Returns:
        Preview summary
    """
    entity_dir = get_vault_path(entity_type, vault_root)

    # List existing files
    existing_files = []
    if entity_dir.exists():
        existing_files = [f.name for f in entity_dir.rglob("*.md")]

    # Placeholder for what would be created (actual logic would load from store)
    return {
        "dry_run": True,
        "entity_type": entity_type,
        "existing_files": existing_files,
        "files_to_create": [],
        "files_to_update": [],
        "files_unchanged": existing_files,  # Placeholder
        "total_operations": 0,
    }
