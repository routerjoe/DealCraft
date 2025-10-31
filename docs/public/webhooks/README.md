# Webhook Integration Guide

**Version:** 1.0  
**Last Updated:** October 29, 2025 EDT  
**Sprint:** 10 - Govly/Radar Webhooks & Secrets

## Overview

The DealCraft system supports webhook ingestion from two primary sources:
- **Govly** - Federal opportunity tracking platform
- **Radar** - Contract modification and award monitoring

Webhooks automatically create opportunities in the Obsidian vault with proper Federal FY routing and triage flags.

## Endpoints

### POST /v1/govly/webhook

Ingests federal opportunity events from Govly.

**Request Headers:**
- `Content-Type: application/json` (required)
- `X-Govly-Signature: <hmac-sha256>` (optional, recommended for production)

**Request Body (GovlyWebhookPayload):**
```json
{
  "event_id": "govly_12345",
  "event_type": "opportunity",
  "title": "IT Services RFQ",
  "description": "Federal IT services contract",
  "estimated_amount": 500000,
  "agency": "Federal Agency A",
  "posted_date": "2025-10-28T00:00:00Z",
  "close_date": "2025-11-15T23:59:59Z",
  "source_url": "https://govly.example.com/opp/12345"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "opportunity_id": "govly_govly_12345",
  "message": "Govly opportunity govly_govly_12345 ingested and triaged"
}
```

**Response Headers:**
- `x-request-id: <uuid>` - Request tracking ID
- `x-latency-ms: <float>` - Request processing time

### POST /v1/radar/webhook

Ingests contract modification and award events from Radar.

**Request Headers:**
- `Content-Type: application/json` (required)
- `X-Radar-Signature: <hmac-sha256>` (optional, recommended for production)

**Request Body (RadarWebhookPayload):**
```json
{
  "radar_id": "radar_67890",
  "radar_type": "contract",
  "company_name": "Acme Corp",
  "contract_value": 1500000,
  "contract_date": "2025-10-28T00:00:00Z",
  "description": "Contract modification for IT services",
  "source_url": "https://radar.example.com/contract/67890"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "opportunity_id": "radar_radar_67890",
  "message": "Radar opportunity radar_radar_67890 ingested and triaged"
}
```

## Authentication & Signature Validation

### HMAC-SHA256 Signature

Both Govly and Radar webhooks support HMAC-SHA256 signature validation to ensure webhook authenticity.

**Signature Format:**
```
X-Govly-Signature: sha256=<hex_digest>
X-Radar-Signature: sha256=<hex_digest>
```

**Signature Calculation:**
```python
import hmac
import hashlib

# Webhook secret from environment
secret = os.environ['GOVLY_WEBHOOK_SECRET']

# Request body as bytes
body = request.body.encode('utf-8')

# Calculate HMAC-SHA256
signature = hmac.new(
    secret.encode('utf-8'),
    body,
    hashlib.sha256
).hexdigest()

# Header value
header = f"sha256={signature}"
```

### Environment Variables

Configure webhook secrets in your `.env` file:

```bash
# Govly webhook authentication
GOVLY_WEBHOOK_SECRET=your_govly_secret_here

# Radar webhook authentication
RADAR_WEBHOOK_SECRET=your_radar_secret_here
```

**Security Best Practices:**
- Generate secrets with high entropy (32+ characters)
- Rotate secrets regularly (every 90 days recommended)
- Never commit secrets to version control
- Use different secrets for development and production

### Secret Rotation

To rotate webhook secrets without downtime:

1. **Generate new secret**:
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   # Example output: ***SECRET***
   ```

2. **Configure dual-secret support**:
   ```bash
   GOVLY_WEBHOOK_SECRET=***SECRET***  # New secret
   GOVLY_SECRET_V2=old_govly_secret_here                  # Old secret (fallback)
   ```

3. **Deploy with both secrets active** - Server now accepts webhooks signed with either secret

4. **Update webhook provider (Govly) with new secret** - Configure Govly to use new signing secret

5. **Monitor logs for old secret usage**:
   ```bash
   # Check for fallback authentication
   grep "fallback secret" /var/log/mcp/webhook.log
   ```

6. **Remove old secret after 24-48 hours**:
   ```bash
   # Once all webhooks use new secret, remove fallback from .env
   GOVLY_WEBHOOK_SECRET=***SECRET***
   # GOVLY_SECRET_V2 removed
   ```

**Example Rotation Scenario:**
```bash
# Step 1: Current production config
GOVLY_WEBHOOK_SECRET=old_secret_abc123

# Step 2: Add new secret while keeping old
GOVLY_WEBHOOK_SECRET=new_secret_xyz789
GOVLY_SECRET_V2=old_secret_abc123

# Step 3: After Govly provider updated and verified
GOVLY_WEBHOOK_SECRET=new_secret_xyz789
# GOVLY_SECRET_V2 removed
```

## Replay Protection

### Event ID Tracking

The system maintains an append-only log of all processed webhook events in `data/state.json`:

```json
{
  "opportunities": [
    {
      "id": "govly_12345",
      "source": "govly",
      "source_id": "12345",
      "created_at": "2025-10-29T12:00:00Z",
      "request_id": "***SECRET***"
    }
  ]
}
```

**Duplicate Detection:**
- Event IDs are checked against existing opportunities
- Duplicate events are logged but not re-processed
- Original opportunity is preserved

### Timestamp Validation

Webhook events should include timestamps to detect replay attacks:

**Govly:**
- `posted_date` - When opportunity was posted
- Validates against current time (reject if > 24 hours old)

**Radar:**
- `contract_date` - When contract was awarded/modified
- Validates against current time (reject if > 7 days old)

## Federal FY Routing

Opportunities are automatically routed to the appropriate Federal Fiscal Year folder based on close dates.

### FY Calculation

Federal Fiscal Year runs from October 1 (N-1) to September 30 (N):

```python
def calculate_fy(close_date: datetime) -> str:
    """Calculate Federal Fiscal Year from close date."""
    if close_date.month >= 10:  # Oct, Nov, Dec
        return f"FY{close_date.year + 1}"
    else:  # Jan-Sep
        return f"FY{close_date.year}"
```

### Routing Logic

**Valid Close Date:**
```
close_date: 2025-11-15
→ FY26 (Oct 2025 - Sep 2026)
→ obsidian/40 Projects/Opportunities/FY26/govly_12345.md
```

**Invalid/Missing Close Date:**
```
close_date: null or invalid
→ Triage
→ obsidian/40 Projects/Opportunities/Triage/govly_12345.md
```

### Opportunity File Structure

Generated opportunities include YAML frontmatter and minimal content:

```markdown
---
id: govly_12345
title: IT Services RFQ
source: Govly
triage: true
created_at: 2025-10-29T12:00:00Z
status: triage
---

# IT Services RFQ

**Source:** Govly
**Status:** Triage
**Created:** 2025-10-29T12:00:00Z

## Summary

Auto-ingested from Govly webhook. Awaiting manual review and enrichment.

## Next Steps

