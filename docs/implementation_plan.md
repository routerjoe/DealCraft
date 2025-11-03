# DealCraft Implementation Plan
## Entity Edit + Govly Integration + Watcher Automation

**Created:** 2025-11-02
**Status:** In Progress
**Priority:** High Business Value

---

## Overview

This plan covers three critical feature sets that complete the DealCraft automation platform:

- **Track A:** Entity Edit Functionality (Immediate usability boost)
- **Track B:** Govly API Integration (High business value - proactive opportunity capture)
- **Track C:** Watcher Automation (Background services for email monitoring, note sync, contract monitoring)

---

## Track A: Entity Edit Functionality

### Goal
Add edit capability to Entity Management screen, allowing users to modify existing entities (OEMs, CVs, Customers, Partners, Distributors, Regions).

### Tasks

#### A1: Create EditEntityModal Component
**Status:** Pending
**Priority:** High
**Complexity:** Medium
**Dependencies:** None

**Implementation:**
- Create `EditEntityModal` class in `tui/dctui/entity_management_view.py`
- Similar structure to `AddEntityModal` but pre-populate fields with existing entity data
- Support all 6 entity types with appropriate forms
- Add validation for required fields

**Acceptance Criteria:**
- [ ] Modal opens with current entity data pre-filled
- [ ] Form validation works for all entity types
- [ ] Cancel button returns to entity list without changes
- [ ] Save button validates and updates entity

**Files to Modify:**
- `tui/dctui/entity_management_view.py`

**Implementation Notes:**
```python
class EditEntityModal(ModalScreen):
    def __init__(self, entity_type: str, entity_data: dict):
        super().__init__()
        self.entity_type = entity_type
        self.entity_data = entity_data  # Current entity to edit

    def compose(self) -> ComposeResult:
        # Similar to AddEntityModal but pre-populate inputs
        # with self.entity_data values
```

---

#### A2: Add Edit Button to EntityManagementScreen
**Status:** Pending
**Priority:** High
**Complexity:** Low
**Dependencies:** A1

**Implementation:**
- Add "e" keybinding for edit action
- Add edit button to actions panel
- Implement `action_edit_entity()` method
- Get selected entity from table
- Launch `EditEntityModal` with entity data
- Handle modal result and refresh table

**Acceptance Criteria:**
- [ ] "e" key opens edit modal for selected entity
- [ ] Edit action requires entity selection (shows warning if none)
- [ ] Successfully edited entity updates in store
- [ ] Table refreshes to show updated data

**Files to Modify:**
- `tui/dctui/entity_management_view.py`

**Implementation Notes:**
```python
BINDINGS = [
    # ... existing bindings
    ("e", "edit_entity", "Edit"),
]

async def action_edit_entity(self) -> None:
    try:
        row = self.table.cursor_row
        if row is None:
            self._update_status("⚠ Select an entity first", "yellow")
            return

        # Get entity data from current selection
        entity_id = self.table.get_row(row)[0]
        entity = self._get_entity_by_id(entity_id)

        result = await self.app.push_screen_wait(
            EditEntityModal(self.current_entity_type, entity.model_dump())
        )

        if result and result.get("success"):
            self._update_status(f"✓ Updated {entity.name}", "green")
            await self._load_entities()
    except Exception as e:
        self._update_status(f"❌ Edit failed: {e}", "red")
```

---

#### A3: Implement Store Update Methods
**Status:** Pending
**Priority:** High
**Complexity:** Low
**Dependencies:** None

**Implementation:**
- Add `update()` method to each entity store (OEMStore, CVStore, etc.)
- Ensure atomic updates (load, modify, save)
- Add validation before update
- Return success/failure status

**Acceptance Criteria:**
- [ ] Update method exists for all store types
- [ ] Updates are atomic (no race conditions)
- [ ] Validation prevents invalid updates
- [ ] Store files saved with proper formatting

**Files to Modify:**
- `mcp/core/entities.py`

