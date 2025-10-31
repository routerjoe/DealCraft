"""
Red River Sales Automation - Intelligent RFQ Filtering Configuration
This module contains the business rules and configuration for automated RFQ filtering

Version: 1.0
Last Updated: October 13, 2025
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

# ============================================================================
# STRATEGIC CUSTOMERS - Always Flag for Review
# ============================================================================
STRATEGIC_CUSTOMERS = {
    'CRITICAL': [
        'Customer Alpha',           # Customer Alpha Command
        'ARCENT',           # Army Central Command
        'US CYBERCOMMAND',  # United States Cyber Command
        'AFSOC',            # Air Force Special Operations Command
        'USSOCOM',          # US Special Operations Command
        'Space Force',      # United States Space Force
        'DARPA',            # Defense Advanced Research Projects Agency
    ],
    'HIGH': [
        'Customer Beta',             # Customer Beta Command
        'Hill AFB',         # Hill Air Force Base
        'Eglin AFB',        # Eglin Air Force Base
        'Tyndall AFB',      # Tyndall Air Force Base
        'Patrick AFB',      # Patrick Space Force Base
        'Andrews AFB',      # Joint Base Andrews
        'Bolling AFB',      # Joint Base Anacostia-Bolling
        'AFOSI',            # Air Force Office of Special Investigations
    ]
}

# ============================================================================
# VALUE THRESHOLDS - Dollar-based Priority Tiers
# ============================================================================
VALUE_THRESHOLDS = {
    'TIER_1_CRITICAL': {
        'min': 1_000_000,
        'max': None,
        'action': 'IMMEDIATE_EXECUTIVE_NOTIFICATION',
        'description': '$1M+ - Critical executive notification'
    },
    'TIER_2_HIGH': {
        'min': 200_000,
        'max': 999_999,
        'action': 'SALES_TEAM_NOTIFICATION',
        'description': '$200K-$1M - Sales team priority'
    },
    'TIER_3_REVIEW': {
        'min': 20_000,
        'max': 199_999,
        'action': 'FLAG_FOR_REVIEW',
        'description': '$20K-$200K - Standard review process'
    },
    'TIER_4_LOW': {
        'min': 0,
        'max': 19_999,
        'action': 'STANDARD_PROCESS',
        'description': '<$20K - Standard/consider auto-decline'
    }
}

# ============================================================================
# TECHNOLOGY VERTICALS - Strategic Focus Areas
# ============================================================================
PRIORITY_TECH_VERTICALS = {
    'HIGH': [
        'Zero Trust',
        'Data Center',
        'Enterprise Networking',
        'Cybersecurity',
    ],
    'MEDIUM': [
        'Cloud Migration',
        'AI/ML Infrastructure',
        'SIEM/Security Analytics',
        'SD-WAN',
        'Hybrid Cloud',
        'Storage/Infrastructure',
        'Application Delivery',
    ]
}

# ============================================================================
# OEM TRACKING - New Business Opportunities
# ============================================================================
TRACKED_OEMS = {
    # Not currently authorized - tracking for potential new lines
    'NEW_BUSINESS_OPPORTUNITIES': {
        'Atlassian': {
            'threshold': 5,  # Occurrences before business case
            'vertical': 'DevOps/Collaboration',
            'notes': 'Growing market for DevOps tools'
        },
        'Graylog': {
            'threshold': 5,
            'vertical': 'SIEM/Security Analytics',
            'notes': 'Security analytics opportunity'
        },
        'LogRhythm': {
            'threshold': 5,
            'vertical': 'SIEM/Security Analytics',
            'notes': 'Security analytics opportunity'
        },
        'Sparx': {
            'threshold': 8,
            'vertical': 'Enterprise Architecture',
            'notes': 'Niche market - higher threshold'
        },
        'Quest/Toad': {
            'threshold': 5,
            'vertical': 'Database Tools',
            'notes': 'Moderate opportunity'
        }
    },
    
    # Currently authorized - core business
    'CURRENT_PARTNERS': [
        'Cisco',
        'Palo Alto Networks',
        'Dell/EMC',
        'NetApp',
        'F5 Networks',
        'Microsoft',
        'VMware',
        'Red Hat',
    ]
}

# ============================================================================
# FILTERING RULES - Automated Decision Logic
# ============================================================================

@dataclass
class FilterRule:
    rule_id: str
    name: str
    action: str  # AUTO_DECLINE, FLAG_FOR_REVIEW, ALERT
    priority: int  # Lower = higher priority
    enabled: bool = True

FILTER_RULES = [
    FilterRule(
        rule_id='R001',
        name='Auto-Decline Consolidated Notices',
        action='AUTO_DECLINE',
        priority=1,
        enabled=True
    ),
    FilterRule(
        rule_id='R002',
        name='High Competition Low Value',
        action='AUTO_DECLINE',
        priority=2,
        enabled=True
    ),
    FilterRule(
        rule_id='R003',
        name='Track Niche OEMs for New Business',
        action='LOG_AND_TRACK',
        priority=3,
        enabled=True
    ),
    FilterRule(
        rule_id='R004',
        name='RFI/MRR Strategic Review',
        action='STRATEGIC_REVIEW',
        priority=4,
        enabled=True
    ),
    FilterRule(
        rule_id='R005',
        name='Ultra Low Value Auto-Decline',
        action='AUTO_DECLINE',
        priority=5,
        enabled=True
    ),
    FilterRule(
        rule_id='R006',
        name='Late RFQ Auto-Decline with Pattern Tracking',
        action='AUTO_DECLINE_AND_LOG',
        priority=6,
        enabled=True
    ),
    FilterRule(
        rule_id='R007',
        name='High-Value Priority Alert',
        action='ALERT',
        priority=7,
        enabled=True
    ),
    FilterRule(
        rule_id='R008',
        name='Existing Customer Renewal Flag',
        action='FLAG_FOR_REVIEW',
        priority=8,
        enabled=True
    ),
    FilterRule(
        rule_id='R009',
        name='Strategic Technology Flag',
        action='FLAG_FOR_REVIEW',
        priority=9,
        enabled=True
    ),
]

# ============================================================================
# RULE LOGIC IMPLEMENTATIONS
# ============================================================================

def apply_rule_r001(rfq_subject: str, rfq_sender: str) -> bool:
    """Rule 1: Auto-decline consolidated notices"""
    consolidated_patterns = [
        'Federal Agency A eBuy Requests and Quotes/Bids (Consolidated Notice)',
        'saved search matches',
    ]
    consolidated_senders = [
        'ebuy_admin@gsa.gov',
        'opportunities@govly.com',
    ]
    
    return (any(pattern in rfq_subject for pattern in consolidated_patterns) or
            rfq_sender in consolidated_senders)

def apply_rule_r002(competition: int, value: float, rfq_type: str) -> bool:
    """Rule 2: High competition + low value"""
    return (competition >= 125 and 
            value < 15000 and 
            rfq_type in ['software renewal', 'license renewal'])

def apply_rule_r003(oem: str) -> Dict[str, Any]:
    """Rule 3: Track niche OEMs"""
    if oem in TRACKED_OEMS['NEW_BUSINESS_OPPORTUNITIES']:
        return {
            'action': 'LOG_AND_TRACK',
            'decline': True,
            'reason': f'Tracking {oem} for potential new business line',
            'threshold': TRACKED_OEMS['NEW_BUSINESS_OPPORTUNITIES'][oem]['threshold']
        }
    return {'action': 'PASS'}

def apply_rule_r004(rfq_type: str, customer: str, estimated_value: float) -> Dict[str, Any]:
    """Rule 4: RFI/MRR strategic response"""
    if rfq_type in ['RFI', 'Market Research Request']:
        is_strategic = is_strategic_customer(customer)
        
        if is_strategic or estimated_value > 50000:
            return {
                'action': 'FLAG_FOR_REVIEW',
                'priority': 'HIGH',
                'note': 'Response recommended for future RFQ consideration'
            }
        elif estimated_value >= 25000:
            return {
                'action': 'FLAG_FOR_REVIEW',
                'priority': 'MEDIUM',
                'note': 'Evaluate case-by-case'
            }
        else:
            return {
                'action': 'CONSIDER_DECLINE',
                'note': 'Low priority - log decision reasoning'
            }
    return {'action': 'PASS'}

def apply_rule_r005(value: float, quantity: int, rfq_type: str) -> bool:
    """Rule 5: Ultra low value"""
    return value < 2000 or (quantity == 1 and rfq_type == 'renewal')

def apply_rule_r006(days_to_deadline: int, has_attachments: bool) -> Dict[str, Any]:
    """Rule 6: Insufficient time with pattern tracking"""
    if days_to_deadline <= 2 and has_attachments:
        return {
            'action': 'AUTO_DECLINE_AND_LOG',
            'reason': 'Insufficient time for quality response',
            'log_pattern': True,
            'pattern_note': 'Late notification - investigate source'
        }
    return {'action': 'PASS'}

def apply_rule_r007(value: float, competition: int, customer: str) -> Dict[str, Any]:
    """Rule 7: High-value alert"""
    tier = get_value_tier(value)
    is_strat = is_strategic_customer(customer)
    
    if tier == 'TIER_1_CRITICAL' or (tier == 'TIER_2_HIGH' and is_strat):
        return {
            'action': 'IMMEDIATE_ALERT',
            'priority': 'CRITICAL',
            'notify': ['executive', 'sales_team']
        }
    elif tier == 'TIER_2_HIGH' or (tier == 'TIER_3_REVIEW' and competition < 20):
        return {
            'action': 'ALERT',
            'priority': 'HIGH',
            'notify': ['sales_team']
        }
    elif tier == 'TIER_3_REVIEW':
        return {
            'action': 'FLAG_FOR_REVIEW',
            'priority': 'MEDIUM'
        }
    return {'action': 'PASS'}

def apply_rule_r008(has_previous_contract: bool, customer: str) -> bool:
    """Rule 8: Existing customer renewal"""
    return has_previous_contract

def apply_rule_r009(tech_vertical: str, value: float) -> bool:
    """Rule 9: Strategic technology"""
    high_priority_tech = PRIORITY_TECH_VERTICALS['HIGH']
    medium_priority_tech = PRIORITY_TECH_VERTICALS['MEDIUM']
    
    if tech_vertical in high_priority_tech:
        return True
    elif tech_vertical in medium_priority_tech and value > 50000:
        return True
    return False

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def is_strategic_customer(customer: str) -> bool:
    """Check if customer is in strategic list"""
    all_strategic = (STRATEGIC_CUSTOMERS['CRITICAL'] + 
                    STRATEGIC_CUSTOMERS['HIGH'])
    return any(strat_cust.lower() in customer.lower() 
               for strat_cust in all_strategic)

def get_value_tier(value: float) -> str:
    """Determine value tier based on thresholds"""
    for tier_name, tier_data in VALUE_THRESHOLDS.items():
        min_val = tier_data['min']
        max_val = tier_data['max']
        
        if max_val is None:
            if value >= min_val:
                return tier_name
        elif min_val <= value <= max_val:
            return tier_name
    
    return 'TIER_4_LOW'

def calculate_rfq_score(
    value: float,
    competition: int,
    customer: str,
    tech_vertical: str,
    oem: str,
    has_previous_contract: bool
) -> Dict[str, Any]:
    """
    Calculate overall RFQ score (0-100) based on multiple factors
    Returns score and recommendation
    """
    score = 0
    factors = []
    
    # Value scoring (0-40 points)
    tier = get_value_tier(value)
    value_scores = {
        'TIER_1_CRITICAL': 40,
        'TIER_2_HIGH': 30,
        'TIER_3_REVIEW': 20,
        'TIER_4_LOW': 10
    }
    score += value_scores.get(tier, 0)
    factors.append(f"Value: {tier} (+{value_scores.get(tier, 0)})")
    
    # Customer strategic value (0-25 points)
    if customer in STRATEGIC_CUSTOMERS['CRITICAL']:
        score += 25
        factors.append("Customer: CRITICAL (+25)")
    elif customer in STRATEGIC_CUSTOMERS['HIGH']:
        score += 15
        factors.append("Customer: HIGH (+15)")
    else:
        factors.append("Customer: Standard (+0)")
    
    # Competition level (0-15 points)
    if competition < 20:
        score += 15
        factors.append("Competition: Low (<20) (+15)")
    elif competition < 50:
        score += 10
        factors.append("Competition: Medium (<50) (+10)")
    elif competition < 100:
        score += 5
        factors.append("Competition: High (<100) (+5)")
    else:
        factors.append(f"Competition: Very High ({competition}) (+0)")
    
    # Technology vertical (0-10 points)
    if tech_vertical in PRIORITY_TECH_VERTICALS['HIGH']:
        score += 10
        factors.append("Tech: High Priority (+10)")
    elif tech_vertical in PRIORITY_TECH_VERTICALS['MEDIUM']:
        score += 5
        factors.append("Tech: Medium Priority (+5)")
    else:
        factors.append("Tech: Standard (+0)")
    
    # OEM relationship (0-10 points)
    if oem in TRACKED_OEMS['CURRENT_PARTNERS']:
        score += 10
        factors.append("OEM: Authorized Partner (+10)")
    else:
        factors.append("OEM: Not authorized (+0)")
    
    # Existing relationship bonus (+10 points)
    if has_previous_contract:
        score += 10
        factors.append("Renewal: Existing Customer (+10)")
    
    # Determine recommendation
    if score >= 75:
        recommendation = "GO - High Priority"
    elif score >= 60:
        recommendation = "GO - Consider Pursuit"
    elif score >= 45:
        recommendation = "REVIEW - Conditional GO"
    elif score >= 30:
        recommendation = "REVIEW - Likely NO-GO"
    else:
        recommendation = "NO-GO - Auto-Decline"
    
    return {
        'score': score,
        'recommendation': recommendation,
        'factors': factors
    }

def evaluate_new_oem_business_case(
    oem: str,
    occurrences_90d: int,
    total_value_90d: float,
    unique_customers: int,
    avg_competition: int
) -> Dict[str, Any]:
    """
    Evaluate whether to pursue new OEM partnership
    
    Recommendation Criteria:
    - 5+ occurrences in 90 days OR
    - $100K+ total addressable value in 90 days OR
    - 3+ strategic customers requesting OR
    - Low competition (<50 avg) AND 3+ occurrences AND $50K+ value
    """
    
    score = 0
    reasons = []
    
    # Frequency scoring
    if occurrences_90d >= 8:
        score += 40
        reasons.append(f"High frequency: {occurrences_90d} RFQs in 90 days")
    elif occurrences_90d >= 5:
        score += 25
        reasons.append(f"Moderate frequency: {occurrences_90d} RFQs in 90 days")
    elif occurrences_90d >= 3:
        score += 10
        reasons.append(f"Some frequency: {occurrences_90d} RFQs in 90 days")
    
    # Value scoring
    if total_value_90d >= 250000:
        score += 40
        reasons.append(f"High value: ${total_value_90d:,.0f} total")
    elif total_value_90d >= 100000:
        score += 25
        reasons.append(f"Moderate value: ${total_value_90d:,.0f} total")
    elif total_value_90d >= 50000:
        score += 10
        reasons.append(f"Some value: ${total_value_90d:,.0f} total")
    
    # Customer diversity
    if unique_customers >= 5:
        score += 10
        reasons.append(f"Good customer diversity: {unique_customers} customers")
    elif unique_customers >= 3:
        score += 5
        reasons.append(f"Some customer diversity: {unique_customers} customers")
    
    # Competition level
    if avg_competition < 50:
        score += 10
        reasons.append(f"Favorable competition: avg {avg_competition} bidders")
    
    # Recommendation
    if score >= 60:
        recommendation = "PURSUE - Strong business case"
        action = "Initiate partnership discussions immediately"
    elif score >= 40:
        recommendation = "CONSIDER - Moderate opportunity"
        action = "Continue monitoring for 30 more days"
    elif score >= 20:
        recommendation = "MONITOR - Weak case currently"
        action = "Continue tracking, reassess in 90 days"
    else:
        recommendation = "NO ACTION - Insufficient opportunity"
        action = "Stop active tracking"
    
    return {
        'oem': oem,
        'score': score,
        'recommendation': recommendation,
        'action': action,
        'reasons': reasons,
        'metrics': {
            'occurrences_90d': occurrences_90d,
            'total_value_90d': total_value_90d,
            'unique_customers': unique_customers,
            'avg_competition': avg_competition
        }
    }

# ============================================================================
# EXPORT CONFIGURATION
# ============================================================================

CONFIG = {
    'strategic_customers': STRATEGIC_CUSTOMERS,
    'value_thresholds': VALUE_THRESHOLDS,
    'tech_verticals': PRIORITY_TECH_VERTICALS,
    'tracked_oems': TRACKED_OEMS,
    'filter_rules': FILTER_RULES,
}

if __name__ == '__main__':
    print("Red River Sales Automation - Configuration Loaded")
    print(f"Strategic Customers: {len(STRATEGIC_CUSTOMERS['CRITICAL']) + len(STRATEGIC_CUSTOMERS['HIGH'])}")
    print(f"Value Tiers: {len(VALUE_THRESHOLDS)}")
    print(f"Priority Tech Verticals: {len(PRIORITY_TECH_VERTICALS['HIGH']) + len(PRIORITY_TECH_VERTICALS['MEDIUM'])}")
    print(f"Tracking OEMs: {len(TRACKED_OEMS['NEW_BUSINESS_OPPORTUNITIES'])}")
    print(f"Filter Rules: {len(FILTER_RULES)}")
