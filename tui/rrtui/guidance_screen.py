from textual.app import ComposeResult
from textual.screen import Screen, ModalScreen
from textual.widgets import Static, DataTable, Button, Input, Checkbox
from textual.containers import Container, Horizontal, Vertical
from textual import events
from textual.binding import Binding

from . import rfq_api


class GuidanceScreen(Screen):
    """Full-screen editor for Analysis Guidance: OEM authorization and Supported Contracts.
    Explicit action buttons and hotkeys are provided. Press Esc or q to return."""

    BINDINGS = [
        Binding("escape", "close", "Back", show=False, priority=True),
        Binding("q", "close", "Back", show=False, priority=True),
        Binding("r", "refresh", "Refresh", show=False, priority=True),
        Binding("a", "add_oem", "Add OEM", show=False, priority=True),
        Binding("c", "add_contract", "Add Contract", show=False, priority=True),
        Binding("t", "toggle_oem", "Toggle OEM Authorized", show=False, priority=True),
        Binding("s", "toggle_contract", "Toggle Contract Supported", show=False, priority=True),
    ]

    CSS = """
    GuidanceScreen {
        align: center middle;
    }
    GuidanceScreen > Container {
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
    #actions {
        dock: bottom;
        height: 3;
        content-align: center middle;
    }
    #actions_top {
        dock: top;
        height: 3;
        content-align: center middle;
    }
    Button {
        margin: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Container():
            yield Static("[b][cyan]Edit Analysis Guidance[/cyan] — OEM Authorization & Supported Contracts[/b]", id="guide_header")
            # Top action bar (visible regardless of terminal height)
            with Horizontal(id="actions_top"):
                yield Button("Add OEM (A)", id="btn_add_oem", variant="primary")
                yield Button("Add Contract (C)", id="btn_add_contract", variant="primary")
                yield Button("Toggle OEM (t)", id="btn_toggle_oem", variant="primary")
                yield Button("Toggle Contract (s)", id="btn_toggle_contract", variant="primary")
                yield Button("Refresh (r)", id="btn_refresh")
                yield Button("Back (Esc/q)", id="btn_close")
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
            # Action bar
            with Horizontal(id="actions"):
                yield Button("Toggle OEM (t)", id="btn_toggle_oem", variant="primary")
                yield Button("Toggle Contract (s)", id="btn_toggle_contract", variant="primary")
                yield Button("Refresh (r)", id="btn_refresh")
                yield Button("Back (Esc/q)", id="btn_close")
            # Footer status
            yield Static("[dim]Use t / s to toggle, r to refresh, Esc/q to go back.[/dim]", id="guide_footer")

    async def on_mount(self) -> None:
        await self.action_refresh()
        # Focus OEM table initially
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
            self._toast(f"[red]OEM load failed: {e}[/red]")
        try:
            self._load_contracts()
        except Exception as e:
            self._toast(f"[red]Contracts load failed: {e}[/red]")
        self._toast("[green]Refreshed[/green]")

    async def action_toggle_oem(self) -> None:
        await self._toggle_oem_authorized()

    async def action_toggle_contract(self) -> None:
        await self._toggle_contract_supported()

    async def action_add_oem(self) -> None:
        try:
            self.app.push_screen(AddOemModal(self))
        except Exception:
            self._toast("[red]Failed to open Add OEM[/red]")

    async def action_add_contract(self) -> None:
        try:
            self.app.push_screen(AddContractModal(self))
        except Exception:
            self._toast("[red]Failed to open Add Contract[/red]")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = (event.button.id or "").strip()
        if bid == "btn_close":
            self.app.pop_screen()
        elif bid == "btn_refresh":
            import asyncio
            asyncio.create_task(self.action_refresh())
        elif bid == "btn_toggle_oem":
            import asyncio
            asyncio.create_task(self.action_toggle_oem())
        elif bid == "btn_toggle_contract":
            import asyncio
            asyncio.create_task(self.action_toggle_contract())
        elif bid == "btn_add_oem":
            import asyncio
            asyncio.create_task(self.action_add_oem())
        elif bid == "btn_add_contract":
            import asyncio
            asyncio.create_task(self.action_add_contract())

    def on_key(self, event: events.Key) -> None:
        # Defensive routing to ensure keys are honored even if a child captures them
        try:
            key = (event.key or "").lower()
        except Exception:
            key = ""
        import asyncio
        # Enter/Space toggle based on current focus (works even if hotkeys are swallowed)
        if key in ("enter", "return", "space"):
            try:
                target_id = getattr(self.focused, "id", "")
            except Exception:
                target_id = ""
            if target_id == "oem_table":
                asyncio.create_task(self.action_toggle_oem()); self._stop(event); return
            if target_id == "contract_table":
                asyncio.create_task(self.action_toggle_contract()); self._stop(event); return
        if key == "t":
            asyncio.create_task(self.action_toggle_oem());  self._stop(event)
        elif key == "s":
            asyncio.create_task(self.action_toggle_contract()); self._stop(event)
        elif key == "r":
            asyncio.create_task(self.action_refresh()); self._stop(event)
        elif key in ("escape", "esc", "q"):
            self.app.pop_screen(); self._stop(event)

    def _stop(self, event: events.Event) -> None:
        try:
            event.stop()
        except Exception:
            pass

    # --- Data loading ---
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
        # Ensure initial selection
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
        # Ensure initial selection
        try:
            if items:
                self.contract_table.move_cursor(row=0, column=0)
        except Exception:
            pass

    # --- Toggle helpers ---
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
            if not res or not isinstance(res, dict):
                self._toast("[red]Failed to update OEM authorization[/red]")
                return
            # Reload and re-focus original OEM row
            self._load_oems()
            # Try to restore selection on the same OEM name
            try:
                # Scan table to find the row index of the OEM we updated
                for idx in range(len(self.oem_table.rows)):
                    r = self.oem_table.get_row(idx)
                    if str(r[0]).strip().lower() == oem_name.lower():
                        self.oem_table.move_cursor(row=idx, column=0)
                        break
            except Exception:
                pass
            # Compute final state from response if present
            final_auth = res.get("authorized")
            if isinstance(final_auth, bool):
                state_txt = "Authorized" if final_auth else "Not Authorized"
            else:
                state_txt = "Authorized" if not current else "Not Authorized"
            self._toast(f"[green]Updated OEM: {oem_name} → {state_txt}[/green]")
        except Exception as e:
            self._toast(f"[red]Toggle failed: {e}[/red]")

class AddOemModal(ModalScreen):
    CSS = """
    AddOemModal {
        align: center middle;
    }
    AddOemModal > Container {
        width: 80;
        height: 14;
        border: thick $accent;
        background: $surface;
    }
    #ao_header { dock: top; height: 3; content-align: center middle; background: $accent; }
    #ao_body { height: 1fr; padding: 1 2; }
    #ao_footer { dock: bottom; height: 3; content-align: center middle; }
    """

    def __init__(self, parent_screen):
        super().__init__()
        self._parent = parent_screen

    def compose(self) -> ComposeResult:
        with Container():
            yield Static("[b][cyan]Add OEM[/cyan][/b]", id="ao_header")
            with Vertical(id="ao_body"):
                yield Static("OEM Name:")
                self.in_name = Input(placeholder="e.g., NewOEM", id="ao_name")
                yield Static("Authorized?")
                self.cb_auth = Checkbox(value=True, id="ao_auth")
                yield Static("Business Case Threshold (optional, integer):")
                self.in_thr = Input(placeholder="5", id="ao_thr")
            with Horizontal(id="ao_footer"):
                yield Button("Cancel", id="ao_cancel")
                yield Button("Save", id="ao_save", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = (event.button.id or "")
        if bid == "ao_cancel":
            self.dismiss(False); return
        if bid == "ao_save":
            name = (self.in_name.value or "").strip()
            if not name:
                try:
                    self._parent._toast("[yellow]Enter OEM name[/yellow]")
                except Exception:
                    pass
                return
            thr_raw = (self.in_thr.value or "").strip().replace(",", "")
            try:
                thr = int(thr_raw) if thr_raw else None
            except Exception:
                thr = None
            auth = bool(self.cb_auth.value)
            # Call MCP (with sqlite fallback in rfq_api)
            try:
                res = rfq_api.config_set_oem_authorized(name, auth, thr)
                ok = isinstance(res, dict) and (res.get("success", True) is not False)
            except Exception:
                ok = False
            if ok:
                try:
                    import asyncio
                    asyncio.create_task(self._parent.action_refresh())
                    self._parent._toast(f"[green]OEM added/updated: {name} ({'Authorized' if auth else 'Not Authorized'})[/green]")
                except Exception:
                    pass
                self.dismiss(True)
            else:
                try:
                    self._parent._toast("[red]Failed to add/update OEM[/red]")
                except Exception:
                    pass

class AddContractModal(ModalScreen):
    CSS = """
    AddContractModal {
        align: center middle;
    }
    AddContractModal > Container {
        width: 80;
        height: 14;
        border: thick $accent;
        background: $surface;
    }
    #ac_header { dock: top; height: 3; content-align: center middle; background: $accent; }
    #ac_body { height: 1fr; padding: 1 2; }
    #ac_footer { dock: bottom; height: 3; content-align: center middle; }
    """

    def __init__(self, parent_screen):
        super().__init__()
        self._parent = parent_screen

    def compose(self) -> ComposeResult:
        with Container():
            yield Static("[b][cyan]Add Contract Vehicle[/cyan][/b]", id="ac_header")
            with Vertical(id="ac_body"):
                yield Static("Contract Vehicle Name:")
                self.in_name = Input(placeholder="e.g., NASA SEWP V", id="ac_name")
                yield Static("Supported?")
                self.cb_sup = Checkbox(value=True, id="ac_sup")
                yield Static("Notes (optional):")
                self.in_notes = Input(placeholder="", id="ac_notes")
            with Horizontal(id="ac_footer"):
                yield Button("Cancel", id="ac_cancel")
                yield Button("Save", id="ac_save", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = (event.button.id or "")
        if bid == "ac_cancel":
            self.dismiss(False); return
        if bid == "ac_save":
            name = (self.in_name.value or "").strip()
            if not name:
                try:
                    self._parent._toast("[yellow]Enter contract vehicle name[/yellow]")
                except Exception:
                    pass
                return
            sup = bool(self.cb_sup.value)
            notes = (self.in_notes.value or "").strip() or None
            # Call MCP with sqlite fallback
            try:
                res = rfq_api.config_upsert_contract(name, sup, notes)
                ok = isinstance(res, dict) and (res.get("success", True) is not False)
            except Exception:
                ok = False
            if ok:
                try:
                    import asyncio
                    asyncio.create_task(self._parent.action_refresh())
                    self._parent._toast(f"[green]Contract saved: {name} ({'Supported' if sup else 'Not Supported'})[/green]")
                except Exception:
                    pass
                self.dismiss(True)
            else:
                try:
                    self._parent._toast("[red]Failed to save contract[/red]")
                except Exception:
                    pass

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
            # Reload and re-focus
            self._load_contracts()
            self._toast(f"[green]Updated Contract: {name} → {'Supported' if not current else 'Not Supported'}[/green]")
        except Exception as e:
            self._toast(f"[red]Toggle failed: {e}[/red]")