**Implementation Notes:**
```python
def update(self, entity: OEM) -> bool:
    """Update an existing OEM in the store."""
    if entity.id not in self._entities:
        return False

    # Validate entity
    if not entity.name or not entity.id:
        return False

    # Update entity
    self._entities[entity.id] = entity
    self._save()
    return True
```

---

#### A4: Add Update Confirmation
**Status:** Pending
**Priority:** Medium
**Complexity:** Low
**Dependencies:** A1, A2

**Implementation:**
- Show success toast after edit
- Display what changed (optional)
- Handle update failures gracefully

**Acceptance Criteria:**
- [ ] Success message shows entity name
- [ ] Failure shows clear error message
- [ ] Status bar updates appropriately

---

### Track A Summary

**Total Tasks:** 4
**Estimated Complexity:** Medium
**Estimated Time:** 2-3 hours
**Business Value:** High (immediate usability improvement)

---

## Track B: Govly API Integration

### Goal
Implement proactive fetching of opportunities from Govly.com API to complement webhook-based ingestion.

### Research Phase

#### B0: Research Govly API
**Status:** Pending
**Priority:** Critical
**Complexity:** Low
**Dependencies:** None

**Research Tasks:**
- [ ] Find Govly API documentation
- [ ] Identify authentication method (API key, OAuth, etc.)
- [ ] Document available endpoints
- [ ] Understand rate limits
- [ ] Identify data model/schema
- [ ] Check if API supports filters (date range, agencies, amounts)

**Deliverable:** API research document with:
- Authentication requirements
- Endpoint URLs and methods
- Request/response schemas
- Rate limits and pagination
- Example curl commands

---

### Implementation Phase

#### B1: Create Govly API Client
**Status:** Pending
**Priority:** High
**Complexity:** Medium
**Dependencies:** B0

**Implementation:**
- Create `mcp/integrations/govly_client.py`
- Implement authentication handling
- Create methods for fetching opportunities
- Add error handling and retries
- Support pagination
- Add logging for debugging

**Acceptance Criteria:**
- [ ] Client authenticates successfully
- [ ] Can fetch opportunities with filters
- [ ] Handles rate limits gracefully
- [ ] Returns standardized data format
- [ ] Logs all API calls

**Files to Create:**
- `mcp/integrations/govly_client.py`

**Implementation Notes:**
```python
class GovlyClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.govly.com/v1"  # TBD from research
        self.session = requests.Session()

    def fetch_opportunities(
        self,
        limit: int = 100,
        since: datetime = None,
        agencies: List[str] = None
    ) -> List[Dict]:
        """Fetch opportunities from Govly API."""
        # Implementation based on API research
```

---

#### B2: Add Configuration for API Keys
**Status:** Pending
**Priority:** High
**Complexity:** Low
**Dependencies:** None

**Implementation:**
- Add Govly API key to `.env`
- Add config validation
- Document setup in README

**Acceptance Criteria:**
- [ ] API key loaded from environment
- [ ] Config validation warns if missing
- [ ] Setup documented

**Files to Modify:**
- `.env.example`
- `config/config_loader.py`
- `README.md`

**Environment Variables:**
```bash
# Govly API Integration
GOVLY_API_KEY=your_api_key_here
GOVLY_BASE_URL=https://api.govly.com/v1  # Optional override
```

---

#### B3: Create Govly Sync Service
**Status:** Pending
**Priority:** High
**Complexity:** Medium
**Dependencies:** B1, B2

**Implementation:**
- Create `mcp/services/govly_sync.py`
- Implement scheduled polling (every N minutes)
- Deduplicate opportunities (check state.json)
- Merge with webhook-ingested data
- Add fiscal year routing
- Log sync results

**Acceptance Criteria:**
- [ ] Service runs on schedule
- [ ] No duplicate opportunities created
- [ ] New opportunities added to state.json
- [ ] Sync status visible in TUI
- [ ] Errors logged and reported

**Files to Create:**
- `mcp/services/govly_sync.py`

