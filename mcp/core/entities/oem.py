"""OEM Entity - Original Equipment Manufacturer management."""

from typing import List, Optional

from pydantic import Field

from mcp.core.entity_store import BaseEntity, EntityStore


class OEM(BaseEntity):
    """OEM entity model."""

    tier: str = Field(..., description="Partnership tier (e.g., Strategic, Gold, Silver)")
    contact_name: Optional[str] = Field(None, description="Primary contact name")
    contact_email: Optional[str] = Field(None, description="Primary contact email")
    contact_phone: Optional[str] = Field(None, description="Primary contact phone")
    programs: List[str] = Field(default_factory=list, description="Partner programs (e.g., Azure, M365)")
    certifications: List[str] = Field(default_factory=list, description="Certifications held")
    notes: Optional[str] = Field(None, description="Additional notes")


class OEMStore(EntityStore[OEM]):
    """Store for OEM entities."""

    def __init__(self, storage_path: str = "data/entities/oems.json"):
        """Initialize OEM store."""
        super().__init__(storage_path, "OEM")

    def _create_entity(self, data: dict) -> OEM:
        """Create OEM entity from dictionary."""
        return OEM(**data)


# Global OEM store instance
oem_store = OEMStore()
