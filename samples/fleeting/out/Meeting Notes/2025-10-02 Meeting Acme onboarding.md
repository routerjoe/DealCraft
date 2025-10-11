---
type: meeting
title: Acme onboarding
date: 2025-10-02
time: 2:00 PM ET
attendees:
  - Jane Smith
  - Bob Taylor
  - ""
organizations: []
customer: ""
related_opportunities: []
related_rfqs: []
oems: []
distributors: []
contract_office: ""
status: open
follow_up_due: 2025-10-10
action_items: []
links: []
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
- Follow-up: 2025-10-10
- Covered onboarding timeline

N: Jane Smith
T: Program Manager
E: jane.smith@example.com
C: Acme Inc.

N: Alan Smithee
T: CIO
E: alan@example.org
C: Contoso LLC

- [ ] Collect reference architectures
- [ ] Schedule discovery workshop — internal


## Action Items
- [ ] Collect reference architectures
- [ ] Schedule discovery workshop — internal

## Cross-Links
- Customer: `= default(this.customer, "—")`
- Opportunities: `= default(join(this.related_opportunities, ", "), "—")`

## Recent Attachments and Screens
- Save to: `60 Sources/screenshots/YYYY/MM/`
- Filename: `YYYYMMDD-HHmm-context-entity.png`
- Example: ![[60 Sources/screenshots/2025/09/20250925-1535-meeting-EXAMPLE.png]]