**Implementation Notes:**
```python
class GovlySync:
    def __init__(self, client: GovlyClient, state_file: Path):
        self.client = client
        self.state_file = state_file
        self.sync_interval = 300  # 5 minutes

    def run(self):
        """Run continuous sync loop."""
        while True:
            try:
                self._sync_opportunities()
                time.sleep(self.sync_interval)
            except Exception as e:
                logger.error(f"Govly sync failed: {e}")

    def _sync_opportunities(self):
        """Fetch new opportunities and merge into state."""
        # Load current state
        state = self._load_state()
        existing_ids = {opp["id"] for opp in state.get("opportunities", [])}

        # Fetch new opportunities
        new_opps = self.client.fetch_opportunities(since=self._last_sync_time())

        # Filter out duplicates
        unique_opps = [opp for opp in new_opps if opp["id"] not in existing_ids]

        # Add to state
        if unique_opps:
            state.setdefault("opportunities", []).extend(unique_opps)
            self._save_state(state)
            logger.info(f"Added {len(unique_opps)} new Govly opportunities")
```

---

#### B4: Integrate with Status Bridge
**Status:** Pending
**Priority:** Medium
**Complexity:** Low
**Dependencies:** B3

**Implementation:**
- Add Govly sync status to `status_bridge.py`
- Report online/offline status
- Report last sync time
- Report error states

**Acceptance Criteria:**
- [ ] TUI shows Govly Sync status as "online" when running
- [ ] Last sync time displayed
- [ ] Errors show as "error" state

**Files to Modify:**
- `mcp/status_bridge.py`
- `tui/dctui/app.py`

---

#### B5: Add Manual Sync Button to TUI
**Status:** Pending
**Priority:** Low
**Complexity:** Low
**Dependencies:** B3

**Implementation:**
- Add "Sync Now" button to Govly viewer
- Trigger manual sync on demand
- Show sync progress

**Acceptance Criteria:**
- [ ] Button triggers immediate sync
- [ ] Progress shown in status bar
- [ ] Table refreshes after sync

**Files to Modify:**
- `tui/dctui/govly_view.py`

---

### Track B Summary

**Total Tasks:** 6 (1 research + 5 implementation)
**Estimated Complexity:** High
**Estimated Time:** 6-8 hours
**Business Value:** Very High (proactive opportunity capture)

**Dependencies:**
- Govly API access/documentation
- API key or credentials

---

## Track C: Watcher Automation

### Goal
Wire up background watcher services for automated email monitoring, note sync, and contract monitoring.

### C1: Outlook RFQ Watcher

#### C1.1: Research Outlook Integration
**Status:** Pending
**Priority:** High
**Complexity:** Low
**Dependencies:** None

**Research Tasks:**
- [ ] Confirm AppleScript/pywin32 approach for Outlook
- [ ] Test folder monitoring capabilities
- [ ] Identify optimal polling interval
- [ ] Document Outlook permissions needed

---

#### C1.2: Implement Outlook Email Watcher
**Status:** Pending
**Priority:** High
**Complexity:** High
**Dependencies:** C1.1

**Implementation:**
- Create `mcp/watchers/outlook_rfq_watcher.py`
- Monitor specific Outlook folder (RFQ inbox)
- Detect new emails
- Download attachments
- Trigger RFQ processing pipeline
- Update watcher status

**Acceptance Criteria:**
- [ ] Detects new emails within 30 seconds
- [ ] Downloads all attachments
- [ ] Triggers processing automatically
- [ ] Status shows "online" in TUI
- [ ] Errors logged and reported

**Files to Create:**
- `mcp/watchers/outlook_rfq_watcher.py`

**Implementation Notes:**
```python
class OutlookRFQWatcher:
    def __init__(self, folder_name: str = "RFQ Inbox"):
        self.folder_name = folder_name
        self.last_check = datetime.now()
        self.poll_interval = 30  # seconds

    def run(self):
        """Run continuous monitoring loop."""
        while True:
            try:
                self._check_for_new_emails()
                time.sleep(self.poll_interval)
            except Exception as e:
                logger.error(f"Outlook watcher failed: {e}")

    def _check_for_new_emails(self):
        """Check for new emails and process them."""
        # Use AppleScript or pywin32 to access Outlook
        # Get emails received after last_check
        # For each new email:
        #   - Download attachments
        #   - Call RFQ processing pipeline
        #   - Update last_check
```

