"""
Base Entity Store - Generic CRUD operations for entity management.

This module provides the foundation for the Entity Management System (EMS),
enabling centralized management of OEMs, Partners, Customers, Distributors,
Regions, and Contract Vehicles.
"""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)

# Generic type for entity models
T = TypeVar("T", bound=BaseModel)


class BaseEntity(BaseModel):
    """Base model for all entities with common fields."""

    model_config = ConfigDict(
        # Use mode='json' for serialization to handle datetime properly
        json_encoders={datetime: lambda v: v.isoformat()}
    )

    id: str
    name: str
    active: bool = True
    created_at: datetime = None
    updated_at: datetime = None
    metadata: Dict = {}

    def __init__(self, **data):
        """Initialize entity with timestamps."""
        if data.get("created_at") is None:
            data["created_at"] = datetime.now(timezone.utc)
        if data.get("updated_at") is None:
            data["updated_at"] = datetime.now(timezone.utc)
        super().__init__(**data)


class EntityStore(Generic[T], ABC):
    """
    Generic entity store with JSON persistence and CRUD operations.

    Type-safe, atomic writes, auto-backup, validation.
    """

    def __init__(self, storage_path: str, entity_type: str):
        """
        Initialize entity store.

        Args:
            storage_path: Path to JSON file for persistence
            entity_type: Type of entity (for logging)
        """
        self.storage_path = Path(storage_path)
        self.entity_type = entity_type
        self.entities: Dict[str, T] = {}
        self.load()

    @abstractmethod
    def _create_entity(self, data: dict) -> T:
        """
        Create entity instance from dictionary.

        Args:
            data: Dictionary with entity data

        Returns:
            Entity instance
        """
        pass

    def load(self) -> None:
        """
        Load entities from JSON file.
        Auto-creates file if missing.
        """
        if not self.storage_path.exists():
            logger.info(f"Creating new {self.entity_type} store at {self.storage_path}")
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            self._write_to_disk({"entities": []})
            self.entities = {}
            return

        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)
                entities_list = data.get("entities", [])
                self.entities = {item["id"]: self._create_entity(item) for item in entities_list}
            logger.info(f"Loaded {len(self.entities)} {self.entity_type} entities")
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to load {self.entity_type} data: {e}")
            raise ValueError(f"Failed to load {self.entity_type} data from {self.storage_path}: {e}")

    def save(self) -> None:
        """Save all entities to JSON file."""
        entities_list = [e.model_dump(mode="json") for e in self.entities.values()]
        self._write_to_disk({"entities": entities_list})
        logger.debug(f"Saved {len(self.entities)} {self.entity_type} entities")

    def _write_to_disk(self, data: dict) -> None:
        """
        Write data to disk atomically with backup.

        Args:
            data: Dictionary to write
        """
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Backup existing file
        if self.storage_path.exists():
            backup_path = self.storage_path.with_suffix(f".backup{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}")
            self.storage_path.rename(backup_path)

        # Write to temp file first for atomic operation
        temp_path = self.storage_path.with_suffix(".tmp")
        with open(temp_path, "w") as f:
            json.dump(data, f, indent=2, default=str)
            f.write("\n")

        # Atomic rename
        temp_path.replace(self.storage_path)

    def get(self, entity_id: str) -> Optional[T]:
        """
        Get entity by ID.

        Args:
            entity_id: ID of the entity

        Returns:
            Entity if found, None otherwise
        """
        return self.entities.get(entity_id)

    def get_by_name(self, name: str) -> Optional[T]:
        """
        Get entity by name (case-insensitive).

        Args:
            name: Name of the entity

        Returns:
            Entity if found, None otherwise
        """
        for entity in self.entities.values():
            if entity.name.lower() == name.lower():
                return entity
        return None

    def get_all(self, active_only: bool = False) -> List[T]:
        """
        Get all entities.

        Args:
            active_only: If True, only return active entities

        Returns:
            List of all entities
        """
        entities = list(self.entities.values())
        if active_only:
            entities = [e for e in entities if e.active]
        return entities

    def add(self, entity: T) -> T:
        """
        Add new entity.

        Args:
            entity: Entity to add

        Returns:
            The added entity

        Raises:
            ValueError: If entity with same ID already exists
        """
        if entity.id in self.entities:
            raise ValueError(f"{self.entity_type} with ID '{entity.id}' already exists")

        entity.created_at = datetime.now(timezone.utc)
        entity.updated_at = datetime.now(timezone.utc)

        self.entities[entity.id] = entity
        self.save()
        logger.info(f"Added {self.entity_type}: {entity.name} ({entity.id})")
        return entity

    def update(self, entity_id: str, entity: T) -> T:
        """
        Update existing entity.

        Args:
            entity_id: ID of entity to update
            entity: Updated entity data

        Returns:
            The updated entity

        Raises:
            ValueError: If entity not found
        """
        if entity_id not in self.entities:
            raise ValueError(f"{self.entity_type} with ID '{entity_id}' not found")

        # Preserve creation timestamp
        entity.created_at = self.entities[entity_id].created_at
        entity.updated_at = datetime.now(timezone.utc)

        self.entities[entity_id] = entity
        self.save()
        logger.info(f"Updated {self.entity_type}: {entity.name} ({entity_id})")
        return entity

    def delete(self, entity_id: str) -> bool:
        """
        Delete entity (soft delete by marking inactive).

        Args:
            entity_id: ID of entity to delete

        Returns:
            True if deleted, False if not found
        """
        if entity_id not in self.entities:
            return False

        self.entities[entity_id].active = False
        self.entities[entity_id].updated_at = datetime.now(timezone.utc)
        self.save()
        logger.info(f"Deactivated {self.entity_type}: {entity_id}")
        return True

    def hard_delete(self, entity_id: str) -> bool:
        """
        Permanently delete entity.

        Args:
            entity_id: ID of entity to delete

        Returns:
            True if deleted, False if not found
        """
        if entity_id not in self.entities:
            return False

        entity_name = self.entities[entity_id].name
        del self.entities[entity_id]
        self.save()
        logger.warning(f"Permanently deleted {self.entity_type}: {entity_name} ({entity_id})")
        return True

    def search(self, **filters) -> List[T]:
        """
        Search entities by filters.

        Args:
            **filters: Field=value pairs to filter by

        Returns:
            List of matching entities
        """
        results = []
        for entity in self.entities.values():
            match = True
            for key, value in filters.items():
                if not hasattr(entity, key) or getattr(entity, key) != value:
                    match = False
                    break
            if match:
                results.append(entity)
        return results

    def count(self, active_only: bool = False) -> int:
        """
        Count entities.

        Args:
            active_only: If True, only count active entities

        Returns:
            Number of entities
        """
        if active_only:
            return sum(1 for e in self.entities.values() if e.active)
        return len(self.entities)
