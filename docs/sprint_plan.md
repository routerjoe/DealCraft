# Sprint 10: Govly/Radar Webhooks & Secrets

**Start:** Wednesday, October 29, 2025 EDT  
**Target Merge Window:** Monday, November 10, 2025 EDT

## Objectives

- Implement secure webhook ingestion for Govly and Radar events
- Add signature validation and replay protection
- Support secret rotation without downtime
- Maintain append-only opportunity tracking in state.json
- Auto-generate minimal Obsidian opportunities with triage flags
- Ensure Federal FY routing for close dates

## Scope (In)

- POST /v1/govly/webhook endpoint (live + dry-run mode)
- POST /v1/radar/webhook endpoint (live + dry-run mode)
- HMAC-SHA256 signature validation
- Secret rotation mechanism (dual-secret support)
- Replay protection via event ID tracking
- Mapping webhook payloads to Obsidian opportunity schema
- Federal FY routing based on close_date
- Environment variable configuration for secrets
- Comprehensive webhook documentation
- Smoke tests with xpass for secret validation when not configured

## Scope (Out)

- Webhook retry logic (handled by webhook provider)
- Rate limiting per webhook source (covered in Sprint 15)
- Historical event backfill
- Real-time Slack notifications for webhook events
- Advanced filtering or transformation rules
- Database storage (using state.json append-only)

## Interfaces & Contracts

### API Endpoints

**POST /v1/govly/webhook**
- Request: GovlyWebhookPayload (JSON)
- Headers: X-Govly-Signature (HMAC-SHA256)
- Response: WebhookResponse (200 OK or 401 Unauthorized)
- Creates: Obsidian opportunity in Triage/ or FYxx/ based on close_date

**POST /v1/radar/webhook**
- Request: RadarWebhookPayload (JSON)
- Headers: X-Radar-Signature (HMAC-SHA256)
- Response: WebhookResponse (200 OK or 401 Unauthorized)
- Creates: Obsidian opportunity in Triage/ or FYxx/ based on contract_date

### MCP Tools

No new MCP tools in this sprint. Existing tools leverage webhook-ingested opportunities:
- `get_forecast` - includes webhook opportunities in projections
- `list_opportunities` - surfaces triaged webhook events

### Files Touched

- `mcp/api/v1/webhooks.py` - Existing implementation (documentation update)
- `docs/webhooks/README.md` - New comprehensive webhook guide
- `docs/sprint_plan.md` - This file
- `.env.example` - Add GOVLY_WEBHOOK_SECRET, RADAR_WEBHOOK_SECRET
- `tests/test_webhooks_smoke.py` - New smoke tests with signature validation
- `data/state.json` - Append-only opportunity storage
- `obsidian/40 Projects/Opportunities/Triage/*.md` - Auto-generated opportunities
- `obsidian/40 Projects/Opportunities/FYxx/*.md` - FY-routed opportunities

## Deliverables

### 1. Code
- ✅ Webhook endpoints already implemented in mcp/api/v1/webhooks.py
- 🆕 Environment variable configuration for secrets
- 🆕 Documentation updates for signature validation
- 🆕 Dry-run mode documentation

### 2. Tests
- ✅ Core webhook tests in tests/test_webhooks.py (16 tests)
- ✅ Smoke tests in tests/test_govly_webhook_smoke.py (4 xfail tests)
- 🆕 tests/test_webhooks_smoke.py - Extended smoke tests with signature validation

### 3. Docs
- 🆕 `/docs/webhooks/README.md` - Comprehensive webhook guide
  - Authentication and signature validation
  - Secret rotation procedures
  - Replay protection mechanisms
  - FY routing logic
  - Dry-run testing instructions
  - Troubleshooting guide
- 🆕 `/docs/sprint_plan.md` - This sprint plan
- Environment variable examples in .env.example

### 4. Ops/Runbooks
- Secret rotation procedure in docs/webhooks/README.md
- Webhook monitoring and debugging guide
- Signature validation troubleshooting

## Success Criteria / DoD

- [ ] All tests passing (existing 20 tests + new smoke tests)
- [ ] Contract checks for x-request-id and x-latency-ms headers
- [ ] Webhook documentation complete with examples
- [ ] .env.example updated with secret placeholders
- [ ] Signature validation documented (even if not enforced initially)
- [ ] Replay protection mechanism documented
- [ ] FY routing logic validated in tests
- [ ] Smoke tests include signature failure scenarios (xpass if secrets unset)
- [ ] PR approved and ready for merge
- [ ] No breaking changes to existing webhook behavior

