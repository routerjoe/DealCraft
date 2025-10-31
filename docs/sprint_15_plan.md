# Sprint 15: Production Hardening

**Start:** Wednesday, October 29, 2025 EDT  
**Target Merge Window:** Monday, November 10, 2025 EDT

## Objectives

- Implement production-ready security controls
- Add rate limiting to prevent abuse
- Validate header contracts across all endpoints
- Implement log redaction for sensitive data
- Define SLOs and SLIs for system health
- Create operational runbooks
- Ensure 99.9% uptime readiness

## Scope (In)

- Rate limiting policies (per-IP, per-endpoint)
- Header validation (x-request-id, x-latency-ms)
- Log redaction for PII and secrets
- Backup and restore procedures
- SLO/SLI definitions
- Production runbook
- Health check enhancements
- Error response standardization
- Security header tests
- Rate limit stub tests (xpass)

## Scope (Out)

- WAF (Web Application Firewall) deployment
- DDoS protection (handled at infrastructure level)
- SSL/TLS certificate management
- Database connection pooling
- Load balancer configuration
- Kubernetes orchestration
- Multi-region deployment
- Advanced authentication (OAuth, SAML)

## Interfaces & Contracts

### Required Response Headers

All API responses MUST include:
```
X-Request-ID: <uuid>
X-Latency-MS: <integer>
```

### Rate Limiting

**Policies:**
```python
RATE_LIMIT_POLICIES = {
    "default": {"requests": 100, "window": 60},  # 100 req/min
    "webhook": {"requests": 1000, "window": 60},  # 1000 req/min
    "ai": {"requests": 20, "window": 60},  # 20 req/min (expensive)
    "export": {"requests": 10, "window": 60},  # 10 req/min (large payloads)
}
```

**Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: ***-***-****
```

### SLOs (Service Level Objectives)

**Availability:** 99.9% uptime (43 minutes/month downtime budget)  
**Latency:** P95 < 100ms, P99 < 500ms  
**Error Rate:** < 0.1% of requests  
**Data Durability:** 99.99% (no data loss)

### SLIs (Service Level Indicators)

**Monitored Metrics:**
- Request success rate (2xx responses / total)
- Response latency (p50, p95, p99)
- Error rate by endpoint
- Rate limit violations
- System resource usage (CPU, memory)

## Deliverables

### 1. Documentation
- 🆕 `/docs/sprint_plan.md` - This sprint plan
- 🆕 `/docs/ops/hardening_runbook.md` - Production runbook
  - Rate limiting policies
  - Header validation requirements
  - Log redaction rules
  - Backup/restore procedures
  - SLO/SLI monitoring
  - Incident response playbook

### 2. Tests
- 🆕 `tests/test_headers_contract.py` - Header validation
  - Ensure x-request-id present on all endpoints
  - Ensure x-latency-ms present on all endpoints
  - Validate UUID format for request IDs
  - Verify latency is numeric

- 🆕 `tests/test_rate_limit_stub.py` - Rate limit stubs
  - Placeholder tests (xpass)
  - Document expected behavior
  - Validation for future implementation

### 3. Code (Minimal)
- Header middleware already exists (verified)
- Rate limit stubs with TODO markers
- Log redaction helpers (documented, not enforced)

## Success Criteria / DEPARTMENT-ALPHA

- [ ] Sprint plan created (docs/sprint_plan.md)
- [ ] Hardening runbook complete (docs/ops/hardening_runbook.md)
- [ ] Header contract tests created (tests/test_headers_contract.py)
- [ ] Rate limit stub tests created (tests/test_rate_limit_stub.py)
- [ ] All header tests passing (validate existing middleware)
- [ ] Rate limit tests as xpass (planned for implementation)
- [ ] SLOs and SLIs documented
- [ ] Log redaction documented
- [ ] Backup procedures documented
- [ ] Code committed with message "docs(sprint15): add sprint plan + stubs"
- [ ] Branch pushed to origin
- [ ] Draft PR opened with labels: sprint, 15, seed, draft

## Risks & Mitigations

### Risk: Rate Limiting Too Aggressive
**Impact:** Medium - Legitimate requests rejected  
**Probability:** Medium  
**Mitigation:**
- Start with generous limits
- Monitor actual usage patterns
- Allow per-client overrides
- Implement backoff headers
- Provide bypass for internal tools

### Risk: Header Validation Breaking Changes
**Impact:** High - Existing clients may fail  
**Probability:** Low  
**Mitigation:**
- Headers already present (Phase 3)
- Tests verify existing behavior
- No new requirements for clients
- Backward compatible

### Risk: Log Redaction Over-Aggressive
**Impact:** Medium - Debugging becomes difficult  
**Probability:** Low  
**Mitigation:**
- Redact only known PII patterns
- Preserve request IDs for correlation
- Document redacted fields
- Provide secure log access for debugging
- Hash instead of full redaction when possible

### Risk: SLO Unrealistic
**Impact:** Low - Can't meet commitments  
**Probability:** Medium  
**Mitigation:**
- Start with achievable targets (99.9%)
- Monitor actual performance first
- Adjust based on baseline
- Document measurement methodology
- Include error budget tracking

## Validation Steps

### 1. Header Contract Tests

```bash
# Run header validation tests
pytest tests/test_headers_contract.py -v

# Should verify all endpoints include:
# - x-request-id (UUID format)
# - x-latency-ms (numeric, > 0)
```

### 2. Rate Limit Tests

```bash
# Run rate limit stub tests
pytest tests/test_rate_limit_stub.py -v

# Expected: xpass (documented but not implemented)
```

### 3. Documentation Review

```bash
# Verify runbook completeness
cat docs/ops/hardening_runbook.md

# Check sections:
# - Rate limiting
# - Log redaction
# - Backup/restore
# - SLO/SLI monitoring
```

### 4. Manual Validation

```bash
# Start server
python -m uvicorn mcp.api.main:app --reload

# Test headers on all endpoints
for endpoint in /healthz /v1/info /v1/forecast/summary; do
  echo "Testing $endpoint"
  curl -i http://localhost:8000$endpoint | grep -E "x-request-id|x-latency-ms"
done
```

## Checklist

- [x] Design reviewed
- [ ] Sprint plan created (docs/sprint_plan.md)
- [ ] Hardening runbook created (docs/ops/hardening_runbook.md)
- [ ] Header contract tests created (tests/test_headers_contract.py)
- [ ] Rate limit stub tests created (tests/test_rate_limit_stub.py)
- [ ] All tests passing (headers validate, rate limits xpass)
- [ ] SLOs and SLIs documented
- [ ] Backup procedures documented
- [ ] Log redaction documented
- [ ] Documentation complete and reviewed
- [ ] Code committed with message "docs(sprint15): add sprint plan + stubs"
- [ ] Branch pushed to origin
- [ ] Draft PR opened with labels: sprint, 15, seed, draft
- [ ] Ready for development phase

## Notes

- Header middleware already exists (Phase 3) - tests validate it works
- Rate limiting to be implemented in development phase
- Log redaction patterns documented but not enforced yet
- SLOs based on current system performance baselines
- Backup procedures leverage existing state.json atomicity

---

**Next Steps After Sprint:**
1. Implement rate limiting middleware
2. Add log redaction filters
3. Set up SLO monitoring dashboards
4. Test backup/restore procedures
5. Create incident response playbook
6. Production deployment checklist