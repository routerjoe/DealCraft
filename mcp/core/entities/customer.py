"""Customer Entity - Customer/Agency management."""

from typing import List, Optional

from pydantic import Field

from mcp.core.entity_store import BaseEntity, EntityStore


class Customer(BaseEntity):
    """Customer entity model."""

    category: str = Field(..., description="Customer category (e.g., DOD, Civilian, SLED, Commercial)")
    region: str = Field(..., description="Geographic region (e.g., East, West, Central)")
    tier: str = Field(default="Standard", description="Customer tier/importance")
    preferred_partners: List[str] = Field(default_factory=list, description="Preferred partner IDs")
    preferred_vehicles: List[str] = Field(default_factory=list, description="Preferred contract vehicle IDs")
    contact_name: Optional[str] = Field(None, description="Primary contact name")
    contact_email: Optional[str] = Field(None, description="Primary contact email")
    contact_phone: Optional[str] = Field(None, description="Primary contact phone")
    annual_spend: Optional[float] = Field(None, description="Estimated annual spend")
    contract_count: Optional[int] = Field(None, description="Number of active contracts")
    notes: Optional[str] = Field(None, description="Additional notes")


class CustomerStore(EntityStore[Customer]):
    """Store for Customer entities."""

    def __init__(self, storage_path: str = "data/entities/customers.json"):
        """Initialize Customer store."""
        super().__init__(storage_path, "Customer")

    def _create_entity(self, data: dict) -> Customer:
        """Create Customer entity from dictionary."""
        return Customer(**data)

    def get_by_category(self, category: str) -> List[Customer]:
        """
        Get all customers by category.

        Args:
            category: Customer category

        Returns:
            List of customers in the category
        """
        return self.search(category=category, active=True)

    def get_by_region(self, region: str) -> List[Customer]:
        """
        Get all customers by region.

        Args:
            region: Geographic region

        Returns:
            List of customers in the region
        """
        return self.search(region=region, active=True)


# Global Customer store instance
customer_store = CustomerStore()
