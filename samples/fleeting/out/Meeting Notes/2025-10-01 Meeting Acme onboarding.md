---
type: meeting
title: Acme onboarding
date: 2025-10-01
time: 10:00 AM ET
attendees:
  - John Doe
  - Jane Smith
  - ""
organizations: []
customer: ""
related_opportunities: []
related_rfqs: []
oems: []
distributors: []
contract_office: ""
status: open
follow_up_due: 2025-10-05
action_items: []
links:
  - https://example.com/specs
created: ""
updated: ""
tags:
  - meeting
---

```dataviewjs
const t = dv.current().title ?? dv.current().file.name;
dv.header(1, t);
```

## Agenda
-

## Notes
- Reviewed initial scope
- Follow-up: 2025-10-05
- Link: https://example.com/specs

### notes
- Contract start date target mid-October

N: John Doe
T: Director, IT
E: john.doe@example.com
M: 555-555-1000
O: 703-555-2222
C: Acme Inc.
A: 123 Main St
Suite 200
Springfield, VA 22150

- [ ] Prepare proposal for Acme onboarding
  - [ ] Draft SOW
  - [ ] Pricing model v1
- [x] Close previous task from backlog

## Action Items
- [ ] Prepare proposal for Acme onboarding
- [ ] Draft SOW
- [ ] Pricing model v1

## Cross-Links
- Customer: `= default(this.customer, "—")`
- Opportunities: `= default(join(this.related_opportunities, ", "), "—")`

## Recent Attachments and Screens
- Save to: `60 Sources/screenshots/YYYY/MM/`
- Filename: `YYYYMMDD-HHmm-context-entity.png`
- Example: ![[60 Sources/screenshots/2025/09/20250925-1535-meeting-EXAMPLE.png]]
