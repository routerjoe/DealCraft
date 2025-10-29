# AI Account Plans Guide

**Version:** 1.0  
**Last Updated:** October 29, 2025 EDT  
**Sprint:** 12 - AI Account Plans

## Overview

The AI Account Plans feature generates strategic account plans for federal customers using AI-powered analysis of opportunities, forecasts, and historical data. Plans include OEM partner strategies, recommended approaches, and actionable next steps.

### Key Features

- 🤖 **AI-Powered Analysis** - Leverages OpenAI/Anthropic for strategic insights
- 🎯 **Customer Focus** - AFCENT and AETC specialization
- 🤝 **OEM Strategies** - Cisco, Nutanix, NetApp, Red Hat positioning
- 📊 **Data Integration** - Uses forecast and opportunity data
- 📝 **Obsidian Export** - Markdown files for team collaboration
- 📄 **Multiple Formats** - Markdown, PDF, JSON output

## Target Customers

### AFCENT (Air Forces Central Command)

**Profile:**
- **Mission:** Air operations in Middle East theater
- **Budget:** $2-4B annually for IT/infrastructure
- **Key Priorities:** Secure communications, data analytics, cloud migration
- **Decision Cycle:** 12-18 months for major programs
- **Buying Preferences:** SEWP, GSA MAS, Air Force Enterprise IT

**Strategic Opportunities:**
- Network modernization for distributed operations
- Secure cloud infrastructure (IL5/IL6)
- Data center consolidation
- Cybersecurity enhancements
- AI/ML for intelligence analysis

### AETC (Air Education and Training Command)

**Profile:**
- **Mission:** Recruit, train, and educate Airmen
- **Budget:** $1-2B annually for IT/infrastructure
- **Key Priorities:** Training systems, simulation, virtual reality, cloud services
- **Decision Cycle:** 9-12 months for training systems
- **Buying Preferences:** GSA MAS, AFWERX, SBIR contracts

**Strategic Opportunities:**
- Virtual training environments
- Learning management systems
- Cloud-based collaboration tools
- Simulation infrastructure
- Secure remote training capabilities

## OEM Partner Strategies

### Cisco - Networking & Security

**Strengths:**
- Market leader in enterprise networking
- Strong federal presence and clearances
- Comprehensive security portfolio (SecureX, Umbrella, Duo)
- Software-defined WAN solutions

**AFCENT Strategy:**
- Position for secure communications infrastructure
- SD-WAN for distributed theater operations
- Zero-trust security architecture
- Cloud-managed networking

**AETC Strategy:**
- Campus networking for training bases
- Secure collaboration (Webex for classified)
- Network analytics for training systems
- Meraki for simplified management

**Competitive Position:**
- vs. Juniper: Better federal relationships
- vs. Arista: Broader portfolio, more services
- vs. Palo Alto: Integrated security + networking

### Nutanix - Hyperconverged Infrastructure

**Strengths:**
- Simplified HCI platform
- Multi-cloud management
- Strong DoD presence
- Software-defined data center

**AFCENT Strategy:**
- Edge computing for forward locations
- Hybrid cloud for classified workloads
- Disaster recovery/business continuity
- Rapid deployment capabilities

**AETC Strategy:**
- VDI for training environments
- Private cloud for simulation systems
- Centralized management across bases
- Cost optimization through consolidation

**Competitive Position:**
- vs. VMware: Simpler licensing, lower TCO
- vs. Dell VxRail: Pure software approach
- vs. HPE SimpliVity: Better DoD traction

### NetApp - Storage & Data Management

**Strengths:**
- Enterprise storage leader
- Cloud data services (AWS, Azure, GCP)
- Data protection and compliance
- All-flash arrays for performance

**AFCENT Strategy:**
- High-performance storage for intelligence data
- Data tiering (hot/warm/cold)
- Cloud backup and archive
- Ransomware protection

**AETC Strategy:**
- Scalable storage for training content
- Cloud integration for distributed access
- Snapshot/backup for training systems
- Cost-effective capacity expansion

**Competitive Position:**
- vs. Dell EMC: Better cloud integration
- vs. Pure Storage: More features, broader portfolio
- vs. HPE: Stronger software capabilities

### Red Hat - Enterprise Linux & OpenShift

**Strengths:**
- DoD's standardized Linux platform
- Kubernetes and containers (OpenShift)
- Automation (Ansible)
- Strong open-source community

**AFCENT Strategy:**
- RHEL for secure server infrastructure
- OpenShift for application modernization
- Ansible for configuration management
- Satellite for patch management

**AETC Strategy:**
- RHEL for training system backends
- OpenShift for DevSecOps training
- Container-based training environments
- Automation for lab provisioning

**Competitive Position:**
- vs. SUSE: Better DoD adoption
- vs. Ubuntu: Enterprise support, certified
- vs. Windows: Lower licensing costs

## Input Schema

### Generate Account Plan Request

```json
{
  "customer": "AFCENT",
  "oem_partners": ["Cisco", "Nutanix"],
  "fiscal_year": "FY26",
  "focus_areas": ["modernization", "security", "cloud"],
  "format": "markdown",
  "options": {
    "include_forecast": true,
    "include_opportunities": true,
    "confidence_threshold": 0.7,
    "max_recommendations": 10
  }
}
```

