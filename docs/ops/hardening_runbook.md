# Production Hardening Runbook

**Version:** 1.0  
**Last Updated:** October 29, 2025 EDT  
**Sprint:** 15 - Production Hardening

## Overview

This runbook covers production-ready security controls, rate limiting, monitoring, and operational procedures for the Red River Sales MCP API.

## Rate Limiting

### Policies

**Default Rate Limits:**
```python
RATE_LIMIT_POLICIES = {
    "default": {
        "requests": 100,
        "window": 60,  # seconds
        "strategy": "sliding_window"
    },
    "webhook": {
        "requests": 1000,
        "window": 60,
        "strategy": "fixed_window"
    },
    "ai": {
        "requests": 20,
        "window": 60,
        "strategy": "token_bucket"
    },
    "export": {
        "requests": 10,
        "window": 60,
        "strategy": "leaky_bucket"
    }
}
```

### Implementation

**Middleware (Planned):**
```python
from fastapi import Request, HTTPException

async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    endpoint = request.url.path
    
    # Check rate limit
    if not check_rate_limit(client_ip, endpoint):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={
                "Retry-After": "60",
                "X-RateLimit-Limit": "100",
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(get_reset_time())
            }
        )
    
    response = await call_next(request)
    
    # Add rate limit headers
    add_rate_limit_headers(response, client_ip, endpoint)
    
    return response
```

### Response Headers

When rate limited:
```
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1698609660
Retry-After: 60
Content-Type: application/json

{
  "error": "rate_limit_exceeded",
  "message": "Too many requests. Please try again later.",
  "retry_after": 60
}
```

## Header Validation

### Required Headers (Response)

ALL responses MUST include:
```
X-Request-ID: <uuid4>
X-Latency-MS: <integer>
```

**Validation:** See [`test_headers_contract.py`](../../tests/test_headers_contract.py)

### Optional Headers (Request)

Clients MAY send:
```
X-Client-ID: <client_identifier>
X-Trace-ID: <distributed_trace_id>
```

### Security Headers (Response)

Recommended security headers:
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000
```

## Log Redaction

### Sensitive Data Patterns

**PII (Personally Identifiable Information):**
- Email addresses
- Phone numbers
- Social Security Numbers
- Credit card numbers

**Secrets:**
- API keys (ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.)
- Webhook secrets (GOVLY_WEBHOOK_SECRET, etc.)
- Slack tokens (SLACK_BOT_TOKEN, etc.)
- Passwords

### Redaction Rules

```python
import re

REDACTION_PATTERNS = {
    "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
    "api_key": r'(sk-|xoxb-|xoxp-)[A-Za-z0-9-_]{20,}',
    "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
}

def redact_sensitive_data(text: str) -> str:
    """Redact sensitive data from logs."""
    for pattern_name, pattern in REDACTION_PATTERNS.items():
        text = re.sub(pattern, f"[REDACTED_{pattern_name.upper()}]", text)
    return text
```

**Example:**
```python
# Before
log.info(f"User joe.nolan@redriver.com accessed API with key sk-abc123")

# After redaction
log.info(f"User [REDACTED_EMAIL] accessed API with key [REDACTED_API_KEY]")
```

## Backup & Restore

### State File Backup

**Automated Backups:**
```bash
#!/bin/bash
# Backup state.json every hour
BACKUP_DIR="data/backups"
mkdir -p $BACKUP_DIR

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
cp data/state.json "$BACKUP_DIR/state_${TIMESTAMP}.json"

# Keep last 168 backups (1 week of hourly)
ls -t $BACKUP_DIR/state_*.json | tail -n +169 | xargs rm -f
```

**Manual Backup:**
```bash
# Create backup
cp data/state.json data/state.backup.json

# With timestamp
cp data/state.json "data/state.$(date +%Y%m%d_%H%M%S).backup.json"
```

### Restore Procedures

**Restore from backup:**
```bash
# Stop API
pm2 stop mcp-api

