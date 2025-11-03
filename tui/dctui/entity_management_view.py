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
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, DataTable, Footer, Header, Input, Label, Static

# Add project root to path for entity imports
project_root = Path(__file__).resolve().parents[2]
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


class EditEntityModal(ModalScreen):
    """Modal screen for editing an existing entity."""

    def __init__(self, entity_type: str, entity_data: dict) -> None:
        super().__init__()
        self.entity_type = entity_type
        self.entity_data = entity_data

    def compose(self) -> ComposeResult:
        """Compose the edit entity modal."""
        with Container(id="add_entity_dialog"):
            yield Label(f"[b]Edit {self.entity_type.upper()}[/b]", id="modal_title")

            with VerticalScroll(id="form_container"):
                if self.entity_type == "oems":
                    yield Label("ID (read-only):")
                    yield Input(id="input_id", value=str(self.entity_data.get("id", "")), disabled=True)
                    yield Label("Name:")
                    yield Input(id="input_name", placeholder="e.g., Juniper Networks", value=str(self.entity_data.get("name", "")))
                    yield Label("Tier (Strategic/Gold/Silver):")
                    yield Input(id="input_tier", placeholder="Strategic", value=str(self.entity_data.get("tier", "Gold")))
                    yield Label("Programs (comma-separated):")
                    programs = ", ".join(self.entity_data.get("programs", []))
                    yield Input(id="input_programs", placeholder="e.g., Routing, Switching", value=programs)
                    yield Label("Contact Email (optional):")
                    yield Input(
                        id="input_contact_email", placeholder="partners@example.com", value=str(self.entity_data.get("contact_email") or "")
                    )

                elif self.entity_type == "cvs":
                    yield Label("ID (read-only):")
                    yield Input(id="input_id", value=str(self.entity_data.get("id", "")), disabled=True)
                    yield Label("Name:")
                    yield Input(id="input_name", placeholder="e.g., STARS III", value=str(self.entity_data.get("name", "")))
                    yield Label("Priority Score (0-100):")
                    yield Input(id="input_priority", placeholder="85", value=str(self.entity_data.get("priority_score", 85)))
                    yield Label("OEMs Supported (comma-separated IDs):")
                    oems = ", ".join(self.entity_data.get("oems_supported", []))
                    yield Input(id="input_oems", placeholder="microsoft,cisco,dell", value=oems)
                    yield Label("Categories (comma-separated):")
                    categories = ", ".join(self.entity_data.get("categories", []))
                    yield Input(id="input_categories", placeholder="IT Hardware, Software", value=categories)
                    yield Label("Active BPAs:")
                    yield Input(id="input_bpas", placeholder="0", value=str(self.entity_data.get("active_bpas", 0)))

                elif self.entity_type == "customers":
                    yield Label("ID (read-only):")
                    yield Input(id="input_id", value=str(self.entity_data.get("id", "")), disabled=True)
                    yield Label("Name:")
                    yield Input(id="input_name", placeholder="e.g., US Navy", value=str(self.entity_data.get("name", "")))
                    yield Label("Category (DOD/Civilian):")
                    yield Input(id="input_category", placeholder="DOD", value=str(self.entity_data.get("category", "DOD")))
                    yield Label("Region (East/West/Central):")
                    yield Input(id="input_region", placeholder="East", value=str(self.entity_data.get("region", "East")))
                    yield Label("Tier (Strategic/Standard):")
                    yield Input(id="input_tier", placeholder="Standard", value=str(self.entity_data.get("tier", "Standard")))
                    yield Label("Annual Spend:")
                    yield Input(id="input_spend", placeholder="5000000", value=str(self.entity_data.get("annual_spend", 0)))

                elif self.entity_type == "partners":
                    yield Label("ID (read-only):")
                    yield Input(id="input_id", value=str(self.entity_data.get("id", "")), disabled=True)
                    yield Label("Name:")
                    yield Input(id="input_name", placeholder="e.g., Acme Technology Partners", value=str(self.entity_data.get("name", "")))
                    yield Label("Tier (Platinum/Gold/Silver):")
                    yield Input(id="input_tier", placeholder="Gold", value=str(self.entity_data.get("tier", "Gold")))
                    yield Label("OEM Affiliations (comma-separated IDs):")
                    oems = ", ".join(self.entity_data.get("oem_affiliations", []))
                    yield Input(id="input_oems", placeholder="microsoft,cisco", value=oems)
                    yield Label("Specializations (comma-separated):")
                    specs = ", ".join(self.entity_data.get("specializations", []))
                    yield Input(id="input_specs", placeholder="Cloud, Security", value=specs)
                    yield Label("Regions Served (comma-separated):")
                    regions = ", ".join(self.entity_data.get("regions_served", []))
                    yield Input(id="input_regions", placeholder="East,West", value=regions)

                elif self.entity_type == "distributors":
                    yield Label("ID (read-only):")
                    yield Input(id="input_id", value=str(self.entity_data.get("id", "")), disabled=True)
                    yield Label("Name:")
                    yield Input(id="input_name", placeholder="e.g., Tech Distribution Co", value=str(self.entity_data.get("name", "")))
                    yield Label("Tier (Premier/Standard):")
                    yield Input(id="input_tier", placeholder="Premier", value=str(self.entity_data.get("tier", "Premier")))
                    yield Label("OEM Authorizations (comma-separated IDs):")
                    oems = ", ".join(self.entity_data.get("oem_authorizations", []))
                    yield Input(id="input_oems", placeholder="microsoft,cisco,dell", value=oems)
                    yield Label("Regions Served (comma-separated):")
                    regions = ", ".join(self.entity_data.get("regions_served", []))
                    yield Input(id="input_regions", placeholder="East,West,Central", value=regions)
                    yield Label("Product Categories (comma-separated):")
                    categories = ", ".join(self.entity_data.get("product_categories", []))
                    yield Input(id="input_categories", placeholder="Hardware, Software", value=categories)

                elif self.entity_type == "regions":
                    yield Label("ID (read-only):")
                    yield Input(id="input_id", value=str(self.entity_data.get("id", "")), disabled=True)
                    yield Label("Name:")
                    yield Input(id="input_name", placeholder="e.g., Southeast", value=str(self.entity_data.get("name", "")))
                    yield Label("Bonus (float):")
                    yield Input(id="input_bonus", placeholder="2.0", value=str(self.entity_data.get("bonus", 2.0)))
                    yield Label("Description:")
                    yield Input(
                        id="input_description", placeholder="Southeast region coverage", value=str(self.entity_data.get("description", ""))
                    )

                else:
                    yield Label(f"[yellow]Edit form for {self.entity_type} not yet implemented.[/yellow]")
                    yield Label("Use CLI tool: python3 scripts/manage_entities.py")

            with Horizontal(id="button_bar"):
                yield Button("Save Changes", id="btn_submit", variant="success")
                yield Button("Cancel", id="btn_cancel", variant="error")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn_cancel":
            self.dismiss(None)
        elif event.button.id == "btn_submit":
            await self._submit_form()

    async def _submit_form(self) -> None:
        """Collect form data and update entity."""
        try:
            entity_id = self.entity_data["id"]

            if self.entity_type == "oems":
                name = self.query_one("#input_name", Input).value.strip()
                tier = self.query_one("#input_tier", Input).value.strip()
                programs_str = self.query_one("#input_programs", Input).value.strip()
                contact_email = self.query_one("#input_contact_email", Input).value.strip()

                if not name:
                    self.app.notify("Name is required", severity="error", timeout=3)
                    return

                programs = [p.strip() for p in programs_str.split(",") if p.strip()]

                updated_oem = OEM(
                    id=entity_id,
                    name=name,
                    tier=tier,
                    programs=programs,
                    contact_email=contact_email or None,
                    active=self.entity_data.get("active", True),
                )
                oem_store.update(entity_id, updated_oem)
                self.dismiss({"success": True, "entity": updated_oem})

            elif self.entity_type == "cvs":
                name = self.query_one("#input_name", Input).value.strip()
                priority = self.query_one("#input_priority", Input).value.strip()
                oems_str = self.query_one("#input_oems", Input).value.strip()
                categories_str = self.query_one("#input_categories", Input).value.strip()
                bpas = self.query_one("#input_bpas", Input).value.strip()

                if not name:
                    self.app.notify("Name is required", severity="error", timeout=3)
                    return

                oems = [o.strip() for o in oems_str.split(",") if o.strip()]
                categories = [c.strip() for c in categories_str.split(",") if c.strip()]

                updated_cv = ContractVehicle(
                    id=entity_id,
                    name=name,
                    priority_score=float(priority) if priority else 85.0,
                    oems_supported=oems,
                    categories=categories,
                    active_bpas=int(bpas) if bpas else 0,
                    active=self.entity_data.get("active", True),
                )
                contract_vehicle_store.update(entity_id, updated_cv)
                self.dismiss({"success": True, "entity": updated_cv})

            elif self.entity_type == "customers":
                name = self.query_one("#input_name", Input).value.strip()
                category = self.query_one("#input_category", Input).value.strip()
                region = self.query_one("#input_region", Input).value.strip()
                tier = self.query_one("#input_tier", Input).value.strip()
                spend = self.query_one("#input_spend", Input).value.strip()

                if not name:
                    self.app.notify("Name is required", severity="error", timeout=3)
                    return

                updated_customer = Customer(
                    id=entity_id,
                    name=name,
                    category=category,
                    region=region,
                    tier=tier,
                    annual_spend=float(spend) if spend else 0.0,
                    active=self.entity_data.get("active", True),
                )
                customer_store.update(entity_id, updated_customer)
                self.dismiss({"success": True, "entity": updated_customer})

            elif self.entity_type == "partners":
                name = self.query_one("#input_name", Input).value.strip()
                tier = self.query_one("#input_tier", Input).value.strip()
                oems_str = self.query_one("#input_oems", Input).value.strip()
                specs_str = self.query_one("#input_specs", Input).value.strip()
                regions_str = self.query_one("#input_regions", Input).value.strip()

                if not name:
                    self.app.notify("Name is required", severity="error", timeout=3)
                    return

                oems = [o.strip() for o in oems_str.split(",") if o.strip()]
                specs = [s.strip() for s in specs_str.split(",") if s.strip()]
                regions = [r.strip() for r in regions_str.split(",") if r.strip()]

                updated_partner = Partner(
                    id=entity_id,
                    name=name,
                    tier=tier,
                    oem_affiliations=oems,
                    specializations=specs,
                    regions_served=regions,
                    active=self.entity_data.get("active", True),
                )
                partner_store.update(entity_id, updated_partner)
                self.dismiss({"success": True, "entity": updated_partner})

            elif self.entity_type == "distributors":
                name = self.query_one("#input_name", Input).value.strip()
                tier = self.query_one("#input_tier", Input).value.strip()
                oems_str = self.query_one("#input_oems", Input).value.strip()
                regions_str = self.query_one("#input_regions", Input).value.strip()
                categories_str = self.query_one("#input_categories", Input).value.strip()

                if not name:
                    self.app.notify("Name is required", severity="error", timeout=3)
                    return

                oems = [o.strip() for o in oems_str.split(",") if o.strip()]
                regions = [r.strip() for r in regions_str.split(",") if r.strip()]
                categories = [c.strip() for c in categories_str.split(",") if c.strip()]

                updated_dist = Distributor(
                    id=entity_id,
                    name=name,
                    tier=tier,
                    oem_authorizations=oems,
                    regions_served=regions,
                    product_categories=categories,
                    active=self.entity_data.get("active", True),
                )
                distributor_store.update(entity_id, updated_dist)
                self.dismiss({"success": True, "entity": updated_dist})

            elif self.entity_type == "regions":
                name = self.query_one("#input_name", Input).value.strip()
                bonus = self.query_one("#input_bonus", Input).value.strip()
                description = self.query_one("#input_description", Input).value.strip()

                if not name:
                    self.app.notify("Name is required", severity="error", timeout=3)
                    return

                updated_region = Region(
                    id=entity_id,
                    name=name,
                    bonus=float(bonus) if bonus else 0.0,
                    description=description or "",
                    active=self.entity_data.get("active", True),
                )
                region_store.update(entity_id, updated_region)
                self.dismiss({"success": True, "entity": updated_region})

            else:
                self.app.notify(f"Edit {self.entity_type} not yet implemented", severity="warning", timeout=3)
                self.dismiss(None)

        except ValueError as e:
            self.app.notify(f"Validation error: {e}", severity="error", timeout=5)
        except Exception as e:
            self.app.notify(f"Error updating entity: {e}", severity="error", timeout=5)


