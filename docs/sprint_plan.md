# Sprint 12: AI Account Plans (AFCENT/AETC Focus)

**Start:** Wednesday, October 29, 2025 EDT  
**Target Merge Window:** Monday, November 10, 2025 EDT

## Objectives

- Generate AI-powered account plans for key federal customers
- Focus on AFCENT (Air Forces Central) and AETC (Air Education and Training Command)
- Support major OEM partners: Cisco, Nutanix, NetApp, Red Hat
- Export plans to Obsidian for sales team collaboration
- Provide reasoning and strategy recommendations
- Integrate with existing forecast and opportunity data

## Scope (In)

- POST /v1/account-plans/generate endpoint
- GET /v1/account-plans/formats endpoint
- Account plan generation for AFCENT and AETC
- OEM partner strategies (Cisco, Nutanix, NetApp, Red Hat)
- AI reasoning for recommendations
- Obsidian export under 50 Dashboards
- Input schema validation
- Multiple output formats (markdown, PDF, JSON)
- Integration with forecast data
- Stub implementation with "not_implemented" responses

## Scope (Out)

- Real-time plan updates
- Multi-year strategic planning (>2 years)
- Budget allocation optimization
- Historical trend analysis (covered in Sprint 14)
- Interactive plan editing
- Collaboration features (comments, approvals)
- Integration with external CRM systems
- Automated plan delivery via email

## Interfaces & Contracts

### API Endpoints

**POST /v1/account-plans/generate**
```json
Request:
{
  "customer": "AFCENT|AETC",
  "oem_partners": ["Cisco", "Nutanix", "NetApp", "Red Hat"],
  "fiscal_year": "FY26",
  "focus_areas": ["modernization", "security", "cloud"],
  "format": "markdown|pdf|json"
}

Response (Stub):
{
  "status": "not_implemented",
  "message": "Account plan generation will be implemented in Sprint 12 development phase",
  "plan_id": null,
  "preview": {
    "customer": "AFCENT",
    "oem_partners": ["Cisco", "Nutanix"],
    "fiscal_year": "FY26"
  }
}
```

**GET /v1/account-plans/formats**
```json
Response (Stub):
{
  "status": "not_implemented",
  "message": "Format listing will be implemented in Sprint 12 development phase",
  "formats": [
    {
      "id": "markdown",
      "name": "Markdown",
      "extension": ".md",
      "supports_obsidian": true
    },
    {
      "id": "pdf",
      "name": "PDF Document",
      "extension": ".pdf",
      "supports_obsidian": false
    },
    {
      "id": "json",
      "name": "JSON Data",
      "extension": ".json",
      "supports_obsidian": false
    }
  ]
}
```

### Obsidian Export Paths

Generated plans exported to:
```
obsidian/50 Dashboards/Account Plans/
├── AFCENT/
│   ├── FY26_AFCENT_Account_Plan.md
│   ├── Cisco_Strategy_AFCENT.md
│   └── Nutanix_Strategy_AFCENT.md
└── AETC/
    ├── FY26_AETC_Account_Plan.md
    ├── NetApp_Strategy_AETC.md
    └── Red_Hat_Strategy_AETC.md
```

### Python Module

**Location:** `mcp/api/v1/account_plans.py`

**Functions:**
- `generate_account_plan()` - Stub returning not_implemented
- `list_formats()` - Stub returning supported formats
- Includes request/response models with Pydantic

## Deliverables

### 1. Code
- 🆕 `mcp/api/v1/account_plans.py` - API endpoint stubs
  - POST /v1/account-plans/generate
  - GET /v1/account-plans/formats
  - Pydantic models for validation
  - Stub responses with "not_implemented": true

### 2. Tests
- 🆕 `tests/test_account_plans_stub.py`
  - Endpoint mounting verification
  - Request/response header validation
  - Schema validation tests
  - Error handling tests

### 3. Docs
- 🆕 `/docs/sprint_plan.md` - This sprint plan
- 🆕 `/docs/guides/ai_account_plans.md` - Complete guide
  - Input schema documentation
  - AI reasoning methodology
  - OEM partner strategies
  - Obsidian export examples
  - Customer profiles (AFCENT/AETC)

### 4. Ops/Runbooks
- Account plan generation workflow
- Export path management
- Template customization guide

