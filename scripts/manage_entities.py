#!/usr/bin/env python3
"""
Entity Management CLI Tool

Interactive command-line tool for managing DealCraft entities:
- OEMs, Partners, Customers, Distributors, Regions, Contract Vehicles

Usage:
    python scripts/manage_entities.py

    # Or with specific commands
    python scripts/manage_entities.py list-oems
    python scripts/manage_entities.py add-oem
    python scripts/manage_entities.py update-oem microsoft
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
    contract_vehicle_store,
    customer_store,
    distributor_store,
    oem_store,
    partner_store,
    region_store,
)


def list_entities(store, entity_type):
    """List all entities of a given type."""
    print(f"\n{'=' * 80}")
    print(f"{entity_type.upper()} (Total: {store.count()})")
    print(f"{'=' * 80}\n")

    entities = store.get_all()
    if not entities:
        print(f"No {entity_type} found.")
        return

    for entity in entities:
        status = "✓ Active" if entity.active else "✗ Inactive"
        print(f"ID: {entity.id:<20} | Name: {entity.name:<30} | {status}")

        # Show additional key fields based on entity type
        if hasattr(entity, "tier"):
            print(f"  Tier: {entity.tier}")
        if hasattr(entity, "priority_score"):
            print(f"  Priority: {entity.priority_score}")
        if hasattr(entity, "bonus"):
            print(f"  Bonus: {entity.bonus}")
        print()


def add_oem():
    """Interactive OEM creation."""
    print("\n=== Add New OEM ===\n")

    entity_id = input("OEM ID (e.g., 'juniper'): ").strip().lower()
    if not entity_id:
        print("Error: ID is required")
        return

    # Check if already exists
    if oem_store.get(entity_id):
        print(f"Error: OEM with ID '{entity_id}' already exists")
        return

    name = input("OEM Name (e.g., 'Juniper Networks'): ").strip()
    tier = input("Tier (Strategic/Gold/Silver): ").strip() or "Silver"
    programs = input("Programs (comma-separated, e.g., 'Routing, Switching'): ").strip()
    programs_list = [p.strip() for p in programs.split(",")] if programs else []

    contact_name = input("Contact Name (optional): ").strip() or None
    contact_email = input("Contact Email (optional): ").strip() or None
    contact_phone = input("Contact Phone (optional): ").strip() or None
    notes = input("Notes (optional): ").strip() or None

    try:
        oem = OEM(
            id=entity_id,
            name=name,
            tier=tier,
            programs=programs_list,
            contact_name=contact_name,
            contact_email=contact_email,
            contact_phone=contact_phone,
            notes=notes,
        )
        oem_store.add(oem)
        print(f"\n✓ Successfully added OEM: {name}")
    except Exception as e:
        print(f"\n✗ Error adding OEM: {e}")


def add_customer():
    """Interactive Customer creation."""
    print("\n=== Add New Customer ===\n")

    entity_id = input("Customer ID (e.g., 'dod-army'): ").strip().lower()
    if not entity_id:
        print("Error: ID is required")
        return

    if customer_store.get(entity_id):
        print(f"Error: Customer with ID '{entity_id}' already exists")
        return

    name = input("Customer Name (e.g., 'US Army'): ").strip()
    category = input("Category (DOD/Civilian): ").strip() or "Civilian"
    region = input("Region (East/West/Central): ").strip() or "East"
    tier = input("Tier (Strategic/Standard): ").strip() or "Standard"

    annual_spend = input("Annual Spend (e.g., 1000000): ").strip()
    annual_spend = float(annual_spend) if annual_spend else 0.0

    contract_count = input("Contract Count (e.g., 5): ").strip()
    contract_count = int(contract_count) if contract_count else 0

    preferred_vehicles = input("Preferred Contract Vehicles (comma-separated IDs): ").strip()
    preferred_vehicles_list = [v.strip() for v in preferred_vehicles.split(",")] if preferred_vehicles else []

    try:
        customer = Customer(
            id=entity_id,
            name=name,
            category=category,
            region=region,
            tier=tier,
            annual_spend=annual_spend,
            contract_count=contract_count,
            preferred_vehicles=preferred_vehicles_list,
        )
        customer_store.add(customer)
        print(f"\n✓ Successfully added Customer: {name}")
    except Exception as e:
        print(f"\n✗ Error adding Customer: {e}")


def add_contract_vehicle():
    """Interactive Contract Vehicle creation."""
    print("\n=== Add New Contract Vehicle ===\n")

    entity_id = input("CV ID (e.g., 'stars-iii'): ").strip().lower()
    if not entity_id:
        print("Error: ID is required")
        return

    if contract_vehicle_store.get(entity_id):
        print(f"Error: Contract Vehicle with ID '{entity_id}' already exists")
        return

    name = input("CV Name (e.g., 'STARS III'): ").strip()
    priority_score = input("Priority Score (0-100, e.g., 88): ").strip()
    priority_score = float(priority_score) if priority_score else 50.0

    oems_supported = input("OEMs Supported (comma-separated IDs, e.g., 'microsoft,cisco,dell'): ").strip()
    oems_supported_list = [o.strip() for o in oems_supported.split(",")] if oems_supported else []

    categories = input("Categories (comma-separated, e.g., 'IT Services, Cloud'): ").strip()
    categories_list = [c.strip() for c in categories.split(",")] if categories else []

    active_bpas = input("Number of Active BPAs (e.g., 2): ").strip()
    active_bpas = int(active_bpas) if active_bpas else 0

    ceiling_amount = input("Ceiling Amount (e.g., 20000000000 or leave empty for None): ").strip()
    ceiling_amount = float(ceiling_amount) if ceiling_amount else None

    contracting_office = input("Contracting Office (e.g., 'GSA'): ").strip() or None
    scope = input("Scope (e.g., 'IT Solutions for Federal Agencies'): ").strip() or None

    try:
        cv = ContractVehicle(
            id=entity_id,
            name=name,
            priority_score=priority_score,
            oems_supported=oems_supported_list,
            categories=categories_list,
            active_bpas=active_bpas,
            ceiling_amount=ceiling_amount,
            contracting_office=contracting_office,
            scope=scope,
        )
        contract_vehicle_store.add(cv)
        print(f"\n✓ Successfully added Contract Vehicle: {name}")
    except Exception as e:
        print(f"\n✗ Error adding Contract Vehicle: {e}")


def update_entity_status(store, entity_type, entity_id, activate=True):
    """Activate or deactivate an entity."""
    entity = store.get(entity_id)
    if not entity:
        print(f"Error: {entity_type} with ID '{entity_id}' not found")
        return

    entity.active = activate
    store.update(entity_id, entity)

    status = "activated" if activate else "deactivated"
    print(f"✓ Successfully {status} {entity_type}: {entity.name}")


def show_menu():
    """Show interactive menu."""
    print("\n" + "=" * 80)
    print("DealCraft Entity Management System")
    print("=" * 80)
    print("\nOPERATIONS:")
    print("  1. List OEMs")
    print("  2. List Customers")
    print("  3. List Contract Vehicles")
    print("  4. List Partners")
    print("  5. List Distributors")
    print("  6. List Regions")
    print()
    print("  7. Add OEM")
    print("  8. Add Customer")
    print("  9. Add Contract Vehicle")
    print()
    print("  10. Deactivate Entity")
    print("  11. Activate Entity")
    print()
    print("  0. Exit")
    print("=" * 80)


def main():
    """Main interactive loop."""

    if len(sys.argv) > 1:
        # Command-line mode
        command = sys.argv[1]

        if command == "list-oems":
            list_entities(oem_store, "OEMs")
        elif command == "list-customers":
            list_entities(customer_store, "Customers")
        elif command == "list-cvs":
            list_entities(contract_vehicle_store, "Contract Vehicles")
        elif command == "list-partners":
            list_entities(partner_store, "Partners")
        elif command == "list-distributors":
            list_entities(distributor_store, "Distributors")
        elif command == "list-regions":
            list_entities(region_store, "Regions")
        elif command == "add-oem":
            add_oem()
        elif command == "add-customer":
            add_customer()
        elif command == "add-cv":
            add_contract_vehicle()
        else:
            print(f"Unknown command: {command}")
            print("\nAvailable commands:")
            print("  list-oems, list-customers, list-cvs, list-partners, list-distributors, list-regions")
            print("  add-oem, add-customer, add-cv")
        return

    # Interactive mode
    while True:
        show_menu()
        choice = input("\nEnter choice (0-11): ").strip()

        if choice == "0":
            print("\nGoodbye!")
            break
        elif choice == "1":
            list_entities(oem_store, "OEMs")
        elif choice == "2":
            list_entities(customer_store, "Customers")
        elif choice == "3":
            list_entities(contract_vehicle_store, "Contract Vehicles")
        elif choice == "4":
            list_entities(partner_store, "Partners")
        elif choice == "5":
            list_entities(distributor_store, "Distributors")
        elif choice == "6":
            list_entities(region_store, "Regions")
        elif choice == "7":
            add_oem()
        elif choice == "8":
            add_customer()
        elif choice == "9":
            add_contract_vehicle()
        elif choice == "10":
            entity_type = input("Entity type (oem/customer/cv/partner/distributor/region): ").strip().lower()
            entity_id = input("Entity ID: ").strip().lower()

            store_map = {
                "oem": oem_store,
                "customer": customer_store,
                "cv": contract_vehicle_store,
                "partner": partner_store,
                "distributor": distributor_store,
                "region": region_store,
            }

            if entity_type in store_map:
                update_entity_status(store_map[entity_type], entity_type, entity_id, activate=False)
            else:
                print(f"Unknown entity type: {entity_type}")
        elif choice == "11":
            entity_type = input("Entity type (oem/customer/cv/partner/distributor/region): ").strip().lower()
            entity_id = input("Entity ID: ").strip().lower()

            store_map = {
                "oem": oem_store,
                "customer": customer_store,
                "cv": contract_vehicle_store,
                "partner": partner_store,
                "distributor": distributor_store,
                "region": region_store,
            }

            if entity_type in store_map:
                update_entity_status(store_map[entity_type], entity_type, entity_id, activate=True)
            else:
                print(f"Unknown entity type: {entity_type}")
        else:
            print("Invalid choice. Please try again.")

        input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