class AddEntityModal(ModalScreen):
    """Modal screen for adding a new entity."""

    def __init__(self, entity_type: str) -> None:
        super().__init__()
        self.entity_type = entity_type

    def compose(self) -> ComposeResult:
        """Compose the add entity modal."""
        with Container(id="add_entity_dialog"):
            yield Label(f"[b]Add New {self.entity_type.upper()}[/b]", id="modal_title")

            with VerticalScroll(id="form_container"):
                if self.entity_type == "oems":
                    yield Label("ID (lowercase, hyphenated):")
                    yield Input(id="input_id", placeholder="e.g., juniper")
                    yield Label("Name:")
                    yield Input(id="input_name", placeholder="e.g., Juniper Networks")
                    yield Label("Tier (Strategic/Gold/Silver):")
                    yield Input(id="input_tier", placeholder="Strategic", value="Gold")
                    yield Label("Programs (comma-separated):")
                    yield Input(id="input_programs", placeholder="e.g., Routing, Switching")
                    yield Label("Contact Email (optional):")
                    yield Input(id="input_contact_email", placeholder="partners@example.com")

                elif self.entity_type == "cvs":
                    yield Label("ID (lowercase, hyphenated):")
                    yield Input(id="input_id", placeholder="e.g., stars-iii")
                    yield Label("Name:")
                    yield Input(id="input_name", placeholder="e.g., STARS III")
                    yield Label("Priority Score (0-100):")
                    yield Input(id="input_priority", placeholder="85", value="85")
                    yield Label("OEMs Supported (comma-separated IDs):")
                    yield Input(id="input_oems", placeholder="microsoft,cisco,dell")
                    yield Label("Categories (comma-separated):")
                    yield Input(id="input_categories", placeholder="IT Hardware, Software")
                    yield Label("Active BPAs:")
                    yield Input(id="input_bpas", placeholder="0", value="0")

                elif self.entity_type == "customers":
                    yield Label("ID (lowercase, hyphenated):")
                    yield Input(id="input_id", placeholder="e.g., dod-navy")
                    yield Label("Name:")
                    yield Input(id="input_name", placeholder="e.g., US Navy")
                    yield Label("Category (DOD/Civilian):")
                    yield Input(id="input_category", placeholder="DOD", value="DOD")
                    yield Label("Region (East/West/Central):")
                    yield Input(id="input_region", placeholder="East", value="East")
                    yield Label("Tier (Strategic/Standard):")
                    yield Input(id="input_tier", placeholder="Standard", value="Standard")
                    yield Label("Annual Spend:")
                    yield Input(id="input_spend", placeholder="5000000", value="0")

                elif self.entity_type == "partners":
                    yield Label("ID (lowercase, hyphenated):")
                    yield Input(id="input_id", placeholder="e.g., acme-tech")
                    yield Label("Name:")
                    yield Input(id="input_name", placeholder="e.g., Acme Technology Partners")
                    yield Label("Tier (Platinum/Gold/Silver):")
                    yield Input(id="input_tier", placeholder="Gold", value="Gold")
                    yield Label("OEM Affiliations (comma-separated IDs):")
                    yield Input(id="input_oems", placeholder="microsoft,cisco")
                    yield Label("Specializations (comma-separated):")
                    yield Input(id="input_specs", placeholder="Cloud, Security")
                    yield Label("Regions Served (comma-separated):")
                    yield Input(id="input_regions", placeholder="East,West")

                elif self.entity_type == "distributors":
                    yield Label("ID (lowercase, hyphenated):")
                    yield Input(id="input_id", placeholder="e.g., tech-dist")
                    yield Label("Name:")
                    yield Input(id="input_name", placeholder="e.g., Tech Distribution Co")
                    yield Label("Tier (Premier/Standard):")
                    yield Input(id="input_tier", placeholder="Premier", value="Premier")
                    yield Label("OEM Authorizations (comma-separated IDs):")
                    yield Input(id="input_oems", placeholder="microsoft,cisco,dell")
                    yield Label("Regions Served (comma-separated):")
                    yield Input(id="input_regions", placeholder="East,West,Central")
                    yield Label("Product Categories (comma-separated):")
                    yield Input(id="input_categories", placeholder="Hardware, Software")

                elif self.entity_type == "regions":
                    yield Label("ID (lowercase):")
                    yield Input(id="input_id", placeholder="e.g., southeast")
                    yield Label("Name:")
                    yield Input(id="input_name", placeholder="e.g., Southeast")
                    yield Label("Bonus (float):")
                    yield Input(id="input_bonus", placeholder="2.0", value="2.0")
                    yield Label("Description:")
                    yield Input(id="input_description", placeholder="Southeast region coverage")

                else:
                    yield Label(f"[yellow]Form for {self.entity_type} not yet implemented.[/yellow]")
                    yield Label("Use CLI tool: python3 scripts/manage_entities.py")

            with Horizontal(id="button_bar"):
                yield Button("Submit", id="btn_submit", variant="success")
                yield Button("Cancel", id="btn_cancel", variant="error")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn_cancel":
            self.dismiss(None)
        elif event.button.id == "btn_submit":
            await self._submit_form()

    async def _submit_form(self) -> None:
        """Collect form data and create entity."""
        try:
            if self.entity_type == "oems":
                entity_id = self.query_one("#input_id", Input).value.strip()
                name = self.query_one("#input_name", Input).value.strip()
                tier = self.query_one("#input_tier", Input).value.strip()
                programs_str = self.query_one("#input_programs", Input).value.strip()
                contact_email = self.query_one("#input_contact_email", Input).value.strip()

                if not entity_id or not name:
                    self.app.notify("ID and Name are required", severity="error", timeout=3)
                    return

                programs = [p.strip() for p in programs_str.split(",") if p.strip()]

                new_oem = OEM(
                    id=entity_id,
                    name=name,
                    tier=tier,
                    programs=programs,
                    contact_email=contact_email or None,
                )
                oem_store.add(new_oem)
                self.dismiss({"success": True, "entity": new_oem})

            elif self.entity_type == "cvs":
                entity_id = self.query_one("#input_id", Input).value.strip()
                name = self.query_one("#input_name", Input).value.strip()
                priority = self.query_one("#input_priority", Input).value.strip()
                oems_str = self.query_one("#input_oems", Input).value.strip()
                categories_str = self.query_one("#input_categories", Input).value.strip()
                bpas = self.query_one("#input_bpas", Input).value.strip()

                if not entity_id or not name:
                    self.app.notify("ID and Name are required", severity="error", timeout=3)
                    return

                oems = [o.strip() for o in oems_str.split(",") if o.strip()]
                categories = [c.strip() for c in categories_str.split(",") if c.strip()]

                new_cv = ContractVehicle(
                    id=entity_id,
                    name=name,
                    priority_score=float(priority) if priority else 85.0,
                    oems_supported=oems,
                    categories=categories,
                    active_bpas=int(bpas) if bpas else 0,
                )
                contract_vehicle_store.add(new_cv)
                self.dismiss({"success": True, "entity": new_cv})

            elif self.entity_type == "customers":
                entity_id = self.query_one("#input_id", Input).value.strip()
                name = self.query_one("#input_name", Input).value.strip()
                category = self.query_one("#input_category", Input).value.strip()
                region = self.query_one("#input_region", Input).value.strip()
                tier = self.query_one("#input_tier", Input).value.strip()
                spend = self.query_one("#input_spend", Input).value.strip()

                if not entity_id or not name:
                    self.app.notify("ID and Name are required", severity="error", timeout=3)
                    return

                new_customer = Customer(
                    id=entity_id,
                    name=name,
                    category=category,
                    region=region,
                    tier=tier,
                    annual_spend=float(spend) if spend else 0.0,
                )
                customer_store.add(new_customer)
                self.dismiss({"success": True, "entity": new_customer})

            elif self.entity_type == "partners":
                entity_id = self.query_one("#input_id", Input).value.strip()
                name = self.query_one("#input_name", Input).value.strip()
                tier = self.query_one("#input_tier", Input).value.strip()
                oems_str = self.query_one("#input_oems", Input).value.strip()
                specs_str = self.query_one("#input_specs", Input).value.strip()
                regions_str = self.query_one("#input_regions", Input).value.strip()

                if not entity_id or not name:
                    self.app.notify("ID and Name are required", severity="error", timeout=3)
                    return

                oems = [o.strip() for o in oems_str.split(",") if o.strip()]
                specs = [s.strip() for s in specs_str.split(",") if s.strip()]
                regions = [r.strip() for r in regions_str.split(",") if r.strip()]

                new_partner = Partner(
                    id=entity_id,
                    name=name,
                    tier=tier,
                    oem_affiliations=oems,
                    specializations=specs,
                    regions_served=regions,
                )
                partner_store.add(new_partner)
                self.dismiss({"success": True, "entity": new_partner})

            elif self.entity_type == "distributors":
                entity_id = self.query_one("#input_id", Input).value.strip()
                name = self.query_one("#input_name", Input).value.strip()
                tier = self.query_one("#input_tier", Input).value.strip()
                oems_str = self.query_one("#input_oems", Input).value.strip()
                regions_str = self.query_one("#input_regions", Input).value.strip()
                categories_str = self.query_one("#input_categories", Input).value.strip()

                if not entity_id or not name:
                    self.app.notify("ID and Name are required", severity="error", timeout=3)
                    return

                oems = [o.strip() for o in oems_str.split(",") if o.strip()]
                regions = [r.strip() for r in regions_str.split(",") if r.strip()]
                categories = [c.strip() for c in categories_str.split(",") if c.strip()]

                new_dist = Distributor(
                    id=entity_id,
                    name=name,
                    tier=tier,
                    oem_authorizations=oems,
                    regions_served=regions,
                    product_categories=categories,
                )
                distributor_store.add(new_dist)
                self.dismiss({"success": True, "entity": new_dist})

            elif self.entity_type == "regions":
                entity_id = self.query_one("#input_id", Input).value.strip()
                name = self.query_one("#input_name", Input).value.strip()
                bonus = self.query_one("#input_bonus", Input).value.strip()
                description = self.query_one("#input_description", Input).value.strip()

                if not entity_id or not name:
                    self.app.notify("ID and Name are required", severity="error", timeout=3)
                    return

                new_region = Region(
                    id=entity_id,
                    name=name,
                    bonus=float(bonus) if bonus else 0.0,
                    description=description or "",
                )
                region_store.add(new_region)
                self.dismiss({"success": True, "entity": new_region})

            else:
                self.app.notify(f"Add {self.entity_type} not yet implemented", severity="warning", timeout=3)
                self.dismiss(None)

        except ValueError as e:
            self.app.notify(f"Validation error: {e}", severity="error", timeout=5)
        except Exception as e:
            self.app.notify(f"Error adding entity: {e}", severity="error", timeout=5)