---

#### C1.3: Add Outlook Watcher Configuration
**Status:** Pending
**Priority:** Medium
**Complexity:** Low
**Dependencies:** None

**Implementation:**
- Add Outlook folder config to settings
- Add polling interval config
- Document setup

**Acceptance Criteria:**
- [ ] Folder name configurable
- [ ] Poll interval configurable
- [ ] Auto-start configurable

**Files to Modify:**
- `tui/config/settings.yaml`
- `config/config_loader.py`

**Configuration:**
```yaml
watchers:
  outlook_rfq:
    enabled: true
    folder: "RFQ Inbox"
    poll_interval: 30  # seconds
    auto_start: true
```

---

### C2: Fleeting Notes Sync

#### C2.1: Implement Fleeting Notes File Watcher
**Status:** Pending
**Priority:** Medium
**Complexity:** Medium
**Dependencies:** None

**Implementation:**
- Create `mcp/watchers/fleeting_notes_watcher.py`
- Monitor Obsidian vault folder for new notes
- Parse note metadata
- Create opportunities or tasks from notes
- Update watcher status

**Acceptance Criteria:**
- [ ] Detects new/modified notes within 10 seconds
- [ ] Parses frontmatter metadata
- [ ] Creates opportunities from tagged notes
- [ ] Status shows "online" in TUI

**Files to Create:**
- `mcp/watchers/fleeting_notes_watcher.py`

**Implementation Notes:**
```python
class FleetingNotesWatcher:
    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.observer = Observer()  # From watchdog library

    def run(self):
        """Start file system monitoring."""
        event_handler = FleetingNotesHandler(self)
        self.observer.schedule(event_handler, str(self.vault_path), recursive=True)
        self.observer.start()

    def on_note_created(self, note_path: Path):
        """Handle new note creation."""
        # Parse frontmatter
        # If tagged with #rfq or #opportunity:
        #   - Extract metadata
        #   - Create opportunity in state.json
```

---

#### C2.2: Add Fleeting Notes Configuration
**Status:** Pending
**Priority:** Low
**Complexity:** Low
**Dependencies:** None

**Implementation:**
- Add vault path to config
- Add tags to monitor
- Document Obsidian plugin setup

**Acceptance Criteria:**
- [ ] Vault path configurable
- [ ] Tags configurable
- [ ] Setup documented

**Configuration:**
```yaml
watchers:
  fleeting_notes:
    enabled: true
    vault_path: "/Users/jonolan/Documents/ObsidianVault"
    watch_tags: ["#rfq", "#opportunity", "#contract"]
```

---

### C3: Radar Contract Monitoring

#### C3.1: Research Radar Integration
**Status:** Pending
**Priority:** Medium
**Complexity:** Low
**Dependencies:** None

**Research Tasks:**
- [ ] Find Radar API documentation or webhook format
- [ ] Identify contract monitoring triggers
- [ ] Document notification format

---

#### C3.2: Implement Radar Monitoring Service
**Status:** Pending
**Priority:** Medium
**Complexity:** Medium
**Dependencies:** C3.1

**Implementation:**
- Create `mcp/watchers/radar_watcher.py`
- Monitor contracts for status changes
- Send notifications for critical events
- Update watcher status

**Acceptance Criteria:**
- [ ] Detects contract updates
- [ ] Sends notifications for important changes
- [ ] Status shows "online" in TUI

**Files to Create:**
- `mcp/watchers/radar_watcher.py`

---

### C4: Service Orchestration

#### C4.1: Create Service Manager
**Status:** Pending
**Priority:** High
**Complexity:** Medium
**Dependencies:** C1.2, C2.1, C3.2

**Implementation:**
- Create `mcp/services/service_manager.py`
- Start/stop all watchers
- Monitor service health
- Restart failed services
- Report status to status_bridge

