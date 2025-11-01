"""Distributor Entity - Distribution Partner management."""

from typing import List, Optional

from pydantic import Field

from mcp.core.entity_store import BaseEntity, EntityStore


class Distributor(BaseEntity):
    """Distributor entity model."""

    tier: str = Field(..., description="Distributor tier (e.g., Premier, Standard)")
    oem_authorizations: List[str] = Field(default_factory=list, description="Authorized OEM IDs")
    regions_served: List[str] = Field(default_factory=list, description="Geographic regions covered")
    product_categories: List[str] = Field(default_factory=list, description="Product categories (e.g., Hardware, Software, Cloud)")
    contact_name: Optional[str] = Field(None, description="Primary contact name")
    contact_email: Optional[str] = Field(None, description="Primary contact email")
    contact_phone: Optional[str] = Field(None, description="Primary contact phone")
    payment_terms: Optional[str] = Field(None, description="Payment terms")
    delivery_options: List[str] = Field(default_factory=list, description="Available delivery methods")
    notes: Optional[str] = Field(None, description="Additional notes")


class DistributorStore(EntityStore[Distributor]):
    """Store for Distributor entities."""

    def __init__(self, storage_path: str = "data/entities/distributors.json"):
        """Initialize Distributor store."""
        super().__init__(storage_path, "Distributor")

    def _create_entity(self, data: dict) -> Distributor:
        """Create Distributor entity from dictionary."""
        return Distributor(**data)

    def get_by_oem(self, oem_id: str) -> List[Distributor]:
        """
        Get all distributors authorized for an OEM.

        Args:
            oem_id: OEM ID to filter by

        Returns:
            List of distributors authorized for the OEM
        """
        return [d for d in self.get_all(active_only=True) if oem_id in d.oem_authorizations]

    def get_by_region(self, region: str) -> List[Distributor]:
        """
        Get all distributors serving a region.

        Args:
            region: Geographic region

        Returns:
            List of distributors serving the region
        """
        return [d for d in self.get_all(active_only=True) if region in d.regions_served]


# Global Distributor store instance
distributor_store = DistributorStore()
