# Obsidian Sync Policies

This document defines the synchronization rules and best practices for integrating the Red River Sales Automation system with the Obsidian vault.

## Table of Contents

1. [Overview](#overview)
2. [Ownership Rules](#ownership-rules)
3. [Path Helpers](#path-helpers)
4. [Conflict Resolution](#conflict-resolution)
5. [Dataview Refresh Strategy](#dataview-refresh-strategy)
6. [File Locking Guidelines](#file-locking-guidelines)
7. [Backup & Restore](#backup--restore)
8. [Safe Export Workflows](#safe-export-workflows)

---

## Overview

The system and Obsidian vault operate on different ownership models for different content types:

- **One-way sync (System → Obsidian)**: System is the source of truth
- **Two-way sync (Obsidian authoritative)**: Manual edits in Obsidian take precedence

Understanding these boundaries prevents data loss and ensures predictable behavior.

---

## Ownership Rules

### One-Way (System → Obsidian)

**The system is the authoritative source. Obsidian is read-only for these files.**

| Content Type | Location | Notes |
|-------------|----------|-------|
| Generated Dashboards | `50 Dashboards/` | Auto-generated summaries, metrics, forecasts |
| SQLite Databases | `80 Reference/bases/*.db` | Contacts, contracts, forecasts, partners |
| Automated Reports | `50 Dashboards/reports/` | Weekly summaries, pipeline reports |
| System Logs | `80 Reference/logs/` | Activity logs, sync history |

**Rules:**
- ✅ System overwrites these files without checking timestamps
- ❌ Manual edits in Obsidian will be lost on next sync
- 📝 To preserve notes, create a separate file in `90 Notes/` and link to it

### Two-Way (Obsidian Authoritative)

**Manual edits in Obsidian take precedence. System syncs FROM Obsidian.**

| Content Type | Location | Notes |
|-------------|----------|-------|
| OEM Hub YAML | `30 Hubs/OEMs/*.md` | Frontmatter metadata (contacts, status, tags) |
| People Hubs | `30 Hubs/People/*.md` | Contact details, relationships |
| Contract Hubs | `30 Hubs/Contracts/*.md` | Contract terms, renewal dates |
| Project Notes | `40 Projects/` | Opportunity tracking, meeting notes |

**Rules:**
- ✅ System reads these files and imports data to database
- ✅ Manual edits in Obsidian are preserved and synced back
- ⚠️ System may append generated sections (clearly marked)
- 📝 Use YAML frontmatter for structured data; body for freeform notes

---

## Path Helpers

Use the centralized path helpers in `config/obsidian_paths.py` to ensure consistent path resolution:

```python
from config.obsidian_paths import (
    get_vault_root,
    get_oems_dir,
    get_dashboards_dir,
    get_reference_dir,
    get_backups_dir,
    ensure_dir,
)

# Example: Export OEM data
oems_dir = get_oems_dir()
ensure_dir(oems_dir)  # Creates directory if needed

for oem in oems_to_export:
    oem_file = oems_dir / f"{oem.name}.md"
    oem_file.write_text(render_oem_hub(oem))
```

### Available Helpers

| Helper | Returns | Example |
|--------|---------|---------|
| `get_vault_root()` | `<VAULT_ROOT>` | `/Users/you/Documents/Obsidian Documents/Red River Sales` |
| `get_oems_dir()` | `<VAULT_ROOT>/30 Hubs/OEMs` | Path to OEM hubs |
| `get_dashboards_dir()` | `<VAULT_ROOT>/50 Dashboards` | Path to dashboards |
| `get_reference_dir()` | `<VAULT_ROOT>/80 Reference` | Path to reference materials |
| `get_backups_dir()` | `<VAULT_ROOT>/80 Reference/backups` | Path to backup archives |
| `ensure_dir(path)` | Same path (creates if needed) | Safe directory creation |

**Environment Setup:**
```bash
export VAULT_ROOT="/Users/yourname/Documents/Obsidian Documents/Red River Sales"
# Or add to .env file
```

---

## Conflict Resolution

### Timestamp Precedence

When conflicts occur, the **most recent modification wins**:

1. Check file `mtime` (modification time)
2. Compare with database `updated_at` timestamp
3. Newer timestamp takes precedence
4. Log conflict resolution in `80 Reference/logs/sync_conflicts.log`

### Authoritative Source Matrix

| Content | Obsidian Wins | System Wins | Resolution |
|---------|---------------|-------------|------------|
| OEM YAML frontmatter | ✅ Always | ❌ Never | System imports from Obsidian |
| Dashboard content | ❌ Never | ✅ Always | System overwrites |
| Contract renewal date | ✅ Manual edit | ⚠️ Auto-detected | Prompt for confirmation |
| Contact email | ✅ Manual edit | ⚠️ CRM sync | Flag for review |

### Manual Override

To force a specific direction:

```python
# Force system → Obsidian (ignore timestamps)
sync_manager.export_to_obsidian(force=True)

# Force Obsidian → system (ignore timestamps)
sync_manager.import_from_obsidian(force=True)
```

---

## Dataview Refresh Strategy

Obsidian's Dataview plugin requires explicit refresh triggers.

### When to Trigger Rescans

1. **After bulk exports** (e.g., nightly dashboard generation)
2. **After database changes** (e.g., new contracts imported)
3. **On-demand** (user requests refresh)

### Refresh Methods

#### Method 1: Touch Files (Recommended)

```python
from pathlib import Path
import time

def trigger_dataview_refresh(file_path: Path):
    """Touch file to trigger Dataview rescan."""
    file_path.touch()  # Updates mtime
```

#### Method 2: Append Trigger Comment

```python
def trigger_dataview_refresh(file_path: Path):
    """Append hidden comment to trigger rescan."""
    content = file_path.read_text()
    timestamp = time.time()
    content += f"\n<!-- sync-trigger: {timestamp} -->\n"
    file_path.write_text(content)
```

#### Method 3: Obsidian URI (if available)

```bash
# Open specific file to force refresh
open "obsidian://open?vault=Red%20River%20Sales&file=50%20Dashboards/Weekly%20Summary"
```

---

## File Locking Guidelines

To avoid concurrent edit conflicts:

### Advisory Locks

Use file-based locking for critical operations:

```python
from pathlib import Path
import fcntl
import contextlib

@contextlib.contextmanager
def file_lock(lock_path: Path):
    """Acquire advisory lock on file."""
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, 'w') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)

# Usage
lock_file = get_reference_dir() / ".locks" / "sync.lock"
with file_lock(lock_file):
    # Perform sync operations
    sync_manager.export_dashboards()
```

### Lock Locations

- **Global sync**: `80 Reference/.locks/sync.lock`
- **OEM exports**: `80 Reference/.locks/oems.lock`
- **Dashboard generation**: `80 Reference/.locks/dashboards.lock`

### Timeout Policy

- **Default timeout**: 30 seconds
- **Long operations**: 5 minutes (with heartbeat)
- **Stale lock detection**: Remove locks older than 10 minutes

---

## Backup & Restore

### Backup Strategy

**Location**: `<VAULT_ROOT>/80 Reference/backups/`

**Naming convention**: `YYYY-MM-DDThh-mm-ss.zip`

Example: `2025-10-30T14-30-00.zip`

### Recommended Cadence

- **Daily**: Automated nightly backup before sync operations
- **Pre-migration**: Before major system updates or schema changes
- **On-demand**: Before risky operations (bulk deletes, rewrites)

### Backup Script

```python
from config.obsidian_paths import get_vault_root, get_backups_dir, ensure_dir
from datetime import datetime
import zipfile
from pathlib import Path

def create_backup():
    """Create timestamped vault backup."""
    vault = get_vault_root()
    backups = ensure_dir(get_backups_dir())
    
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    backup_file = backups / f"{timestamp}.zip"
    
    with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file in vault.rglob('*'):
            if file.is_file() and 'backups' not in file.parts:
                arcname = file.relative_to(vault)
                zf.write(file, arcname)
    
    print(f"✓ Backup created: {backup_file}")
    return backup_file
```

### Restore Procedure

1. **Stop sync operations** (acquire global lock)
2. **Extract backup** to temporary directory
3. **Compare file hashes** to detect changes
4. **Restore selected files** or full vault
5. **Resume sync operations**

```bash
# Quick restore
cd /path/to/vault
unzip ../backups/2025-10-30T14-30-00.zip -d restore_preview
# Review changes, then copy desired files
```

---

## Safe Export Workflows

### Example 1: Export OEM Hubs

```python
from config.obsidian_paths import get_oems_dir, ensure_dir
from datetime import datetime

def safe_export_oem_hubs(oems: list):
    """Safely export OEM hubs to Obsidian."""
    oems_dir = ensure_dir(get_oems_dir())
    
    # Create backup before export
    backup_file = create_backup()
    print(f"Backup: {backup_file}")
    
    # Export each OEM
    for oem in oems:
        oem_path = oems_dir / f"{oem.name}.md"
        
        # Check if file exists and is newer
        if oem_path.exists():
            file_mtime = oem_path.stat().st_mtime
            db_mtime = oem.updated_at.timestamp()
            if file_mtime > db_mtime:
                print(f"⚠️  Skipping {oem.name}: Obsidian version is newer")
                continue
        
        # Safe write: tmp file + atomic rename
        tmp_path = oem_path.with_suffix('.tmp')
        tmp_path.write_text(render_oem_hub(oem))
        tmp_path.rename(oem_path)
        print(f"✓ Exported: {oem.name}")
```

### Example 2: Import Contract Updates

```python
from config.obsidian_paths import get_vault_root
import yaml

def safe_import_contracts():
    """Import contract updates from Obsidian (two-way sync)."""
    vault = get_vault_root()
    contracts_dir = vault / "30 Hubs" / "Contracts"
    
    for contract_file in contracts_dir.glob("*.md"):
        content = contract_file.read_text()
        
        # Extract YAML frontmatter
        if content.startswith('---'):
            _, yaml_section, _ = content.split('---', 2)
            metadata = yaml.safe_load(yaml_section)
            
            # Import to database
            contract_id = metadata.get('contract_id')
            if contract_id:
                update_contract_from_obsidian(contract_id, metadata)
                print(f"✓ Imported: {contract_file.name}")
```

### Example 3: Generate Dashboard with Dataview Refresh

```python
from config.obsidian_paths import get_dashboards_dir, ensure_dir
from datetime import datetime

def generate_weekly_dashboard():
    """Generate weekly dashboard and trigger Dataview refresh."""
    dashboards = ensure_dir(get_dashboards_dir())
    dashboard_file = dashboards / "Weekly Summary.md"
    
    # Generate content
    content = render_weekly_summary(get_weekly_data())
    
    # Write to tmp file
    tmp_file = dashboard_file.with_suffix('.tmp')
    tmp_file.write_text(content)
    
    # Atomic rename
    tmp_file.rename(dashboard_file)
    
    # Trigger Dataview refresh
    trigger_dataview_refresh(dashboard_file)
    
    print(f"✓ Dashboard generated: {dashboard_file}")
```

---

## Best Practices Summary

✅ **DO:**
- Use path helpers from `config/obsidian_paths.py`
- Create backups before risky operations
- Check timestamps before overwriting
- Log all conflicts and resolutions
- Use advisory locks for critical sections
- Document ownership boundaries clearly

❌ **DON'T:**
- Hardcode absolute paths in code
- Overwrite Obsidian-authoritative content without checking
- Assume Dataview auto-refreshes
- Skip backups for "small" changes
- Ignore file locks (risk of corruption)
- Mix one-way and two-way content in same file

---

## Troubleshooting

### Issue: "VAULT_ROOT not set"

**Solution**: Set environment variable
```bash
export VAULT_ROOT="/Users/yourname/Documents/Obsidian Documents/Red River Sales"
```

### Issue: Dataview not showing updates

**Solution**: Touch the file to force refresh
```python
from pathlib import Path
Path("50 Dashboards/Weekly Summary.md").touch()
```

### Issue: Sync conflicts frequent

**Solution**: Review ownership rules and adjust sync frequency

### Issue: Lock file stale

**Solution**: Remove manually if older than 10 minutes
```bash
rm "80 Reference/.locks/sync.lock"
```

---

## References

- [Obsidian Dataview Plugin](https://blacksmithgu.github.io/obsidian-dataview/)
- [Python pathlib documentation](https://docs.python.org/3/library/pathlib.html)
- [File locking with fcntl](https://docs.python.org/3/library/fcntl.html)