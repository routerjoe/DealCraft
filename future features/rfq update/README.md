# Red River Sales Automation - Configuration Setup Guide

## 📋 Overview

This configuration system provides intelligent RFQ filtering and business intelligence tracking based on your strategic priorities.

**Your Configuration Settings:**
- **Strategic Customers:** 15 high-priority customers identified
- **Value Thresholds:** $20K, $200K, $1M+ tiers
- **Competition:** Situational - depends on OEM relationships
- **RFI Response:** Case-by-case evaluation
- **Tech Priorities:** Zero Trust, Data Center, Enterprise Networking
- **OEM Tracking:** Atlassian (5+), Graylog/LogRhythm (5+), Sparx (8+)

## 🗂️ Files Included

1. **rfq_config.sql** - Database schema with your strategic configuration
2. **rfq_filtering_config.py** - Python module with filtering logic
3. **setup.sh** - Automated setup script
4. **README.md** - This documentation file

## 🚀 Quick Start Installation

### Method 1: Automated Setup (Recommended)

```bash
# 1. Navigate to this directory
cd /path/to/rfq-config-setup

# 2. Run the setup script
./setup.sh

# 3. Follow the prompts to locate your database
# Example: ~/Library/Application Support/red-river-sales/sales_automation.db
```

### Method 2: Manual Installation

```bash
# 1. Find your database location
find ~ -name "sales_automation.db" 2>/dev/null

# 2. Apply the SQL schema
sqlite3 /path/to/sales_automation.db < rfq_config.sql

# 3. Verify tables were created
sqlite3 /path/to/sales_automation.db "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'config_%';"

# 4. Copy Python module to your MCP directory
cp rfq_filtering_config.py /path/to/your/mcp/server/
```

## 📊 Your Strategic Configuration

### Strategic Customers (15 Total)

**CRITICAL Priority (7):**
- AFCENT - Air Forces Central Command
- ARCENT - Army Central Command  
- US CYBERCOMMAND
- AFSOC - Air Force Special Operations Command
- USSOCOM - US Special Operations Command
- Space Force
- DARPA

**HIGH Priority (8):**
- AETC - Air Education and Training Command
- Hill AFB, Eglin AFB, Tyndall AFB, Patrick AFB
- Andrews AFB, Bolling AFB
- AFOSI

### Value Thresholds

| Tier | Range | Action | Priority |
|------|-------|--------|----------|
| **TIER 1** | $1M+ | Executive Notification | CRITICAL |
| **TIER 2** | $200K-$1M | Sales Team Alert | HIGH |
| **TIER 3** | $20K-$200K | Flag for Review | MEDIUM |
| **TIER 4** | <$20K | Standard Process | LOW |

### Technology Verticals

**HIGH Priority (4):**
- ✓ Zero Trust
- ✓ Data Center
- ✓ Enterprise Networking  
- ✓ Cybersecurity

**MEDIUM Priority (9):**
- Cloud Migration
- AI/ML Infrastructure
- SIEM/Security Analytics
- SD-WAN
- Hybrid Cloud
- Storage/Infrastructure
- Application Delivery

### OEM Tracking Strategy

**Tracking for New Business (Not Currently Authorized):**

| OEM | Threshold | Category | Notes |
|-----|-----------|----------|-------|
| Atlassian | 5 occurrences | DevOps/Collaboration | Growing DevOps market |
| Graylog | 5 occurrences | SIEM | Security analytics |
| LogRhythm | 5 occurrences | SIEM | Security analytics |
| Sparx | 8 occurrences | Enterprise Architecture | Niche market |
| Quest/Toad | 5 occurrences | Database Tools | Moderate opportunity |

**Currently Authorized Partners:**
- Cisco, Palo Alto Networks, Dell/EMC, NetApp
- F5 Networks, Microsoft, VMware, Red Hat

## 🎯 Automated Filtering Rules

### ✅ Auto-Decline Rules (Active)

**Rule 1:** Consolidated Notices
- Auto-decline eBuy/Govly consolidated emails
- No review needed

**Rule 2:** High Competition + Low Value  
- 125+ bidders AND <$15K AND software renewal
- Auto-decline to save time