## Success Criteria / DoD

- [ ] Sprint plan created (docs/sprint_plan.md)
- [ ] AI account plans guide complete (docs/guides/ai_account_plans.md)
- [ ] API stubs created (mcp/api/v1/account_plans.py)
- [ ] Python tests created (tests/test_account_plans_stub.py)
- [ ] All tests passing (endpoint mounting, headers, not_implemented responses)
- [ ] Endpoints return 200 with "not_implemented": true
- [ ] Request/response models defined with Pydantic
- [ ] Header validation (x-request-id, x-latency-ms)
- [ ] Documentation complete
- [ ] Code committed with message "docs(sprint12): add sprint plan + stubs"
- [ ] Branch pushed to origin
- [ ] Draft PR opened with labels: sprint, 12, seed, draft

## Risks & Mitigations

### Risk: AI Quality Inconsistency
**Impact:** High - Poor recommendations damage credibility  
**Probability:** Medium  
**Mitigation:**
- Document reasoning methodology clearly
- Include confidence scores
- Require human review before finalization
- Provide editable templates
- Reference source data

### Risk: OEM Partner Strategy Conflicts
**Impact:** Medium - Competing recommendations  
**Probability:** Low  
**Mitigation:**
- Document OEM overlap areas
- Provide complementary positioning
- Include exclusivity clauses
- Allow multi-vendor strategies
- Reference competitive analysis

### Risk: Customer Profile Accuracy
**Impact:** High - Incorrect assumptions lead to poor plans  
**Probability:** Medium  
**Mitigation:**
- Validate with sales team
- Include data sources
- Support profile updates
- Allow manual overrides
- Document assumptions clearly

### Risk: Obsidian Export Path Conflicts
**Impact:** Low - Files overwrite existing plans  
**Probability:** Low  
**Mitigation:**
- Include timestamps in filenames
- Version control for plans
- Backup existing files
- Support custom export paths
- Document naming conventions

## Validation Steps

### 1. Local API Testing

```bash
# Test account plan generation endpoint
curl -X POST http://localhost:8000/v1/account-plans/generate \
  -H "Content-Type: application/json" \
  -d '{
    "customer": "AFCENT",
    "oem_partners": ["Cisco", "Nutanix"],
    "fiscal_year": "FY26",
    "format": "markdown"
  }'

# Expected: 200 with "not_implemented": true

# Test formats endpoint
curl http://localhost:8000/v1/account-plans/formats

# Expected: 200 with format list
```

### 2. Python Tests

```bash
# Run account plans tests
pytest tests/test_account_plans_stub.py -v

# Verify all pass with stub responses
```

### 3. Header Validation

```bash
# Check response headers
curl -i http://localhost:8000/v1/account-plans/formats | grep -E "x-request-id|x-latency-ms"
```

### 4. Documentation Review

```bash
# Verify docs exist
cat docs/sprint_plan.md
cat docs/guides/ai_account_plans.md
```

## Checklist

- [x] Design reviewed
- [ ] Sprint plan created (docs/sprint_plan.md)
- [ ] AI account plans guide created (docs/guides/ai_account_plans.md)
- [ ] API stubs created (mcp/api/v1/account_plans.py)
- [ ] Python tests created (tests/test_account_plans_stub.py)
- [ ] All tests passing
- [ ] Documentation complete and reviewed
- [ ] Code committed with message "docs(sprint12): add sprint plan + stubs"
- [ ] Branch pushed to origin
- [ ] Draft PR opened with labels: sprint, 12, seed, draft
- [ ] Ready for development phase

## Notes

- Account plans focus on AFCENT and AETC initially
- OEM strategies: Cisco (networking), Nutanix (HCI), NetApp (storage), Red Hat (Linux/OpenShift)
- AI reasoning uses existing forecast data and opportunity analysis
- Plans exported to Obsidian 50 Dashboards for visibility
- Full implementation in development phase will include:
  - OpenAI/Anthropic integration for reasoning
  - Template-based plan generation
  - PDF export via markdown → PDF conversion
  - Interactive plan refinement

---

**Next Steps After Sprint:**
1. Implement AI reasoning engine
2. Create plan templates for AFCENT/AETC
3. Add OEM partner strategy library
4. Build PDF export pipeline
5. Set up automated plan refresh (quarterly)