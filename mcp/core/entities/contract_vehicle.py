"""Contract Vehicle Entity - Government contract vehicle management."""

from typing import List, Optional

from pydantic import Field

from mcp.core.entity_store import BaseEntity, EntityStore


class ContractVehicle(BaseEntity):
    """Contract Vehicle entity model."""

    priority_score: float = Field(..., description="Base priority score for recommendations")
    oems_supported: List[str] = Field(default_factory=list, description="Supported OEM IDs")
    categories: List[str] = Field(default_factory=list, description="Product/service categories")
    active_bpas: int = Field(default=0, description="Number of active BPAs")
    ceiling_amount: Optional[float] = Field(None, description="Contract ceiling amount in dollars")
    contracting_office: Optional[str] = Field(None, description="Primary contracting office")
    scope: Optional[str] = Field(None, description="Scope of contract vehicle")
    url: Optional[str] = Field(None, description="URL to contract vehicle information")
    notes: Optional[str] = Field(None, description="Additional notes")


class ContractVehicleStore(EntityStore[ContractVehicle]):
    """Store for Contract Vehicle entities."""

    def __init__(self, storage_path: str = "data/entities/contract_vehicles.json"):
        """Initialize Contract Vehicle store."""
        super().__init__(storage_path, "ContractVehicle")

    def _create_entity(self, data: dict) -> ContractVehicle:
        """Create Contract Vehicle entity from dictionary."""
        return ContractVehicle(**data)

    def get_by_oem(self, oem_id: str) -> List[ContractVehicle]:
        """
        Get all contract vehicles supporting an OEM.

        Args:
            oem_id: OEM ID to filter by

        Returns:
            List of contract vehicles supporting the OEM
        """
        return [cv for cv in self.get_all(active_only=True) if oem_id in cv.oems_supported]

    def get_by_category(self, category: str) -> List[ContractVehicle]:
        """
        Get all contract vehicles by category.

        Args:
            category: Product/service category

        Returns:
            List of contract vehicles in the category
        """
        return [cv for cv in self.get_all(active_only=True) if category in cv.categories]

    def get_priority_score(self, cv_name: str) -> float:
        """
        Get priority score for a contract vehicle.

        Args:
            cv_name: Name of the contract vehicle

        Returns:
            Priority score (0.0 if not found)
        """
        cv = self.get_by_name(cv_name)
        return cv.priority_score if cv and cv.active else 0.0


# Global Contract Vehicle store instance
contract_vehicle_store = ContractVehicleStore()
