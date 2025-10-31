# Hardening Runbook

Operational guide for production hardening, monitoring, and incident response for the Red River Sales MCP API.

## Table of Contents

1. [Service Level Objectives (SLOs)](#service-level-objectives-slos)
2. [Rate Limiting Policy](#rate-limiting-policy)
3. [Log Redaction](#log-redaction)
4. [Incident Response](#incident-response)
5. [Backup & Restore](#backup--restore)
6. [Monitoring & Alerts](#monitoring--alerts)
7. [Security Checklist](#security-checklist)

---

## Service Level Objectives (SLOs)

### Target SLOs

| Metric | Target | Measurement Window |
|--------|--------|-------------------|
| **Availability** | 99.9% | 30 days |
| **P95 Latency** | < 100ms | 1 hour |
| **P99 Latency** | < 500ms | 1 hour |
| **Error Rate** | < 0.1% | 1 hour |
| **Rate Limit Rejections** | < 1% | 1 hour |

### SLO Monitoring

**Health Check Endpoint**: `GET /healthz`
- Expected response: `{"status":"healthy"}`
- Should return within 10ms
- Monitor every 30 seconds

**Metrics Endpoint**: `GET /v1/metrics`
- Returns aggregated request statistics
- Use for SLO dashboard

### SLO Violation Response

1. **Availability < 99.9%**
   - Check server logs: `tail -f logs/mcp.log`
   - Verify dependencies (database, external APIs)
   - Review recent deployments
   - Escalate to P1 if outage > 5 minutes

2. **P95 Latency > 100ms**
   - Check slow query log
   - Review rate limit rejections (may indicate load)
   - Check external API latencies
   - Consider horizontal scaling

3. **Error Rate > 0.1%**
   - Review error logs: `grep ERROR logs/mcp.log`
   - Check for malformed requests
   - Verify API contract compliance

---

## Rate Limiting Policy

### Rate Limit Groups

| Group | Limit (req/min) | Routes | Justification |
|-------|-----------------|--------|---------------|
| **GENERAL** | 100 | All routes (default) | Standard API usage |
| **WEBHOOKS** | 1000 | `/v1/govly/webhook`, `/v1/radar/webhook` | High-volume external integrations |
| **AI** | 20 | `/v1/ai/*` | Expensive AI operations |

### Rate Limit Response

When rate limited, clients receive:
```json
{
  "error": "rate_limited",
  "message": "Rate limit exceeded for AI endpoints",
  "retry_after": 45,
  "limit": 20
}
```

**Status Code**: `429 Too Many Requests`

**Header**: `Retry-After: <seconds>`

### Checking Rate Limit Status

```python
from mcp.api.middleware.rate_limit import _buckets, RATE_LIMITS

# View current bucket counts
for (group, minute), count in _buckets.items():
    print(f"{group} (minute {minute}): {count}/{RATE_LIMITS[group]}")
```

### Override/Escalation Path

⚠️ **Temporary rate limit lifts should be used sparingly and documented.**

#### Method 1: Environment Override (Recommended)

```python
# In mcp/api/middleware/rate_limit.py
import os

RATE_LIMITS = {
    "GENERAL": int(os.getenv("RATE_LIMIT_GENERAL", "100")),
    "WEBHOOKS": int(os.getenv("RATE_LIMIT_WEBHOOKS", "1000")),
    "AI": int(os.getenv("RATE_LIMIT_AI", "20")),
}
```

Set environment variable:
```bash
export RATE_LIMIT_AI=50  # Temporarily increase AI limit
```

#### Method 2: Code Modification (Emergency Only)

1. Edit `mcp/api/middleware/rate_limit.py`
2. Update `RATE_LIMITS` dictionary
3. Restart server
4. **Create incident ticket** documenting change
5. Revert after emergency resolved

**Risk**: Permanent changes may lead to abuse or infrastructure strain.

### Rate Limit Bypass for Testing

```python
# In tests only - monkeypatch the limits
import mcp.api.middleware.rate_limit as rl
monkeypatch.setattr(rl, "RATE_LIMITS", {
    "GENERAL": 999999,
    "WEBHOOKS": 999999,
    "AI": 999999,
})
```

---

## Log Redaction

### Redacted Patterns

The system automatically redacts sensitive information in all logs:

| Pattern | Example | Redacted |
|---------|---------|----------|
| Bearer tokens | `Authorization: Bearer abc123` | `Authorization: Bearer ***` |
| API keys | `sk-***` | `sk-***` |
| Email addresses | `***@***.***` | `***@***.***` |
| Slack tokens | `xoxb-***-***-****` | `xox*-***` |
| Webhook signatures | `x-webhook-signature: abc123` | `x-webhook-signature: ***` |
| Secret params | `token=abc123` | `token=***` |
| URL secrets | `?apikey=*** | `?apikey=*** |

### Extending Redaction Patterns

Edit `mcp/core/log_filters.py`:

```python
self.patterns.append((
    re.compile(r"your-new-pattern", re.IGNORECASE),
    "your-replacement"
))
```

**Testing redaction**:
```python
from mcp.core.log_filters import RedactingFilter
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test")
filter = RedactingFilter()
logger.addFilter(filter)

logger.info("User logged in with token=abc123")
# Output: "User logged in with token=***"
```

### Verifying Redaction

```bash
# Check logs for exposed secrets (should return nothing)
grep -E 'sk-[A-Za-z0-9]{20,}' logs/mcp.log
grep -E 'Bearer [A-Za-z0-9]+' logs/mcp.log
grep -E '[a-z0-9]+@[a-z0-9]+\.[a-z]+' logs/mcp.log

# If any matches found, investigate immediately
```

---

## Incident Response

### Incident Severity Levels

#### P0 - Critical (Complete Outage)
**Response Time**: < 5 minutes
**Examples**:
- API completely down
- Database unavailable
- Security breach

**Actions**:
1. Page on-call engineer
2. Enable incident bridge
3. Post status update every 15 minutes
4. Create incident ticket

**Commands**:
```bash
# Check if server is running
ps aux | grep uvicorn

# Check logs for crashes
tail -100 logs/mcp.log | grep -i error

# Restart server (if safe)
./start-server.sh

# Check health
curl http://localhost:8000/healthz
```

#### P1 - Major (Degraded Service)
**Response Time**: < 15 minutes
**Examples**:
- Error rate > 5%
- Latency > 1s
- Rate limits blocking legitimate traffic

**Actions**:
1. Notify team via Slack
2. Investigate logs
3. Apply temporary fixes
4. Schedule permanent fix

**Commands**:
```bash
# Check error rate
grep ERROR logs/mcp.log | tail -100

# Check slow requests (latency > 1000ms)
grep "x-latency-ms" logs/mcp.log | awk '$NF > 1000'

# Check rate limit rejections
grep "rate_limited" logs/mcp.log | wc -l
```

#### P2 - Minor (Limited Impact)
**Response Time**: < 1 hour
**Examples**:
- Single endpoint failing
- Non-critical feature broken
- Increased error rate on low-traffic endpoint

**Actions**:
1. Create ticket
2. Investigate during business hours
3. Document workaround if available

#### P3 - Cosmetic (No Impact)
**Response Time**: Next sprint
**Examples**:
- Log formatting issues
- Minor documentation errors

### Incident Command Center

**Log Location**: `/Users/jonolan/projects/red-river-sales-automation/logs/`

**Key Log Files**:
- `mcp.log` - Main application log
- `error.log` - Error-level messages only
- `access.log` - HTTP access log (if configured)

**Quick Log Analysis**:
```bash
# Last 100 errors
tail -100 logs/mcp.log | grep ERROR

# Error frequency by type
grep ERROR logs/mcp.log | cut -d: -f3 | sort | uniq -c | sort -rn

# Recent 429 responses (rate limited)
grep "429" logs/mcp.log | tail -20

# Slow requests (> 500ms)
grep "x-latency-ms" logs/mcp.log | awk -F'x-latency-ms: ' '$2 > 500' | tail -20
```

### Rollback Procedure

1. **Identify last known good commit**:
   ```bash
   git log --oneline -10
   ```

2. **Checkout previous version**:
   ```bash
   git checkout <commit-hash>
   ```

3. **Restart services**:
   ```bash
   ./start-server.sh
   ```

4. **Verify health**:
   ```bash
   curl http://localhost:8000/healthz
   pytest tests/test_health.py
   ```

5. **Notify stakeholders** of rollback

---

## Backup & Restore

### Backup Strategy

#### Application State

**Location**: `data/state.json`, `data/forecast.json`

**Cadence**: Continuous (auto-save on every write)

**Backup**:
```bash
# Manual backup
cp data/state.json data/state.json.$(date +%Y%m%d_%H%M%S)
cp data/forecast.json data/forecast.json.$(date +%Y%m%d_%H%M%S)

# Automated backup (add to cron)
0 2 * * * cd /path/to/project && ./scripts/backup_data.sh
```

#### Database Backups

**SQLite databases**: `data/*.db`

**Backup**:
```bash
# Backup all databases
for db in data/*.db; do
    sqlite3 "$db" ".backup 'data/backups/$(basename $db).$(date +%Y%m%d_%H%M%S)'"
done
```

**Retention**: Keep 30 days of daily backups

### Restore Procedure

1. **Stop services**:
   ```bash
   pkill -f uvicorn
   ```

2. **Restore files**:
   ```bash
   cp data/backups/state.json.20251030_140000 data/state.json
   ```

3. **Verify integrity**:
   ```bash
   python3 -c "import json; json.load(open('data/state.json'))"
   ```

4. **Restart services**:
   ```bash
   ./start-server.sh
   ```

5. **Verify health**:
   ```bash
   curl http://localhost:8000/healthz
   curl http://localhost:8000/v1/info
   ```

### Quick Verify Commands

```bash
# Check state file integrity
jq . data/state.json > /dev/null && echo "Valid JSON" || echo "CORRUPT"

# Check forecast file
jq . data/forecast.json > /dev/null && echo "Valid JSON" || echo "CORRUPT"

# Check database integrity
sqlite3 data/partners_base.db "PRAGMA integrity_check;"
```

---

## Monitoring & Alerts

### Health Check Monitoring

**Endpoint**: `GET /healthz`

**Expected Response**: `{"status":"healthy"}`

**Monitoring Setup** (example with curl + cron):
```bash
# Add to crontab: */5 * * * * (every 5 minutes)
curl -sf http://localhost:8000/healthz | grep -q healthy || echo "ALERT: Health check failed"
```

### Metrics Collection

**Endpoint**: `GET /v1/metrics`

**Response**:
```json
{
  "requests_total": 12345,
  "requests_per_minute": 42,
  "error_rate": 0.002,
  "avg_latency_ms": 45
}
```

### Alert Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| Error Rate | > 1% | > 5% |
| P95 Latency | > 200ms | > 500ms |
| Health Check Fails | 2 consecutive | 5 consecutive |
| Rate Limit Rejections | > 5% | > 10% |

---

## Security Checklist

### Pre-Deployment

- [ ] All secrets in environment variables (not committed)
- [ ] Rate limiting enabled
- [ ] Log redaction filter installed
- [ ] HTTPS/TLS configured (production)
- [ ] Firewall rules applied
- [ ] Database access restricted
- [ ] Backup automation configured

### Production

- [ ] Monitor health check endpoint
- [ ] Review logs daily for anomalies
- [ ] Verify no secrets in logs
- [ ] Test incident response procedures monthly
- [ ] Keep dependencies updated
- [ ] Review rate limit effectiveness weekly

### Incident Post-Mortem

After any P0 or P1 incident:
1. Document timeline
2. Identify root cause
3. List action items
4. Update runbook with lessons learned
5. Test prevention measures

---

## Quick Reference

### Start Server
```bash
./start-server.sh
# or
uvicorn mcp.api.main:app --host 0.0.0.0 --port 8000
```

### Stop Server
```bash
pkill -f uvicorn
```

### Check Logs
```bash
tail -f logs/mcp.log
```

### Run Tests
```bash
pytest -v
```

### Check Rate Limits
```bash
curl -I http://localhost:8000/v1/info
# Look for x-request-id and x-latency-ms headers
```

### Emergency Contacts

- **On-Call Engineer**: [Configure paging system]
- **Team Slack**: #red-river-ops
- **Escalation**: [Manager contact]

---

## Appendix

### Log Rotation

Configure logrotate:
```
/path/to/logs/mcp.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload mcp-api
    endscript
}
```

### Performance Tuning

**Uvicorn workers** (for production):
```bash
uvicorn mcp.api.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level info
```

**Database optimization**:
```sql
-- Add indexes for common queries
CREATE INDEX idx_contracts_oem ON contracts(oem_id);
CREATE INDEX idx_forecast_date ON forecast(created_at);
```

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-30 | Initial hardening runbook |