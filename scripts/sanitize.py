#!/usr/bin/env python3
"""
Sanitize sensitive customer and organization data from DealCraft repository.
Replaces specific customer names with generic placeholders.
"""

import re
from pathlib import Path

# Replacement mappings
REPLACEMENTS = {
    # Customer Names (case-sensitive) - including filenames
    r"\bAFCENT\b": "CustomerAlpha",
    r"Customer Alpha Command": "Customer Alpha Command",
    r"\bAETC\b": "CustomerBeta",
    r"Customer Beta Command": "Customer Beta Command",
    # Plan IDs and filenames
    r"plan-customer-alpha": "plan-customer-alpha",
    r"plan-customer-beta": "plan-customer-beta",
    # Organization Names
    r"Federal Department A": "Federal Department A",
    r"\bGSA\b(?! Schedule)": "Federal Agency A",  # Don't replace "GSA Schedule"
    r"\bSPAWAR\b": "Federal Agency B",
    r"\bNAVAIR\b": "Federal Agency C",
    # Vault references
    r"DealCraft vault": "DealCraft vault",
    # Tool name references
    r"DealCraft": "DealCraft",
    r"DealCraft sales automation": "DealCraft sales automation",
}

# File patterns to process
INCLUDE_PATTERNS = ["*.md", "*.py", "*.ts", "*.tsx", "*.json", "*.yml", "*.yaml", "*.txt"]

# Directories to exclude
EXCLUDE_DIRS = {".git", "node_modules", "dist", ".venv", "__pycache__", ".pytest_cache"}


def should_process_file(filepath):
    """Check if file should be processed."""
    # Skip if in excluded directory
    parts = filepath.parts
    if any(excluded in parts for excluded in EXCLUDE_DIRS):
        return False

    # Skip package-lock.json
    if filepath.name == "package-lock.json":
        return False

    # Check if matches include patterns
    return any(filepath.match(pattern) for pattern in INCLUDE_PATTERNS)


def sanitize_file(filepath):
    """Sanitize a single file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content
        replaced_count = 0

        # Apply each replacement
        for pattern, replacement in REPLACEMENTS.items():
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                replaced_count += 1
                content = new_content

        # Write back if changed
        if content != original_content:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return True, replaced_count

        return False, 0

    except Exception as e:
        print(f"  ⚠️  Error processing {filepath}: {e}")
        return False, 0


def main():
    print("🔒 Sanitizing sensitive data from DealCraft repository...")
    print("=" * 60)

    root_dir = Path(".")
    files_modified = 0
    total_replacements = 0

    # Find all files to process
    all_files = []
    for pattern in INCLUDE_PATTERNS:
        all_files.extend(root_dir.rglob(pattern))

    # Filter and process
    files_to_process = [f for f in all_files if should_process_file(f)]

    print(f"Found {len(files_to_process)} files to process")
    print()

    for filepath in files_to_process:
        modified, count = sanitize_file(filepath)
        if modified:
            files_modified += 1
            total_replacements += count
            print(f"  ✓ Modified: {filepath}")

    print()
    print("=" * 60)
    print("✅ Sanitization complete!")
    print(f"Files modified: {files_modified}")
    print(f"Pattern matches replaced: {total_replacements}")
    print()
    print("⚠️  Important: Review changes before committing!")
    print("Run: git diff | head -200")


if __name__ == "__main__":
    main()
