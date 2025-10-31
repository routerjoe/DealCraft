# RFQ Rules Rollout Plan

Purpose: safely adopt the new rules, scoring, and analytics with staged validation and clear success criteria before enabling auto-decline.

Core implementation
- Engine and rules: [src/tools/rfq/rules.ts](src/tools/rfq/rules.ts)
- RFQ tools: [src/tools/rfq/index.ts](src/tools/rfq/index.ts)
- Analytics tool: [src/tools/analytics/index.ts](src/tools/analytics/index.ts)
- DB initialization and seeding: [src/database/init.ts](src/database/init.ts)
- Seed SQL: [future features/rfq update/rfq_config.sql](future features/rfq update/rfq_config.sql)

Safety defaults
- RFQ_AUTO_DECLINE_ENABLED=false by default. NO-GO is not auto-recorded unless explicitly enabled.
- Outlook deletion is never automatic; requires delete_from_outlook=true.
- SMTP settings required for internal notification emails. See [src/email/sendRfqEmail.ts](src/email/sendRfqEmail.ts).

Phase 0 — Prerequisites
- Ensure server starts cleanly and seeds config at startup.
- Copy .env.example to .env and keep RFQ_AUTO_DECLINE_ENABLED=false during validation.
- Confirm the following CLI checks:
  - Rule unit tests: npm run test:rfq-rules
  - E2E smoke test: npm run test:rfq-e2e

Phase 1 — Validation Window (2–4 weeks, auto-decline disabled)
- Workflow
  1) Process incoming RFQs as usual (rfq_process_email or rfq_batch_process).
  2) Populate attributes via rfq_set_attributes for value, competition, tech_vertical, oem, has_previous_contract, deadline, customer.
  3) Run rfq_analyze to view score, rule flags, and a missing-fields checklist.
  4) Run rfq_apply_rules to record rule outcomes and recommendation. Auto-decline remains disabled, so no decisions are auto-recorded.
  5) Manually decide GO/NO-GO using rfq_update_decision when needed.

- Metrics to monitor weekly
  - Rule triggers by rule_id
  - Auto-decline candidates by rule_id (diagnostic only while disabled)
  - Score distribution by tier and recommendation
  - Strategic customer hit rate
  - OEM occurrence counts vs thresholds (analytics_oem_business_case_90d)

- How to pull data
  - OEM view: call analytics_oem_business_case_90d with optional min_occurrences and min_total_value.
  - Activity log: query SQLite for action IN ('rules_applied','scored','decision') using a lightweight ad-hoc script or direct SQLite inspection.
  - Use server logs in ~/RedRiver/logs for trace-level analysis.

- Validation targets
  - False positive rate for auto-decline candidates ≤ 5%
  - Score alignment with human decision ≥ 85% for GO buckets (≥60)
  - Rule coverage: R001, R005, R006 trigger appropriately with minimal noise

Phase 2 — Partial Enablement (opt-in)
- Recommended initial rules to allow marking NO-GO automatically:
  - R001 Auto-Decline Consolidated Notices
  - R005 Ultra Low Value Auto-Decline
  - R006 Late RFQ Auto-Decline with Pattern Tracking
- Keep RFQ_AUTO_DECLINE_ENABLED=false globally and selectively enable operationally by running rfq_apply_rules and recording decisions manually for a subset, or:
  - Turn RFQ_AUTO_DECLINE_ENABLED=true and immediately monitor activity_log and decision_log daily.
- Continue manual oversight; never enable Outlook deletion by default.

Phase 3 — Full Enablement Decision
- Decision gate: Once KPIs meet targets for 2 consecutive weeks, enable:
  - RFQ_AUTO_DECLINE_ENABLED=true in .env
- Daily checks:
  - Review new NO-GO decisions created by auto-decline
  - Randomly sample to confirm accuracy
  - Escalate misfires; adjust thresholds or disable specific rules temporarily if needed

Enablement procedure
1) Edit .env and set RFQ_AUTO_DECLINE_ENABLED=true
2) Restart MCP server: npm run build && npm run start (or restart your host process)
3) Verify by running rfq_apply_rules on a sample RFQ and confirming NO-GO is auto-recorded only when rules match
4) Document enablement with date/time and send internal notice

Rollback procedure
- Set RFQ_AUTO_DECLINE_ENABLED=false in .env and restart MCP server.
- All rules remain evaluative; no decisions will be auto-recorded.
- Review recent auto-created NO-GO decisions and rescind if appropriate via rfq_update_decision.

Training & reference
- Keep a printed quick reference of rules and thresholds; see: docs/rfq/QUICK_REFERENCE.md
- Encourage use of rfq_analyze to check a missing-field checklist before rule application.
- Review OEM analytics weekly: analytics_oem_business_case_90d.

Success criteria
- Time saved: measurable reduction in review time for low-value/late/consolidated RFQs
- Focus: increased proportion of strategic/high-value GO decisions
- Intelligence: OEM occurrences trending into business case recommendations with clear action

Appendix — Handy examples
- Set attributes:
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

- Apply rules:
  { "name": "rfq_apply_rules", "arguments": { "rfq_id": 123, "rfq_type": "renewal", "quantity": 1 } }

- Score only:
  { "name": "rfq_calculate_score", "arguments": { "rfq_id": 123 } }

- OEM analytics:
  { "name": "analytics_oem_business_case_90d", "arguments": { "min_occurrences": 0, "min_total_value": 0 } }