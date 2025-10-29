"""
Tests for Obsidian path configuration management.

Sprint 13: Obsidian Sync Policies
Validates that paths use config constants and environment variables.
"""

import re
from pathlib import Path

import pytest


@pytest.mark.xfail(reason="Config constants to be added in Sprint 13 development")
class TestPathConfiguration:
    """Test path configuration in codebase."""

    def test_no_hardcoded_home_paths_in_python(self):
        """Test that Python code doesn't contain hardcoded home directory paths."""
        # Scan Python files for hardcoded paths
        mcp_dir = Path("mcp")
        hardcoded_patterns = [
            r"/Users/jonolan/Documents",
            r"/Users/jonolan/projects",
            r"~/Documents",
        ]

        violations = []
        for py_file in mcp_dir.rglob("*.py"):
            with open(py_file, "r") as f:
                content = f.read()
                for pattern in hardcoded_patterns:
                    if re.search(pattern, content):
                        # Check if it's in a comment or docstring explaining the path
                        # Allow mentions in comments/docs
                        lines = content.split("\n")
                        for i, line in enumerate(lines):
                            if pattern in line and not (line.strip().startswith("#") or '"""' in line or "'''" in line):
                                violations.append(f"{py_file}:{i+1} - {line.strip()}")

        assert len(violations) == 0, "Hardcoded paths found:\n" + "\n".join(violations)

    def test_config_has_obsidian_path_constant(self):
        """Test that config.py defines OBSIDIAN path constants."""
        config_file = Path("mcp/core/config.py")
        if not config_file.exists():
            pytest.skip("config.py not found")

        with open(config_file, "r") as f:
            content = f.read()

        # Should have environment variable usage
        assert "OBSIDIAN" in content or "obsidian" in content.lower()
        # Should use os.getenv or os.environ
        assert "os.getenv" in content or "os.environ" in content

    def test_relative_paths_in_config(self):
        """Test that relative paths are defined for vault organization."""
        config_file = Path("mcp/core/config.py")
        if not config_file.exists():
            pytest.skip("config.py not found")

        with open(config_file, "r") as f:
            content = f.read()

        # Should define relative paths
        expected_paths = ["Opportunities", "Dashboards", "Triage"]
        for path in expected_paths:
            assert path in content, f"Config should define relative path for {path}"


class TestEnvironmentVariableUsage:
    """Test environment variable configuration."""

    def test_env_example_has_obsidian_path(self):
        """Test that .env.example documents OBSIDIAN_VAULT_PATH."""
        env_example = Path(".env.example")
        assert env_example.exists()

        with open(env_example, "r") as f:
            content = f.read()

        # Should document Obsidian path variable
        assert "OBSIDIAN" in content


class TestPathConstructionHelpers:
    """Test path construction helper functions if they exist."""

    def test_path_helpers_exist(self):
        """Test that path construction helpers are defined."""
        # This is a placeholder - actual implementation may vary
        config_file = Path("mcp/core/config.py")
        if not config_file.exists():
            pytest.skip("config.py not found")

        with open(config_file, "r") as f:
            content = f.read()

        # Should have path construction logic
        # Look for os.path.join usage
        assert "os.path.join" in content or "Path(" in content


@pytest.mark.xfail(reason="Config integration to be added in Sprint 13 development")
class TestObsidianIntegration:
    """Test Obsidian integration code."""

    def test_obsidian_module_uses_config(self):
        """Test that obsidian.py imports from config."""
        obsidian_file = Path("mcp/api/v1/obsidian.py")
        if not obsidian_file.exists():
            pytest.skip("obsidian.py not found")

        with open(obsidian_file, "r") as f:
            content = f.read()

        # Should import or use config
        assert "from mcp.core.config import" in content or "import mcp.core.config" in content or "config." in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
