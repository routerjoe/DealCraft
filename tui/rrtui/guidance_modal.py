from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Static, DataTable, Button, Checkbox
from textual.containers import Container, Horizontal, Vertical
from textual import events
from textual.binding import Binding

from . import rfq_api
from .operation_modal import OperationModal


class GuidanceModal(ModalScreen):
    """Edit RFQ analysis guidance: OEM authorization and Supported Contracts.

    Keyboard:
      r  Refresh both tables
      t  Toggle OEM Authorized (on selected row)
      s  Toggle Contract Supported (on selected row)
      Esc Close
    """

    # Explicit key bindings to ensure modal captures hotkeys regardless of focus.
    BINDINGS = [
        Binding("t", "toggle_oem", "Toggle OEM Authorized", show=False, priority=True),
        Binding("s", "toggle_contract", "Toggle Contract Supported", show=False, priority=True),
        Binding("r", "refresh_all", "Refresh", show=False, priority=True),
        Binding("escape", "close_modal", "Close", show=False, priority=True),
    ]

    CSS = """
    GuidanceModal {
        align: center middle;
    }
    GuidanceModal > Container {
        width: 100;
        height: 32;
        border: thick $accent;
        background: $surface;
    }
    #guide_header {
        dock: top;
        height: 3;
        content-align: center middle;
        background: $accent;
    }
    #guide_footer {
        dock: bottom;
        height: 3;
        content-align: center middle;
        background: $surface;
    }
    #left, #right {
        height: 1fr;
        padding: 1 1;
    }
    #oem_card, #contracts_card {
        height: 1fr;
        border: solid $accent;
        margin: 0 1;
    }
    .card_header {
        height: 1;
        content-align: left middle;
        padding: 0 1;
    }
    .card_body {
        height: 1fr;
        padding: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Container():
            yield Static("[b][cyan]Edit Analysis Guidance[/cyan] — OEM Authorization & Supported Contracts[/b]", id="guide_header")
            with Horizontal():
                with Vertical(id="left"):
                    with Vertical(id="oem_card"):
                        yield Static("[b]OEM Authorization[/b]", classes="card_header")
                        self.oem_table = DataTable(id="oem_table", zebra_stripes=True)
                        self.oem_table.add_columns("OEM", "Authorized", "Threshold")
                        yield self.oem_table
                with Vertical(id="right"):
                    with Vertical(id="contracts_card"):
                        yield Static("[b]Supported Contract Vehicles[/b]", classes="card_header")
                        self.contract_table = DataTable(id="contract_table", zebra_stripes=True)
                        self.contract_table.add_columns("Contract", "Supported", "Notes")
                        yield self.contract_table
            yield Static(
                "[dim]Keys:[/dim] r=Refresh  t=Toggle OEM Authorized  s=Toggle Contract Supported   Esc=Close",
                id="guide_footer"
            )

    async def on_mount(self) -> None:
        await self._refresh_all()
        # Give initial focus to the OEM table so hotkeys act on a visible selection
        try:
            self.set_focus(self.oem_table)
        except Exception:
            pass

    async def _refresh_all(self) -> None:
        try:
            self._load_oems()
        except Exception as e:
            self._toast(f"[red]OEM load failed: {e}[/red]")
        try:
            self._load_contracts()
        except Exception as e:
            self._toast(f"[red]Contracts load failed: {e}[/red]")

    def _load_oems(self) -> None:
        data = rfq_api.config_list_oems() or {}
        items = (data.get("items") if isinstance(data, dict) else []) or []
        self.oem_table.clear()
        for row in items:
            oem = str(row.get("oem_name", ""))
            auth = "Yes" if bool(row.get("authorized", False)) else "No"
            thr = row.get("business_case_threshold", None)
            thr_str = "" if thr in (None, "", "null") else str(thr)
            self.oem_table.add_row(oem, auth, thr_str)
        # Ensure a valid selection exists so 't' works immediately
        try:
            if items:
                self.oem_table.move_cursor(row=0, column=0)
        except Exception:
            pass

    def _load_contracts(self) -> None:
        data = rfq_api.config_list_contracts() or {}
        items = (data.get("items") if isinstance(data, dict) else []) or []
        self.contract_table.clear()
        for row in items:
            name = str(row.get("vehicle_name", ""))
            sup = "Yes" if bool(row.get("supported", False)) else "No"
            notes = str(row.get("notes", "") or "")
            self.contract_table.add_row(name, sup, notes)
        # Ensure a valid selection exists so 's' works immediately
        try:
            if items:
                self.contract_table.move_cursor(row=0, column=0)
        except Exception:
            pass

    # Hotkey actions wired via BINDINGS
    async def action_toggle_oem(self) -> None:
        await self._toggle_oem_authorized()

    async def action_toggle_contract(self) -> None:
        await self._toggle_contract_supported()

    async def action_refresh_all(self) -> None:
        await self._refresh_all()
        self._toast("[green]Refreshed[/green]")

    def action_close_modal(self) -> None:
        self.dismiss(True)

    def _toast(self, msg: str) -> None:
        try:
            self.query_one("#guide_footer", Static).update(msg)
        except Exception:
            pass

    # Ensure keys always fire even if a child widget captures them
    def on_key(self, event: events.Key) -> None:
        try:
            key = (event.key or "").lower()
        except Exception:
            key = ""
        import asyncio
        if key == "t":
            asyncio.create_task(self.action_toggle_oem())
            try:
                event.stop()
            except Exception:
                pass
        elif key == "s":
            asyncio.create_task(self.action_toggle_contract())
            try:
                event.stop()
            except Exception:
                pass
        elif key == "r":
            asyncio.create_task(self.action_refresh_all())
            try:
                event.stop()
            except Exception:
                pass
        elif key in ("escape", "esc"):
            self.action_close_modal()
            try:
                event.stop()
            except Exception:
                pass

    async def _toggle_oem_authorized(self) -> None:
        try:
            row_key = getattr(self.oem_table, "cursor_row", None)
            if row_key is None:
                self._toast("[yellow]Select an OEM row to toggle[/yellow]")
                return
            try:
                row = self.oem_table.get_row(row_key)
            except Exception:
                self._toast("[yellow]Select a data row in OEM table (use ↑/↓), then press 't'[/yellow]")
                return
            oem_name = str(row[0]).strip()
            if not oem_name:
                self._toast("[yellow]No OEM selected[/yellow]")
                return
            current = str(row[1]).strip().lower() == "yes"
            res = rfq_api.config_set_oem_authorized(oem_name, not current)
            if not res:
                self._toast("[red]Failed to update OEM authorization[/red]")
                return
            self._load_oems()
            self._toast(f"[green]Updated OEM: {oem_name} → {'Authorized' if not current else 'Not Authorized'}[/green]")
        except Exception as e:
            self._toast(f"[red]Toggle failed: {e}[/red]")

    async def _toggle_contract_supported(self) -> None:
        try:
            row_key = getattr(self.contract_table, "cursor_row", None)
            if row_key is None:
                self._toast("[yellow]Select a Contract row to toggle[/yellow]")
                return
            try:
                row = self.contract_table.get_row(row_key)
            except Exception:
                self._toast("[yellow]Select a data row in Contracts table (use ↑/↓), then press 's'[/yellow]")
                return
            name = str(row[0]).strip()
            if not name:
                self._toast("[yellow]No Contract selected[/yellow]")
                return
            current = str(row[1]).strip().lower() == "yes"
            res = rfq_api.config_upsert_contract(name, not current, None)
            if not res:
                self._toast("[red]Failed to update contract[/red]")
                return
            self._load_contracts()
            self._toast(f"[green]Updated Contract: {name} → {'Supported' if not current else 'Not Supported'}[/green]")
        except Exception as e:
            self._toast(f"[red]Toggle failed: {e}[/red]")


class CleanupModal(ModalScreen):
    """Confirm cleanup of an RFQ with optional Outlook email deletion (performed first)."""

    CSS = """
    CleanupModal {
        align: center middle;
    }
    CleanupModal > Container {
        width: 80;
        height: 16;
        border: thick $accent;
        background: $surface;
    }
    #cl_header {
        dock: top;
        height: 3;
        content-align: center middle;
        background: $accent;
    }
    #cl_body {
        height: 1fr;
        padding: 1 2;
    }
    #cl_footer {
        dock: bottom;
        height: 3;
        content-align: center middle;
    }
    Button {
        margin: 0 1;
    }
    """

    def __init__(self, rfq_id: int):
        super().__init__()
        self.rfq_id = int(rfq_id)

    def compose(self) -> ComposeResult:
        with Container():
            yield Static(f"[b][cyan]Cleanup RFQ #{self.rfq_id}[/cyan][/b]", id="cl_header")
            with Vertical(id="cl_body"):
                yield Static("This will remove the RFQ record and local artifacts.\n"
                             "[yellow]Only NO-GO RFQs will be cleaned (enforced by backend).[/yellow]\n\n"
                             "Optional: Also delete the Outlook email first.", id="cl_msg")
                self.cb_delete = Checkbox("Also delete Outlook email (performed first)", value=False, id="cl_cb")
            with Horizontal(id="cl_footer"):
                yield Button("Cancel", id="cancel_btn")
                yield Button("Proceed", id="proceed_btn", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel_btn":
            self.dismiss(False)
            return
        if event.button.id == "proceed_btn":
            delete_outlook = bool(self.cb_delete.value if hasattr(self, "cb_delete") else False)
            # Chain to OperationModal which streams the CLI
            op = OperationModal(
                f"Cleanup RFQ #{self.rfq_id}",
                lambda: rfq_api.cleanup_rfq_with_output(self.rfq_id, delete_outlook)
            )
            self.app.push_screen(op)
            self.dismiss(True)