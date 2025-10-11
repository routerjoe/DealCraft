---
type: hub.people
person_name: Jane Smith
zkid: ""
created: 2025-10-11T21:56:46.980Z
updated: 2025-10-11T21:56:46.983Z
tags:
  - person
role: Program Manager
orgs:
  - "[[Acme .]]"
email: jane.smith@example.com
phone: ""
accounts: []
oems: []
contracts: []
notes: ""
---
# `= default(this.person_name, this.file.name)` (People)

## Overview
- Role: `= default(this.role, "—")`
- Orgs: `= default(join(this.orgs, ", "), "—")`
- Email: `= default(this.email, "—")`
- Phone: `= default(this.phone, "—")`

## Affiliations
- Accounts: `= default(join(this.accounts, ", "), "—")`
- OEMs: `= default(join(this.oems, ", "), "—")`
- Contracts: `= default(join(this.contracts, ", "), "—")`

## Notes
- `= default(this.notes, "—")`

## Related RFQs
```dataview
TABLE rfq_id, radar_id, status, est_close, customer
FROM "60 Sources"
WHERE type = "rfq" AND contains(links, this.file.link)
```

## Related Opportunities
```dataview
TABLE file.link AS Opportunity, stage, radar_level, customer, contract_vehicle, est_close
FROM "40 Projects"
WHERE type = "opportunity" AND contains(links, this.file.link)
SORT est_close ASC
```
