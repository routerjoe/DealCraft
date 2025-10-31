"""
Tests for config/obsidian_paths.py

Validates:
- All path helpers return correct Path objects
- VAULT_ROOT environment variable handling
- No hardcoded absolute paths in the module
"""

import os
import re
from pathlib import Path

import pytest

from config.obsidian_paths import (
    ensure_dir,
    get_backups_dir,
    get_dashboards_dir,
    get_oems_dir,
    get_opportunities_dir,
    get_projects_dir,
    get_reference_dir,
    get_vault_root,
)


def test_vault_root_missing_raises_error():
    """Test that missing VAULT_ROOT raises a helpful ValueError."""
    # Remove VAULT_ROOT if present
    original = os.environ.pop("VAULT_ROOT", None)
    try:
        with pytest.raises(ValueError) as exc_info:
            get_vault_root()

        error_msg = str(exc_info.value)
        assert "VAULT_ROOT" in error_msg
        assert "environment variable" in error_msg
        # Check for remediation guidance
        assert "export" in error_msg or ".env" in error_msg
    finally:
        # Restore original if it existed
        if original:
            os.environ["VAULT_ROOT"] = original


def test_vault_root_returns_path(monkeypatch, tmp_path):
    """Test that get_vault_root returns a Path object."""
    test_vault = tmp_path / "test_vault"
    monkeypatch.setenv("VAULT_ROOT", str(test_vault))

    result = get_vault_root()
    assert isinstance(result, Path)
    assert result == test_vault


def test_oems_dir_correct_path(monkeypatch, tmp_path):
    """Test that get_oems_dir returns correct subdirectory."""
    test_vault = tmp_path / "test_vault"
    monkeypatch.setenv("VAULT_ROOT", str(test_vault))

    result = get_oems_dir()
    assert isinstance(result, Path)
    assert result == test_vault / "30 Hubs" / "OEMs"


def test_dashboards_dir_correct_path(monkeypatch, tmp_path):
    """Test that get_dashboards_dir returns correct subdirectory."""
    test_vault = tmp_path / "test_vault"
    monkeypatch.setenv("VAULT_ROOT", str(test_vault))

    result = get_dashboards_dir()
    assert isinstance(result, Path)
    assert result == test_vault / "50 Dashboards"


def test_reference_dir_correct_path(monkeypatch, tmp_path):
    """Test that get_reference_dir returns correct subdirectory."""
    test_vault = tmp_path / "test_vault"
    monkeypatch.setenv("VAULT_ROOT", str(test_vault))

    result = get_reference_dir()
    assert isinstance(result, Path)
    assert result == test_vault / "80 Reference"


def test_backups_dir_correct_path(monkeypatch, tmp_path):
    """Test that get_backups_dir returns correct subdirectory."""
    test_vault = tmp_path / "test_vault"
    monkeypatch.setenv("VAULT_ROOT", str(test_vault))

    result = get_backups_dir()
    assert isinstance(result, Path)
    assert result == test_vault / "80 Reference" / "backups"


def test_projects_dir_correct_path(monkeypatch, tmp_path):
    """Test that get_projects_dir returns correct subdirectory."""
    test_vault = tmp_path / "test_vault"
    monkeypatch.setenv("VAULT_ROOT", str(test_vault))

    result = get_projects_dir()
    assert isinstance(result, Path)
    assert result == test_vault / "40 Projects"


def test_opportunities_dir_correct_path(monkeypatch, tmp_path):
    """Test that get_opportunities_dir returns correct subdirectory."""
    test_vault = tmp_path / "test_vault"
    monkeypatch.setenv("VAULT_ROOT", str(test_vault))

    result = get_opportunities_dir()
    assert isinstance(result, Path)
    assert result == test_vault / "40 Projects" / "Opportunities"


def test_opportunities_dir_nested_under_projects(monkeypatch, tmp_path):
    """Test that opportunities dir is correctly nested under projects."""
    test_vault = tmp_path / "test_vault"
    monkeypatch.setenv("VAULT_ROOT", str(test_vault))

    projects = get_projects_dir()
    opportunities = get_opportunities_dir()

    # Opportunities should be a subdirectory of Projects
    assert str(opportunities).startswith(str(projects))
    assert opportunities.parent == projects


def test_ensure_dir_creates_directory(monkeypatch, tmp_path):
    """Test that ensure_dir creates the directory."""
    test_vault = tmp_path / "test_vault"
    monkeypatch.setenv("VAULT_ROOT", str(test_vault))

    test_dir = tmp_path / "nested" / "directory" / "path"
    assert not test_dir.exists()

    result = ensure_dir(test_dir)
    assert test_dir.exists()
    assert test_dir.is_dir()
    assert result == test_dir


def test_ensure_dir_idempotent(monkeypatch, tmp_path):
    """Test that ensure_dir is safe to call multiple times."""
    test_vault = tmp_path / "test_vault"
    monkeypatch.setenv("VAULT_ROOT", str(test_vault))

    test_dir = tmp_path / "test_directory"

    result1 = ensure_dir(test_dir)
    result2 = ensure_dir(test_dir)

    assert result1 == result2
    assert test_dir.exists()


def test_no_hardcoded_absolute_paths():
    """
    Verify that config/obsidian_paths.py contains NO hardcoded absolute paths.

    This test reads the source file and checks for patterns that would indicate
    hardcoded user-specific paths (e.g., /Users/jonolan/).
    """
    config_file = Path(__file__).parent.parent / "config" / "obsidian_paths.py"
    assert config_file.exists(), f"Config file not found: {config_file}"

    content = config_file.read_text()

    # Check for common absolute path patterns
    forbidden_patterns = [
        r"/Users/jonolan/",  # Specific user home
        r"/Users/[a-zA-Z0-9_-]+/Documents/",  # Any user Documents path
        r'"/Users/',  # Any quoted /Users/ path
        r"'/Users/",  # Any single-quoted /Users/ path
    ]

    violations = []
    for pattern in forbidden_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            violations.append(f"Found pattern '{pattern}': {matches}")

    assert not violations, "config/obsidian_paths.py contains hardcoded absolute paths:\n" + "\n".join(violations)


def test_all_helpers_use_relative_paths(monkeypatch, tmp_path):
    """Test that all helpers build paths relative to VAULT_ROOT."""
    test_vault = tmp_path / "custom_vault_location"
    monkeypatch.setenv("VAULT_ROOT", str(test_vault))

    # All paths should start with the custom vault location
    assert get_vault_root() == test_vault
    assert str(get_oems_dir()).startswith(str(test_vault))
    assert str(get_dashboards_dir()).startswith(str(test_vault))
    assert str(get_reference_dir()).startswith(str(test_vault))
    assert str(get_backups_dir()).startswith(str(test_vault))
    assert str(get_projects_dir()).startswith(str(test_vault))
    assert str(get_opportunities_dir()).startswith(str(test_vault))