1. Review opportunity details
2. Validate estimated amount and close date
3. Assign to appropriate FY folder
4. Update triage flag to false when ready
```

## Mapping to Obsidian Schema

### Govly → Obsidian Mapping

| Govly Field | Obsidian Field | Notes |
|-------------|----------------|-------|
| event_id | source_id | Original event ID |
| title | title | Opportunity title |
| description | content | Full description |
| estimated_amount | estimated_amount | Contract value |
| agency | agency | Federal agency |
| posted_date | posted_date | ISO 8601 format |
| close_date | close_date | Determines FY routing |
| source_url | source_url | Link to Govly |

### Radar → Obsidian Mapping

| Radar Field | Obsidian Field | Notes |
|-------------|----------------|-------|
| radar_id | source_id | Original radar ID |
| company_name | title | Formatted as "Company - Type" |
| radar_type | type | contract, modification, etc. |
| contract_value | estimated_amount | Contract value |
| contract_date | close_date | Determines FY routing |
| description | content | Full description |
| source_url | source_url | Link to Radar |

## Dry-Run Mode

For testing webhooks without creating opportunities, use dry-run mode:

### Dry-Run Request

```bash
curl -X POST "http://localhost:8000/v1/govly/webhook?dry_run=true" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "test_123",
    "event_type": "opportunity",
    "title": "Test Opportunity",
    "estimated_amount": 100000,
    "close_date": "2025-11-15T23:59:59Z"
  }'
```

**Dry-Run Response:**
```json
{
  "status": "success",
  "opportunity_id": "govly_test_123",
  "message": "Dry-run: Govly opportunity govly_test_123 would be ingested",
  "dry_run": true,
  "fy_route": "FY26"
}
```

### Dry-Run Behavior

When `?dry_run=true` query parameter is specified:
- ✅ Validates payload schema
- ✅ Verifies signature (if secrets configured)
- ✅ Checks replay protection (marks as seen)
- ✅ Calculates FY routing
- ✅ Generates opportunity ID
- ❌ Does NOT create state.json entry
- ❌ Does NOT create Obsidian file
- ✅ Returns preview with FY routing

**Use Cases:**
- Testing webhook integration before going live
- Validating payload schemas
- Verifying FY routing logic
- Confirming signature verification works

### Example: Testing Contract Vehicles

**SEWP (NASA GSFC):**
```bash
curl -X POST "http://localhost:8000/v1/govly/webhook?dry_run=true" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "sewp_001",
    "event_type": "opportunity",
    "title": "SEWP VI IT Hardware Acquisition",
    "description": "Federal IT hardware procurement under SEWP VI",
    "estimated_amount": 750000,
    "agency": "NASA",
    "close_date": "2026-03-15T23:59:59Z"
  }'
```

**CHESS (Army):**
```bash
curl -X POST "http://localhost:8000/v1/govly/webhook?dry_run=true" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "chess_002",
    "event_type": "opportunity",
    "title": "CHESS IT Services Contract",
    "description": "Army IT services under CHESS contract vehicle",
    "estimated_amount": 1250000,
    "agency": "Army",
    "close_date": "2026-02-28T23:59:59Z"
  }'
```

**AGENCY-ALPHA (Air Force Central Command):**
```bash
curl -X POST "http://localhost:8000/v1/govly/webhook?dry_run=true" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "afcent_003",
    "event_type": "opportunity",
    "title": "AGENCY-ALPHA Cybersecurity Services",
    "description": "Air Force Central Command cybersecurity contract",
    "estimated_amount": 2500000,
    "agency": "Air Force",
    "close_date": "2026-06-30T23:59:59Z"
  }'
```

**Expected Response for Each:**
```json
{
  "status": "success",
  "opportunity_id": "govly_sewp_001",  // or chess_002, afcent_003
  "message": "Dry-run: Govly opportunity would be ingested",
  "dry_run": true,
  "fy_route": "FY26"  // Calculated based on close_date
}
```

## Testing & Validation

### Local Testing

```bash
# Start development server
python -m uvicorn mcp.api.main:app --reload

# Test Govly webhook
curl -X POST http://localhost:8000/v1/govly/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "test_001",
    "event_type": "opportunity",
    "title": "Test Federal RFQ",
    "estimated_amount": 250000,
    "agency": "Federal Department A",
    "close_date": "2025-12-31T23:59:59Z"
  }'

# Verify state.json updated
cat data/state.json | jq '.opportunities | last'

# Check Obsidian file created
ls -la obsidian/40\ Projects/Opportunities/FY26/
```

### Running Tests

```bash
# Run all webhook tests
pytest tests/test_webhooks.py -v

