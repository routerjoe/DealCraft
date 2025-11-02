"""
Entity Management Screen for DealCraft TUI

Provides interactive management of:
- OEMs
- Contract Vehicles
- Customers
- Partners
- Distributors
- Regions
"""

import sys
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Header, Static

# Add project root to path for entity imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from mcp.core.entities import (  # noqa: E402
    contract_vehicle_store,
    customer_store,
    distributor_store,
    oem_store,
    partner_store,
    region_store,
)


class EntityManagementScreen(Screen):
    """Entity Management Screen with CRUD operations."""

    BINDINGS = [
        ("escape", "app.pop_screen", "Back"),
        ("q", "app.pop_screen", "Back"),
        ("a", "add_entity", "Add"),
        ("d", "delete_entity", "Deactivate"),
        ("r", "refresh", "Refresh"),
        ("1", "show_oems", "OEMs"),
        ("2", "show_cvs", "CVs"),
        ("3", "show_customers", "Customers"),
        ("4", "show_partners", "Partners"),
        ("5", "show_distributors", "Distributors"),
        ("6", "show_regions", "Regions"),
    ]

    current_entity_type = reactive("oems")
    status_message = reactive("")

    def compose(self) -> ComposeResult:
        """Compose the Entity Management UI."""
        yield Header()

        with Container(id="entity_main"):
            # Top panel - Entity type selector and actions
            with Horizontal(id="entity_header"):
                yield Static("[b][cyan]Entity Management[/cyan][/b]", id="title_text")
                yield Static(id="entity_type_display")
                yield Static(id="entity_count")

            # Entity table
            with Vertical(id="entity_content"):
                self.table = DataTable(id="entity_table")
                yield self.table

            # Status/message bar
            yield Static(id="status_bar")

            # Action buttons
            with Horizontal(id="entity_actions"):
                yield Button("Add [a]", id="btn_add", variant="success")
                yield Button("Deactivate [d]", id="btn_delete", variant="error")
                yield Button("Refresh [r]", id="btn_refresh", variant="primary")

        yield Footer()

    async def on_mount(self) -> None:
        """Initialize the entity management screen."""
        # Set up table columns for OEMs (default view)
        await self.action_show_oems()

    def _update_status(self, message: str, style: str = "dim") -> None:
        """Update status bar with a message."""
        self.status_message = message
        status_bar = self.query_one("#status_bar", Static)
        status_bar.update(f"[{style}]{message}[/{style}]")

    async def _load_entities(self):
        """Load and display entities based on current type."""
        self.table.clear()

        if self.current_entity_type == "oems":
            await self._load_oems()
        elif self.current_entity_type == "cvs":
            await self._load_contract_vehicles()
        elif self.current_entity_type == "customers":
            await self._load_customers()
        elif self.current_entity_type == "partners":
            await self._load_partners()
        elif self.current_entity_type == "distributors":
            await self._load_distributors()
        elif self.current_entity_type == "regions":
            await self._load_regions()

        # Update entity type display
        type_display = self.query_one("#entity_type_display", Static)
        type_display.update(f"[b]Type:[/b] {self.current_entity_type.upper()}")

        # Update count
        count_display = self.query_one("#entity_count", Static)
        count = self.table.row_count
        count_display.update(f"[b]Count:[/b] {count}")

    async def _load_oems(self) -> None:
        """Load OEMs into table."""
        self.table.clear(columns=True)
        self.table.add_columns("ID", "Name", "Tier", "Programs", "Status")

        oems = oem_store.get_all()
        for oem in oems:
            status = "✓ Active" if oem.active else "✗ Inactive"
            programs = ", ".join(oem.programs[:3]) if oem.programs else "—"
            if len(oem.programs) > 3:
                programs += f" (+{len(oem.programs) - 3})"

            self.table.add_row(
                oem.id,
                oem.name,
                oem.tier,
                programs,
                status,
            )

        self._update_status(f"Loaded {len(oems)} OEMs")

    async def _load_contract_vehicles(self) -> None:
        """Load Contract Vehicles into table."""
        self.table.clear(columns=True)
        self.table.add_columns("ID", "Name", "Priority", "BPAs", "OEMs", "Status")

        cvs = contract_vehicle_store.get_all()
        for cv in cvs:
            status = "✓ Active" if cv.active else "✗ Inactive"
            oems_count = len(cv.oems_supported)

            self.table.add_row(
                cv.id,
                cv.name,
                f"{cv.priority_score:.1f}",
                str(cv.active_bpas),
                f"{oems_count} OEMs",
                status,
            )

        self._update_status(f"Loaded {len(cvs)} Contract Vehicles")

    async def _load_customers(self) -> None:
        """Load Customers into table."""
        self.table.clear(columns=True)
        self.table.add_columns("ID", "Name", "Category", "Region", "Tier", "Status")

        customers = customer_store.get_all()
        for customer in customers:
            status = "✓ Active" if customer.active else "✗ Inactive"

            self.table.add_row(
                customer.id,
                customer.name,
                customer.category,
                customer.region,
                customer.tier,
                status,
            )

        self._update_status(f"Loaded {len(customers)} Customers")

    async def _load_partners(self) -> None:
        """Load Partners into table."""
        self.table.clear(columns=True)
        self.table.add_columns("ID", "Name", "Tier", "OEM Affiliations", "Regions", "Status")

        partners = partner_store.get_all()
        for partner in partners:
            status = "✓ Active" if partner.active else "✗ Inactive"
            oems = ", ".join(partner.oem_affiliations[:2]) if partner.oem_affiliations else "—"
            if len(partner.oem_affiliations) > 2:
                oems += f" (+{len(partner.oem_affiliations) - 2})"
            regions = ", ".join(partner.regions_served[:2]) if partner.regions_served else "—"

            self.table.add_row(
                partner.id,
                partner.name,
                partner.tier,
                oems,
                regions,
                status,
            )

        self._update_status(f"Loaded {len(partners)} Partners")

    async def _load_distributors(self) -> None:
        """Load Distributors into table."""
        self.table.clear(columns=True)
        self.table.add_columns("ID", "Name", "Tier", "OEM Authorizations", "Regions", "Status")

        distributors = distributor_store.get_all()
        for distributor in distributors:
            status = "✓ Active" if distributor.active else "✗ Inactive"
            oems = ", ".join(distributor.oem_authorizations[:2]) if distributor.oem_authorizations else "—"
            if len(distributor.oem_authorizations) > 2:
                oems += f" (+{len(distributor.oem_authorizations) - 2})"
            regions = ", ".join(distributor.regions_served[:2]) if distributor.regions_served else "—"

            self.table.add_row(
                distributor.id,
                distributor.name,
                distributor.tier,
                oems,
                regions,
                status,
            )

        self._update_status(f"Loaded {len(distributors)} Distributors")

    async def _load_regions(self) -> None:
        """Load Regions into table."""
        self.table.clear(columns=True)
        self.table.add_columns("ID", "Name", "Bonus", "Description", "Status")

        regions = region_store.get_all()
        for region in regions:
            status = "✓ Active" if region.active else "✗ Inactive"
            desc = (region.description[:40] + "...") if region.description and len(region.description) > 40 else (region.description or "—")

            self.table.add_row(
                region.id,
                region.name,
                f"{region.bonus:.1f}",
                desc,
                status,
            )

        self._update_status(f"Loaded {len(regions)} Regions")

    async def action_show_oems(self) -> None:
        """Switch to OEMs view."""
        self.current_entity_type = "oems"
        await self._load_entities()

    async def action_show_cvs(self) -> None:
        """Switch to Contract Vehicles view."""
        self.current_entity_type = "cvs"
        await self._load_entities()

    async def action_show_customers(self) -> None:
        """Switch to Customers view."""
        self.current_entity_type = "customers"
        await self._load_entities()

    async def action_show_partners(self) -> None:
        """Switch to Partners view."""
        self.current_entity_type = "partners"
        await self._load_entities()

    async def action_show_distributors(self) -> None:
        """Switch to Distributors view."""
        self.current_entity_type = "distributors"
        await self._load_entities()

    async def action_show_regions(self) -> None:
        """Switch to Regions view."""
        self.current_entity_type = "regions"
        await self._load_entities()

    async def action_add_entity(self) -> None:
        """Add a new entity (placeholder - show message)."""
        self._update_status(f"Add {self.current_entity_type} - Use CLI tool: python3 scripts/manage_entities.py", "yellow")

    async def action_delete_entity(self) -> None:
        """Deactivate selected entity."""
        try:
            row = self.table.cursor_row
            if row is None:
                self._update_status("No entity selected", "yellow")
                return

            entity_id = self.table.get_row(row)[0]

            # Get the appropriate store
            store_map = {
                "oems": oem_store,
                "cvs": contract_vehicle_store,
                "customers": customer_store,
                "partners": partner_store,
                "distributors": distributor_store,
                "regions": region_store,
            }

            store = store_map.get(self.current_entity_type)
            if not store:
                self._update_status("Unknown entity type", "red")
                return

            # Deactivate the entity
            entity = store.get(entity_id)
            if not entity:
                self._update_status(f"Entity '{entity_id}' not found", "red")
                return

            entity.active = False
            store.update(entity_id, entity)

            self._update_status(f"Deactivated {self.current_entity_type[:-1]}: {entity.name}", "green")

            # Refresh the view
            await self._load_entities()

        except Exception as e:
            self._update_status(f"Error deactivating entity: {e}", "red")

    async def action_refresh(self) -> None:
        """Refresh entity list."""
        await self._load_entities()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn_add":
            await self.action_add_entity()
        elif event.button.id == "btn_delete":
            await self.action_delete_entity()
        elif event.button.id == "btn_refresh":
            await self.action_refresh()
