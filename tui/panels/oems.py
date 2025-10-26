"""OEM Authorization panel for TUI."""

import time
from typing import Optional

import httpx
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Input, Label, Static


class OEMAddModal(ModalScreen):
    """Modal for adding a new OEM."""

    def compose(self) -> ComposeResult:
        """Compose the modal layout."""
        with Container(id="add-oem-modal"):
            yield Label("Add New OEM", id="modal-title")
            yield Input(placeholder="OEM Name", id="oem-name")
            yield Input(placeholder="Threshold (number)", id="oem-threshold")
            with Vertical():
                yield Button("Add", variant="primary", id="add-confirm")
                yield Button("Cancel", variant="default", id="add-cancel")

    @on(Button.Pressed, "#add-confirm")
    async def confirm_add(self) -> None:
        """Handle confirm button."""
        name_input = self.query_one("#oem-name", Input)
        threshold_input = self.query_one("#oem-threshold", Input)

        name = name_input.value.strip()
        threshold_str = threshold_input.value.strip()

        if not name:
            self.app.notify("OEM name is required", severity="error")
            return

        try:
            threshold = int(threshold_str) if threshold_str else 0
        except ValueError:
            self.app.notify("Threshold must be a number", severity="error")
            return

        self.dismiss({"name": name, "threshold": threshold})

    @on(Button.Pressed, "#add-cancel")
    def cancel_add(self) -> None:
        """Handle cancel button."""
        self.dismiss(None)


class OEMPanel(Static):
    """OEM Authorization panel with table and key bindings."""

    def __init__(self, api_base: str) -> None:
        """Initialize OEM panel."""
        super().__init__()
        self.api_base = api_base
        self.selected_row: Optional[int] = None

    def compose(self) -> ComposeResult:
        """Compose the panel layout."""
        yield Label("OEM Authorization", classes="panel-title")
        yield Label("A:Add | T:Toggle | ↑↓:Threshold | D:Delete | R:Refresh", classes="help-text")

        table = DataTable(id="oem-table")
        table.add_columns("OEM", "Authorized", "Threshold")
        table.cursor_type = "row"
        yield table

    async def on_mount(self) -> None:
        """Load data when panel mounts."""
        await self.refresh_data()

    async def refresh_data(self) -> None:
        """Refresh OEM data from API."""
        table = self.query_one("#oem-table", DataTable)
        table.clear()

        try:
            start_time = time.time()
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_base}/v1/oems")
                response.raise_for_status()
                latency_ms = (time.time() - start_time) * 1000
                request_id = response.headers.get("X-Request-ID", "N/A")

                oems = response.json()

                for oem in oems:
                    auth_symbol = "✓" if oem["authorized"] else "✗"
                    table.add_row(oem["name"], auth_symbol, str(oem["threshold"]))

                self.app.update_request_info(request_id, latency_ms)
                self.app.notify(f"Loaded {len(oems)} OEMs", severity="information")
        except Exception as e:
            self.app.notify(f"Failed to load OEMs: {str(e)}", severity="error")

    async def add_oem(self) -> None:
        """Show modal to add new OEM."""
        result = await self.app.push_screen_wait(OEMAddModal())

        if result:
            try:
                start_time = time.time()
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.api_base}/v1/oems",
                        json={
                            "name": result["name"],
                            "authorized": False,
                            "threshold": result["threshold"],
                        },
                    )
                    response.raise_for_status()
                    latency_ms = (time.time() - start_time) * 1000
                    request_id = response.headers.get("X-Request-ID", "N/A")
                    self.app.update_request_info(request_id, latency_ms)
                    self.app.notify(f"Added OEM: {result['name']}", severity="success")
                    await self.refresh_data()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 409:
                    self.app.notify(f"OEM '{result['name']}' already exists", severity="error")
                else:
                    self.app.notify(f"Failed to add OEM: {str(e)}", severity="error")
            except Exception as e:
                self.app.notify(f"Error: {str(e)}", severity="error")

    async def toggle_authorized(self) -> None:
        """Toggle authorized status of selected OEM."""
        table = self.query_one("#oem-table", DataTable)

        if table.cursor_row >= 0:
            row_key = table.get_row_at(table.cursor_row)
            oem_name = row_key[0]
            current_auth = row_key[1] == "✓"

            try:
                start_time = time.time()
                async with httpx.AsyncClient() as client:
                    response = await client.patch(f"{self.api_base}/v1/oems/{oem_name}", json={"authorized": not current_auth})
                    response.raise_for_status()
                    latency_ms = (time.time() - start_time) * 1000
                    request_id = response.headers.get("X-Request-ID", "N/A")
                    self.app.update_request_info(request_id, latency_ms)
                    self.app.notify(f"Toggled {oem_name}", severity="success")
                    await self.refresh_data()
            except Exception as e:
                self.app.notify(f"Failed to toggle: {str(e)}", severity="error")

    async def adjust_threshold(self, delta: int) -> None:
        """Adjust threshold of selected OEM."""
        table = self.query_one("#oem-table", DataTable)

        if table.cursor_row >= 0:
            row_key = table.get_row_at(table.cursor_row)
            oem_name = row_key[0]
            current_threshold = int(row_key[2])
            new_threshold = max(0, current_threshold + delta)

            try:
                start_time = time.time()
                async with httpx.AsyncClient() as client:
                    response = await client.patch(f"{self.api_base}/v1/oems/{oem_name}", json={"threshold": new_threshold})
                    response.raise_for_status()
                    latency_ms = (time.time() - start_time) * 1000
                    request_id = response.headers.get("X-Request-ID", "N/A")
                    self.app.update_request_info(request_id, latency_ms)
                    self.app.notify(f"Updated threshold for {oem_name}", severity="success")
                    await self.refresh_data()
            except Exception as e:
                self.app.notify(f"Failed to update threshold: {str(e)}", severity="error")

    async def delete_oem(self) -> None:
        """Delete selected OEM."""
        table = self.query_one("#oem-table", DataTable)

        if table.cursor_row >= 0:
            row_key = table.get_row_at(table.cursor_row)
            oem_name = row_key[0]

            try:
                start_time = time.time()
                async with httpx.AsyncClient() as client:
                    response = await client.delete(f"{self.api_base}/v1/oems/{oem_name}")
                    response.raise_for_status()
                    latency_ms = (time.time() - start_time) * 1000
                    request_id = response.headers.get("X-Request-ID", "N/A")
                    self.app.update_request_info(request_id, latency_ms)
                    self.app.notify(f"Deleted OEM: {oem_name}", severity="success")
                    await self.refresh_data()
            except Exception as e:
                self.app.notify(f"Failed to delete: {str(e)}", severity="error")

    async def on_key(self, event) -> None:
        """Handle key presses."""
        if event.key == "a":
            await self.add_oem()
        elif event.key == "t":
            await self.toggle_authorized()
        elif event.key == "up":
            await self.adjust_threshold(100)
        elif event.key == "down":
            await self.adjust_threshold(-100)
        elif event.key == "d":
            await self.delete_oem()
        elif event.key == "r":
            await self.refresh_data()
