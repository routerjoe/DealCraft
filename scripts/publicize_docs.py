#!/usr/bin/env python3
"""
Publicize documentation with PII redaction and configurable agency masking.

This script:
1. Redacts PII (emails, phone numbers, API keys, secrets, etc.)
2. Applies configurable agency/customer name masking from config/public_terms.yml
3. Preserves vendor/vehicle context (Cisco, Nutanix, SEWP, CHESS, etc.)
4. Generates sanitized public documentation in docs/public/

Usage:
    python3 scripts/publicize_docs.py
"""

import fnmatch
import re
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(".").resolve()
SRC = ROOT / "docs"
DST = ROOT / "docs" / "public"
CFG = ROOT / "config" / "public_terms.yml"

# PII Redaction Patterns
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"(\+?1[-.\s]?)?(\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b")
SLACK_RE = re.compile(r"\bxox[baprs]-[A-Za-z0-9-]+\b")
OPENAI_RE = re.compile(r"\bsk-[A-Za-z0-9]{10,}\b")
BEARER_RE = re.compile(r"(?i)Bearer\s+[A-Za-z0-9._\-]{8,}")
AWS_RE = re.compile(r"\bAKIA[0-9A-Z]{12,}\b")
LONGSECRET_RE = re.compile(r"(?<![A-Za-z0-9_-])[A-Za-z0-9_\-]{32,}(?![A-Za-z0-9_-])")
QUERYSECRET_RE = re.compile(r"([?&](?:apikey|token|sig|signature|secret)=[^&\s]+)", re.I)


def load_cfg():
    """Load configuration from public_terms.yml."""
    if not CFG.exists():
        print(f"ERROR: Configuration file not found: {CFG}")
        sys.exit(1)

    with open(CFG, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def redact_pii_line(s: str) -> str:
    """Redact PII from a single line of text."""
    s = EMAIL_RE.sub("***@***.***", s)
    s = PHONE_RE.sub("***-***-****", s)
    s = SLACK_RE.sub("xox*-***", s)
    s = OPENAI_RE.sub("sk-***", s)
    s = BEARER_RE.sub("Bearer ***", s)
    s = AWS_RE.sub("AKIA***REDACTED***", s)
    s = QUERYSECRET_RE.sub(lambda m: m.group(0).split("=")[0] + "=***", s)
    s = LONGSECRET_RE.sub("***SECRET***", s)
    return s


def should_include(path: Path, patterns):
    """Check if path matches any of the glob patterns."""
    # path is already relative or needs to be made relative
    if path.is_absolute():
        try:
            rel = str(path.relative_to(ROOT))
        except ValueError:
            rel = str(path)
    else:
        rel = str(path)
    return any(fnmatch.fnmatch(rel, pat) for pat in patterns)


def copy_binary(src: Path, dst: Path):
    """Copy binary file without modifications."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"  [BINARY] {src.relative_to(ROOT)} → {dst.relative_to(ROOT)}")


def process_text(src: Path, dst: Path, mask_map: dict):
    """Process text file: redact PII and apply agency masking."""
    try:
        text = src.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        print(f"  [SKIP] {src.relative_to(ROOT)}: {e}")
        return

    # PII redaction
    lines = text.splitlines()
    redacted_lines = [redact_pii_line(line) for line in lines]
    text = "\n".join(redacted_lines)

    # Apply masking (word-boundary, preserve case)
    for original_term, masked_term in mask_map.items():
        # Match exact case and common variations
        text = re.sub(rf"\b{re.escape(original_term)}\b", masked_term, text)
        text = re.sub(rf"\b{re.escape(original_term.upper())}\b", masked_term, text)
        text = re.sub(rf"\b{re.escape(original_term.lower())}\b", masked_term, text)

    # Write output
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")
    print(f"  [TEXT] {src.relative_to(ROOT)} → {dst.relative_to(ROOT)}")


def main():
    """Main publicization process."""
    print("=" * 70)
    print("DealCraft Documentation Publicizer")
    print("PII Redaction + Configurable Agency Masking")
    print("=" * 70)

    # Load configuration
    print(f"\n📋 Loading configuration from: {CFG.relative_to(ROOT)}")
    cfg = load_cfg()
    mask_map = cfg.get("mask_map", {})
    include_globs = cfg.get("include_globs", [])
    binary_globs = cfg.get("binary_globs", [])

    print(f"   - Masking {len(mask_map)} terms")
    print(f"   - Processing {len(include_globs)} text patterns")
    print(f"   - Copying {len(binary_globs)} binary patterns")

    # Clean destination
    if DST.exists():
        print(f"\n🗑️  Removing existing: {DST.relative_to(ROOT)}")
        shutil.rmtree(DST)
    DST.mkdir(parents=True, exist_ok=True)

    # Process all files
    print(f"\n📁 Processing files from: {SRC.relative_to(ROOT)}")
    all_files = list(SRC.rglob("*"))
    text_count = 0
    binary_count = 0
    skip_count = 0

    for p in all_files:
        if p.is_dir():
            continue

        rel = p.relative_to(ROOT)

        # Skip if already in public directory
        if "docs/public" in str(rel):
            continue

        # Binary files
        if should_include(rel, binary_globs):
            copy_binary(p, DST / p.relative_to(SRC))
            binary_count += 1
            continue

        # Text files
        if should_include(rel, include_globs):
            process_text(p, DST / p.relative_to(SRC), mask_map)
            text_count += 1
            continue

        # Everything else under docs/: try to process as text
        if str(rel).startswith("docs/"):
            out = DST / p.relative_to(SRC)
            out.parent.mkdir(parents=True, exist_ok=True)
            try:
                process_text(p, out, mask_map)
                text_count += 1
            except Exception:
                # Fallback to binary copy
                copy_binary(p, out)
                binary_count += 1
        else:
            skip_count += 1

    print("\n✅ Publicization complete!")
    print(f"   - {text_count} text files processed")
    print(f"   - {binary_count} binary files copied")
    print(f"   - {skip_count} files skipped")
    print(f"   - Output: {DST.relative_to(ROOT)}")
    print("=" * 70)


if __name__ == "__main__":
    main()