# Restore state
cp data/backups/state_20251029_120000.json data/state.json

# Restart API
pm2 restart mcp-api

# Verify
curl http://localhost:8000/v1/system/recent-actions
```

**Validate restore:**
```bash
# Check JSON validity
python -c "import json; json.load(open('data/state.json'))"

# Check required structure
jq '.opportunities, .recent_actions' data/state.json
```

## SLO & SLI Monitoring

### Service Level Objectives

| Metric | Target | Measurement | Alert Threshold |
|--------|--------|-------------|-----------------|
| Availability | 99.9% | Uptime / Total Time | < 99.8% |
| Latency (P95) | < 100ms | Response time distribution | > 150ms |
| Latency (P99) | < 500ms | Response time distribution | > 750ms |
| Error Rate | < 0.1% | 5xx / Total Requests | > 0.2% |
| Rate Limit Violations | < 1% | 429 / Total Requests | > 2% |

### Monitoring Queries

**Prometheus/Grafana:**
```promql
# Availability (last 30 days)
avg_over_time(up{job="mcp-api"}[30d])

# P95 Latency
histogram_quantile(0.95, rate(http_request_duration_ms_bucket[5m]))

# Error Rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])
```

**Log-Based (Loki/CloudWatch):**
```logql
# Error rate
count_over_time({job="mcp-api"} |= "ERROR" [5m]) / count_over_time({job="mcp-api"} [5m])
```

### Alerting Rules

**Critical Alerts:**
- Availability < 99.5% (5 min window)
- P99 Latency > 1s (5 min window)
- Error rate > 1% (5 min window)

**Warning Alerts:**
- Availability < 99.8% (15 min window)
- P95 Latency > 150ms (15 min window)
- Error rate > 0.2% (15 min window)

## Security Controls

### Authentication (Future)

**Planned for post-Sprint 15:**
- API key authentication
- JWT token validation
- OAuth 2.0 integration
- Role-based access control (RBAC)

### Input Validation

**All endpoints validate:**
- Request payload schema (Pydantic)
- Query parameters
- Header formats
- File uploads (if applicable)

### Output Sanitization

**Prevent information disclosure:**
- No stack traces in production
- Generic error messages
- Redact internal paths
- No version info in headers

## Incident Response

### Severity Levels

**P0 - Critical:** Service down, data loss
- Response: Immediate (< 15 min)
- Communication: Notify stakeholders
- Resolution: All hands on deck

**P1 - High:** Severe degradation, security issue
- Response: Within 1 hour
- Communication: Notify team
- Resolution: Assigned owner + backup

**P2 - Medium:** Partial degradation, non-critical bug
- Response: Within 4 hours
- Communication: Team slack
- Resolution: Regular sprint work

**P3 - Low:** Minor issue, enhancement request
- Response: Next sprint
- Communication: Backlog
- Resolution: Prioritize in planning

### Escalation Path

1. **On-Call Engineer** - First responder
2. **Team Lead** - Escalate if no resolution in 30 min
3. **Engineering Manager** - Escalate if P0 or >2 hours
4. **CTO** - Escalate if data loss or security breach

### Communication Templates

**Incident Start:**
```
🚨 INCIDENT: <Brief Description>
Severity: P<0-3>
Start Time: <timestamp>
Impact: <affected services>
Status: Investigating
ETA: <estimate or unknown>
```

**Incident Update:**
```
📢 UPDATE: <Incident ID>
Status: <investigating|identified|fixing|monitoring>
Progress: <what's been done>
Next Steps: <what's next>
ETA: <updated estimate>
```

**Incident Resolved:**
```
✅ RESOLVED: <Incident ID>
Resolution: <what fixed it>
Duration: <total time>
Root Cause: <brief explanation>
Follow-up: <link to postmortem>
```

## Production Deployment

### Pre-Deployment Checklist

- [ ] All tests passing (pytest -v)
- [ ] Linting clean (ruff check .)
- [ ] Environment variables configured
- [ ] Secrets rotated (if needed)
- [ ] Backup created
- [ ] Rollback plan ready
- [ ] Monitoring enabled
- [ ] On-call schedule set

### Deployment Process

1. **Pre-deployment:**
   ```bash
   # Run full test suite
   pytest -v
   
   # Create backup
   ./scripts/backup.sh
   
   # Tag release
   git tag -a v1.7.0 -m "Release v1.7.0: Sprint 15 Hardening"
   git push origin v1.7.0
   ```

2. **Deployment:**
   ```bash
   # Pull latest code
   git pull origin main
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Restart service
   pm2 restart mcp-api
   ```

3. **Post-deployment:**
   ```bash
   # Health check
   curl http://localhost:8000/healthz
   
   # Verify version
   curl http://localhost:8000/v1/info | jq '.version'
   
   # Check logs
   pm2 logs mcp-api --lines 50
   ```

### Rollback Procedure

```bash
# Stop current version
pm2 stop mcp-api

