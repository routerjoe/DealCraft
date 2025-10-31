# RFQ Rules Quick Reference

This quick reference summarizes the RFQ rules, thresholds, scoring, and tool usage implemented in this MCP server.

Core implementation files
- [src/tools/rfq/rules.ts](src/tools/rfq/rules.ts)
- [src/tools/rfq/index.ts](src/tools/rfq/index.ts)
- [src/tools/analytics/index.ts](src/tools/analytics/index.ts)
- [src/database/init.ts](src/database/init.ts)
- [future features/rfq update/rfq_config.sql](future features/rfq update/rfq_config.sql)

Safety defaults
- Auto-decline is disabled by default: set RFQ_AUTO_DECLINE_ENABLED=false in [.env.example](.env.example) or your .env.
- Outlook deletion is disabled by default; cleanup deletes Outlook email only when delete_from_outlook is true.
- SMTP settings for internal RFQ notification emails: see [src/email/sendRfqEmail.ts](src/email/sendRfqEmail.ts) and configure in .env.

1) Auto-Decline Triggers
- Consolidated notices: eBuy admin, Govly saved searches.
- High competition + low value renewals: 125+ bidders and < 15K and renewal.
- Ultra low value: < 2K total or single license renewal.
- Insufficient time: ≤ 2 days remaining with attachments/complexity.

2) Always Flag for Immediate Review
- $1M+ value (executive notification).
- $200K–$1M (sales team alert).
- Strategic customers (see list below).
- < 20 bidders + $20K+ value.
- Zero Trust / Data Center / Enterprise Networking (any value).
- Existing customer renewals.

3) Strategic Customers (15)
- CRITICAL: Customer Alpha, ARCENT, US CYBERCOMMAND, AFSOC, USSOCOM, Space Force, DARPA
- HIGH: Customer Beta, Hill AFB, Eglin AFB, Tyndall AFB, Patrick AFB, Andrews AFB, Bolling AFB, AFOSI

4) Value Tiers
- TIER 1: $1M+ → Immediate executive notification
- TIER 2: $200K–$1M → Sales team priority
- TIER 3: $20K–$200K → Standard review process
- TIER 4: < $20K → Consider auto-decline

5) Technology Priorities
- HIGH: Zero Trust, Data Center, Enterprise Networking, Cybersecurity
- MEDIUM: Cloud Migration, AI/ML Infrastructure, SIEM/Security Analytics, SD-WAN, Hybrid Cloud, Storage/Infrastructure, Application Delivery

6) OEM Tracking (New Business)
- Atlassian (5+), Graylog (5+), LogRhythm (5+), Sparx (8+), Quest/Toad (5+)
- Action: Log occurrences; when threshold reached, generate business case for partnership review.

7) Scoring System (0–100)
- Value (0–40): $1M+=40, $200K+=30, $20K+=20, <$20K=10
- Customer (0–25): CRITICAL=25, HIGH=15, Standard=0
- Competition (0–15): <20=15, <50=10, <100=5, 100+=0
- Technology (0–10): HIGH=10, MEDIUM=5, Other=0
- OEM (0–10): Authorized=10, Not authorized=0
- Renewal (0–10): Existing customer=10, New=0
- Recommendations:
  - 75–100: GO – High Priority
  - 60–74: GO – Consider Pursuit
  - 45–59: REVIEW – Conditional GO
  - 30–44: REVIEW – Likely NO-GO
  - 0–29: NO-GO – Auto-Decline

8) Decision Workflow
- Check Auto-Decline rules → If match, auto-decline (when enabled) and log reason.
- Check strategic/high-value flags → Immediate review/alerts.
- Calculate score → Use thresholds to guide GO/NO-GO.
- Log decision and track OEM occurrences.

MCP tools (RFQ)
- rfq_set_attributes
  - Purpose: Update RFQ fields used by rules/scoring.
  - Args: rfq_id, estimated_value?, competition_level?, tech_vertical?, oem?, has_previous_contract?, deadline?, customer?
  - Example:
    {
      "name": "rfq_set_attributes",
      "arguments": {
        "rfq_id": 123,
        "estimated_value": 250000,
        "competition_level": 15,
        "tech_vertical": "Zero Trust",
        "oem": "Cisco",
        "has_previous_contract": true,
        "deadline": "2025-10-20",
        "customer": "Space Force"
      }
    }

- rfq_calculate_score
  - Purpose: Compute 0–100 score and recommendation and persist to RFQ.
  - Args: rfq_id
  - Example:
    { "name": "rfq_calculate_score", "arguments": { "rfq_id": 123 } }

- rfq_apply_rules
  - Purpose: Apply rules R001–R009, compute score, log outcomes; honor RFQ_AUTO_DECLINE_ENABLED for NO-GO marking (no Outlook deletion).
  - Args: rfq_id, rfq_type?, quantity?
  - Example:
    { "name": "rfq_apply_rules", "arguments": { "rfq_id": 123, "rfq_type": "renewal", "quantity": 1 } }

- rfq_track_oem_occurrence
  - Purpose: Log OEM occurrence for an RFQ and update counters; feeds analytics view.
  - Args: rfq_id, oem?, estimated_value?, competition_level?, technology_vertical?
  - Example:
    {
      "name": "rfq_track_oem_occurrence",
      "arguments": {
        "rfq_id": 123,
        "oem": "Atlassian",
        "estimated_value": 15000,
        "competition_level": 80,
        "technology_vertical": "DevOps/Collaboration"
      }
    }

- rfq_analyze
  - Purpose: Returns RFQ + attachments + CSVs, plus score, rule outcomes, auto-decline candidates, and missing-fields checklist (enhanced).
  - Args: rfq_id
  - Notes: Use rfq_set_attributes to fill missing fields and then run rfq_apply_rules.

MCP tools (Analytics)
- analytics_oem_business_case_90d
  - Purpose: 90-day OEM rollup view from seeded SQL.
  - Args: min_occurrences?, min_total_value?
  - Example:
    { "name": "analytics_oem_business_case_90d", "arguments": { "min_occurrences": 0, "min_total_value": 0 } }

Operational notes
- Seeding: Config is seeded from [future features/rfq update/rfq_config.sql](future features/rfq update/rfq_config.sql) at server startup.
- Schema: RFQs include fields competition_level, tech_vertical, oem, has_previous_contract, rfq_score, rfq_recommendation. See [src/database/init.ts](src/database/init.ts).
- Tests: Run npm run test:rfq-rules and npm run test:rfq-e2e to validate the rules and an end-to-end flow.

Tips
- Keep RFQ_AUTO_DECLINE_ENABLED=false during initial validation. Review rule outcomes first, then decide on enabling auto-decline.
- Use rfq_set_attributes to populate structured values before rule application.
- Use analytics_oem_business_case_90d weekly to assess tracked OEMs for business case development.