"""
Partner Tier Sync Module

Loads partner tier data from CSV/JSON files, normalizes schema,
diffs against existing OEMStore, and updates records.
"""

import csv
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class PartnerSyncError(Exception):
    """Base exception for partner sync operations"""

    pass


class PartnerTierRecord:
    """Normalized partner tier record"""

    def __init__(
        self,
        name: str,
        tier: str,
        program: str,
        oem: str,
        poc: Optional[str] = None,
        notes: Optional[str] = None,
        updated_at: Optional[str] = None,
        created_at: Optional[str] = None,
    ):
        self.name = name.strip()
        self.tier = self._normalize_tier(tier)
        self.program = program.strip()
        self.oem = self._normalize_oem(oem)
        self.poc = poc.strip() if poc else None
        self.notes = notes.strip() if notes else None
        self.updated_at = updated_at or datetime.now(timezone.utc).isoformat()
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def _normalize_tier(self, tier: str) -> str:
        """Normalize tier to standard capitalization"""
        tier_clean = tier.strip().lower()
        tier_map = {
            "platinum": "Platinum",
            "gold": "Gold",
            "silver": "Silver",
            "bronze": "Bronze",
            "partner": "Partner",
            "authorized": "Authorized",
        }
        return tier_map.get(tier_clean, tier.strip().title())

    def _normalize_oem(self, oem: str) -> str:
        """Normalize OEM name"""
        oem_clean = oem.strip().lower()
        oem_map = {
            "cisco": "Cisco",
            "nutanix": "Nutanix",
            "dell": "Dell",
            "hp": "HP",
            "hpe": "HPE",
            "lenovo": "Lenovo",
            "vmware": "VMware",
            "microsoft": "Microsoft",
            "aws": "AWS",
            "azure": "Azure",
            "google": "Google",
            "oracle": "Oracle",
            "ibm": "IBM",
            "redhat": "Red Hat",
            "red hat": "Red Hat",
        }
        return oem_map.get(oem_clean, oem.strip())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "tier": self.tier,
            "program": self.program,
            "oem": self.oem,
            "poc": self.poc,
            "notes": self.notes,
            "updated_at": self.updated_at,
            "created_at": self.created_at,
        }