**Parameters:**
- `customer` (required): "AFCENT" or "AETC"
- `oem_partners` (required): Array of ["Cisco", "Nutanix", "NetApp", "Red Hat"]
- `fiscal_year` (required): "FY26", "FY27", etc.
- `focus_areas` (optional): ["modernization", "security", "cloud", "networking", "storage"]
- `format` (required): "markdown", "pdf", or "json"
- `options` (optional): Additional generation options

## AI Reasoning Methodology

### Step 1: Data Collection

1. **Forecast Data:** Pull opportunities for customer + fiscal year
2. **Historical Wins:** Analyze past successful engagements
3. **Market Trends:** Federal IT spending patterns
4. **OEM Positioning:** Partner capabilities and strengths
5. **Customer Profile:** Mission, priorities, buying behavior

### Step 2: Analysis

```
AI Prompt Template:
"You are a federal sales strategist. Analyze the following data and generate
an account plan for [CUSTOMER] in [FISCAL_YEAR] focusing on [OEM_PARTNERS].

Data:
- Customer Profile: [profile]
- Forecast Opportunities: [opportunities]
- Historical Performance: [history]
- OEM Capabilities: [oem_data]

Generate:
1. Executive Summary
2. Customer Priorities
3. OEM Strategy Recommendations
4. Opportunity Prioritization
5. Action Plan with Timeline
6. Risk Assessment
"
```

### Step 3: Reasoning Output

The AI provides:
- **Confidence Scores:** 0.0-1.0 for each recommendation
- **Supporting Evidence:** References to forecast data
- **Alternatives:** Multiple approaches with trade-offs
- **Risk Factors:** Competitive threats, budget constraints
- **Success Metrics:** How to measure plan effectiveness

### Step 4: Post-Processing

1. Validate recommendations against business rules
2. Ensure OEM partner compatibility
3. Check fiscal year alignment
4. Format for selected output type
5. Export to Obsidian

## Output Formats

### Markdown (Obsidian)

```markdown
---
customer: AFCENT
fiscal_year: FY26
generated: 2025-10-29
oem_partners: [Cisco, Nutanix]
confidence: 0.85
---

# FY26 Account Plan: AFCENT

## Executive Summary

AFCENT presents a $3.2M opportunity in FY26 focused on secure cloud
infrastructure and network modernization...

## Customer Priorities

1. **Secure Communications** (High Priority)
   - Upgrade classified network infrastructure
   - Implement zero-trust architecture
   - Deploy SD-WAN for theater operations

2. **Cloud Migration** (Medium Priority)
   - Move applications to IL5 cloud
   - Implement hybrid cloud management
   - Data sovereignty compliance

## OEM Strategy

### Cisco - Lead with Security + Networking

**Opportunity:** Network Modernization ($1.5M)
**Approach:** Position SD-WAN + SecureX bundle
**Confidence:** 0.87
**Timeline:** Q2 FY26
**Competition:** Juniper (low threat), Palo Alto (medium)

**Action Items:**
- [ ] Schedule architecture workshop
- [ ] Provide IL5 reference architecture
- [ ] Connect with DISA for compliance
- [ ] Demo SD-WAN capabilities

### Nutanix - Follow with HCI for Edge

**Opportunity:** Edge Computing Infrastructure ($800K)
**Approach:** HCI for forward operating locations
**Confidence:** 0.73
**Timeline:** Q3 FY26
**Competition:** VMware (medium threat)

**Action Items:**
- [ ] Site survey for edge locations
- [ ] Provide TCO analysis vs VMware
- [ ] Demo rapid deployment capabilities
- [ ] Arrange DoD reference calls

## Opportunity Prioritization

| Rank | Opportunity | Amount | Close Date | OEM | Confidence |
|------|-------------|--------|------------|-----|------------|
| 1 | Network Modernization | $1.5M | 2026-03-31 | Cisco | 0.87 |
| 2 | Cloud Infrastructure | $900K | 2026-05-15 | Nutanix | 0.78 |
| 3 | Edge Computing | $800K | 2026-06-30 | Nutanix | 0.73 |

## Timeline

**Q1 FY26 (Oct-Dec 2025)**
- Customer engagement and discovery
- Cisco architecture workshop
- Initial proposals

**Q2 FY26 (Jan-Mar 2026)**
- Cisco opportunity closure
- Nutanix edge computing scoping
- AETC cross-sell exploration

**Q3 FY26 (Apr-Jun 2026)**
- Nutanix opportunity closure
- Cloud migration planning
- FY27 pipeline development

## Risk Assessment

**High Risk:**
- Budget cuts due to federal spending freeze
- Competitive displacement by incumbent vendor

**Medium Risk:**
- Extended decision timelines
- Security accreditation delays

**Low Risk:**
- Technical objections (strong solutions)
- Pricing concerns (competitive positioning)

## Success Metrics

- Close rate: 60%+ on prioritized opportunities
- Revenue: $2.0M+ in FY26
- Customer satisfaction: 4.5/5
- Renewal rate: 90%+
- Expansion opportunities: 2+ identified

---
Generated by AI Account Plans v1.0
```

