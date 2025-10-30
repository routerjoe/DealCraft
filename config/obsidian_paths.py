"""
Centralized Obsidian Vault Path Helpers

This module provides consistent path resolution for the Obsidian vault structure.
All paths are resolved relative to the VAULT_ROOT environment variable at runtime.

Ownership Boundaries (for future sync policy enforcement):
- One-way (System → Obsidian): Generated dashboards, databases in /80 Reference/bases/,
  automated reports. The system is the source of truth.
- Two-way (Obsidian authoritative): OEM Hub YAML frontmatter, People Hubs, Contract Hubs.
  Manual edits in Obsidian take precedence; system should sync from Obsidian.

Usage:
    from config.obsidian_paths import get_vault_root, get_oems_dir

    vault = get_vault_root()
    oems = get_oems_dir()
"""

import os
from pathlib import Path


def get_vault_root() -> Path:
    """
    Get the root path of the Obsidian vault.

    Returns:
        Path: Absolute path to the vault root directory

    Raises:
        ValueError: If VAULT_ROOT environment variable is not set

    Example:
        >>> vault = get_vault_root()
        >>> print(vault)
        PosixPath('/path/to/your/vault')
    """
    vault_root = os.environ.get("VAULT_ROOT")
    if not vault_root:
        raise ValueError(
            "VAULT_ROOT environment variable is not set. "
            "Please set it to your Obsidian vault path, e.g.:\n"
            '  export VAULT_ROOT="/path/to/your/vault"\n'
            "Or add it to your .env file."
        )
    return Path(vault_root)


def get_oems_dir() -> Path:
    """
    Get the OEMs directory within the vault.

    Returns:
        Path: <VAULT_ROOT>/30 Hubs/OEMs

    Example:
        >>> oems_dir = get_oems_dir()
        >>> oem_file = oems_dir / "Dell.md"
    """
    return get_vault_root() / "30 Hubs" / "OEMs"


def get_dashboards_dir() -> Path:
    """
    Get the Dashboards directory within the vault.

    Returns:
        Path: <VAULT_ROOT>/50 Dashboards

    Example:
        >>> dashboards = get_dashboards_dir()
        >>> summary = dashboards / "Weekly Summary.md"
    """
    return get_vault_root() / "50 Dashboards"


def get_reference_dir() -> Path:
    """
    Get the Reference directory within the vault.

    Returns:
        Path: <VAULT_ROOT>/80 Reference

    Example:
        >>> reference = get_reference_dir()
        >>> bases = reference / "bases"
    """
    return get_vault_root() / "80 Reference"


def get_backups_dir() -> Path:
    """
    Get the backups directory within the vault.

    Returns:
        Path: <VAULT_ROOT>/80 Reference/backups

    Example:
        >>> backups = get_backups_dir()
        >>> backup_file = backups / "2025-01-15T10-30-00.zip"
    """
    return get_reference_dir() / "backups"


def ensure_dir(path: Path) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path to create

    Returns:
        Path: The same path (for chaining)

    Example:
        >>> backup_dir = ensure_dir(get_backups_dir())
        >>> # Directory now exists, safe to write files
    """
    path.mkdir(parents=True, exist_ok=True)
    return path
