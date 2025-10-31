# Red River → DealCraft Rebrand Remediation Plan

**Date:** October 31, 2025
**Priority:** HIGH (Pre-GA Blocker)
**Estimated Time:** 2-4 hours

---

## Overview

Found **59 files** with "Red River Sales Automation" or "RedRiver" references that need updating to complete the DealCraft rebrand.

---

## File Categories & Actions

### Category 1: Documentation Files (21 files)
**Action:** Find and replace text references

#### "Red River Sales Automation" in Documentation (12 files)
```
integrations/slack_bot.md
docs/sprint_11_plan.md
docs/public/sprint_11_plan.md
docs/public/integrations/slack_bot.md
docs/integrations/slack_bot.md
future features/rfq update/INDEX.txt
future features/rfq update/QUICK_REFERENCE.txt
future features/rfq update/test_config.py
future features/rfq update/setup.sh
future features/rfq update/rfq_filtering_config.py
future features/rfq update/rfq_config.sql
setup.sh
```

**Replace:**
- "Red River Sales Automation" → "DealCraft"
- "DealCraft" → "DealCraft"

#### "red-river-sales-automation" in Documentation (9+ files)
```
ops/hardening_runbook.md
architecture/phase3.md
README.md
docs/releases/v2.0.0.md
CHANGELOG.md
docs/releases/README.md
docs/public/releases/README.md
docs/public/ops/hardening_runbook.md
docs/branch_seed_summary_20251029_1335.md
docs/architecture/phase3.md
docs/README.md
docs/ops/hardening_runbook.md
future features/revamp/kilocode_prompts_2025-10-27_project_setup_scaffolding.md
setup.sh
```

**Replace:**
- "red-river-sales-automation" → "dealcraft"
- Repository references: `routerjoe/red-river-sales-automation` → `routerjoe/DealCraft`

---

### Category 2: Environment & Config Files (3 files)
**Action:** Update comments and example values

#### .env (NOT committed - user's local file)
**Lines to update:**
- Line 101: `# RED_RIVER_BASE_DIR=/Users/you/RedRiver`
- Line 102: `# OBSIDIAN_VAULT_PATH=/Users/you/Documents/RedRiverSales`
- Line 103: `# ATTACHMENTS_DIR=/Users/you/RedRiver/attachments`
- Line 104: `# SQLITE_DB_PATH=/Users/you/RedRiver/data/rfq_tracking.db`
- Line 119: `INTROMAIL_INBOX_DIR=/Users/you/RedRiver/campaigns/inbox`

**Replace:**
- `/RedRiver` → `/DealCraft`
- `RedRiverSales` → `DealCraft`

⚠️ **WARNING:** Don't overwrite user's .env! Update .env.example instead.

#### .env.example
**Update path examples:**
```
# Before:
# OBSIDIAN_VAULT_PATH=/Users/you/Documents/RedRiverSales

# After:
# OBSIDIAN_VAULT_PATH=/Users/you/Documents/DealCraft
```

#### .claude/config.json
Contains "red-river-sales-automation" reference

---

### Category 3: Source Code Files (11 files)
**Action:** Update import paths, variables, and comments

```
src/index.ts
src/utils/env.ts
src/utils/logger.ts
src/tools/intromail/index.ts
src/dev/watch_intromail_inbox.ts
src/dev/create_oem_outlook_draft_eml.ts
tui/app.py
tui/rrtui/rfq_api.py
tui/rrtui/intromail_api.py
scripts/create_oem_draft.applescript
```

**Common replacements:**
- Variable names: `RED_RIVER_*` → `DEALCRAFT_*`
- Path references: `RedRiver` → `DealCraft`
- Comments: "Red River" → "DealCraft"

**Special cases:**
- `tui/rrtui/` directory name: Consider renaming module from `rrtui` → `dctui` (DealCraft TUI)

---

### Category 4: Future Features & Legacy Code (14 files)
**Action:** Update for consistency (lower priority)

```
future features/IntroMail/IntroMail Creation/.env.example
future features/IntroMail/IntroMail Analyzer/.env.example
future features/IntroMail/IntroMail Analyzer/README_INTROMAIL_ANALYZER.md
future features/IntroMail/IntroMail Analyzer/prompts/kilo_intromail_analyzer_prompt.md
future features/IntroMail/IntroMail Analyzer/scripts/watch_inbox.ts
future features/IntroMail/IntroMail Analyzer/src/tools/intromail_analyzer.ts
[others in rfq update/]
```

---

### Category 5: Directory Rename (1 directory)
**Action:** Rename directory and update references

```
red-river-rfq-email-drafts/  →  dealcraft-rfq-email-drafts/
```

**Files in directory:**
```
red-river-rfq-email-drafts/README.md
red-river-rfq-email-drafts/mcp/tools/rfq_draft_email.py
red-river-rfq-email-drafts/sample_rfq.json
red-river-rfq-email-drafts/kilo_prompt_add_rfq_drafts_to_mcp.md
```

