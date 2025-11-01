"""Entity Management System - Centralized entity management for DealCraft.

This module provides the Entity Management System (EMS) for managing:
- OEMs (Original Equipment Manufacturers)
- Partners (Channel Partners)
- Customers (Agencies/Organizations)
- Distributors (Distribution Partners)
- Regions (Geographic Regions)
- Contract Vehicles (Government Contract Vehicles)

Each entity type has its own store with CRUD operations and specialized query methods.
"""

from mcp.core.entities.contract_vehicle import ContractVehicle, ContractVehicleStore, contract_vehicle_store
from mcp.core.entities.customer import Customer, CustomerStore, customer_store
from mcp.core.entities.distributor import Distributor, DistributorStore, distributor_store
from mcp.core.entities.oem import OEM, OEMStore, oem_store
from mcp.core.entities.partner import Partner, PartnerStore, partner_store
from mcp.core.entities.region import Region, RegionStore, region_store

__all__ = [
    # Entity Models
    "OEM",
    "Partner",
    "Customer",
    "Distributor",
    "Region",
    "ContractVehicle",
    # Store Classes
    "OEMStore",
    "PartnerStore",
    "CustomerStore",
    "DistributorStore",
    "RegionStore",
    "ContractVehicleStore",
    # Global Store Instances
    "oem_store",
    "partner_store",
    "customer_store",
    "distributor_store",
    "region_store",
    "contract_vehicle_store",
]