# Run smoke tests
pytest tests/test_govly_webhook_smoke.py -v
pytest tests/test_webhooks_smoke.py -v

# Run with coverage
pytest tests/test_webhooks*.py --cov=mcp.api.v1.webhooks
```

## Monitoring & Debugging

### Log Analysis

All webhook requests are logged with structured JSON:

```json
{
  "timestamp": "2025-10-29T12:00:00Z",
  "level": "INFO",
  "message": "Govly webhook ingested: govly_12345",
  "request_id": "***SECRET***",
  "latency_ms": 2.45,
  "source": "govly",
  "opportunity_id": "govly_12345"
}
```

### Common Issues

#### 401 Unauthorized - Invalid Signature

**Symptom:** Webhook returns 401 with "Invalid signature"

**Causes:**
- Incorrect webhook secret in .env
- Signature calculation mismatch
- Clock skew between systems

**Solution:**
```bash
# Verify secret is set
echo $GOVLY_WEBHOOK_SECRET

# Test without signature first (development only)
curl -X POST http://localhost:8000/v1/govly/webhook \
  -H "Content-Type: application/json" \
  -d '{"event_id":"test","title":"Test","estimated_amount":100000}'
```

#### 422 Validation Error - Invalid Payload

**Symptom:** Webhook returns 422 with field validation errors

**Causes:**
- Missing required fields (event_id, title)
- Invalid data types (amount as string instead of number)
- Malformed JSON

**Solution:**
- Validate payload against schema
- Check required fields are present
- Ensure proper JSON encoding

#### Duplicate Event IDs

**Symptom:** Same event processed multiple times

**Causes:**
- Webhook provider retry without deduplication
- Multiple webhook endpoints configured

**Solution:**
- Review state.json for duplicate IDs
- Check webhook provider configuration
- Enable replay protection

## Production Deployment

### Checklist

- [ ] Configure `GOVLY_WEBHOOK_SECRET` in production environment
- [ ] Configure `RADAR_WEBHOOK_SECRET` in production environment
- [ ] Enable signature validation in production
- [ ] Set up webhook endpoint monitoring
- [ ] Configure log aggregation for webhook events
- [ ] Test signature validation with production secrets
- [ ] Document secret rotation schedule
- [ ] Set up alerting for webhook failures (>5% error rate)
- [ ] Verify FY routing logic for production dates
- [ ] Test replay protection with duplicate events

### Security Hardening

1. **Enable signature validation** (never skip in production)
2. **Use HTTPS only** for webhook endpoints
3. **Implement rate limiting** (covered in Sprint 15)
4. **Monitor for suspicious patterns** (rapid duplicate events, invalid signatures)
5. **Rotate secrets regularly** (90-day recommended)
6. **Log all authentication failures** for security review
7. **Restrict webhook IPs** if provider supports IP allowlisting

## API Reference

### Error Responses

**400 Bad Request:**
```json
{
  "status": "error",
  "message": "Invalid request payload",
  "details": {
    "field": "estimated_amount",
    "error": "must be a positive number"
  }
}
```

**401 Unauthorized:**
```json
{
  "status": "error",
  "message": "Invalid webhook signature",
  "opportunity_id": null
}
```

**500 Internal Server Error:**
```json
{
  "status": "error",
  "message": "Failed to create opportunity",
  "opportunity_id": null,
  "details": "IOError: Unable to write state.json"
}
```

## Support & Troubleshooting

For webhook issues:
1. Check application logs for detailed error messages
2. Verify payload matches documented schema
3. Test signature validation independently
4. Review [RUNBOOK.md](../RUNBOOK.md) for operational procedures
5. Consult state.json for event history

---

**Related Documentation:**
- [API Endpoints](../api/endpoints.md)
- [Obsidian Integration](../obsidian/README.md)
- [Sprint 10 Plan](sprint_plan.md)
- [System Architecture](../architecture/README.md)