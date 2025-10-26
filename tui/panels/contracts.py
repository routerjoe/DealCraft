"""Contract Vehicles panel for TUI."""

from typing import Optional

import httpx
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Input, Label, Static, TextArea


class ContractAddModal(ModalScreen):
    """Modal for adding a new contract."""

    def compose(self) -> ComposeResult:
        """Compose the modal layout."""
        with Container(id="add-contract-modal"):
            yield Label("Add New Contract Vehicle", id="modal-title")
            yield Input(placeholder="Contract Name", id="contract-name")
            yield TextArea(id="contract-notes")
            with Vertical():
                yield Button("Add", variant="primary", id="add-confirm")
                yield Button("Cancel", variant="default", id="add-cancel")

    @on(Button.Pressed, "#add-confirm")
    async def confirm_add(self) -> None:
        """Handle confirm button."""
        name_input = self.query_one("#contract-name", Input)
        notes_area = self.query_one("#contract-notes", TextArea)

        name = name_input.value.strip()
        notes = notes_area.text.strip()

        if not name:
            self.app.notify("Contract name is required", severity="error")
            return

        self.dismiss({"name": name, "notes": notes})

    @on(Button.Pressed, "#add-cancel")
    def cancel_add(self) -> None:
        """Handle cancel button."""
        self.dismiss(None)


class ContractEditModal(ModalScreen):
    """Modal for editing contract notes."""

    def __init__(self, contract_name: str, current_notes: str) -> None:
        """Initialize edit modal."""
        super().__init__()
        self.contract_name = contract_name
        self.current_notes = current_notes

    def compose(self) -> ComposeResult:
        """Compose the modal layout."""
        with Container(id="edit-contract-modal"):
            yield Label(f"Edit Notes for {self.contract_name}", id="modal-title")
            notes_area = TextArea(id="contract-notes")
            notes_area.text = self.current_notes
            yield notes_area
            with Vertical():
                yield Button("Save", variant="primary", id="edit-confirm")
                yield Button("Cancel", variant="default", id="edit-cancel")

    @on(Button.Pressed, "#edit-confirm")
    async def confirm_edit(self) -> None:
        """Handle confirm button."""
        notes_area = self.query_one("#contract-notes", TextArea)
        self.dismiss(notes_area.text.strip())

    @on(Button.Pressed, "#edit-cancel")
    def cancel_edit(self) -> None:
        """Handle cancel button."""
        self.dismiss(None)


class ContractsPanel(Static):
    """Contract Vehicles panel with table and key bindings."""

    def __init__(self, api_base: str) -> None:
        """Initialize Contracts panel."""
        super().__init__()
        self.api_base = api_base
        self.selected_row: Optional[int] = None

    def compose(self) -> ComposeResult:
        """Compose the panel layout."""
        yield Label("Contract Vehicles", classes="panel-title")
        yield Label("C:Add | S:Toggle | E:Edit Notes | X:Delete | R:Refresh", classes="help-text")

        table = DataTable(id="contract-table")
        table.add_columns("Contract", "Supported", "Notes")
        table.cursor_type = "row"
        yield table

    async def on_mount(self) -> None:
        """Load data when panel mounts."""
        await self.refresh_data()

    async def refresh_data(self) -> None:
        """Refresh contract data from API."""
        table = self.query_one("#contract-table", DataTable)
        table.clear()

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_base}/v1/contracts")
                response.raise_for_status()
                contracts = response.json()

                for contract in contracts:
                    support_symbol = "✓" if contract["supported"] else "✗"
                    notes_preview = contract["notes"][:30] + "..." if len(contract["notes"]) > 30 else contract["notes"]
                    table.add_row(contract["name"], support_symbol, notes_preview)

                self.app.notify(f"Loaded {len(contracts)} contracts", severity="information")
        except Exception as e:
            self.app.notify(f"Failed to load contracts: {str(e)}", severity="error")

    async def add_contract(self) -> None:
        """Show modal to add new contract."""
        result = await self.app.push_screen_wait(ContractAddModal())

        if result:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.api_base}/v1/contracts",
                        json={"name": result["name"], "supported": False, "notes": result["notes"]},
                    )
                    response.raise_for_status()
                    self.app.notify(f"Added contract: {result['name']}", severity="success")
                    await self.refresh_data()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 409:
                    self.app.notify(f"Contract '{result['name']}' already exists", severity="error")
                else:
                    self.app.notify(f"Failed to add contract: {str(e)}", severity="error")
            except Exception as e:
                self.app.notify(f"Error: {str(e)}", severity="error")

    async def toggle_supported(self) -> None:
        """Toggle supported status of selected contract."""
        table = self.query_one("#contract-table", DataTable)

        if table.cursor_row >= 0:
            row_key = table.get_row_at(table.cursor_row)
            contract_name = row_key[0]
            current_support = row_key[1] == "✓"

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.patch(
                        f"{self.api_base}/v1/contracts/{contract_name}",
                        json={"supported": not current_support},
                    )
                    response.raise_for_status()
                    self.app.notify(f"Toggled {contract_name}", severity="success")
                    await self.refresh_data()
            except Exception as e:
                self.app.notify(f"Failed to toggle: {str(e)}", severity="error")

    async def edit_notes(self) -> None:
        """Edit notes for selected contract."""
        table = self.query_one("#contract-table", DataTable)

        if table.cursor_row >= 0:
            row_key = table.get_row_at(table.cursor_row)
            contract_name = row_key[0]

            # Fetch current notes from API
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{self.api_base}/v1/contracts")
                    response.raise_for_status()
                    contracts = response.json()

                    current_notes = ""
                    for c in contracts:
                        if c["name"] == contract_name:
                            current_notes = c["notes"]
                            break

                    # Show edit modal
                    new_notes = await self.app.push_screen_wait(ContractEditModal(contract_name, current_notes))

                    if new_notes is not None:
                        # Update notes
                        response = await client.patch(
                            f"{self.api_base}/v1/contracts/{contract_name}",
                            json={"notes": new_notes},
                        )
                        response.raise_for_status()
                        self.app.notify(f"Updated notes for {contract_name}", severity="success")
                        await self.refresh_data()
            except Exception as e:
                self.app.notify(f"Failed to edit notes: {str(e)}", severity="error")

    async def delete_contract(self) -> None:
        """Delete selected contract."""
        table = self.query_one("#contract-table", DataTable)

        if table.cursor_row >= 0:
            row_key = table.get_row_at(table.cursor_row)
            contract_name = row_key[0]

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.delete(f"{self.api_base}/v1/contracts/{contract_name}")
                    response.raise_for_status()
                    self.app.notify(f"Deleted contract: {contract_name}", severity="success")
                    await self.refresh_data()
            except Exception as e:
                self.app.notify(f"Failed to delete: {str(e)}", severity="error")

    async def on_key(self, event) -> None:
        """Handle key presses."""
        if event.key == "c":
            await self.add_contract()
        elif event.key == "s":
            await self.toggle_supported()
        elif event.key == "e":
            await self.edit_notes()
        elif event.key == "x":
            await self.delete_contract()
        elif event.key == "r":
            await self.refresh_data()