**Rule 5:** Ultra Low Value
- <$2K total value OR single license renewal
- Auto-decline unless strategic customer

**Rule 6:** Insufficient Response Time
- ≤2 days to deadline with complex requirements
- Auto-decline + log pattern for source analysis

### 📊 Tracking & Review Rules (Active)

**Rule 3:** Track Niche OEMs
- Log every occurrence of Atlassian, Graylog, LogRhythm, Sparx, Quest/Toad
- Generate business case report when threshold reached
- **Agreement:** Track for 4-8 weeks, investigate if threshold met

**Rule 4:** RFI/MRR Strategic Response
- **Strategy:** Case-by-case evaluation
- Always respond to strategic customers (CRITICAL/HIGH)
- Respond to $50K+ opportunities
- Evaluate $25-50K opportunities
- Usually decline <$25K non-strategic

**Rule 7:** High-Value Alerts
- $1M+: Immediate executive notification
- $200K-$1M: Sales team priority
- $20K-$200K: Standard review

**Rule 8:** Existing Customer Renewals
- Flag all renewals for review
- Prioritize relationship retention

**Rule 9:** Strategic Technology
- Flag all Zero Trust, Data Center, Enterprise Networking
- Flag $50K+ in MEDIUM priority tech areas

## 📈 RFQ Scoring Algorithm

Every RFQ gets a 0-100 score:

**Scoring Breakdown:**
- **Value (0-40 pts):** $1M+ = 40, $200K+ = 30, $20K+ = 20, <$20K = 10
- **Customer (0-25 pts):** CRITICAL = 25, HIGH = 15, Standard = 0
- **Competition (0-15 pts):** <20 = 15, <50 = 10, <100 = 5, 100+ = 0
- **Technology (0-10 pts):** HIGH priority = 10, MEDIUM = 5, Other = 0
- **OEM (0-10 pts):** Authorized = 10, Not authorized = 0
- **Renewal (0-10 pts):** Existing customer = 10, New = 0

**Recommendations:**
- **75-100:** GO - High Priority (pursue immediately)
- **60-74:** GO - Consider Pursuit (good opportunity)
- **45-59:** REVIEW - Conditional GO (needs evaluation)
- **30-44:** REVIEW - Likely NO-GO (weak case)
- **0-29:** NO-GO - Auto-Decline (reject)

### Example Scoring

**USSOCOM Palo Alto Firewall:**
```
Value: $150K (TIER_2) = 30 pts
Customer: USSOCOM (CRITICAL) = 25 pts
Competition: 13 bidders = 15 pts
Technology: Enterprise Networking (HIGH) = 10 pts
OEM: Palo Alto (Authorized) = 10 pts
Renewal: No = 0 pts
------------------------
TOTAL: 90 pts = "GO - High Priority" ✅
```

**Generic Low-Value Software Renewal:**
```
Value: $5K (TIER_4) = 10 pts
Customer: Unknown = 0 pts
Competition: 127 bidders = 0 pts
Technology: Standard = 0 pts
OEM: Not authorized = 0 pts
Renewal: No = 0 pts
------------------------
TOTAL: 10 pts = "NO-GO - Auto-Decline" ❌
```

## 🏢 New OEM Business Case Evaluation

### Recommendation Criteria

**PURSUE (60+ points):**
- 8+ occurrences in 90 days OR
- $250K+ total value in 90 days OR
- 5+ diverse customers AND favorable competition

**CONSIDER (40-59 points):**
- 5+ occurrences in 90 days OR
- $100K+ total value in 90 days OR
- 3+ diverse customers AND moderate value

**MONITOR (20-39 points):**
- 3+ occurrences in 90 days OR
- $50K+ total value in 90 days
- Continue tracking, reassess in 90 days

**NO ACTION (<20 points):**
- Insufficient data
- Stop active tracking

### Example: Atlassian Business Case

**Scenario:** 5 RFQs in 90 days
- Total value: $75K
- 3 unique customers
- Avg competition: 80 bidders

**Scoring:**
- Frequency (5 = moderate): 25 pts
- Value ($75K): 10 pts
- Customer diversity (3): 5 pts
- Competition (80 = high): 0 pts
- **TOTAL: 40 pts**

