"""OEM Partner Intelligence - Data models and persistence."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field


class OEMPartner(BaseModel):
    """OEM Partner data model for partner intelligence tracking."""

    oem_name: str = Field(..., description="OEM partner name")
    tier: str = Field(..., description="Partner tier level")
    partner_poc: Optional[str] = Field(None, description="Partner point of contact")
    notes: Optional[str] = Field(None, description="Additional notes about the partner")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last update timestamp")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class OEMStore:
    """
    In-memory store with JSON persistence for OEM partners.

    Storage location: data/oems.json
    No secrets stored.
    """

    def __init__(self, storage_path: str = "data/oems.json"):
        """
        Initialize OEM store.

        Args:
            storage_path: Path to JSON file for persistence
        """
        self.storage_path = Path(storage_path)
        self.partners: List[OEMPartner] = []
        self.load()

    def load(self) -> None:
        """
        Load OEM partners from JSON file.
        Auto-creates file if missing.
        """
        if not self.storage_path.exists():
            # Auto-create with empty list
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            self._write_to_disk([])
            self.partners = []
            return

        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)
                self.partners = [OEMPartner(**item) for item in data]
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Failed to load OEM data from {self.storage_path}: {e}")

    def save(self) -> None:
        """Save OEM partners to JSON file."""
        data = [p.model_dump(mode="json") for p in self.partners]
        self._write_to_disk(data)

    def _write_to_disk(self, data: list) -> None:
        """
        Write data to disk atomically.

        Args:
            data: List of partner dictionaries to write
        """
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to temp file first for atomic operation
        temp_path = self.storage_path.with_suffix(".tmp")
        with open(temp_path, "w") as f:
            json.dump(data, f, indent=2, default=str)
            f.write("\n")

        # Atomic rename
        temp_path.replace(self.storage_path)

    def get(self, oem_name: str) -> Optional[OEMPartner]:
        """
        Get OEM partner by name.

        Args:
            oem_name: Name of the OEM partner

        Returns:
            OEMPartner if found, None otherwise
        """
        for partner in self.partners:
            if partner.oem_name == oem_name:
                return partner
        return None

    def add_or_update(self, partner: OEMPartner) -> OEMPartner:
        """
        Add new OEM partner or update existing one.

        Args:
            partner: OEMPartner to add or update

        Returns:
            The added or updated OEMPartner
        """
        # Update timestamp
        partner.updated_at = datetime.now(timezone.utc)

        # Check if partner exists
        for i, existing in enumerate(self.partners):
            if existing.oem_name == partner.oem_name:
                # Update existing
                self.partners[i] = partner
                self.save()
                return partner

        # Add new
        self.partners.append(partner)
        self.save()
        return partner

    def get_all(self) -> List[OEMPartner]:
        """
        Get all OEM partners.

        Returns:
            List of all OEMPartner objects
        """
        return self.partners.copy()

    def export_markdown(self) -> str:
        """
        Export all OEM partners as Obsidian-compatible markdown.

        Returns:
            Markdown-formatted string with all OEM partners
        """
        if not self.partners:
            return "# OEM Partners\n\nNo OEM partners recorded.\n"

        lines = ["# OEM Partners\n"]

        for partner in sorted(self.partners, key=lambda p: p.oem_name):
            lines.append(f"## OEM: {partner.oem_name}")
            lines.append(f"Tier: {partner.tier}")
            lines.append(f"POC: {partner.partner_poc or 'N/A'}")
            lines.append(f"Updated: {partner.updated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            lines.append("Notes:")
            lines.append(partner.notes or "N/A")
            lines.append("")  # Blank line between entries

        return "\n".join(lines)