## Risks & Mitigations

### Risk: Secret Management Complexity
**Impact:** High - Improper secret handling could expose webhook endpoints  
**Probability:** Medium  
**Mitigation:**
- Document clear secret rotation procedures
- Support dual-secret validation during rotation
- Provide environment variable templates
- Include troubleshooting guide for signature failures

### Risk: Replay Attack Vulnerability
**Impact:** Medium - Duplicate event processing  
**Probability:** Low  
**Mitigation:**
- Implement event ID tracking in state.json
- Document replay detection mechanism
- Add timestamp validation for event freshness
- Log and alert on duplicate event IDs

### Risk: Federal FY Routing Errors
**Impact:** Medium - Opportunities in wrong FY folder  
**Probability:** Low  
**Mitigation:**
- Validate FY calculation logic in tests
- Default to Triage/ for invalid/missing dates
- Document FY routing rules clearly
- Include FY boundary test cases

### Risk: Breaking Existing Webhook Functionality
**Impact:** High - Disrupts current integrations  
**Probability:** Low  
**Mitigation:**
- Keep existing implementation unchanged
- Add documentation only for new features
- Maintain backward compatibility
- Test existing webhook flows

## Validation Steps

### 1. Local Testing

```bash
# Run all webhook tests
pytest tests/test_webhooks.py -v
pytest tests/test_govly_webhook_smoke.py -v
pytest tests/test_webhooks_smoke.py -v

# Test webhook endpoints with curl
curl -X POST http://localhost:8000/v1/govly/webhook \
  -H "Content-Type: application/json" \
  -d '{"event_id":"test_123","event_type":"opportunity","title":"Test","estimated_amount":100000}'

# Verify state.json updated
cat data/state.json | jq '.opportunities | last'

# Check Obsidian file created
ls -la obsidian/40\ Projects/Opportunities/Triage/
```

### 2. API Contract Validation

```bash
# Verify response headers
curl -i http://localhost:8000/v1/govly/webhook \
  -X POST -H "Content-Type: application/json" \
  -d '{"event_id":"header_test","title":"Test","estimated_amount":50000}' \
  | grep -E "x-request-id|x-latency-ms"

# Test signature validation (should fail without secret)
curl -X POST http://localhost:8000/v1/govly/webhook \
  -H "Content-Type: application/json" \
  -H "X-Govly-Signature: invalid_signature" \
  -d '{"event_id":"sig_test","title":"Test","estimated_amount":50000}'
```

### 3. Documentation Verification

```bash
# Ensure all docs exist and are readable
cat docs/sprint_plan.md
cat docs/webhooks/README.md
cat .env.example | grep WEBHOOK_SECRET

# Validate markdown formatting
npx markdownlint docs/webhooks/README.md
```

### 4. Integration Testing

- Verify webhook payloads create proper Obsidian opportunities
- Confirm FY routing works for different close dates
- Test triage flag is set correctly
- Validate state.json append-only behavior

## Checklist

- [x] Design reviewed
- [ ] Sprint plan created (docs/sprint_plan.md)
- [ ] Webhook documentation created (docs/webhooks/README.md)
- [ ] Environment variables added to .env.example
- [ ] Smoke tests added (tests/test_webhooks_smoke.py)
- [ ] All tests passing (including xpass for unimplemented features)
- [ ] Documentation complete and reviewed
- [ ] Code committed with message "docs(sprint10): add sprint plan + stubs"
- [ ] Branch pushed to origin
- [ ] Draft PR opened with labels: sprint, 10, seed, draft
- [ ] Ready for development phase

## Notes

- Webhook implementation already exists and is well-tested (20 passing tests)
- This sprint focuses on documentation, security features, and operational procedures
- Signature validation will be documented but not enforced until secrets are configured
- FY routing is already implemented; tests validate the logic
- Dry-run mode support to be documented for testing without side effects

---

**Next Steps After Sprint:**
1. Configure webhook secrets in production environment
2. Enable signature validation in production
3. Set up monitoring for webhook failures
4. Implement webhook retry dashboard (Sprint 15)