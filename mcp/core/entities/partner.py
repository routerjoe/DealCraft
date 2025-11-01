"""Partner Entity - Channel Partner management."""

from typing import List, Optional

from pydantic import Field

from mcp.core.entity_store import BaseEntity, EntityStore


class Partner(BaseEntity):
    """Partner entity model."""

    tier: str = Field(..., description="Partner tier (e.g., Platinum, Gold, Silver)")
    oem_affiliations: List[str] = Field(default_factory=list, description="Associated OEM IDs")
    program: Optional[str] = Field(None, description="Partner program name")
    contact_name: Optional[str] = Field(None, description="Primary contact name")
    contact_email: Optional[str] = Field(None, description="Primary contact email")
    contact_phone: Optional[str] = Field(None, description="Primary contact phone")
    specializations: List[str] = Field(default_factory=list, description="Technical specializations")
    regions_served: List[str] = Field(default_factory=list, description="Geographic regions served")
    notes: Optional[str] = Field(None, description="Additional notes")


class PartnerStore(EntityStore[Partner]):
    """Store for Partner entities."""

    def __init__(self, storage_path: str = "data/entities/partners.json"):
        """Initialize Partner store."""
        super().__init__(storage_path, "Partner")

    def _create_entity(self, data: dict) -> Partner:
        """Create Partner entity from dictionary."""
        return Partner(**data)

    def get_by_oem(self, oem_id: str) -> List[Partner]:
        """
        Get all partners affiliated with an OEM.

        Args:
            oem_id: OEM ID to filter by

        Returns:
            List of partners affiliated with the OEM
        """
        return [p for p in self.get_all(active_only=True) if oem_id in p.oem_affiliations]


# Global Partner store instance
partner_store = PartnerStore()