**Recommendation:** "CONSIDER - Continue monitoring for 30 days"
**Action:** Track for another month. If reaches 7+ occurrences or $100K+, escalate to partnership discussions.

## 🔄 Usage Examples

### Python API Examples

#### Check Strategic Customer Status
```python
from rfq_filtering_config import is_strategic_customer

is_strategic_customer("AFCENT")  # True - CRITICAL
is_strategic_customer("Hill AFB")  # True - HIGH
is_strategic_customer("Random Base")  # False
```

#### Calculate RFQ Score
```python
from rfq_filtering_config import calculate_rfq_score

result = calculate_rfq_score(
    value=250000,           # $250K
    competition=45,          # 45 bidders
    customer="Space Force",  # CRITICAL customer
    tech_vertical="Zero Trust",  # HIGH priority
    oem="Cisco",            # Authorized partner
    has_previous_contract=True  # Renewal
)

print(result['score'])          # 85
print(result['recommendation']) # "GO - High Priority"
print(result['factors'])        # Detailed breakdown
```

#### Evaluate OEM Business Case
```python
from rfq_filtering_config import evaluate_new_oem_business_case

business_case = evaluate_new_oem_business_case(
    oem="Atlassian",
    occurrences_90d=7,
    total_value_90d=150000,
    unique_customers=4,
    avg_competition=75
)

print(business_case['recommendation'])  # "PURSUE - Strong business case"
print(business_case['action'])          # "Initiate partnership discussions immediately"
```

## 📊 Database Queries

### View All Strategic Customers
```sql
SELECT customer_name, priority_level, notes 
FROM config_strategic_customers 
ORDER BY priority_level, customer_name;
```

### Check OEM Tracking Status
```sql
SELECT 
    oem_name,
    occurrence_count,
    total_value_seen,
    business_case_threshold,
    CASE 
        WHEN occurrence_count >= business_case_threshold 
        THEN 'READY FOR BUSINESS CASE'
        ELSE 'TRACKING'
    END as status
FROM config_oem_tracking
WHERE currently_authorized = 0
ORDER BY occurrence_count DESC;
```

### View Recent OEM Occurrences (90 days)
```sql
SELECT 
    o.oem_name,
    o.rfq_number,
    o.customer,
    o.estimated_value,
    o.competition_level,
    o.occurred_at
FROM oem_occurrence_log o
WHERE o.occurred_at >= date('now', '-90 days')
ORDER BY o.occurred_at DESC;
```

### Generate OEM Business Case Report
```sql
SELECT * FROM v_oem_business_case_90d;
```

### Track RFI Response Success Rate
```sql
SELECT 
    responded,
    COUNT(*) as total_rfis,
    SUM(subsequent_rfq_received) as rfqs_received,
    SUM(awarded) as awards_won,
    ROUND(CAST(SUM(awarded) AS FLOAT) / NULLIF(SUM(subsequent_rfq_received), 0) * 100, 1) as win_rate_pct
FROM rfi_tracking
GROUP BY responded;
```

### Identify Late RFQ Patterns
```sql
SELECT 
    COUNT(*) as late_rfqs,
    AVG(days_to_respond) as avg_days,
    reason_late,
    COUNT(DISTINCT rfq_number) as unique_sources
FROM late_rfq_tracking
WHERE received_date >= date('now', '-90 days')
GROUP BY reason_late
ORDER BY late_rfqs DESC;
```

## 🔧 Customization

### Add New Strategic Customer
```sql
INSERT INTO config_strategic_customers (customer_name, priority_level, notes)
VALUES ('NORTHCOM', 'CRITICAL', 'Northern Command');
```

### Update Value Threshold
```sql
UPDATE config_value_thresholds
SET min_value = 25000
WHERE tier_name = 'TIER_3_REVIEW';
```

### Add Technology Vertical
```sql
INSERT INTO config_technology_verticals (vertical_name, priority_level, notes)
VALUES ('Edge Computing', 'MEDIUM', 'Emerging IoT/edge opportunity');
```

