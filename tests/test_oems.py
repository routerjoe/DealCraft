"""Tests for OEM management endpoints."""

import json
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mcp.api.main import app

client = TestClient(app)


@pytest.fixture
def temp_state_file(monkeypatch):
    """Create a temporary state file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"oems": [], "contracts": [], "selected_ai": "gpt-5-thinking"}, f)
        temp_path = f.name

    # Patch the STATE_FILE in both modules
    from mcp.api.v1 import oems

    monkeypatch.setattr(oems, "STATE_FILE", Path(temp_path))

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


def test_list_oems_empty(temp_state_file):
    """Test listing OEMs when none exist."""
    response = client.get("/v1/oems")
    assert response.status_code == 200
    assert response.json() == []


def test_create_oem(temp_state_file):
    """Test creating a new OEM."""
    oem_data = {"name": "Dell", "authorized": True, "threshold": 1000}
    response = client.post("/v1/oems", json=oem_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Dell"
    assert data["authorized"] is True
    assert data["threshold"] == 1000


def test_create_oem_duplicate(temp_state_file):
    """Test creating a duplicate OEM returns 409."""
    oem_data = {"name": "HP", "authorized": False, "threshold": 500}

    # Create first OEM
    response = client.post("/v1/oems", json=oem_data)
    assert response.status_code == 201

    # Try to create duplicate
    response = client.post("/v1/oems", json=oem_data)
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_list_oems_with_data(temp_state_file):
    """Test listing OEMs after creating some."""
    # Create multiple OEMs
    oems = [
        {"name": "Dell", "authorized": True, "threshold": 1000},
        {"name": "HP", "authorized": False, "threshold": 500},
    ]

    for oem in oems:
        client.post("/v1/oems", json=oem)

    # List all
    response = client.get("/v1/oems")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert any(o["name"] == "Dell" for o in data)
    assert any(o["name"] == "HP" for o in data)


def test_update_oem(temp_state_file):
    """Test updating an OEM."""
    # Create OEM
    oem_data = {"name": "Lenovo", "authorized": False, "threshold": 750}
    client.post("/v1/oems", json=oem_data)

    # Update it
    update_data = {"authorized": True, "threshold": 2000}
    response = client.patch("/v1/oems/Lenovo", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Lenovo"
    assert data["authorized"] is True
    assert data["threshold"] == 2000


def test_update_oem_partial(temp_state_file):
    """Test partial update of an OEM."""
    # Create OEM
    oem_data = {"name": "Cisco", "authorized": True, "threshold": 1500}
    client.post("/v1/oems", json=oem_data)

    # Update only threshold
    update_data = {"threshold": 3000}
    response = client.patch("/v1/oems/Cisco", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Cisco"
    assert data["authorized"] is True  # unchanged
    assert data["threshold"] == 3000  # updated


def test_update_oem_not_found(temp_state_file):
    """Test updating a non-existent OEM returns 404."""
    update_data = {"authorized": True}
    response = client.patch("/v1/oems/NonExistent", json=update_data)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_delete_oem(temp_state_file):
    """Test deleting an OEM."""
    # Create OEM
    oem_data = {"name": "Oracle", "authorized": True, "threshold": 2500}
    client.post("/v1/oems", json=oem_data)

    # Delete it
    response = client.delete("/v1/oems/Oracle")
    assert response.status_code == 204

    # Verify it's gone
    response = client.get("/v1/oems")
    assert response.status_code == 200
    assert len(response.json()) == 0


def test_delete_oem_not_found(temp_state_file):
    """Test deleting a non-existent OEM returns 404."""
    response = client.delete("/v1/oems/NonExistent")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_oem_crud_workflow(temp_state_file):
    """Test complete CRUD workflow."""
    # Create
    oem_data = {"name": "Microsoft", "authorized": False, "threshold": 800}
    response = client.post("/v1/oems", json=oem_data)
    assert response.status_code == 201

    # Read
    response = client.get("/v1/oems")
    assert response.status_code == 200
    assert len(response.json()) == 1

    # Update
    update_data = {"authorized": True}
    response = client.patch("/v1/oems/Microsoft", json=update_data)
    assert response.status_code == 200
    assert response.json()["authorized"] is True

    # Delete
    response = client.delete("/v1/oems/Microsoft")
    assert response.status_code == 204

    # Verify empty
    response = client.get("/v1/oems")
    assert response.status_code == 200
    assert len(response.json()) == 0
