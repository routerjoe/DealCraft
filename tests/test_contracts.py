"""Tests for Contract Vehicle management endpoints."""

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
    from mcp.api.v1 import contracts

    monkeypatch.setattr(contracts, "STATE_FILE", Path(temp_path))

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


def test_list_contracts_empty(temp_state_file):
    """Test listing contracts when none exist."""
    response = client.get("/v1/contracts")
    assert response.status_code == 200
    assert response.json() == []


def test_create_contract(temp_state_file):
    """Test creating a new contract."""
    contract_data = {
        "name": "GSA Schedule",
        "supported": True,
        "notes": "Federal government contract vehicle",
    }
    response = client.post("/v1/contracts", json=contract_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "GSA Schedule"
    assert data["supported"] is True
    assert data["notes"] == "Federal government contract vehicle"


def test_create_contract_duplicate(temp_state_file):
    """Test creating a duplicate contract returns 409."""
    contract_data = {"name": "NASPO", "supported": False, "notes": "State contract"}

    # Create first contract
    response = client.post("/v1/contracts", json=contract_data)
    assert response.status_code == 201

    # Try to create duplicate
    response = client.post("/v1/contracts", json=contract_data)
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_list_contracts_with_data(temp_state_file):
    """Test listing contracts after creating some."""
    # Create multiple contracts
    contracts = [
        {"name": "GSA Schedule", "supported": True, "notes": "Federal"},
        {"name": "NASPO", "supported": False, "notes": "State"},
    ]

    for contract in contracts:
        client.post("/v1/contracts", json=contract)

    # List all
    response = client.get("/v1/contracts")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert any(c["name"] == "GSA Schedule" for c in data)
    assert any(c["name"] == "NASPO" for c in data)


def test_update_contract(temp_state_file):
    """Test updating a contract."""
    # Create contract
    contract_data = {"name": "TIPS", "supported": False, "notes": "Initial note"}
    client.post("/v1/contracts", json=contract_data)

    # Update it
    update_data = {"supported": True, "notes": "Updated note"}
    response = client.patch("/v1/contracts/TIPS", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "TIPS"
    assert data["supported"] is True
    assert data["notes"] == "Updated note"


def test_update_contract_partial(temp_state_file):
    """Test partial update of a contract."""
    # Create contract
    contract_data = {"name": "WSCA", "supported": True, "notes": "Western states"}
    client.post("/v1/contracts", json=contract_data)

    # Update only notes
    update_data = {"notes": "Updated western states contract"}
    response = client.patch("/v1/contracts/WSCA", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "WSCA"
    assert data["supported"] is True  # unchanged
    assert data["notes"] == "Updated western states contract"  # updated


def test_update_contract_not_found(temp_state_file):
    """Test updating a non-existent contract returns 404."""
    update_data = {"supported": True}
    response = client.patch("/v1/contracts/NonExistent", json=update_data)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_delete_contract(temp_state_file):
    """Test deleting a contract."""
    # Create contract
    contract_data = {"name": "OMNIA", "supported": True, "notes": "Cooperative"}
    client.post("/v1/contracts", json=contract_data)

    # Delete it
    response = client.delete("/v1/contracts/OMNIA")
    assert response.status_code == 204

    # Verify it's gone
    response = client.get("/v1/contracts")
    assert response.status_code == 200
    assert len(response.json()) == 0


def test_delete_contract_not_found(temp_state_file):
    """Test deleting a non-existent contract returns 404."""
    response = client.delete("/v1/contracts/NonExistent")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_contract_crud_workflow(temp_state_file):
    """Test complete CRUD workflow."""
    # Create
    contract_data = {"name": "E&I", "supported": False, "notes": "Education"}
    response = client.post("/v1/contracts", json=contract_data)
    assert response.status_code == 201

    # Read
    response = client.get("/v1/contracts")
    assert response.status_code == 200
    assert len(response.json()) == 1

    # Update
    update_data = {"supported": True}
    response = client.patch("/v1/contracts/E&I", json=update_data)
    assert response.status_code == 200
    assert response.json()["supported"] is True

    # Delete
    response = client.delete("/v1/contracts/E&I")
    assert response.status_code == 204

    # Verify empty
    response = client.get("/v1/contracts")
    assert response.status_code == 200
    assert len(response.json()) == 0