# Restore previous version
git checkout v1.6.0

# Restore state backup
cp data/backups/state_<timestamp>.json data/state.json

# Restart service
pm2 restart mcp-api

# Verify
curl http://localhost:8000/healthz
```

## Monitoring & Observability

### Health Checks

**Liveness:** `/healthz` - Returns 200 if service running  
**Readiness:** `/v1/info` - Returns 200 with version info

### Metrics to Track

**Request Metrics:**
- Total requests per minute
- Requests by endpoint
- Requests by status code (2xx, 4xx, 5xx)
- Average latency per endpoint

**Resource Metrics:**
- CPU usage (target: < 70%)
- Memory usage (target: < 80%)
- Disk usage (target: < 85%)
- Network I/O

**Application Metrics:**
- Opportunities created per hour
- Webhooks processed per hour
- Forecast calculations per day
- AI requests per hour

### Log Aggregation

**Structured Logging:**
All logs in JSON format:
```json
{
  "timestamp": "2025-10-29T13:00:00Z",
  "level": "INFO",
  "message": "Request processed",
  "request_id": "a1b2c3d4",
  "method": "GET",
  "path": "/v1/forecast/summary",
  "status": 200,
  "latency_ms": 45
}
```

**Log Retention:**
- Development: 7 days
- Staging: 30 days
- Production: 90 days

## Troubleshooting

### High Latency

**Symptoms:**
- P95 latency > 100ms
- P99 latency > 500ms
- Slow API responses

**Diagnosis:**
```bash
# Check recent actions for slow requests
curl http://localhost:8000/v1/system/recent-actions | jq '.actions[] | select(.latency_ms > 100)'

# Review logs
grep "latency_ms" logs/app.log | awk '{if($NF > 100) print}'
```

**Solutions:**
- Add caching for frequent queries
- Optimize database queries
- Scale horizontally
- Add CDN for static content

### High Error Rate

**Symptoms:**
- Error rate > 0.1%
- Frequent 5xx responses
- Client complaints

**Diagnosis:**
```bash
# Check error distribution
curl http://localhost:8000/v1/metrics | jq '.errors_by_endpoint'

# Review error logs
grep "ERROR" logs/app.log | tail -50
```

**Solutions:**
- Fix application bugs
- Add retry logic
- Improve error handling
- Validate inputs more strictly

### Rate Limit Violations

**Symptoms:**
- Frequent 429 responses
- Client reports being blocked

**Diagnosis:**
```bash
# Check rate limit stats
grep "429" logs/app.log | wc -l

# Identify top offenders
grep "429" logs/app.log | grep -oE 'client_ip":"[^"]+' | sort | uniq -c | sort -rn
```

**Solutions:**
- Increase limits for legitimate clients
- Add API key authentication
- Implement tiered rate limits
- Block abusive IPs

---

**Related Documentation:**
- [Sprint 15 Plan](../sprint_plan.md)
- [API Documentation](../api/endpoints.md)
- [RUNBOOK.md](../../RUNBOOK.md)