class PartnerTierSync:
    """
    Partner tier data ingestion and sync.

    Responsibilities:
      - Load CSV/JSON partner tier data
      - Normalize schema
      - Compute diffs vs OEMStore
      - Update OEMStore
      - Export to Obsidian markdown
    """

    def __init__(self, vault_root: Optional[Path] = None, store_path: str = "data/oems.json"):
        """
        Initialize partner tier sync.

        Args:
            vault_root: Path to Obsidian vault (optional)
            store_path: Path to OEMStore JSON file
        """
        self.vault_root = Path(vault_root) if vault_root else None
        self.store_path = Path(store_path)
        self.partners_dir = Path("data/partners")

    def load_sources(self, paths: Optional[List[Path]] = None) -> List[PartnerTierRecord]:
        """
        Load partner tier data from CSV/JSON files.

        Args:
            paths: Optional list of specific paths to load.
                  If None, loads all partners_*.csv and partners_*.json from data/partners/

        Returns:
            List of normalized PartnerTierRecord objects
        """
        if paths is None:
            # Auto-discover files in data/partners/
            if not self.partners_dir.exists():
                logger.info(f"Partners directory {self.partners_dir} does not exist, returning empty list")
                return []

            paths = []
            paths.extend(self.partners_dir.glob("partners_*.csv"))
            paths.extend(self.partners_dir.glob("partners_*.json"))

        records = []

        for path in paths:
            try:
                if path.suffix.lower() == ".csv":
                    records.extend(self._load_csv(path))
                elif path.suffix.lower() == ".json":
                    records.extend(self._load_json(path))
                else:
                    logger.warning(f"Skipping unsupported file: {path}")
            except Exception as e:
                logger.error(f"Failed to load {path}: {e}")
                raise PartnerSyncError(f"Failed to load {path}: {e}")

        return records

    def _load_csv(self, path: Path) -> List[PartnerTierRecord]:
        """Load partner tier records from CSV file"""
        records = []

        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                try:
                    record = PartnerTierRecord(
                        name=row.get("name", ""),
                        tier=row.get("tier", ""),
                        program=row.get("program", ""),
                        oem=row.get("oem", ""),
                        poc=row.get("poc"),
                        notes=row.get("notes"),
                        updated_at=row.get("updated_at"),
                        created_at=row.get("created_at"),
                    )
                    records.append(record)
                except Exception as e:
                    logger.error(f"Failed to parse CSV row from {path}: {e}")

        return records

    def _load_json(self, path: Path) -> List[PartnerTierRecord]:
        """Load partner tier records from JSON file"""
        records = []

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

            # Support both array and object with 'partners' key
            if isinstance(data, dict) and "partners" in data:
                data = data["partners"]

            if not isinstance(data, list):
                raise PartnerSyncError(f"JSON file {path} must contain an array or object with 'partners' key")

            for item in data:
                try:
                    record = PartnerTierRecord(
                        name=item.get("name", ""),
                        tier=item.get("tier", ""),
                        program=item.get("program", ""),
                        oem=item.get("oem", ""),
                        poc=item.get("poc"),
                        notes=item.get("notes"),
                        updated_at=item.get("updated_at"),
                        created_at=item.get("created_at"),
                    )
                    records.append(record)
                except Exception as e:
                    logger.error(f"Failed to parse JSON item from {path}: {e}")

        return records

    def validate(self, records: List[PartnerTierRecord]) -> Tuple[bool, List[str]]:
        """
        Validate partner tier records.

        Args:
            records: List of PartnerTierRecord objects to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        for i, record in enumerate(records):
            if not record.name:
                errors.append(f"Record {i}: missing name")
            if not record.tier:
                errors.append(f"Record {i}: missing tier")
            if not record.program:
                errors.append(f"Record {i}: missing program")
            if not record.oem:
                errors.append(f"Record {i}: missing oem")

        return len(errors) == 0, errors

    def plan_updates(self, records: List[PartnerTierRecord]) -> Dict[str, Any]:
        """
        Compute diff vs existing OEMStore.

        Args:
            records: List of new PartnerTierRecord objects

        Returns:
            Dict with 'added', 'updated', 'unchanged' keys containing record diffs
        """
        # Load existing store
        existing = self._load_store()
        existing_map = {p["name"]: p for p in existing}

        added = []
        updated = []
        unchanged = []

        for record in records:
            record_dict = record.to_dict()

            if record.name not in existing_map:
                # New record
                added.append(record_dict)
            else:
                # Check if updated
                existing_record = existing_map[record.name]

                # Compare key fields (excluding timestamps)
                fields_to_compare = ["tier", "program", "oem", "poc", "notes"]
                has_changes = any(record_dict.get(field) != existing_record.get(field) for field in fields_to_compare)

                if has_changes:
                    # Preserve created_at from existing
                    record_dict["created_at"] = existing_record.get("created_at", record_dict["created_at"])
                    updated.append(record_dict)
                else:
                    unchanged.append(existing_record)

        return {
            "added": added,
            "updated": updated,
            "unchanged": unchanged,
        }

    def apply_updates(self, plan: Dict[str, Any], dry_run: bool = True) -> Dict[str, Any]:
        """
        Apply updates to OEMStore.

        Args:
            plan: Update plan from plan_updates()
            dry_run: If True, don't write changes

        Returns:
            Dict with execution results
        """
        if dry_run:
            return {
                "dry_run": True,
                "applied": False,
                "summary": plan,
            }

        # Merge all records
        all_records = []
        all_records.extend(plan["added"])
        all_records.extend(plan["updated"])
        all_records.extend(plan["unchanged"])

        # Write to store
        self._write_store(all_records)

        return {
            "dry_run": False,
            "applied": True,
            "summary": {
                "added_count": len(plan["added"]),
                "updated_count": len(plan["updated"]),
                "unchanged_count": len(plan["unchanged"]),
                "total": len(all_records),
            },
        }

    def export_obsidian(self) -> Dict[str, Any]:
        """
        Export partner tier data to Obsidian markdown files.

        Writes per-OEM markdown files to:
            <VAULT_ROOT>/30 Hubs/OEMs/<oem_name>.md

        Returns:
            Dict with export results
        """
        if not self.vault_root:
            raise PartnerSyncError("VAULT_ROOT not configured")

        # Load current store
        partners = self._load_store()

        # Group by OEM
        oem_groups: Dict[str, List[Dict]] = {}
        for partner in partners:
            oem = partner["oem"]
            if oem not in oem_groups:
                oem_groups[oem] = []
            oem_groups[oem].append(partner)

        # Create output directory
        oems_dir = self.vault_root / "30 Hubs" / "OEMs"
        oems_dir.mkdir(parents=True, exist_ok=True)

        files_written = []

        # Write per-OEM files
        for oem, oem_partners in oem_groups.items():
            filename = f"{oem}.md"
            filepath = oems_dir / filename

            # Generate markdown content
            content = self._generate_oem_markdown(oem, oem_partners)

            # Write file
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

            files_written.append(str(filepath))

        return {
            "status": "success",
            "files_written": files_written,
            "oems_count": len(oem_groups),
        }

    def _generate_oem_markdown(self, oem: str, partners: List[Dict]) -> str:
        """Generate markdown content for an OEM"""
        lines = [
            f"# {oem}",
            "",
            "## Partner Tiers",
            "",
        ]

        for partner in sorted(partners, key=lambda p: p["name"]):
            lines.append(f"### {partner['name']}")
            lines.append(f"- **Tier**: {partner['tier']}")
            lines.append(f"- **Program**: {partner['program']}")
            if partner.get("poc"):
                lines.append(f"- **POC**: {partner['poc']}")
            if partner.get("notes"):
                lines.append(f"- **Notes**: {partner['notes']}")
            lines.append(f"- **Updated**: {partner.get('updated_at', 'N/A')}")
            lines.append("")

        return "\n".join(lines)

    def _load_store(self) -> List[Dict]:
        """Load existing OEMStore data"""
        if not self.store_path.exists():
            return []

        try:
            with open(self.store_path, "r") as f:
                data = json.load(f)

                # Handle both old OEMPartner format and new partner tier format
                if isinstance(data, list):
                    # New format or empty
                    return data
                else:
                    # Unknown format
                    logger.warning(f"Unexpected store format in {self.store_path}")
                    return []
        except Exception as e:
            logger.error(f"Failed to load store from {self.store_path}: {e}")
            return []

    def _write_store(self, records: List[Dict]) -> None:
        """Write records to OEMStore atomically"""
        self.store_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to temp file first
        temp_path = self.store_path.with_suffix(".tmp")
        with open(temp_path, "w") as f:
            json.dump(records, f, indent=2, default=str)
            f.write("\n")

        # Atomic rename
        temp_path.replace(self.store_path)