**Acceptance Criteria:**
- [ ] All watchers start on system startup
- [ ] Failed watchers auto-restart
- [ ] Status reported to TUI
- [ ] Graceful shutdown

**Files to Create:**
- `mcp/services/service_manager.py`

**Implementation Notes:**
```python
class ServiceManager:
    def __init__(self):
        self.services = []
        self.running = False

    def register_service(self, service):
        """Register a service for management."""
        self.services.append(service)

    def start_all(self):
        """Start all registered services."""
        for service in self.services:
            if service.config.get("enabled"):
                service.start()

    def stop_all(self):
        """Stop all services gracefully."""
        for service in self.services:
            service.stop()

    def health_check(self):
        """Check health of all services."""
        return {
            service.name: service.status()
            for service in self.services
        }
```

---

#### C4.2: Add Service Controls to TUI
**Status:** Pending
**Priority:** Low
**Complexity:** Low
**Dependencies:** C4.1

**Implementation:**
- Add service start/stop buttons to dashboard
- Show service status in real-time
- Allow individual service restart

**Acceptance Criteria:**
- [ ] Can start/stop individual services
- [ ] Status updates in real-time
- [ ] Error states clearly visible

**Files to Modify:**
- `tui/dctui/app.py`

---

### Track C Summary

**Total Tasks:** 10 (3 research + 7 implementation)
**Estimated Complexity:** Very High
**Estimated Time:** 10-12 hours
**Business Value:** Very High (full automation)

**Dependencies:**
- Outlook access and permissions
- Obsidian vault setup
- Radar API/webhook access

---

## Implementation Order

### Phase 1: Quick Wins (Day 1)
1. **A1-A4:** Complete Entity Edit functionality (2-3 hours)
   - Immediate usability improvement
   - Low risk, high user satisfaction

### Phase 2: High-Value Features (Days 2-3)
2. **B0-B2:** Govly API research and client (4-5 hours)
   - Research API and implement client
   - High business value

3. **B3-B5:** Govly sync service and TUI integration (2-3 hours)
   - Complete Govly proactive fetching
   - Major feature completion

### Phase 3: Automation Infrastructure (Days 4-5)
4. **C1.1-C1.3:** Outlook RFQ watcher (4-5 hours)
   - Most critical watcher
   - Highest automation value

5. **C2.1-C2.2:** Fleeting Notes sync (2-3 hours)
   - Secondary watcher
   - Nice-to-have feature

### Phase 4: Complete Automation (Days 6-7)
6. **C3.1-C3.2:** Radar monitoring (3-4 hours)
   - Contract monitoring
   - Completes Radar feature

7. **C4.1-C4.2:** Service orchestration (3-4 hours)
   - Unified service management
   - Production-ready automation

---

## Risk Assessment

### High Risk
- **Govly API Access:** May not have API or requires paid plan
  - **Mitigation:** Verify API access before starting Track B
- **Outlook Integration:** Platform-specific (Mac vs Windows)
  - **Mitigation:** Test on target platform early

### Medium Risk
- **Service Reliability:** Background services may crash
  - **Mitigation:** Implement auto-restart and health checks
- **Rate Limits:** External APIs may have strict limits
  - **Mitigation:** Implement exponential backoff and caching

### Low Risk
- **Entity Edit:** Straightforward CRUD operation
- **Configuration:** Well-understood pattern

---

## Success Metrics

### Track A Success
- [ ] Users can edit all entity types from TUI
- [ ] Edit success rate > 99%
- [ ] No data corruption from edits

### Track B Success
- [ ] Govly opportunities fetched every 5 minutes
- [ ] Zero duplicate opportunities
- [ ] > 95% uptime for sync service

### Track C Success
- [ ] All watchers running with > 95% uptime
- [ ] New RFQ emails processed within 1 minute
- [ ] Zero missed opportunities

---

## Testing Strategy

### Unit Tests
- Entity store update methods
- Govly API client
- Service manager

### Integration Tests
- Full RFQ workflow with watcher
- Govly sync with state.json
- Service restart after failure

