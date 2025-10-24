from textual.app import ComposeResult
from textual.screen import Screen, ModalScreen
from textual.widgets import Static, DataTable, Button, Input, Checkbox, Label
from textual.containers import Container, Horizontal, Vertical
from textual import events
from textual.binding import Binding

from . import rfq_api


class GuidanceScreen(Screen):
    """Full-screen editor for Analysis Guidance: OEM authorization and Supported Contracts."""

    BINDINGS = [
        Binding("escape", "close", "Back", show=True, priority=True),
        Binding("q", "close", "Quit", show=True, priority=True),
        Binding("r", "refresh", "Refresh", show=True, priority=True),
        Binding("a", "add_oem", "Add OEM", show=True, priority=True),
        Binding("c", "add_contract", "Add Contract", show=True, priority=True),
        Binding("t", "toggle_oem", "Toggle OEM", show=True, priority=True),
        Binding("s", "toggle_contract", "Toggle Contract", show=True, priority=True),
    ]

    CSS = """
    GuidanceScreen {
        background: $surface;
    }
    #guide_header {
        dock: top;
        height: 3;
        content-align: center middle;
        background: $primary;
        color: $text;
    }
    #guide_instructions {
        dock: top;
        height: 4;
        padding: 1 2;
        background: $panel;
        border: solid $primary;
    }
    #guide_footer {
        dock: bottom;
        height: 2;
        content-align: center middle;
        background: $panel;
        color: $text;
    }
    #left, #right {
        width: 1fr;
        height: 1fr;
        padding: 1;
    }
    #oem_card, #contracts_card {
        height: 1fr;
        border: solid $primary;
        background: $surface;
    }
    .card_header {
        height: 3;
        content-align: center middle;
        background: $primary;
        color: $text;
    }
    .card_body {
        height: 1fr;
        padding: 1;
    }
    DataTable {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        with Container():
            yield Static("⚙️  Analysis Guidance Configuration", id="guide_header")
            yield Static(
                "[b]Instructions:[/b] Use arrow keys to navigate tables. "
                "Press [b]t[/b] to toggle OEM authorization, [b]s[/b] to toggle contract support. "
                "Press [b]a[/b] to add new OEM, [b]c[/b] to add contract. "
                "Changes save automatically. Press [b]r[/b] to refresh, [b]Esc[/b] to exit.",
                id="guide_instructions"
            )
            with Horizontal():
                with Vertical(id="left"):
                    with Vertical(id="oem_card"):
                        yield Static("OEM AUTHORIZATIONS", classes="card_header")
                        with Vertical(classes="card_body"):
                            self.oem_table = DataTable(id="oem_table", zebra_stripes=True, cursor_type="row")
                            self.oem_table.add_columns("OEM Name", "Authorized", "Threshold")
                            yield self.oem_table
                with Vertical(id="right"):
                    with Vertical(id="contracts_card"):
                        yield Static("SUPPORTED CONTRACT VEHICLES", classes="card_header")
                        with Vertical(classes="card_body"):
                            self.contract_table = DataTable(id="contract_table", zebra_stripes=True, cursor_type="row")
                            self.contract_table.add_columns("Vehicle Name", "Supported", "Notes")
                            yield self.contract_table
            yield Static("Ready", id="guide_footer")

    async def on_mount(self) -> None:
        await self.action_refresh()
        try:
            self.set_focus(self.oem_table)
        except Exception:
            pass

    def _toast(self, msg: str) -> None:
        try:
            self.query_one("#guide_footer", Static).update(msg)
        except Exception:
            pass

    async def action_close(self) -> None:
        self.app.pop_screen()

    async def action_refresh(self) -> None:
        try:
            self._load_oems()
        except Exception as e:
            self._toast(f"[red]OEM load error: {e}[/red]")
        try:
            self._load_contracts()
        except Exception as e:
            self._toast(f"[red]Contract load error: {e}[/red]")
        self._toast("[green]✓ Tables refreshed[/green]")

    async def action_toggle_oem(self) -> None:
        await self._toggle_oem_authorized()

    async def action_toggle_contract(self) -> None:
        await self._toggle_contract_supported()

    async def action_add_oem(self) -> None:
        try:
            self.app.push_screen(AddOemModal(self))
        except Exception as e:
            self._toast(f"[red]Add OEM failed: {e}[/red]")

    async def action_add_contract(self) -> None:
        try:
            self.app.push_screen(AddContractModal(self))
        except Exception as e:
            self._toast(f"[red]Add Contract failed: {e}[/red]")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = (event.button.id or "").strip()
        import asyncio
        if bid == "btn_close":
            self.app.pop_screen()
        elif bid == "btn_refresh":
            asyncio.create_task(self.action_refresh())
        elif bid == "btn_toggle_oem":
            asyncio.create_task(self.action_toggle_oem())
        elif bid == "btn_toggle_contract":
            asyncio.create_task(self.action_toggle_contract())
        elif bid == "btn_add_oem":
            asyncio.create_task(self.action_add_oem())
        elif bid == "btn_add_contract":
            asyncio.create_task(self.action_add_contract())

    def on_key(self, event: events.Key) -> None:
        try:
            key = (event.key or "").lower()
        except Exception:
            return
        import asyncio
        # Enter/Space toggle based on focus
        if key in ("enter", "space"):
            try:
                target_id = getattr(self.focused, "id", "")
            except Exception:
                target_id = ""
            if target_id == "oem_table":
                asyncio.create_task(self.action_toggle_oem())
                event.stop()
                return
            if target_id == "contract_table":
                asyncio.create_task(self.action_toggle_contract())
                event.stop()
                return

    def _load_oems(self) -> None:
        data = rfq_api.config_list_oems() or {}
        items = (data.get("items") if isinstance(data, dict) else []) or []
        self.oem_table.clear()
        for row in items:
            oem = str(row.get("oem_name", ""))
            auth = bool(row.get("authorized", False))
            auth_display = "[green]✓ Yes[/green]" if auth else "[red]✗ No[/red]"
            thr = row.get("business_case_threshold", None)
            thr_str = str(thr) if thr not in (None, "", "null") else "—"
            self.oem_table.add_row(oem, auth_display, thr_str)
        try:
            if items:
                self.oem_table.move_cursor(row=0)
        except Exception:
            pass

    def _load_contracts(self) -> None:
        data = rfq_api.config_list_contracts() or {}
        items = (data.get("items") if isinstance(data, dict) else []) or []
        self.contract_table.clear()
        for row in items:
            name = str(row.get("vehicle_name", ""))
            sup = bool(row.get("supported", False))
            sup_display = "[green]✓ Yes[/green]" if sup else "[red]✗ No[/red]"
            notes = str(row.get("notes", "") or "—")
            self.contract_table.add_row(name, sup_display, notes[:40])
        try:
            if items:
                self.contract_table.move_cursor(row=0)
        except Exception:
            pass

    async def _toggle_oem_authorized(self) -> None:
        try:
            row_key = getattr(self.oem_table, "cursor_row", None)
            if row_key is None:
                self._toast("[yellow]⚠ Select an OEM row first (use ↑/↓)[/yellow]")
                return
            try:
                row = self.oem_table.get_row(row_key)
            except Exception:
                self._toast("[yellow]⚠ No OEM row selected[/yellow]")
                return
            
            oem_name = str(row[0]).strip()
            if not oem_name:
                self._toast("[yellow]⚠ Invalid OEM name[/yellow]")
                return
            
            # Extract current state from display text
            auth_text = str(row[1]).strip()
            current = "yes" in auth_text.lower()
            new_state = not current
            
            # Call backend
            res = rfq_api.config_set_oem_authorized(oem_name, new_state)
            
            # Check response
            if not res or not isinstance(res, dict):
                self._toast("[red]✗ Update failed: no response[/red]")
                return
            
            # Check for error
            if res.get("success") is False or "error" in res:
                err = res.get("error", "unknown error")
                self._toast(f"[red]✗ Update failed: {err}[/red]")
                return
            
            # Reload tables
            self._load_oems()
            
            # Restore selection to updated OEM
            try:
                for idx in range(self.oem_table.row_count):
                    r = self.oem_table.get_row(idx)
                    if str(r[0]).strip().lower() == oem_name.lower():
                        self.oem_table.move_cursor(row=idx)
                        break
            except Exception:
                pass
            
            state_text = "Authorized ✓" if new_state else "Not Authorized ✗"
            self._toast(f"[green]✓ {oem_name} → {state_text}[/green]")
            
        except Exception as e:
            self._toast(f"[red]✗ Toggle error: {e}[/red]")

    async def _toggle_contract_supported(self) -> None:
        try:
            row_key = getattr(self.contract_table, "cursor_row", None)
            if row_key is None:
                self._toast("[yellow]⚠ Select a Contract row first (use ↑/↓)[/yellow]")
                return
            try:
                row = self.contract_table.get_row(row_key)
            except Exception:
                self._toast("[yellow]⚠ No Contract row selected[/yellow]")
                return
            
            name = str(row[0]).strip()
            if not name:
                self._toast("[yellow]⚠ Invalid contract name[/yellow]")
                return
            
            # Extract current state from display text
            sup_text = str(row[1]).strip()
            current = "yes" in sup_text.lower()
            new_state = not current
            
            # Call backend
            res = rfq_api.config_upsert_contract(name, new_state, None)
            
            # Check response
            if not res or not isinstance(res, dict):
                self._toast("[red]✗ Update failed: no response[/red]")
                return
            
            if res.get("success") is False or "error" in res:
                err = res.get("error", "unknown error")
                self._toast(f"[red]✗ Update failed: {err}[/red]")
                return
            
            # Reload tables
            self._load_contracts()
            
            # Restore selection
            try:
                for idx in range(self.contract_table.row_count):
                    r = self.contract_table.get_row(idx)
                    if str(r[0]).strip().lower() == name.lower():
                        self.contract_table.move_cursor(row=idx)
                        break
            except Exception:
                pass
            
            state_text = "Supported ✓" if new_state else "Not Supported ✗"
            self._toast(f"[green]✓ {name} → {state_text}[/green]")
            
        except Exception as e:
            self._toast(f"[red]✗ Toggle error: {e}[/red]")


class AddOemModal(ModalScreen):
    """Modal dialog to add a new OEM with authorization settings."""
    
    CSS = """
    AddOemModal {
        align: center middle;
    }
    AddOemModal > Container {
        width: 70;
        height: 18;
        border: thick $primary;
        background: $surface;
    }
    #ao_header {
        dock: top;
        height: 3;
        content-align: center middle;
        background: $primary;
    }
    #ao_body {
        height: 1fr;
        padding: 2;
    }
    #ao_footer {
        dock: bottom;
        height: 4;
        content-align: center middle;
        padding: 1;
    }
    Label {
        margin: 1 0;
    }
    Input {
        margin: 0 0 1 0;
    }
    Checkbox {
        margin: 0 0 1 0;
    }
    """

    def __init__(self, parent_screen):
        super().__init__()
        self._parent = parent_screen

    def compose(self) -> ComposeResult:
        with Container():
            yield Static("➕ Add New OEM", id="ao_header")
            with Vertical(id="ao_body"):
                yield Label("OEM Name:")
                self.in_name = Input(placeholder="Enter OEM name (e.g., LogRhythm)", id="ao_name")
                yield self.in_name
                
                yield Label("Authorized for Red River?")
                self.cb_auth = Checkbox("Yes, authorized", value=True, id="ao_auth")
                yield self.cb_auth
                
                yield Label("Business Case Threshold (optional):")
                self.in_thr = Input(placeholder="5", id="ao_thr")
                yield self.in_thr
                
            with Horizontal(id="ao_footer"):
                yield Button("Cancel", id="ao_cancel", variant="error")
                yield Button("Save OEM", id="ao_save", variant="success")

    async def on_mount(self) -> None:
        # Auto-focus the name input
        try:
            self.set_focus(self.in_name)
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = (event.button.id or "")
        if bid == "ao_cancel":
            self.dismiss(False)
            return
        if bid == "ao_save":
            name = (self.in_name.value or "").strip()
            if not name:
                self._parent._toast("[yellow]⚠ OEM name required[/yellow]")
                return
            
            thr_raw = (self.in_thr.value or "").strip().replace(",", "")
            try:
                thr = int(thr_raw) if thr_raw else None
            except Exception:
                thr = None
            
            auth = bool(self.cb_auth.value)
            
            try:
                res = rfq_api.config_set_oem_authorized(name, auth, thr)
                success = isinstance(res, dict) and res.get("success") is not False
            except Exception as e:
                self._parent._toast(f"[red]✗ Save failed: {e}[/red]")
                return
            
            if success:
                import asyncio
                asyncio.create_task(self._parent.action_refresh())
                state = "Authorized ✓" if auth else "Not Authorized ✗"
                self._parent._toast(f"[green]✓ Added {name} ({state})[/green]")
                self.dismiss(True)
            else:
                err = res.get("error", "unknown") if isinstance(res, dict) else "unknown"
                self._parent._toast(f"[red]✗ Failed: {err}[/red]")


class AddContractModal(ModalScreen):
    """Modal dialog to add a new supported contract vehicle."""
    
    CSS = """
    AddContractModal {
        align: center middle;
    }
    AddContractModal > Container {
        width: 70;
        height: 18;
        border: thick $primary;
        background: $surface;
    }
    #ac_header {
        dock: top;
        height: 3;
        content-align: center middle;
        background: $primary;
    }
    #ac_body {
        height: 1fr;
        padding: 2;
    }
    #ac_footer {
        dock: bottom;
        height: 4;
        content-align: center middle;
        padding: 1;
    }
    Label {
        margin: 1 0;
    }
    Input {
        margin: 0 0 1 0;
    }
    Checkbox {
        margin: 0 0 1 0;
    }
    """

    def __init__(self, parent_screen):
        super().__init__()
        self._parent = parent_screen

    def compose(self) -> ComposeResult:
        with Container():
            yield Static("➕ Add Contract Vehicle", id="ac_header")
            with Vertical(id="ac_body"):
                yield Label("Contract Vehicle Name:")
                self.in_name = Input(placeholder="e.g., NASA SEWP V", id="ac_name")
                yield self.in_name
                
                yield Label("Is this vehicle supported by Red River?")
                self.cb_sup = Checkbox("Yes, supported", value=True, id="ac_sup")
                yield self.cb_sup
                
                yield Label("Notes (optional):")
                self.in_notes = Input(placeholder="e.g., Primary NASA GWAC", id="ac_notes")
                yield self.in_notes
                
            with Horizontal(id="ac_footer"):
                yield Button("Cancel", id="ac_cancel", variant="error")
                yield Button("Save Contract", id="ac_save", variant="success")

    async def on_mount(self) -> None:
        # Auto-focus the name input
        try:
            self.set_focus(self.in_name)
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = (event.button.id or "")
        if bid == "ac_cancel":
            self.dismiss(False)
            return
        if bid == "ac_save":
            name = (self.in_name.value or "").strip()
            if not name:
                self._parent._toast("[yellow]⚠ Contract name required[/yellow]")
                return
            
            sup = bool(self.cb_sup.value)
            notes = (self.in_notes.value or "").strip() or None
            
            try:
                res = rfq_api.config_upsert_contract(name, sup, notes)
                success = isinstance(res, dict) and res.get("success") is not False
            except Exception as e:
                self._parent._toast(f"[red]✗ Save failed: {e}[/red]")
                return
            
            if success:
                import asyncio
                asyncio.create_task(self._parent.action_refresh())
                state = "Supported ✓" if sup else "Not Supported ✗"
                self._parent._toast(f"[green]✓ Added {name} ({state})[/green]")
                self.dismiss(True)
            else:
                err = res.get("error", "unknown") if isinstance(res, dict) else "unknown"
                self._parent._toast(f"[red]✗ Failed: {err}[/red]")