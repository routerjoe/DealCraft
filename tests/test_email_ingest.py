"""Tests for email ingestion endpoints."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mcp.api.main import app

client = TestClient(app)

# Test data file path
STATE_FILE = Path("data/state.json")


@pytest.fixture(autouse=True)
def reset_state():
    """Reset state file before and after each test."""
    # Save original state
    original_state = None
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            original_state = json.load(f)

    # Reset to minimal state
    with open(STATE_FILE, "w") as f:
        json.dump({"oems": [], "contracts": [], "selected_ai": "gpt-5-thinking"}, f)

    yield

    # Restore original state
    if original_state:
        with open(STATE_FILE, "w") as f:
            json.dump(original_state, f)


def test_ingest_rfq_minimal():
    """Test RFQ ingestion with minimal payload."""
    response = client.post(
        "/v1/email/rfq/ingest",
        json={
            "subject": "RFQ for Office Supplies",
            "body": "We need office supplies for Q1 2025",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert "ingest_id" in data
    assert "received_at" in data
    assert data["record_count"] == 1
    assert "X-Request-ID" in response.headers


def test_ingest_rfq_with_attachments():
    """Test RFQ ingestion with attachments."""
    response = client.post(
        "/v1/email/rfq/ingest",
        json={
            "subject": "RFQ for Laptops",
            "body": "Need 50 laptops",
            "attachments": ["specs.pdf", "requirements.xlsx"],
            "received_at": "2025-01-15T10:30:00Z",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["record_count"] == 1
    assert data["received_at"] == "2025-01-15T10:30:00Z"


def test_ingest_rfq_invalid_empty_subject():
    """Test RFQ ingestion with invalid empty subject."""
    response = client.post(
        "/v1/email/rfq/ingest",
        json={
            "subject": "",
            "body": "Some body text",
        },
    )

    assert response.status_code == 422


def test_ingest_rfq_missing_body():
    """Test RFQ ingestion with missing body."""
    response = client.post(
        "/v1/email/rfq/ingest",
        json={
            "subject": "Test subject",
        },
    )

    assert response.status_code == 422


def test_ingest_rfq_persistence():
    """Test that RFQ is persisted to state file."""
    # First ingestion
    response1 = client.post(
        "/v1/email/rfq/ingest",
        json={
            "subject": "First RFQ",
            "body": "First body",
        },
    )
    assert response1.status_code == 201
    assert response1.json()["record_count"] == 1

    # Second ingestion
    response2 = client.post(
        "/v1/email/rfq/ingest",
        json={
            "subject": "Second RFQ",
            "body": "Second body",
        },
    )
    assert response2.status_code == 201
    assert response2.json()["record_count"] == 2

    # Verify persistence
    with open(STATE_FILE) as f:
        state = json.load(f)
    assert len(state["rfqs"]) == 2
    assert state["rfqs"][0]["subject"] == "First RFQ"
    assert state["rfqs"][1]["subject"] == "Second RFQ"


def test_ingest_govly_event():
    """Test Govly event ingestion."""
    response = client.post(
        "/v1/email/govly/ingest",
        json={
            "event": "opportunity.created",
            "payload": {
                "id": "opp-123",
                "title": "IT Equipment",
                "agency": "DoD",
            },
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert "ingest_id" in data
    assert "received_at" in data
    assert data["event"] == "opportunity.created"
    assert data["record_count"] == 1


def test_ingest_govly_invalid_empty_event():
    """Test Govly ingestion with empty event."""
    response = client.post(
        "/v1/email/govly/ingest",
        json={
            "event": "",
            "payload": {"test": "data"},
        },
    )

    assert response.status_code == 422


def test_ingest_govly_missing_payload():
    """Test Govly ingestion with missing payload."""
    response = client.post(
        "/v1/email/govly/ingest",
        json={
            "event": "test.event",
        },
    )

    assert response.status_code == 422


def test_ingest_govly_persistence():
    """Test that Govly events are persisted."""
    response1 = client.post(
        "/v1/email/govly/ingest",
        json={
            "event": "event.one",
            "payload": {"data": "one"},
        },
    )
    assert response1.status_code == 201
    assert response1.json()["record_count"] == 1

    response2 = client.post(
        "/v1/email/govly/ingest",
        json={
            "event": "event.two",
            "payload": {"data": "two"},
        },
    )
    assert response2.status_code == 201
    assert response2.json()["record_count"] == 2

    # Verify persistence
    with open(STATE_FILE) as f:
        state = json.load(f)
    assert len(state["govly_events"]) == 2


def test_ingest_intromail():
    """Test IntroMail ingestion."""
    response = client.post(
        "/v1/email/intromail/ingest",
        json={
            "to": "customer@example.com",
            "from": "sales@redriver.com",
            "body": "Introduction email body",
            "tags": ["aerospace", "high-value"],
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert "ingest_id" in data
    assert "received_at" in data
    assert data["record_count"] == 1


def test_ingest_intromail_invalid_email():
    """Test IntroMail with invalid email format."""
    response = client.post(
        "/v1/email/intromail/ingest",
        json={
            "to": "invalid-email",
            "from": "sales@redriver.com",
            "body": "Test body",
        },
    )

    assert response.status_code == 422


def test_ingest_intromail_missing_to():
    """Test IntroMail with missing to field."""
    response = client.post(
        "/v1/email/intromail/ingest",
        json={
            "from": "sales@redriver.com",
            "body": "Test body",
        },
    )

    assert response.status_code == 422


def test_ingest_intromail_persistence():
    """Test that IntroMails are persisted."""
    response1 = client.post(
        "/v1/email/intromail/ingest",
        json={
            "to": "customer1@example.com",
            "from": "sales@redriver.com",
            "body": "First intro",
        },
    )
    assert response1.status_code == 201

    response2 = client.post(
        "/v1/email/intromail/ingest",
        json={
            "to": "customer2@example.com",
            "from": "sales@redriver.com",
            "body": "Second intro",
        },
    )
    assert response2.status_code == 201
    assert response2.json()["record_count"] == 2

    # Verify persistence
    with open(STATE_FILE) as f:
        state = json.load(f)
    assert len(state["intromails"]) == 2
    assert state["intromails"][0]["to"] == "customer1@example.com"
    assert state["intromails"][1]["to"] == "customer2@example.com"


def test_all_endpoints_have_request_id():
    """Test that all ingestion endpoints return X-Request-ID header."""
    # RFQ
    response = client.post(
        "/v1/email/rfq/ingest",
        json={"subject": "Test", "body": "Test"},
    )
    assert "X-Request-ID" in response.headers

    # Govly
    response = client.post(
        "/v1/email/govly/ingest",
        json={"event": "test", "payload": {}},
    )
    assert "X-Request-ID" in response.headers

    # IntroMail
    response = client.post(
        "/v1/email/intromail/ingest",
        json={"to": "test@example.com", "from": "sales@redriver.com", "body": "Test"},
    )
    assert "X-Request-ID" in response.headers
