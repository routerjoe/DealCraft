# Govly API Integration Research
**Date:** 2025-11-02
**Status:** ⚠️ BLOCKED - Enterprise Access Required
**Researcher:** Claude Code

---

## Executive Summary

Govly provides **webhook integrations** (✅ already implemented in DealCraft) and **API access** for proactive fetching. However, the API is **enterprise-only** and requires:
1. Govly enterprise customer account
2. API key from Govly dashboard
3. Contacting support@govly.com for specific endpoint access

**Current State:** DealCraft has a fully functional webhook receiver. Proactive API fetching is blocked pending enterprise API access.

---

## API Access Requirements

### Authentication
- **Method:** API Key Authentication
- **Key Location:** https://www.govly.com/app/settings/api_settings
- **Header:** Likely `Authorization: Bearer <api_key>` or `X-Govly-API-Key: <api_key>`
- **Protocol:** HTTPS only (HTTP 301 redirects to HTTPS)
- **Response Format:** JSON

### API Documentation
- **Official Docs:** https://docs.govly.com/
- **Access Level:** Enterprise customers only
- **Specific Endpoints:** Not publicly documented - surface on demand per customer request
- **Support Contact:** support@govly.com

### Rate Limits
- **Unknown** - would need to be discovered during implementation or from documentation

---

## Webhook Integration (Already Implemented)

DealCraft already has a **complete webhook integration** for Govly events:

### Webhook Endpoint
- **URL:** `POST /v1/govly/webhook`
- **Authentication:** HMAC-SHA256 signature verification
- **Replay Protection:** 5-minute nonce cache
- **Features:**
  - Federal FY routing based on close_date
  - Dry-run mode support
  - Automatic Obsidian note generation
  - Triage flagging

### Payload Schema

```python
class GovlyWebhookPayload(BaseModel):
    """Govly event webhook payload."""
    event_id: str  # Unique event identifier (required)
    event_type: str  # Event type (e.g., 'opportunity', 'update') (required)
    title: str  # Opportunity title (required)
    description: Optional[str]  # Opportunity description
    estimated_amount: Optional[float]  # Estimated contract amount
    agency: Optional[str]  # Federal agency name
    posted_date: Optional[str]  # ISO 8601 date posted
    close_date: Optional[str]  # ISO 8601 close date
    source_url: Optional[str]  # Source URL
```

### Example Webhook Payload

```json
{
  "event_id": "govly_12345",
  "event_type": "opportunity",
  "title": "IT Services RFQ",
  "description": "Federal IT services contract",
  "estimated_amount": 500000,
  "agency": "Department of Defense",
  "posted_date": "2025-10-29T00:00:00Z",
  "close_date": "2025-11-15T23:59:59Z",
  "source_url": "https://www.govly.com/contract/12345"
}
```

### Storage

Webhooks are stored in:
- **File:** `data/state.json`
- **Structure:** Append-only opportunities list
- **Format:**
```json
{
  "opportunities": [
    {
      "id": "govly_12345",
      "title": "IT Services RFQ",
      "source": "govly",
      "estimated_amount": 500000,
      "agency": "Department of Defense",
      "triage": true,
      "created_at": "2025-11-02T13:45:00Z"
    }
  ],
  "recent_actions": []
}
```

---

## Govly Platform Capabilities

### Coverage
- Captures opportunities from **40+ top contract vehicles**
- Includes: GSA, SEWP, ITES, and more
- Uses AI for normalization (OpenAI GPT-3.5, AWS Comprehend)

### Features
- Opportunity search and discovery
- Contract vehicle tracking
- Classification code normalization
- Federal opportunity alerts

---

## Proposed API Integration (When Access Available)

### API Client Architecture

```python
class GovlyClient:
    """Govly API client for proactive opportunity fetching."""

    def __init__(self, api_key: str, base_url: str = "https://api.govly.com/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })

    def fetch_opportunities(
        self,
        limit: int = 100,
        since: datetime = None,
        agencies: List[str] = None,
        amount_min: float = None,
        amount_max: float = None
    ) -> List[Dict]:
        """Fetch opportunities from Govly API."""
        # Implementation pending endpoint documentation
```

### Assumed Endpoints (TBD)

These are **assumptions** based on typical government contracting APIs:

```
GET /v1/opportunities
  - Fetch opportunities with filters
  - Query params: limit, offset, since, agency, amount_min, amount_max

GET /v1/opportunities/{id}
  - Fetch single opportunity by ID

GET /v1/contract-vehicles
  - List available contract vehicles

GET /v1/agencies
  - List federal agencies
```

