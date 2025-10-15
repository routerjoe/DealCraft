#!/usr/bin/env python3
"""
Test script for Red River Sales Automation Configuration
This script verifies the configuration is working correctly
"""

import sys
from rfq_filtering_config import (
    is_strategic_customer,
    get_value_tier,
    calculate_rfq_score,
    evaluate_new_oem_business_case,
    STRATEGIC_CUSTOMERS,
    VALUE_THRESHOLDS,
    TRACKED_OEMS
)

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def print_test(name, result, expected=True):
    status = "✓ PASS" if result == expected else "✗ FAIL"
    print(f"{status}: {name}")
    return result == expected

def main():
    print_header("Red River Sales Automation Config Test Suite")
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Strategic Customer Detection
    print_header("Test 1: Strategic Customer Detection")
    tests_total += 1
    test1 = (
        print_test("AFCENT is strategic (CRITICAL)", is_strategic_customer("AFCENT"), True) and
        print_test("Hill AFB is strategic (HIGH)", is_strategic_customer("Hill AFB"), True) and
        print_test("Random Base is not strategic", is_strategic_customer("Random Base"), False) and
        print_test("Case insensitive: afcent", is_strategic_customer("afcent"), True)
    )
    if test1:
        tests_passed += 1
        print("✓ Strategic customer detection working correctly")
    else:
        print("✗ Strategic customer detection has issues")
    
    # Test 2: Value Tier Classification
    print_header("Test 2: Value Tier Classification")
    tests_total += 1
    test2 = (
        print_test("$1.5M = TIER_1_CRITICAL", get_value_tier(1500000) == "TIER_1_CRITICAL", True) and
        print_test("$500K = TIER_2_HIGH", get_value_tier(500000) == "TIER_2_HIGH", True) and
        print_test("$75K = TIER_3_REVIEW", get_value_tier(75000) == "TIER_3_REVIEW", True) and
        print_test("$5K = TIER_4_LOW", get_value_tier(5000) == "TIER_4_LOW", True)
    )
    if test2:
        tests_passed += 1
        print("✓ Value tier classification working correctly")
    else:
        print("✗ Value tier classification has issues")
    
    # Test 3: RFQ Scoring - High Priority Opportunity
    print_header("Test 3: RFQ Scoring - High Priority Opportunity")
    tests_total += 1
    
    result_high = calculate_rfq_score(
        value=250000,               # $250K = TIER_2 (30 pts)
        competition=15,             # <20 = Low (15 pts)
        customer="Space Force",     # CRITICAL (25 pts)
        tech_vertical="Zero Trust", # HIGH priority (10 pts)
        oem="Cisco",               # Authorized (10 pts)
        has_previous_contract=True  # Renewal (10 pts)
    )
    
    print(f"Score: {result_high['score']}/100")
    print(f"Recommendation: {result_high['recommendation']}")
    print(f"Factors: {', '.join(result_high['factors'])}")
    
    test3 = result_high['score'] == 100 and "GO - High Priority" in result_high['recommendation']
    if test3:
        tests_passed += 1
        print("✓ High priority RFQ scoring correct (100 pts)")
    else:
        print(f"✗ Expected 100 points, got {result_high['score']}")
    
    # Test 4: RFQ Scoring - Auto-Decline Opportunity
    print_header("Test 4: RFQ Scoring - Auto-Decline Opportunity")
    tests_total += 1
    
    result_low = calculate_rfq_score(
        value=5000,                # $5K = TIER_4 (10 pts)
        competition=127,           # Very high (0 pts)
        customer="Unknown Base",   # Not strategic (0 pts)
        tech_vertical="Misc",      # Not priority (0 pts)
        oem="Unknown Vendor",      # Not authorized (0 pts)
        has_previous_contract=False # Not renewal (0 pts)
    )
    
    print(f"Score: {result_low['score']}/100")
    print(f"Recommendation: {result_low['recommendation']}")
    
    test4 = result_low['score'] == 10 and "NO-GO" in result_low['recommendation']
    if test4:
        tests_passed += 1
        print("✓ Low priority RFQ scoring correct (10 pts = Auto-Decline)")
    else:
        print(f"✗ Expected 10 points and NO-GO, got {result_low['score']}")
    
    # Test 5: OEM Business Case - Strong Case
    print_header("Test 5: OEM Business Case - Strong Opportunity")
    tests_total += 1
    
    strong_case = evaluate_new_oem_business_case(
        oem="Atlassian",
        occurrences_90d=8,      # High frequency
        total_value_90d=200000,  # Strong value
        unique_customers=5,      # Good diversity
        avg_competition=45       # Favorable competition
    )
    
    print(f"OEM: {strong_case['oem']}")
    print(f"Score: {strong_case['score']}/100")
    print(f"Recommendation: {strong_case['recommendation']}")
    print(f"Action: {strong_case['action']}")
    
    test5 = strong_case['score'] >= 60 and "PURSUE" in strong_case['recommendation']
    if test5:
        tests_passed += 1
        print("✓ Strong business case correctly identified")
    else:
        print(f"✗ Expected PURSUE recommendation, got {strong_case['recommendation']}")
    
    # Test 6: OEM Business Case - Weak Case
    print_header("Test 6: OEM Business Case - Weak Opportunity")
    tests_total += 1
    
    weak_case = evaluate_new_oem_business_case(
        oem="Sparx",
        occurrences_90d=2,      # Low frequency
        total_value_90d=15000,   # Low value
        unique_customers=1,      # Poor diversity
        avg_competition=120      # High competition
    )
    
    print(f"OEM: {weak_case['oem']}")
    print(f"Score: {weak_case['score']}/100")
    print(f"Recommendation: {weak_case['recommendation']}")
    
    test6 = weak_case['score'] < 20 and "NO ACTION" in weak_case['recommendation']
    if test6:
        tests_passed += 1
        print("✓ Weak business case correctly identified")
    else:
        print(f"✗ Expected NO ACTION recommendation, got {weak_case['recommendation']}")
    
    # Test 7: Configuration Loading
    print_header("Test 7: Configuration Data Loading")
    tests_total += 1
    
    critical_count = len(STRATEGIC_CUSTOMERS['CRITICAL'])
    high_count = len(STRATEGIC_CUSTOMERS['HIGH'])
    total_strategic = critical_count + high_count
    
    tier_count = len(VALUE_THRESHOLDS)
    tracked_oem_count = len(TRACKED_OEMS['NEW_BUSINESS_OPPORTUNITIES'])
    
    print(f"Strategic Customers (CRITICAL): {critical_count}")
    print(f"Strategic Customers (HIGH): {high_count}")
    print(f"Total Strategic Customers: {total_strategic}")
    print(f"Value Tiers: {tier_count}")
    print(f"Tracked OEMs: {tracked_oem_count}")
    
    test7 = total_strategic == 15 and tier_count == 4 and tracked_oem_count == 5
    if test7:
        tests_passed += 1
        print("✓ Configuration data loaded correctly")
    else:
        print("✗ Configuration data mismatch")
    
    # Final Results
    print_header("Test Results Summary")
    print(f"Tests Passed: {tests_passed}/{tests_total}")
    print(f"Success Rate: {(tests_passed/tests_total)*100:.1f}%")
    
    if tests_passed == tests_total:
        print("\n✓ ALL TESTS PASSED - Configuration is working correctly! 🎉")
        return 0
    else:
        print(f"\n✗ {tests_total - tests_passed} TEST(S) FAILED - Review configuration")
        return 1

if __name__ == "__main__":
    sys.exit(main())
