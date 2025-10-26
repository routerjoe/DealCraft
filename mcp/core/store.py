"""JSON file store with atomic read/write operations."""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict


def read_json(path: str) -> Dict[str, Any]:
    """
    Read JSON data from a file.

    Args:
        path: Path to the JSON file

    Returns:
        Dictionary containing the JSON data

    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    file_path = Path(path)
    with open(file_path, "r") as f:
        return json.load(f)


def write_json(path: str, data: Dict[str, Any]) -> None:
    """
    Write JSON data to a file atomically.

    Uses atomic write pattern: write to temp file, then rename.
    This ensures the file is never left in a partially written state.

    Args:
        path: Path to the JSON file
        data: Dictionary to write as JSON
    """
    file_path = Path(path)

    # Ensure parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to temporary file in the same directory
    # Using same directory ensures atomic rename works across filesystems
    fd, temp_path = tempfile.mkstemp(dir=file_path.parent, prefix=f".{file_path.name}.", suffix=".tmp")

    try:
        # Write JSON to temp file
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")  # Add trailing newline

        # Atomic rename
        os.replace(temp_path, file_path)
    except Exception:
        # Clean up temp file on error
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise
