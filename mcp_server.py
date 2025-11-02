#!/usr/bin/env python3
"""
DealCraft MCP Server

Anthropic Model Context Protocol server for DealCraft entity management.
Provides tools for managing OEMs, Contract Vehicles, Customers, Partners, Distributors, and Regions.

Usage:
    Add to Claude Desktop config:
    {
      "mcpServers": {
        "dealcraft": {
          "command": "python3",
          "args": ["/Users/jonolan/projects/DealCraft/mcp_server.py"]
        }
      }
    }
"""

import sys
from pathlib import Path
from typing import Any

# Save and temporarily remove current directory from sys.path
# to avoid conflict with local mcp/ directory
PROJECT_ROOT = Path(__file__).parent
_project_root_str = str(PROJECT_ROOT)
_original_path = sys.path.copy()

# Filter out project root to prioritize installed mcp package
sys.path = [p for p in sys.path if Path(p).resolve() != PROJECT_ROOT.resolve()]

# Import Anthropic MCP modules (now that local mcp/ is not in path)
from mcp import stdio_server  # noqa: E402
from mcp.server import Server  # noqa: E402
from mcp.types import TextContent, Tool  # noqa: E402

# Restore original path with project root at the beginning
sys.path = [_project_root_str] + [p for p in _original_path if Path(p).resolve() != PROJECT_ROOT.resolve()]

# Clear the cached 'mcp' module to allow importing from local mcp/ directory
# The Anthropic MCP modules (Server, stdio_server, etc.) are already imported above
if "mcp" in sys.modules:
    del sys.modules["mcp"]

# Import DealCraft entities from local mcp/ directory
from mcp.core.entities import (  # noqa: E402
    OEM,
    ContractVehicle,
    contract_vehicle_store,
    customer_store,
    distributor_store,
    oem_store,
    partner_store,
    region_store,
)

# Initialize MCP server
app = Server("dealcraft")


# =============================================================================
# OEM Tools
# =============================================================================


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools."""
    return [
        # OEM Tools
        Tool(
            name="list_oems",
            description="List all OEMs with optional filtering by tier or active status",
            inputSchema={
                "type": "object",
                "properties": {
                    "tier": {
                        "type": "string",
                        "description": "Filter by tier (Strategic, Gold, Silver)",
                        "enum": ["Strategic", "Gold", "Silver"],
                    },
                    "active_only": {
                        "type": "boolean",
                        "description": "Only show active OEMs",
                        "default": True,
                    },
                },
            },
        ),
        Tool(
            name="get_oem",
            description="Get detailed information about a specific OEM",
            inputSchema={
                "type": "object",
                "properties": {"id": {"type": "string", "description": "OEM ID (e.g., 'microsoft', 'cisco')"}},
                "required": ["id"],
            },
        ),
        Tool(
            name="add_oem",
            description="Add a new OEM to the system",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "Unique OEM ID (lowercase, hyphenated)"},
                    "name": {"type": "string", "description": "OEM display name"},
                    "tier": {
                        "type": "string",
                        "description": "OEM tier",
                        "enum": ["Strategic", "Gold", "Silver"],
                    },
                    "programs": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Partner programs",
                    },
                    "contact_name": {"type": "string", "description": "Contact person name"},
                    "contact_email": {"type": "string", "description": "Contact email"},
                    "contact_phone": {"type": "string", "description": "Contact phone"},
                    "notes": {"type": "string", "description": "Additional notes"},
                },
                "required": ["id", "name", "tier"],
            },
        ),
        Tool(
            name="update_oem",
            description="Update an existing OEM",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "OEM ID to update"},
                    "name": {"type": "string", "description": "OEM display name"},
                    "tier": {
                        "type": "string",
                        "description": "OEM tier",
                        "enum": ["Strategic", "Gold", "Silver"],
                    },
                    "programs": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Partner programs",
                    },
                    "contact_name": {"type": "string", "description": "Contact person name"},
                    "contact_email": {"type": "string", "description": "Contact email"},
                    "contact_phone": {"type": "string", "description": "Contact phone"},
                    "notes": {"type": "string", "description": "Additional notes"},
                    "active": {"type": "boolean", "description": "Active status"},
                },
                "required": ["id"],
            },
        ),
        Tool(
            name="deactivate_oem",
            description="Deactivate (soft delete) an OEM",
            inputSchema={
                "type": "object",
                "properties": {"id": {"type": "string", "description": "OEM ID to deactivate"}},
                "required": ["id"],
            },
        ),
        # Contract Vehicle Tools
        Tool(
            name="list_contract_vehicles",
            description="List all contract vehicles with optional filtering",
            inputSchema={
                "type": "object",
                "properties": {
                    "active_only": {
                        "type": "boolean",
                        "description": "Only show active contract vehicles",
                        "default": True,
                    },
                    "min_priority": {
                        "type": "number",
                        "description": "Minimum priority score",
                    },
                },
            },
        ),
        Tool(
            name="get_contract_vehicle",
            description="Get detailed information about a specific contract vehicle",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "Contract vehicle ID (e.g., 'sewp-v', 'gsa-schedule')",
                    }
                },
                "required": ["id"],
            },
        ),
        Tool(
            name="add_contract_vehicle",
            description="Add a new contract vehicle to the system",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "Unique CV ID (lowercase, hyphenated)",
                    },
                    "name": {"type": "string", "description": "Contract vehicle display name"},
                    "priority_score": {
                        "type": "number",
                        "description": "Priority score (0-100)",
                    },
                    "oems_supported": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of supported OEM IDs",
                    },
                    "categories": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Product/service categories",
                    },
                    "active_bpas": {
                        "type": "integer",
                        "description": "Number of active BPAs",
                    },
                    "ceiling_amount": {
                        "type": "number",
                        "description": "Contract ceiling amount (null for unlimited)",
                    },
                    "contracting_office": {
                        "type": "string",
                        "description": "Contracting office name",
                    },
                    "scope": {"type": "string", "description": "Contract scope description"},
                },
                "required": ["id", "name", "priority_score"],
            },
        ),
        # Customer Tools
        Tool(
            name="list_customers",
            description="List all customers with optional filtering",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Filter by category",
                        "enum": ["DOD", "Civilian"],
                    },
                    "region": {
                        "type": "string",
                        "description": "Filter by region",
                        "enum": ["East", "West", "Central"],
                    },
                    "tier": {
                        "type": "string",
                        "description": "Filter by tier",
                        "enum": ["Strategic", "Standard"],
                    },
                    "active_only": {
                        "type": "boolean",
                        "description": "Only show active customers",
                        "default": True,
                    },
                },
            },
        ),
        Tool(
            name="get_customer",
            description="Get detailed information about a specific customer",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "Customer ID",
                    }
                },
                "required": ["id"],
            },
        ),
        # Partner Tools
        Tool(
            name="list_partners",
            description="List all partners with optional filtering",
            inputSchema={
                "type": "object",
                "properties": {
                    "tier": {
                        "type": "string",
                        "description": "Filter by tier",
                        "enum": ["Platinum", "Gold", "Silver"],
                    },
                    "active_only": {
                        "type": "boolean",
                        "description": "Only show active partners",
                        "default": True,
                    },
                },
            },
        ),
        # Distributor Tools
        Tool(
            name="list_distributors",
            description="List all distributors with optional filtering",
            inputSchema={
                "type": "object",
                "properties": {
                    "tier": {
                        "type": "string",
                        "description": "Filter by tier",
                        "enum": ["Premier", "Standard"],
                    },
                    "active_only": {
                        "type": "boolean",
                        "description": "Only show active distributors",
                        "default": True,
                    },
                },
            },
        ),
        # Region Tools
        Tool(
            name="list_regions",
            description="List all regions with bonus information",
            inputSchema={
                "type": "object",
                "properties": {
                    "active_only": {
                        "type": "boolean",
                        "description": "Only show active regions",
                        "default": True,
                    }
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""

    try:
        # OEM Tools
        if name == "list_oems":
            tier = arguments.get("tier")
            active_only = arguments.get("active_only", True)

            oems = oem_store.get_all(active_only=active_only)

            if tier:
                oems = [o for o in oems if o.tier == tier]

            result = f"Found {len(oems)} OEM(s):\n\n"
            for oem in oems:
                status = "✓ Active" if oem.active else "✗ Inactive"
                programs = ", ".join(oem.programs[:3]) if oem.programs else "None"
                result += f"• {oem.name} ({oem.tier}) - {status}\n"
                result += f"  ID: {oem.id}\n"
                result += f"  Programs: {programs}\n"
                if oem.contact_email:
                    result += f"  Contact: {oem.contact_email}\n"
                result += "\n"

            return [TextContent(type="text", text=result)]

        elif name == "get_oem":
            oem_id = arguments["id"]
            oem = oem_store.get(oem_id)

            if not oem:
                return [TextContent(type="text", text=f"OEM '{oem_id}' not found")]

            result = f"OEM: {oem.name}\n\n"
            result += f"ID: {oem.id}\n"
            result += f"Tier: {oem.tier}\n"
            result += f"Status: {'✓ Active' if oem.active else '✗ Inactive'}\n"
            result += f"Programs: {', '.join(oem.programs) if oem.programs else 'None'}\n"
            if oem.contact_name:
                result += f"Contact Name: {oem.contact_name}\n"
            if oem.contact_email:
                result += f"Contact Email: {oem.contact_email}\n"
            if oem.contact_phone:
                result += f"Contact Phone: {oem.contact_phone}\n"
            if oem.notes:
                result += f"Notes: {oem.notes}\n"
            result += f"Created: {oem.created_at}\n"
            result += f"Updated: {oem.updated_at}\n"

            return [TextContent(type="text", text=result)]

        elif name == "add_oem":
            oem = OEM(
                id=arguments["id"],
                name=arguments["name"],
                tier=arguments["tier"],
                programs=arguments.get("programs", []),
                contact_name=arguments.get("contact_name"),
                contact_email=arguments.get("contact_email"),
                contact_phone=arguments.get("contact_phone"),
                notes=arguments.get("notes"),
            )
            oem_store.add(oem)

            return [
                TextContent(
                    type="text",
                    text=f"✓ Successfully added OEM: {oem.name} ({oem.tier})\nID: {oem.id}",
                )
            ]

        elif name == "update_oem":
            oem_id = arguments["id"]
            oem = oem_store.get(oem_id)

            if not oem:
                return [TextContent(type="text", text=f"OEM '{oem_id}' not found")]

            # Update fields if provided
            if "name" in arguments:
                oem.name = arguments["name"]
            if "tier" in arguments:
                oem.tier = arguments["tier"]
            if "programs" in arguments:
                oem.programs = arguments["programs"]
            if "contact_name" in arguments:
                oem.contact_name = arguments["contact_name"]
            if "contact_email" in arguments:
                oem.contact_email = arguments["contact_email"]
            if "contact_phone" in arguments:
                oem.contact_phone = arguments["contact_phone"]
            if "notes" in arguments:
                oem.notes = arguments["notes"]
            if "active" in arguments:
                oem.active = arguments["active"]

            oem_store.update(oem_id, oem)

            return [TextContent(type="text", text=f"✓ Successfully updated OEM: {oem.name}")]

        elif name == "deactivate_oem":
            oem_id = arguments["id"]
            oem = oem_store.get(oem_id)

            if not oem:
                return [TextContent(type="text", text=f"OEM '{oem_id}' not found")]

            oem.active = False
            oem_store.update(oem_id, oem)

            return [TextContent(type="text", text=f"✓ Deactivated OEM: {oem.name}")]

        # Contract Vehicle Tools
        elif name == "list_contract_vehicles":
            active_only = arguments.get("active_only", True)
            min_priority = arguments.get("min_priority")

            cvs = contract_vehicle_store.get_all(active_only=active_only)

            if min_priority:
                cvs = [cv for cv in cvs if cv.priority_score >= min_priority]

            # Sort by priority descending
            cvs.sort(key=lambda cv: cv.priority_score, reverse=True)

            result = f"Found {len(cvs)} Contract Vehicle(s):\n\n"
            for cv in cvs:
                status = "✓ Active" if cv.active else "✗ Inactive"
                result += f"• {cv.name} - Priority: {cv.priority_score:.1f} - {status}\n"
                result += f"  ID: {cv.id}\n"
                result += f"  BPAs: {cv.active_bpas}\n"
                result += f"  OEMs: {len(cv.oems_supported)} supported\n"
                if cv.ceiling_amount:
                    result += f"  Ceiling: ${cv.ceiling_amount:,.0f}\n"
                result += "\n"

            return [TextContent(type="text", text=result)]

        elif name == "get_contract_vehicle":
            cv_id = arguments["id"]
            cv = contract_vehicle_store.get(cv_id)

            if not cv:
                return [TextContent(type="text", text=f"Contract vehicle '{cv_id}' not found")]

            result = f"Contract Vehicle: {cv.name}\n\n"
            result += f"ID: {cv.id}\n"
            result += f"Priority Score: {cv.priority_score}\n"
            result += f"Status: {'✓ Active' if cv.active else '✗ Inactive'}\n"
            result += f"Active BPAs: {cv.active_bpas}\n"
            result += f"Categories: {', '.join(cv.categories)}\n"
            result += f"OEMs Supported ({len(cv.oems_supported)}): {', '.join(cv.oems_supported[:5])}"
            if len(cv.oems_supported) > 5:
                result += f" (+{len(cv.oems_supported) - 5} more)"
            result += "\n"
            if cv.ceiling_amount:
                result += f"Ceiling Amount: ${cv.ceiling_amount:,.0f}\n"
            if cv.contracting_office:
                result += f"Contracting Office: {cv.contracting_office}\n"
            if cv.scope:
                result += f"Scope: {cv.scope}\n"
            result += f"Created: {cv.created_at}\n"
            result += f"Updated: {cv.updated_at}\n"

            return [TextContent(type="text", text=result)]

        elif name == "add_contract_vehicle":
            cv = ContractVehicle(
                id=arguments["id"],
                name=arguments["name"],
                priority_score=arguments["priority_score"],
                oems_supported=arguments.get("oems_supported", []),
                categories=arguments.get("categories", []),
                active_bpas=arguments.get("active_bpas", 0),
                ceiling_amount=arguments.get("ceiling_amount"),
                contracting_office=arguments.get("contracting_office"),
                scope=arguments.get("scope"),
            )
            contract_vehicle_store.add(cv)

            return [
                TextContent(
                    type="text",
                    text=f"✓ Successfully added Contract Vehicle: {cv.name} (Priority: {cv.priority_score})\nID: {cv.id}",
                )
            ]

        # Customer Tools
        elif name == "list_customers":
            category = arguments.get("category")
            region = arguments.get("region")
            tier = arguments.get("tier")
            active_only = arguments.get("active_only", True)

            customers = customer_store.get_all(active_only=active_only)

            if category:
                customers = [c for c in customers if c.category == category]
            if region:
                customers = [c for c in customers if c.region == region]
            if tier:
                customers = [c for c in customers if c.tier == tier]

            result = f"Found {len(customers)} Customer(s):\n\n"
            for customer in customers:
                status = "✓ Active" if customer.active else "✗ Inactive"
                result += f"• {customer.name} ({customer.tier}) - {status}\n"
                result += f"  ID: {customer.id}\n"
                result += f"  Category: {customer.category} | Region: {customer.region}\n"
                result += f"  Annual Spend: ${customer.annual_spend:,.0f}\n"
                result += f"  Contracts: {customer.contract_count}\n"
                result += "\n"

            return [TextContent(type="text", text=result)]

        elif name == "get_customer":
            customer_id = arguments["id"]
            customer = customer_store.get(customer_id)

            if not customer:
                return [TextContent(type="text", text=f"Customer '{customer_id}' not found")]

            result = f"Customer: {customer.name}\n\n"
            result += f"ID: {customer.id}\n"
            result += f"Category: {customer.category}\n"
            result += f"Region: {customer.region}\n"
            result += f"Tier: {customer.tier}\n"
            result += f"Status: {'✓ Active' if customer.active else '✗ Inactive'}\n"
            result += f"Annual Spend: ${customer.annual_spend:,.0f}\n"
            result += f"Contract Count: {customer.contract_count}\n"
            result += f"Preferred Vehicles: {', '.join(customer.preferred_vehicles) if customer.preferred_vehicles else 'None'}\n"
            result += f"Created: {customer.created_at}\n"
            result += f"Updated: {customer.updated_at}\n"

            return [TextContent(type="text", text=result)]

        # Partner Tools
        elif name == "list_partners":
            tier = arguments.get("tier")
            active_only = arguments.get("active_only", True)

            partners = partner_store.get_all(active_only=active_only)

            if tier:
                partners = [p for p in partners if p.tier == tier]

            result = f"Found {len(partners)} Partner(s):\n\n"
            for partner in partners:
                status = "✓ Active" if partner.active else "✗ Inactive"
                result += f"• {partner.name} ({partner.tier}) - {status}\n"
                result += f"  ID: {partner.id}\n"
                result += f"  OEM Affiliations: {', '.join(partner.oem_affiliations[:3]) if partner.oem_affiliations else 'None'}\n"
                result += f"  Regions: {', '.join(partner.regions_served) if partner.regions_served else 'None'}\n"
                result += "\n"

            return [TextContent(type="text", text=result)]

        # Distributor Tools
        elif name == "list_distributors":
            tier = arguments.get("tier")
            active_only = arguments.get("active_only", True)

            distributors = distributor_store.get_all(active_only=active_only)

            if tier:
                distributors = [d for d in distributors if d.tier == tier]

            result = f"Found {len(distributors)} Distributor(s):\n\n"
            for distributor in distributors:
                status = "✓ Active" if distributor.active else "✗ Inactive"
                result += f"• {distributor.name} ({distributor.tier}) - {status}\n"
                result += f"  ID: {distributor.id}\n"
                result += (
                    f"  OEM Authorizations: {', '.join(distributor.oem_authorizations[:3]) if distributor.oem_authorizations else 'None'}\n"
                )
                result += f"  Payment Terms: {distributor.payment_terms}\n"
                result += "\n"

            return [TextContent(type="text", text=result)]

        # Region Tools
        elif name == "list_regions":
            active_only = arguments.get("active_only", True)

            regions = region_store.get_all(active_only=active_only)

            result = f"Found {len(regions)} Region(s):\n\n"
            for region in regions:
                status = "✓ Active" if region.active else "✗ Inactive"
                result += f"• {region.name} - Bonus: {region.bonus:.1f} - {status}\n"
                result += f"  ID: {region.id}\n"
                if region.description:
                    result += f"  Description: {region.description}\n"
                result += "\n"

            return [TextContent(type="text", text=result)]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
