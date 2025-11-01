#!/usr/bin/env python3
"""
Entity Migration Script - Extract hardcoded data to Entity Management System

This script migrates hardcoded entity data from scoring.py and cv_recommender.py
into the new Entity Management System with JSON persistence.

Entities migrated:
- OEMs from OEM_ALIGNMENT_SCORES
- Regions from REGION_BONUS_AUDITED
- Contract Vehicles from CONTRACT_VEHICLES
- Sample Partners, Customers, and Distributors

Also creates scoring_weights.json configuration file.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp.core.entities import (  # noqa: E402
    OEM,
    ContractVehicle,
    Customer,
    Distributor,
    Partner,
    Region,
    contract_vehicle_store,
    customer_store,
    distributor_store,
    oem_store,
    partner_store,
    region_store,
)


def migrate_oems():
    """Migrate OEMs from OEM_ALIGNMENT_SCORES."""
    print("\n=== Migrating OEMs ===")

    # Data from scoring.py OEM_ALIGNMENT_SCORES
    oem_data = [
        {"id": "microsoft", "name": "Microsoft", "tier": "Strategic", "programs": ["Azure", "M365", "Dynamics"]},
        {"id": "cisco", "name": "Cisco", "tier": "Strategic", "programs": ["Networking", "Security", "Collaboration"]},
        {"id": "dell", "name": "Dell", "tier": "Gold", "programs": ["PowerEdge", "VxRail", "Latitude"]},
        {"id": "hpe", "name": "HPE", "tier": "Gold", "programs": ["ProLiant", "Synergy", "GreenLake"]},
        {"id": "vmware", "name": "VMware", "tier": "Gold", "programs": ["vSphere", "NSX", "vSAN"]},
        {"id": "netapp", "name": "NetApp", "tier": "Gold", "programs": ["ONTAP", "Cloud Volumes", "SnapCenter"]},
        {"id": "palo-alto", "name": "Palo Alto Networks", "tier": "Gold", "programs": ["Firewalls", "Prisma", "Cortex"]},
        {"id": "fortinet", "name": "Fortinet", "tier": "Silver", "programs": ["FortiGate", "FortiAnalyzer", "FortiManager"]},
        {"id": "aws", "name": "AWS", "tier": "Silver", "programs": ["EC2", "S3", "RDS"]},
        {"id": "google", "name": "Google", "tier": "Silver", "programs": ["GCP", "Workspace", "Cloud AI"]},
        {"id": "oracle", "name": "Oracle", "tier": "Silver", "programs": ["Database", "Cloud", "Applications"]},
        {"id": "ibm", "name": "IBM", "tier": "Silver", "programs": ["Cloud", "Watson", "Security"]},
    ]

    for data in oem_data:
        try:
            oem = OEM(**data)
            oem_store.add(oem)
            print(f"  ✓ Added OEM: {oem.name} ({oem.tier})")
        except ValueError as e:
            print(f"  ⚠ Skipped {data['name']}: {e}")


def migrate_regions():
    """Migrate Regions from REGION_BONUS_AUDITED."""
    print("\n=== Migrating Regions ===")

    # Data from scoring.py REGION_BONUS_AUDITED
    region_data = [
        {"id": "east", "name": "East", "bonus": 2.5, "description": "East Coast region (65% win rate)"},
        {"id": "west", "name": "West", "bonus": 2.0, "description": "West Coast region (60% win rate)"},
        {"id": "central", "name": "Central", "bonus": 1.5, "description": "Central region (55% win rate)"},
    ]

    for data in region_data:
        try:
            region = Region(**data)
            region_store.add(region)
            print(f"  ✓ Added Region: {region.name} (bonus: {region.bonus})")
        except ValueError as e:
            print(f"  ⚠ Skipped {data['name']}: {e}")


def migrate_contract_vehicles():
    """Migrate Contract Vehicles from CONTRACT_VEHICLES."""
    print("\n=== Migrating Contract Vehicles ===")

    # Data from cv_recommender.py CONTRACT_VEHICLES
    cv_data = [
        {
            "id": "sewp-v",
            "name": "SEWP V",
            "priority_score": 95.0,
            "oems_supported": ["microsoft", "cisco", "dell", "hpe", "vmware", "netapp"],
            "categories": ["IT Hardware", "Software", "Cloud Services"],
            "active_bpas": 3,
            "ceiling_amount": 50000000000,
            "contracting_office": "NASA SEWP",
            "scope": "IT Products and Services for Federal Agencies",
        },
        {
            "id": "nasa-solutions",
            "name": "NASA SOLUTIONS",
            "priority_score": 92.0,
            "oems_supported": ["dell", "hpe", "cisco", "microsoft"],
            "categories": ["IT Hardware", "Professional Services"],
            "active_bpas": 2,
            "ceiling_amount": 20000000000,
            "contracting_office": "NASA SEWP",
            "scope": "IT Solutions and Professional Services",
        },
        {
            "id": "gsa-schedule",
            "name": "GSA Schedule",
            "priority_score": 90.0,
            "oems_supported": [
                "microsoft",
                "cisco",
                "dell",
                "hpe",
                "vmware",
                "netapp",
                "palo-alto",
                "fortinet",
                "aws",
                "google",
                "oracle",
                "ibm",
            ],
            "categories": ["All Categories"],
            "active_bpas": 5,
            "ceiling_amount": None,
            "contracting_office": "GSA",
            "scope": "Multiple Award Schedule for IT Products and Services",
        },
        {
            "id": "dhs-firstsource-ii",
            "name": "DHS FirstSource II",
            "priority_score": 88.0,
            "oems_supported": ["cisco", "palo-alto", "fortinet"],
            "categories": ["Cybersecurity", "Networking"],
            "active_bpas": 1,
            "ceiling_amount": 22000000000,
            "contracting_office": "DHS",
            "scope": "Cybersecurity and Network Solutions",
        },
        {
            "id": "cio-sp3",
            "name": "CIO-SP3",
            "priority_score": 85.0,
            "oems_supported": [
                "microsoft",
                "cisco",
                "dell",
                "hpe",
                "vmware",
                "netapp",
                "palo-alto",
                "fortinet",
                "aws",
                "google",
                "oracle",
                "ibm",
            ],
            "categories": ["IT Services", "Cloud", "Cybersecurity"],
            "active_bpas": 0,
            "ceiling_amount": 20000000000,
            "contracting_office": "NIH",
            "scope": "IT Services for Health and Human Services",
        },
        {
            "id": "alliant-2",
            "name": "Alliant 2",
            "priority_score": 83.0,
            "oems_supported": [
                "microsoft",
                "cisco",
                "dell",
                "hpe",
                "vmware",
                "netapp",
                "palo-alto",
                "fortinet",
                "aws",
                "google",
                "oracle",
                "ibm",
            ],
            "categories": ["IT Services", "Professional Services"],
            "active_bpas": 0,
            "ceiling_amount": 65000000000,
            "contracting_office": "GSA",
            "scope": "Integrated IT Solutions for Federal Agencies",
        },
        {
            "id": "8a-stars-ii",
            "name": "8(a) STARS II",
            "priority_score": 80.0,
            "oems_supported": [
                "microsoft",
                "cisco",
                "dell",
                "hpe",
                "vmware",
                "netapp",
                "palo-alto",
                "fortinet",
                "aws",
                "google",
                "oracle",
                "ibm",
            ],
            "categories": ["IT Services", "Small Business"],
            "active_bpas": 0,
            "ceiling_amount": 15000000000,
            "contracting_office": "GSA",
            "scope": "IT Services for 8(a) Small Businesses",
        },
    ]

    for data in cv_data:
        try:
            cv = ContractVehicle(**data)
            contract_vehicle_store.add(cv)
            print(f"  ✓ Added CV: {cv.name} (priority: {cv.priority_score})")
        except ValueError as e:
            print(f"  ⚠ Skipped {data['name']}: {e}")


def migrate_partners():
    """Create sample Partner entities."""
    print("\n=== Creating Sample Partners ===")

    partner_data = [
        {
            "id": "partner-alpha",
            "name": "TechPartner Alpha",
            "tier": "Platinum",
            "oem_affiliations": ["microsoft", "cisco", "vmware"],
            "specializations": ["Cloud Migration", "Cybersecurity", "Data Center"],
            "regions_served": ["East", "Central"],
            "program": "Microsoft Gold Partner",
        },
        {
            "id": "partner-beta",
            "name": "SolutionsCo Beta",
            "tier": "Gold",
            "oem_affiliations": ["dell", "hpe", "netapp"],
            "specializations": ["Storage Solutions", "Server Infrastructure"],
            "regions_served": ["West"],
            "program": "Dell Titanium Partner",
        },
    ]

    for data in partner_data:
        try:
            partner = Partner(**data)
            partner_store.add(partner)
            print(f"  ✓ Added Partner: {partner.name} ({partner.tier})")
        except ValueError as e:
            print(f"  ⚠ Skipped {data['name']}: {e}")


def migrate_customers():
    """Create sample Customer entities."""
    print("\n=== Creating Sample Customers ===")

    customer_data = [
        {
            "id": "customer-alpha",
            "name": "CustomerAlpha",
            "category": "DOD",
            "region": "East",
            "tier": "Strategic",
            "annual_spend": 5000000.0,
            "contract_count": 12,
            "preferred_vehicles": ["sewp-v", "nasa-solutions"],
        },
        {
            "id": "customer-beta",
            "name": "CustomerBeta",
            "category": "DOD",
            "region": "Central",
            "tier": "Strategic",
            "annual_spend": 3500000.0,
            "contract_count": 8,
            "preferred_vehicles": ["gsa-schedule", "dhs-firstsource-ii"],
        },
        {
            "id": "customer-gamma",
            "name": "Agency Gamma",
            "category": "Civilian",
            "region": "West",
            "tier": "Standard",
            "annual_spend": 1200000.0,
            "contract_count": 4,
            "preferred_vehicles": ["gsa-schedule"],
        },
    ]

    for data in customer_data:
        try:
            customer = Customer(**data)
            customer_store.add(customer)
            print(f"  ✓ Added Customer: {customer.name} ({customer.category})")
        except ValueError as e:
            print(f"  ⚠ Skipped {data['name']}: {e}")


def migrate_distributors():
    """Create sample Distributor entities."""
    print("\n=== Creating Sample Distributors ===")

    distributor_data = [
        {
            "id": "distributor-alpha",
            "name": "Tech Distribution Alpha",
            "tier": "Premier",
            "oem_authorizations": ["microsoft", "cisco", "dell", "hpe"],
            "regions_served": ["East", "West", "Central"],
            "product_categories": ["Hardware", "Software", "Cloud Services"],
            "payment_terms": "Net 30",
            "delivery_options": ["Direct Ship", "Warehouse", "Drop Ship"],
        },
        {
            "id": "distributor-beta",
            "name": "Solutions Distributor Beta",
            "tier": "Standard",
            "oem_authorizations": ["vmware", "netapp", "palo-alto"],
            "regions_served": ["West"],
            "product_categories": ["Software", "Storage", "Security"],
            "payment_terms": "Net 45",
            "delivery_options": ["Direct Ship"],
        },
    ]

    for data in distributor_data:
        try:
            distributor = Distributor(**data)
            distributor_store.add(distributor)
            print(f"  ✓ Added Distributor: {distributor.name} ({distributor.tier})")
        except ValueError as e:
            print(f"  ⚠ Skipped {data['name']}: {e}")


def create_scoring_weights_config():
    """Create scoring_weights.json configuration file."""
    print("\n=== Creating Scoring Weights Config ===")

    import json

    config = {
        "version": "2.1",
        "description": "Scoring weights and bonuses for DealCraft opportunity scoring engine",
        "last_updated": "2025-11-01",
        "oem_alignment_scores": {
            "Microsoft": 95,
            "Cisco": 92,
            "Dell": 90,
            "HPE": 88,
            "VMware": 85,
            "NetApp": 83,
            "Palo Alto Networks": 88,
            "Fortinet": 85,
            "AWS": 80,
            "Google": 75,
            "Oracle": 70,
            "IBM": 68,
            "Default": 50,
        },
        "contract_vehicle_scores": {
            "GSA Schedule": 90,
            "SEWP V": 95,
            "NASA SOLUTIONS": 92,
            "DHS FirstSource II": 88,
            "CIO-SP3": 85,
            "Alliant 2": 83,
            "8(a) STARS II": 80,
            "Direct": 60,
            "Default": 50,
        },
        "region_bonuses": {
            "East": 2.5,
            "West": 2.0,
            "Central": 1.5,
        },
        "customer_org_bonuses": {
            "DOD": 4.0,
            "Civilian": 3.0,
            "Default": 2.0,
        },
        "cv_recommendation_bonuses": {
            "single": 5.0,
            "multiple": 7.0,
        },
        "stage_multipliers": {
            "Qualification": 0.15,
            "Discovery": 0.25,
            "Proposal": 0.45,
            "Negotiation": 0.75,
            "Closed Won": 1.0,
            "Closed Lost": 0.0,
            "Default": 0.20,
        },
        "guardrails": {
            "max_total_bonus": 15.0,
            "min_score": 0.0,
            "max_score": 100.0,
            "min_win_prob": 0.0,
            "max_win_prob": 1.0,
        },
    }

    config_path = project_root / "data" / "config" / "scoring_weights.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
        f.write("\n")

    print(f"  ✓ Created scoring weights config at {config_path}")


def main():
    """Run all migrations."""
    print("=" * 80)
    print("DealCraft Entity Migration Script")
    print("=" * 80)

    try:
        migrate_oems()
        migrate_regions()
        migrate_contract_vehicles()
        migrate_partners()
        migrate_customers()
        migrate_distributors()
        create_scoring_weights_config()

        print("\n" + "=" * 80)
        print("Migration Complete!")
        print("=" * 80)
        print("\nEntity counts:")
        print(f"  OEMs: {oem_store.count()}")
        print(f"  Regions: {region_store.count()}")
        print(f"  Contract Vehicles: {contract_vehicle_store.count()}")
        print(f"  Partners: {partner_store.count()}")
        print(f"  Customers: {customer_store.count()}")
        print(f"  Distributors: {distributor_store.count()}")
        print("\nJSON files created in data/entities/")
        print("Config file created at data/config/scoring_weights.json")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
