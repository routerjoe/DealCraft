# Sprint Plans Index

**Project:** DealCraft  
**Sprint Cycle:** Sprints 10-15  
**Date Range:** October 29 - November 10, 2025 EDT

## Overview

This document provides an index of all sprint plans for the DealCraft project. Each sprint has a dedicated plan document containing objectives, scope, deliverables, success criteria, risks, and validation steps.

## Active Sprints

### Sprint 10: Govly/Radar Webhooks & Secrets
**Branch:** `feature/sprint10-webhooks`  
**Plan:** [docs/sprint_plan.md](../feature/sprint10-webhooks/docs/sprint_plan.md)  
**Focus:** Webhook ingestion, signature validation, secret rotation, replay protection

**Key Deliverables:**
- POST /v1/govly/webhook (live + dry-run)
- POST /v1/radar/webhook (live + dry-run)
- Signature validation & secret rotation
- Replay protection mechanisms
- Mapping to Obsidian opportunities with FY routing

---

### Sprint 11: Slack Bot + MCP Bridge
**Branch:** `feature/sprint11-slack-bot`  
**Plan:** [docs/sprint_plan.md](../feature/sprint11-slack-bot/docs/sprint_plan.md)  
**Focus:** Slack integration, slash commands, MCP bridge

**Key Deliverables:**
- Slash commands: `/rr forecast top`, `/rr cv recommend`, `/rr recent`
- Permission model and authorization
- Command parsing and queue management
- Dry-run testing capability

---

### Sprint 12: AI Account Plans
**Branch:** `feature/sprint12-ai-account-plans`  
**Plan:** [docs/sprint_plan.md](../feature/sprint12-ai-account-plans/docs/sprint_plan.md)  
**Focus:** AI-generated account plans for AGENCY-ALPHA/AGENCY-BRAVO with OEM partners

**Key Deliverables:**
- POST /v1/account-plans/generate
- GET /v1/account-plans/formats
- Account plan reasoning engine
- Obsidian export under 50 Dashboards
- Support for Cisco, Nutanix, NetApp, Red Hat

---

### Sprint 13: Obsidian Sync Policies
**Branch:** `feature/sprint13-obsidian-sync`  
**Plan:** [docs/sprint_plan.md](../feature/sprint13-obsidian-sync/docs/sprint_plan.md)  
**Focus:** Sync policies, conflict handling, Dataview refresh

**Key Deliverables:**
- One-way vs two-way sync policies
- Conflict resolution rules
- Dataview/Base refresh notes
- Path configuration management
- Vault path: `/Users/jonolan/Documents/Obsidian Documents/Red River Sales`

---

### Sprint 14: ML Refinement (Forecast v2.1)
**Branch:** `feature/sprint14-ml-refinement`  
**Plan:** [docs/sprint_plan.md](../feature/sprint14-ml-refinement/docs/sprint_plan.md)  
**Focus:** Scoring model improvements, feature store, offline evaluation

**Key Deliverables:**
- Scoring Model v2.1 with region/org/CV bonuses
- Feature store implementation
- Offline evaluation framework
- Guardrails and thresholds
- Audit trail for scoring decisions

---

### Sprint 15: Production Hardening
**Branch:** `feature/sprint15-hardening`  
**Plan:** [docs/sprint_plan.md](../feature/sprint15-hardening/docs/sprint_plan.md)  
**Focus:** Auth, rate limiting, SLOs, production readiness

**Key Deliverables:**
- Rate limiting policies
- Request header validation (x-request-id, x-latency-ms)
- Log redaction for sensitive data
- Backup/restore procedures
- SLOs and SLIs definition
- Production runbook

---

## Sprint Structure

Each sprint plan follows a consistent structure:

1. **Objectives** - High-level goals for the sprint
2. **Scope (In/Out)** - Clear boundaries of what's included and excluded
3. **Interfaces & Contracts** - API endpoints, MCP tools, file paths
4. **Deliverables** - Code, tests, docs, and operational artifacts
5. **Success Criteria / Federal Department A** - Definition of Done with measurable criteria
6. **Risks & Mitigations** - Known risks and mitigation strategies
7. **Validation Steps** - Local, API, TUI/MCP, and documentation checks
8. **Checklist** - Sprint execution tracking

## Common Standards

### Testing Requirements
- All tests must pass (xpass allowed for not-yet-implemented features)
- Contract checks for x-request-id and x-latency-ms headers
- Smoke tests for new endpoints
- Integration tests for cross-component features

### Documentation Requirements
- API endpoint documentation in /docs
- Integration guides for external services
- Operational runbooks for production features
- Architecture decision records (ADRs) for significant changes

### Code Quality
- Linting with ruff
- Type hints for Python code
- Error handling and logging
- Feature flags for experimental features

## Sprint Timeline

**Start Date:** Wednesday, October 29, 2025 EDT  
**Target Merge Window:** Monday, November 10, 2025 EDT  
**Sprint Duration:** 12 days

## Release Process

1. **Seed Phase** (Day 1): Create sprint plan + minimal stubs
2. **Development Phase** (Days 2-8): Implementation and testing
3. **Review Phase** (Days 9-10): Code review and QA
4. **Merge Phase** (Day 11): Final approval and merge to main
5. **Tag Phase** (Day 12): Create release tag if applicable

## Branch Naming Convention

All sprint branches follow the pattern: `feature/sprint<N>-<description>`

Example: `feature/sprint10-webhooks`

## PR Labels

When opening PRs, use the following labels:
- `sprint` - Indicates sprint-related work
- `<N>` - Sprint number (e.g., `10`, `11`, etc.)
- `seed` - Initial seeding PR with stubs
- `draft` - Draft PR (work in progress)
- `ready-for-review` - Ready for code review

## Contact & Support

For questions about sprint plans or implementation details:
- Review the individual sprint plan documents
- Check the [RUNBOOK.md](../RUNBOOK.md) for operational procedures
- Consult the [architecture documentation](architecture/README.md)

---

**Last Updated:** October 29, 2025 EDT  
**Maintained By:** Development Team