### JSON Format

```json
{
  "customer": "AFCENT",
  "fiscal_year": "FY26",
  "generated": "2025-10-29T13:00:00Z",
  "confidence": 0.85,
  "oem_partners": ["Cisco", "Nutanix"],
  "executive_summary": "AFCENT presents a $3.2M opportunity...",
  "priorities": [
    {
      "title": "Secure Communications",
      "priority": "high",
      "description": "Upgrade classified network infrastructure..."
    }
  ],
  "oem_strategies": [
    {
      "oem": "Cisco",
      "opportunity": "Network Modernization",
      "amount": 1500000,
      "confidence": 0.87,
      "approach": "Position SD-WAN + SecureX bundle",
      "timeline": "Q2 FY26",
      "competition": ["Juniper", "Palo Alto"],
      "action_items": [
        "Schedule architecture workshop",
        "Provide IL5 reference architecture"
      ]
    }
  ],
  "opportunities": [
    {
      "rank": 1,
      "title": "Network Modernization",
      "amount": 1500000,
      "close_date": "2026-03-31",
      "oem": "Cisco",
      "confidence": 0.87
    }
  ],
  "risks": {
    "high": ["Budget cuts", "Competitive displacement"],
    "medium": ["Extended timelines", "Security delays"],
    "low": ["Technical objections", "Pricing concerns"]
  },
  "success_metrics": {
    "close_rate_target": 0.60,
    "revenue_target": 2000000,
    "satisfaction_target": 4.5,
    "renewal_target": 0.90
  }
}
```

## Obsidian Export

Plans are exported to structured directories:

```
obsidian/50 Dashboards/Account Plans/
├── AFCENT/
│   ├── FY26_AFCENT_Account_Plan.md
│   ├── Cisco_Strategy_AFCENT_FY26.md
│   ├── Nutanix_Strategy_AFCENT_FY26.md
│   └── Opportunities_AFCENT_FY26.md
└── AETC/
    ├── FY26_AETC_Account_Plan.md
    ├── NetApp_Strategy_AETC_FY26.md
    ├── Red_Hat_Strategy_AETC_FY26.md
    └── Opportunities_AETC_FY26.md
```

## Usage Examples

### Generate AFCENT Plan

```bash
curl -X POST http://localhost:8000/v1/account-plans/generate \
  -H "Content-Type: application/json" \
  -d '{
    "customer": "AFCENT",
    "oem_partners": ["Cisco", "Nutanix"],
    "fiscal_year": "FY26",
    "focus_areas": ["modernization", "security"],
    "format": "markdown"
  }'
```

### Generate Multi-OEM AETC Plan

```bash
curl -X POST http://localhost:8000/v1/account-plans/generate \
  -H "Content-Type: application/json" \
  -d '{
    "customer": "AETC",
    "oem_partners": ["NetApp", "Red Hat", "Cisco"],
    "fiscal_year": "FY26",
    "focus_areas": ["cloud", "training"],
    "format": "pdf"
  }'
```

### List Available Formats

```bash
curl http://localhost:8000/v1/account-plans/formats
```

## Best Practices

### Plan Generation

1. **Start with One OEM** - Focus on primary partner first
2. **Validate Customer Profile** - Ensure current information
3. **Include Forecast Data** - Reference real opportunities
4. **Review AI Reasoning** - Check confidence scores
5. **Customize Templates** - Adjust for customer specifics

### OEM Strategy

1. **Lead with Strength** - Position OEM's core capability
2. **Address Competitors** - Acknowledge and differentiate
3. **Provide References** - DoD success stories
4. **Show ROI** - TCO analysis and business case
5. **Timeline Realistic** - Account for federal procurement

### Collaboration

1. **Share in Obsidian** - Team visibility and feedback
2. **Version Control** - Track plan iterations
3. **Regular Updates** - Quarterly refresh minimum
4. **Stakeholder Review** - Sales, SEs, management
5. **Track Metrics** - Measure plan effectiveness

## Limitations

- **AI Accuracy:** Recommendations are suggestions, not guarantees
- **Data Freshness:** Based on available forecast/opportunity data
- **Customer Dynamics:** May not reflect recent organizational changes
- **Competition:** Intel on competitors may be incomplete
- **Budget Constraints:** Assumes historical spending patterns

## Future Enhancements

Planned for post-Sprint 12:
- **Interactive Refinement** - Chat interface for plan iteration
- **Competitive Intelligence** - Integration with GovWin/Bloomberg
- **Budget Tracking** - Real-time federal spending data
- **Success Prediction** - ML model for win probability
- **Automated Updates** - Quarterly plan refresh
- **Multi-Customer Plans** - Theater-wide strategies
- **Template Library** - Pre-built plans for common scenarios

---

**Related Documentation:**
- [Sprint 12 Plan](../sprint_plan.md)
- [API Endpoints](../api/endpoints.md)
- [Forecast Engine](forecast_engine.md)
- [Obsidian Integration](../obsidian/README.md)