**After rename, update:**
- Any import statements referencing the old directory
- Documentation links
- Scripts that reference the path

---

### Category 6: Special Cases

#### TUI Module Rename
**Current:** `tui/rrtui/` (Red River TUI)
**Proposed:** `tui/dctui/` (DealCraft TUI)

**Files to update:**
- `tui/app.py` - import statements
- `tui/README.md` - documentation
- Any other files importing from `rrtui`

#### Email Addresses in .env
**Lines 69, 77:** Email addresses ending with `@redriver.com`

⚠️ **DO NOT CHANGE** - These are real Red River company email addresses for the user's team. The company name is "Red River Technology" - the product is being renamed to "DealCraft" but the company remains Red River.

---

### Category 7: Git-Related Files
**Action:** Review but likely skip

```
.git/FETCH_HEAD
.gitignore
```

- FETCH_HEAD: Auto-generated, will update on next fetch
- .gitignore: Review for any hardcoded paths

---

### Category 8: Checklist Update

**File:** `docs/GO_LIVE_CHECKLIST_v2.0.0.md`
**Line 18:** References "DealCraft vault"

```markdown
# Before:
- [ ] Env: `echo $VAULT_ROOT` points at the **Red River Sales** vault root

# After:
- [ ] Env: `echo $VAULT_ROOT` points at the **DealCraft** vault root
```

---

## Execution Plan

### Phase 1: Documentation (Quick Wins)
**Time:** 30-60 minutes
**Files:** 30+ documentation files

1. Find/replace "Red River Sales Automation" → "DealCraft"
2. Find/replace "red-river-sales-automation" → "dealcraft"
3. Update repository URLs: `routerjoe/red-river-sales-automation` → `routerjoe/DealCraft`
4. Update GO_LIVE_CHECKLIST.md references

**Script approach:**
```bash
# Backup first
git checkout -b rebrand-cleanup

# Replace in docs
find docs/ -type f -name "*.md" -exec sed -i '' 's/Red River Sales Automation/DealCraft/g' {} +
find docs/ -type f -name "*.md" -exec sed -i '' 's/red-river-sales-automation/dealcraft/g' {} +

# Review changes
git diff
```

### Phase 2: Config Files
**Time:** 15-30 minutes
**Files:** .env.example, .claude/config.json

1. Update .env.example path comments
2. Update .claude/config.json
3. **DO NOT** modify user's .env (document required changes instead)

### Phase 3: Source Code
**Time:** 1-2 hours
**Files:** TypeScript, Python source files

1. Review each file individually
2. Update variable names (RED_RIVER_* → DEALCRAFT_*)
3. Update path references
4. Update comments
5. Test after changes

⚠️ **Caution:** Code changes require testing!

### Phase 4: Directory Renames
**Time:** 30 minutes
**Directories:** red-river-rfq-email-drafts/, tui/rrtui/

```bash
# Rename directories
git mv red-river-rfq-email-drafts dealcraft-rfq-email-drafts
git mv tui/rrtui tui/dctui

# Update imports and references
# (Manual review required)
```

### Phase 5: Testing & Validation
**Time:** 30-60 minutes

1. Run server: `./scripts/dev.sh`
2. Test API endpoints
3. Run pytest (fix any import errors)
4. Verify no broken references

### Phase 6: Commit & Document
**Time:** 15 minutes

```bash
git add .
git commit -m "chore: complete DealCraft rebrand - remove remaining Red River references"
git push origin rebrand-cleanup
```

---

## Exclusions (Do NOT Change)

### Company Email Addresses
**Keep as-is:**
- `@redriver.com` email addresses (real company emails)
- Team member names and contact info

### Company Name References
Red River Technology is the company name - only the product is being rebranded to DealCraft.

**Keep:** References to "Red River" as the company
**Change:** References to "Red River Sales Automation" (the old product name)

---

## Risk Assessment

### Low Risk (Safe to automate)
- Documentation files (*.md)
- Comment updates
- .env.example updates

### Medium Risk (Review carefully)
- Variable name changes
- Path references in code
- Directory renames

### High Risk (Manual only)
- Import statement changes
- Module renames
- Database/config migrations

---

## Testing Checklist

After rebrand:
- [ ] Server starts without errors
- [ ] API endpoints respond correctly
- [ ] No broken imports
- [ ] Documentation links work
- [ ] Environment variables load correctly
- [ ] Tests pass (or same failure count as before)

---

## Rollback Plan

```bash
# If issues found:
git checkout main
git branch -D rebrand-cleanup

# All changes reverted
```

---

## Summary

- **Total files:** 59
- **Documentation:** 30+ files (low risk)
- **Config files:** 3 files (medium risk)
- **Source code:** 11 files (high risk)
- **Future features:** 14 files (low priority)
- **Directory renames:** 2 directories (medium risk)

**Recommended approach:** Start with documentation, then config, then source code. Test thoroughly after each phase.

---

**Created:** October 31, 2025
**Status:** Ready for execution
**Requires:** User approval before proceeding