**⚠️ Warning:** These endpoints are speculative and must be confirmed with Govly API documentation.

---

## Implementation Blockers

### Critical Blockers

1. **🚫 No API Key**
   - **Required:** Govly enterprise account
   - **Action:** Contact Govly sales or support@govly.com
   - **Timeline:** Unknown

2. **🚫 No Endpoint Documentation**
   - **Required:** Access to enterprise API docs
   - **Action:** Request from support@govly.com after API access granted
   - **Timeline:** Unknown

3. **🚫 No Rate Limit Information**
   - **Required:** Rate limit specs to avoid throttling
   - **Action:** Check API docs or test empirically
   - **Timeline:** After API access

### Non-Blockers

- ✅ Data schema known (from webhook integration)
- ✅ Authentication method known (API key)
- ✅ Storage structure ready (state.json)
- ✅ TUI viewer ready (Govly viewer screen)

---

## Alternative: SAM.gov API

As a **potential alternative** or supplement to Govly, the official government API is available:

### GSA Get Opportunities API
- **Documentation:** https://open.gsa.gov/api/get-opportunities-public-api/
- **Access:** Public, free
- **Coverage:** Official federal opportunities from SAM.gov
- **Authentication:** API key from api.data.gov
- **Rate Limit:** 1,000 requests/hour (public tier)

### Comparison

| Feature | Govly API | SAM.gov API |
|---------|-----------|-------------|
| **Access** | Enterprise only | Public |
| **Cost** | Paid (likely) | Free |
| **Coverage** | 40+ vehicles | Official SAM.gov |
| **AI Features** | Yes (GPT-3.5) | No |
| **Rate Limits** | Unknown | 1,000/hour |
| **Documentation** | Enterprise docs | Public docs |

**Recommendation:** Consider implementing SAM.gov API integration as a free, accessible alternative while waiting for Govly enterprise access.

---

## Implementation Plan (When Unblocked)

### Phase 1: Setup & Configuration
1. Obtain Govly API key
2. Add API key to environment configuration
3. Review official API documentation
4. Understand rate limits and pagination

### Phase 2: API Client Implementation
1. Create `mcp/integrations/govly_client.py`
2. Implement authentication
3. Implement opportunity fetching
4. Add error handling and retries
5. Add logging

### Phase 3: Sync Service
1. Create `mcp/services/govly_sync.py`
2. Implement scheduled polling (every 5-10 minutes)
3. Deduplicate with webhook-ingested data
4. Merge into state.json
5. Add FY routing

### Phase 4: Integration
1. Wire into status_bridge for monitoring
2. Add manual sync button to TUI
3. Add configuration for sync interval
4. Test with real data

**Estimated Time:** 6-8 hours (after blockers removed)

---

## Next Steps

### Immediate Actions

1. **Contact Govly:**
   - Email: support@govly.com
   - Request: Enterprise API access and documentation
   - Context: DealCraft automation platform integration

2. **Alternative Implementation:**
   - Consider SAM.gov API as free alternative
   - Provides official federal opportunity data
   - Can be implemented without blocking

3. **Document User Decision:**
   - Does user have Govly enterprise access?
   - Is user willing to pay for Govly API access?
   - Should we implement SAM.gov instead/additionally?

### Parallel Work

While waiting for Govly API access:
- ✅ Proceed with Track C (Watcher Automation)
- ✅ Implement Outlook RFQ watcher
- ✅ Implement Fleeting Notes sync
- ✅ Implement Radar monitoring

---

## Conclusion

**Track B (Govly API Integration) is BLOCKED** pending:
1. Govly enterprise customer account
2. API key acquisition
3. Access to enterprise API documentation

**Recommendation:** Proceed with **Track C (Watcher Automation)** which has no external dependencies, then revisit Track B once Govly API access is secured.

**Alternative:** Consider implementing **SAM.gov API** integration as a free, accessible source of federal opportunities.

---

## References

- Govly Website: https://www.govly.com/
- Govly API Docs: https://docs.govly.com/
- Govly API Settings: https://www.govly.com/app/settings/api_settings
- SAM.gov API: https://open.gsa.gov/api/get-opportunities-public-api/
- Govly Support: support@govly.com
- TechCrunch Article: https://techcrunch.com/2023/11/02/govly-wants-to-make-it-easier-for-companies-to-spot-federal-contract-opportunities/