### Manual Testing
- Entity edit for all types
- Govly sync with real data
- Outlook watcher with test emails
- Service controls in TUI

---

## Documentation Updates

### User Documentation
- [ ] Entity Management guide with edit instructions
- [ ] Govly setup guide (API key configuration)
- [ ] Watcher configuration guide
- [ ] Service management guide

### Developer Documentation
- [ ] API client architecture
- [ ] Service manager design
- [ ] Watcher development guide

---

## Progress Tracking

This document will be updated as tasks are completed. Use the following format for updates:

```markdown
**[YYYY-MM-DD HH:MM]** Task A1 completed - EditEntityModal implemented
**[YYYY-MM-DD HH:MM]** Task B0 blocked - Waiting for Govly API credentials
```

### Track A Progress

**[2025-11-02 13:45]** ✅ **Track A Complete: Entity Edit Functionality**
- A1: ✅ EditEntityModal component created with all 6 entity type forms
- A2: ✅ Edit button [e] and keybinding added to EntityManagementScreen
- A3: ✅ Store update methods already existed in EntityStore base class
- A4: ✅ Update confirmation via status bar implemented

**Total Time:** ~1 hour (faster than estimated 2-3 hours)
**Status:** All acceptance criteria met

---

## Notes and Decisions

### 2025-11-02
- Created initial implementation plan
- Prioritized Entity Edit (Track A) for immediate completion
- Govly API research (B0) required before Track B implementation
- Service orchestration (C4) depends on individual watchers

**13:45** - Track A completed ahead of schedule. Entity edit functionality fully working:
  - All 6 entity types supported (OEMs, CVs, Customers, Partners, Distributors, Regions)
  - ID field is read-only during edit
  - Entity active status is preserved
  - Success/error messages via status bar
  - Table refreshes after successful edit

**Next:** Beginning Track B - Govly API Integration research

**14:30** - Track B research completed. **BLOCKED** - Govly API is enterprise-only:
  - ✅ Webhook integration already complete and working
  - ❌ API requires Govly enterprise customer account
  - ❌ API endpoints not publicly documented
  - ❌ Must contact support@govly.com for access
  - 📄 Full research documented in `/docs/govly_api_research.md`

**Alternative:** SAM.gov public API available as free alternative

**Decision:** Pivot to Track C (Watcher Automation) - no external dependencies

**Next:** Beginning Track C - Watcher Automation

**15:00** - Track B completed! User has Govly API key:
  - ✅ B1: Govly API client created (`mcp/integrations/govly_client.py`)
  - ✅ B2: API key already configured in `.env` file
  - ✅ B3: Govly sync service created (`mcp/services/govly_sync.py`)
  - ✅ B4: Integrated with status bridge (shows in TUI dashboard)
  - ✅ B5: Manual sync button added to Govly viewer ([s] key)

**Features:**
  - Periodic polling every 5 minutes (configurable)
  - Deduplication with webhook data
  - Federal FY routing
  - Background threading
  - Rate limit handling
  - Error recovery
  - Status reporting in TUI

**Usage:** Service auto-starts when configured. Manual sync via [s] key in Govly view.

**Next:** Track C skipped (Outlook watcher makes email unusable per user)

---

## Appendix: File Structure

```
DealCraft/
├── mcp/
│   ├── core/
│   │   └── entities.py (modify: add update methods)
│   ├── integrations/
│   │   └── govly_client.py (create)
│   ├── services/
│   │   ├── govly_sync.py (create)
│   │   └── service_manager.py (create)
│   ├── watchers/
│   │   ├── outlook_rfq_watcher.py (create)
│   │   ├── fleeting_notes_watcher.py (create)
│   │   └── radar_watcher.py (create)
│   └── status_bridge.py (modify)
├── tui/
│   ├── config/
│   │   └── settings.yaml (modify)
│   └── dctui/
│       ├── app.py (modify)
│       ├── entity_management_view.py (modify)
│       └── govly_view.py (modify)
├── config/
│   └── config_loader.py (modify)
├── .env.example (modify)
└── docs/
    └── implementation_plan.md (this file)
```
