"""
Tests for CRM Write-Safety Gate - Phase 12

Validates:
- Default behavior is dry-run (safe mode)
- Explicit dry_run=false required for writes
- Response format for both modes
- No accidental destructive operations
"""

from fastapi.testclient import TestClient

from mcp.api.main import app

client = TestClient(app)


def test_crm_export_no_dry_run_field_defaults_to_safe():
    """Test that missing dry_run field defaults to dry-run mode (safe)."""
    response = client.post(
        "/v1/crm/export",
        json={
            "format": "generic_json"
            # dry_run field intentionally omitted
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Should default to dry-run mode
    assert data["dry_run"] is True
    assert data["status"] == "ok"
    assert "no external changes applied" in data["note"]
    assert "total" in data


def test_crm_export_dry_run_true_explicit():
    """Test explicit dry_run=true returns safe response."""
    response = client.post("/v1/crm/export", json={"format": "salesforce", "dry_run": True})

    assert response.status_code == 200
    data = response.json()

    assert data["dry_run"] is True
    assert data["status"] == "ok"
    assert "no external changes applied" in data["note"]


def test_crm_export_dry_run_false_requires_explicit():
    """Test dry_run=false enables write path (gated, returns 200/202)."""
    response = client.post(
        "/v1/crm/export",
        json={
            "format": "generic_json",
            "dry_run": False,  # Explicit false required
        },
    )

    # Should return 200 with accepted status (integration not configured)
    assert response.status_code == 200
    data = response.json()

    assert data["dry_run"] is False
    assert data["status"] == "accepted"
    assert "write path allowed" in data["note"]
    assert "integration target not configured" in data["note"]
    assert "would_export" in data or "total" in data


def test_crm_export_with_specific_opportunities_dry_run():
    """Test dry-run mode with specific opportunity IDs."""
    response = client.post("/v1/crm/export", json={"opportunity_ids": ["test-opp-1", "test-opp-2"], "format": "hubspot", "dry_run": True})

    # Should still return 200 even if opportunities don't exist (validation only)
    # Or 404 if no opportunities found
    assert response.status_code in [200, 404]

    if response.status_code == 200:
        data = response.json()
        assert data["dry_run"] is True


def test_crm_export_write_mode_with_specific_opportunities():
    """Test write mode (dry_run=false) with specific opportunity IDs."""
    response = client.post("/v1/crm/export", json={"opportunity_ids": ["test-opp-1"], "format": "salesforce", "dry_run": False})

    # Should return 200 with accepted status or 404 if no opportunities
    assert response.status_code in [200, 404]

    if response.status_code == 200:
        data = response.json()
        assert data["dry_run"] is False
        assert data["status"] == "accepted"


def test_crm_export_preserves_request_id_header():
    """Test that x-request-id header is preserved in response."""
    test_request_id = "test-req-12345"

    response = client.post("/v1/crm/export", json={"format": "generic_json"}, headers={"x-request-id": test_request_id})

    assert response.status_code == 200
    data = response.json()
    assert data["request_id"] == test_request_id


def test_crm_export_different_formats_dry_run():
    """Test that dry-run works consistently across different formats."""
    formats = ["generic_json", "salesforce", "hubspot"]

    for fmt in formats:
        response = client.post("/v1/crm/export", json={"format": fmt, "dry_run": True})

        assert response.status_code == 200
        data = response.json()
        assert data["dry_run"] is True
        assert data["format"] == fmt


def test_crm_export_safety_gate_prevents_accidental_writes():
    """Test that omitting dry_run or setting it to anything but false is safe."""
    # Test various cases that should all result in dry-run mode
    test_cases = [
        {},  # No dry_run field
        {"dry_run": True},  # Explicit true
        {"dry_run": None},  # Explicit None (should default to true)
    ]

    for request_body in test_cases:
        request_body["format"] = "generic_json"
        response = client.post("/v1/crm/export", json=request_body)

        assert response.status_code == 200
        data = response.json()
        assert data["dry_run"] is True, f"Failed for request: {request_body}"
        assert "no external changes applied" in data["note"]


def test_crm_attribution_not_affected_by_write_gate():
    """Test that attribution endpoint (read-only) is not affected by write-safety gate."""
    response = client.post("/v1/crm/attribution", json={})

    # Attribution is read-only, should work normally
    # May return 404 if no opportunities exist, or 200 with data
    assert response.status_code in [200, 404]


def test_crm_formats_endpoint_still_works():
    """Test that formats endpoint (read-only) still works."""
    response = client.get("/v1/crm/formats")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