### Log OEM Occurrence (Manual)
```sql
-- Log the occurrence
INSERT INTO oem_occurrence_log 
(oem_name, rfq_number, customer, estimated_value, technology_vertical, competition_level)
VALUES 
('Atlassian', '361571', 'Hill AFB', 15000, 'DevOps/Collaboration', 127);

-- Update tracking counter
UPDATE config_oem_tracking
SET occurrence_count = occurrence_count + 1,
    total_value_seen = total_value_seen + 15000,
    updated_at = CURRENT_TIMESTAMP
WHERE oem_name = 'Atlassian';
```

## 📅 Maintenance Schedule

### Daily
- Review high-value alerts (TIER 1 & 2)
- Process new RFQs through filtering rules

### Weekly
- Check OEM occurrence counts
- Review flagged strategic opportunities
- Update tracking totals

### Monthly
- Generate OEM business case reports
- Review RFI response success rates
- Analyze late RFQ patterns
- Update strategic customer list if needed

### Quarterly
- Evaluate OEMs that hit threshold (90-day window)
- Review and adjust value thresholds if needed
- Update technology vertical priorities
- Audit filtering rule effectiveness
- Generate win/loss analysis

## 🎓 Training Notes

### For Sales Team

**Know Your Priorities:**
- CRITICAL customers: AFCENT, ARCENT, CYBERCOMMAND, AFSOC, USSOCOM, Space Force, DARPA
- HIGH customers: AETC, Hill/Eglin/Tyndall/Patrick AFB, Andrews, Bolling, AFOSI
- Value tiers: $20K, $200K, $1M breakpoints
- Tech focus: Zero Trust, Data Center, Enterprise Networking

**Key Actions:**
- Flag any strategic customer RFQ immediately
- Alert on $200K+ opportunities
- Report niche OEM sightings (Atlassian, Graylog, etc.)
- Note late RFQs for pattern analysis

### For Management

**Monitor:**
- High-value alert frequency
- OEM business case progress
- RFI response correlation to awards
- Late RFQ patterns (source analysis)

**Review Quarterly:**
- OEM partnership opportunities
- Value threshold effectiveness
- Strategic customer list updates
- Technology vertical alignment
- Filter rule performance

## 🔒 Security & Compliance

- Customer names are INTERNAL USE ONLY
- Do not share configuration externally
- Backup database weekly
- Review access permissions monthly
- Document all configuration changes

## 📞 Support

### Configuration Changes
1. Update database via SQL
2. Update Python config if business logic changes
3. Test on sample data
4. Document in version control

### Troubleshooting

**Database not found:**
```bash
find ~ -name "sales_automation.db" 2>/dev/null
# or
find ~/Library/Application\ Support -name "*.db" 2>/dev/null
```

**Tables not created:**
```bash
sqlite3 /path/to/db "SELECT name FROM sqlite_master WHERE type='table';"
```

**Python import error:**
```python
import sys
sys.path.append('/path/to/config')
from rfq_filtering_config import CONFIG
```

## 📈 Success Metrics

Track these KPIs to measure effectiveness:

**Efficiency Metrics:**
- Time saved on auto-declined RFQs
- % of RFQs requiring manual review
- Average decision time per RFQ

**Quality Metrics:**
- Win rate on GO decisions
- Strategic customer response rate
- High-value opportunity capture rate

**Intelligence Metrics:**
- OEM business cases generated
- New partnerships initiated
- Technology trend identification accuracy

---

**Version:** 1.0  
**Last Updated:** October 13, 2025  
**Configuration Date:** October 13, 2025  
**Next Review:** January 13, 2026

---

## 🎯 Quick Reference Card

**Auto-Decline Triggers:**
- ✗ Consolidated notices (eBuy/Govly)
- ✗ 125+ bidders + <$15K + software renewal
- ✗ <$2K value
- ✗ ≤2 days to respond (complex)

**Always Flag/Alert:**
- ✓ Strategic customers (15 total)
- ✓ $200K+ value
- ✓ <20 bidders + $20K+ value
- ✓ Zero Trust / Data Center / Enterprise Networking
- ✓ Existing customer renewals

**Track & Monitor:**
- 📊 Atlassian (5+ = business case)
- 📊 Graylog/LogRhythm (5+ = business case)
- 📊 Sparx (8+ = business case)
- 📊 RFI responses vs. awards
- 📊 Late RFQ patterns

**For Help:** See full documentation above or contact sales ops team.
