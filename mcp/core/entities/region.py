"""Region Entity - Geographic region management."""

from typing import Optional

from pydantic import Field

from mcp.core.entity_store import BaseEntity, EntityStore


class Region(BaseEntity):
    """Region entity model."""

    bonus: float = Field(default=0.0, description="Scoring bonus for this region")
    description: Optional[str] = Field(None, description="Region description")
    notes: Optional[str] = Field(None, description="Additional notes")


class RegionStore(EntityStore[Region]):
    """Store for Region entities."""

    def __init__(self, storage_path: str = "data/entities/regions.json"):
        """Initialize Region store."""
        super().__init__(storage_path, "Region")

    def _create_entity(self, data: dict) -> Region:
        """Create Region entity from dictionary."""
        return Region(**data)

    def get_bonus(self, region_name: str) -> float:
        """
        Get scoring bonus for a region.

        Args:
            region_name: Name of the region

        Returns:
            Bonus score for the region (0.0 if not found)
        """
        region = self.get_by_name(region_name)
        return region.bonus if region and region.active else 0.0


# Global Region store instance
region_store = RegionStore()
