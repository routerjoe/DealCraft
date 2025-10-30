# Sprint 13: Obsidian Sync Policies & Conflict Handling

**Start:** Wednesday, October 29, 2025 EDT  
**Target Merge Window:** Monday, November 10, 2025 EDT

## Objectives

- Define sync policies for Obsidian vault integration
- Establish conflict resolution rules
- Document one-way vs two-way sync patterns
- Implement path configuration management
- Ensure Dataview/Base refresh consistency
- Prevent data loss scenarios

## Scope (In)

- Sync policy documentation (one-way, two-way)
- Conflict resolution rules
- Path configuration validation
- Dataview query refresh strategy
- Base markdown update procedures
- File locking mechanisms
- Backup and restore procedures
- Path constants validation tests

## Scope (Out)

- Real-time file system watching
- Automatic conflict resolution (AI-powered)
- Version control integration (git-based)
- Multi-vault synchronization
- Cloud sync integration (Obsidian Sync)
- Mobile app sync support
- Collaborative editing features

## Interfaces & Contracts

### Obsidian Vault Path

**Primary Vault:**
```
/Users/jonolan/Documents/Obsidian Documents/Red River Sales
```

**Directory Structure:**
```
obsidian/
├── 40 Projects/
│   ├── Opportunities/
│   │   ├── FY26/
│   │   ├── FY27/
│   │   └── Triage/
│   └── Accounts/
├── 50 Dashboards/
│   ├── Opportunities Dashboard.md
│   ├── Forecast Dashboard.md
│   └── Account Plans/
└── 60 Projects/
    └── Sprint Summaries/
```

### Configuration Constants

**Location:** `mcp/core/config.py`

```python
# Obsidian vault paths - DO NOT HARDCODE
OBSIDIAN_VAULT_PATH = os.getenv(
    "OBSIDIAN_VAULT_PATH",
    "/Users/jonolan/Documents/Obsidian Documents/Red River Sales"
)

# Relative paths within vault
OPPORTUNITIES_PATH = "40 Projects/Opportunities"
DASHBOARDS_PATH = "50 Dashboards"
TRIAGE_PATH = "40 Projects/Opportunities/Triage"
```

### Sync Policies

**Policy Types:**
1. **One-Way (API → Obsidian):** API writes, manual edits discouraged
2. **Two-Way (API ↔ Obsidian):** Bidirectional sync with conflict detection
3. **Read-Only:** Dashboards generated from API, no manual edits

## Deliverables

### 1. Documentation
- 🆕 `/docs/sprint_plan.md` - This sprint plan
- 🆕 `/docs/obsidian/sync_policies.md` - Complete sync policy guide
  - One-way vs two-way sync patterns
  - Conflict detection and resolution
  - File locking strategies
  - Backup/restore procedures
  - Dataview refresh guidelines

### 2. Tests
- 🆕 `tests/test_obsidian_paths_config.py` - Path validation tests
  - Verify no hardcoded paths in code
  - Ensure environment variable usage
  - Validate path constants in config
  - Check relative path construction

### 3. Configuration
- Validate `mcp/core/config.py` path management
- Document environment variables
- Provide `.env.example` updates

## Success Criteria / DoD

- [ ] Sprint plan created (docs/sprint_plan.md)
- [ ] Sync policies documented (docs/obsidian/sync_policies.md)
- [ ] Path validation tests created (tests/test_obsidian_paths_config.py)
- [ ] All tests passing (no hardcoded paths detected)
- [ ] Environment variables documented
- [ ] Conflict resolution rules clearly defined
- [ ] Backup procedures documented
- [ ] Code committed with message "docs(sprint13): add sprint plan + stubs"
- [ ] Branch pushed to origin
- [ ] Draft PR opened with labels: sprint, 13, seed, draft

## Risks & Mitigations

### Risk: Data Loss from Sync Conflicts
**Impact:** Critical - Lost opportunity data  
**Probability:** Medium  
**Mitigation:**
- Implement file-level locking
- Automatic backups before writes
- Conflict detection with manual resolution
- Read-only Dataview dashboards
- Document conflict scenarios

### Risk: Path Configuration Errors
**Impact:** High - Files written to wrong locations  
**Probability:** Low  
**Mitigation:**
- Centralized path configuration
- Environment variable validation
- Path construction helpers
- Tests for hardcoded paths
- Relative path usage

### Risk: Dataview Query Staleness
**Impact:** Medium - Dashboard shows outdated data  
**Probability:** Medium  
**Mitigation:**
- Document refresh patterns
- Timestamp all generated files
- Clear cache mechanisms
- Scheduled dashboard regeneration
- Manual refresh procedures

### Risk: Concurrent Access Issues
**Impact:** Medium - Race conditions during writes  
**Probability:** Low  
**Mitigation:**
- File-level locking
- Atomic writes (temp file + rename)
- Retry logic with exponential backoff
- Queue-based write operations
- Log concurrent access attempts

## Validation Steps

### 1. Path Configuration Tests

```bash
# Run path validation tests
pytest tests/test_obsidian_paths_config.py -v

# Should verify:
# - No hardcoded home paths (/Users/jonolan)
# - All paths use config constants
# - Environment variables respected
```

### 2. Documentation Review

```bash
# Verify documentation exists
cat docs/sprint_plan.md
cat docs/obsidian/sync_policies.md

# Check for complete coverage:
# - One-way sync
# - Two-way sync
# - Conflict scenarios
# - Backup procedures
```

### 3. Configuration Validation

```bash
# Check config file
grep -n "OBSIDIAN" mcp/core/config.py

# Verify environment variable usage
grep -r "/Users/jonolan" mcp/  # Should find no hardcoded paths in code
```

## Checklist

- [x] Design reviewed
- [ ] Sprint plan created (docs/sprint_plan.md)
- [ ] Sync policies documented (docs/obsidian/sync_policies.md)
- [ ] Path validation tests created (tests/test_obsidian_paths_config.py)
- [ ] All tests passing
- [ ] No hardcoded paths in code
- [ ] Environment variables documented
- [ ] Documentation complete and reviewed
- [ ] Code committed with message "docs(sprint13): add sprint plan + stubs"
- [ ] Branch pushed to origin
- [ ] Draft PR opened with labels: sprint, 13, seed, draft
- [ ] Ready for development phase

## Notes

- Obsidian vault path should always come from environment variable
- Use relative paths within vault for flexibility
- One-way sync (API → Obsidian) is default for opportunities
- Dashboards are always one-way (API → Obsidian, read-only)
- Two-way sync requires conflict detection (future sprint)
- Manual edits to opportunities should trigger warnings
- Dataview queries are cached by Obsidian, refresh manually or restart

---

**Next Steps After Sprint:**
1. Implement file-level locking for concurrent writes
2. Add automatic backup before overwrites
3. Create conflict detection for two-way sync
4. Build dashboard auto-refresh scheduler
5. Add validation hooks for manual edits