class EntityManagementScreen(Screen):
    """Entity Management Screen with CRUD operations."""

    INHERIT_BINDINGS = False  # Don't inherit parent app bindings

    BINDINGS = [
        ("escape", "app.pop_screen", "Back"),
        ("q", "app.pop_screen", "Back"),
        ("a", "add_entity", "Add"),
        ("e", "edit_entity", "Edit"),
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
                yield Button("Edit [e]", id="btn_edit", variant="primary")
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
        """Add a new entity using modal form."""
        result = await self.app.push_screen_wait(AddEntityModal(self.current_entity_type))
        if result and result.get("success"):
            entity = result.get("entity")
            self._update_status(f"✓ Added {entity.name}", "green")
            await self._load_entities()
        elif result is None:
            self._update_status("Cancelled", "dim")

    async def action_edit_entity(self) -> None:
        """Edit selected entity using modal form."""
        try:
            row = self.table.cursor_row
            if row is None:
                self._update_status("⚠ Select an entity first", "yellow")
                return

            entity_id = self.table.get_row(row)[0]

            # Get the appropriate store and entity data
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

            entity = store.get(entity_id)
            if not entity:
                self._update_status(f"Entity '{entity_id}' not found", "red")
                return

            # Convert entity to dict for the modal
            entity_data = entity.model_dump()

            # Open edit modal
            result = await self.app.push_screen_wait(EditEntityModal(self.current_entity_type, entity_data))

            if result and result.get("success"):
                updated_entity = result.get("entity")
                self._update_status(f"✓ Updated {updated_entity.name}", "green")
                await self._load_entities()
            elif result is None:
                self._update_status("Edit cancelled", "dim")

        except Exception as e:
            self._update_status(f"❌ Edit failed: {e}", "red")

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
        elif event.button.id == "btn_edit":
            await self.action_edit_entity()
        elif event.button.id == "btn_delete":
            await self.action_delete_entity()
        elif event.button.id == "btn_refresh":
            await self.action_refresh()
