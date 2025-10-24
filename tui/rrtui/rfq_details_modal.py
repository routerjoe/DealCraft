from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Static, Input, Button, Checkbox
from textual.containers import Container, Horizontal, Vertical, Grid
from textual import events
import json
from .guidance_screen import GuidanceScreen


class RFQDetailsModal(ModalScreen):
    """View & edit RFQ attributes; re-run rules/analysis for a single RFQ."""

    CSS = """
    RFQDetailsModal {
        align: center middle;
    }
    RFQDetailsModal > Container {
        width: 100;
        height: 34;
        border: thick $accent;
        background: $surface;
    }
    #rd_header {
        dock: top;
        height: 3;
        content-align: center middle;
        background: $accent;
    }
    #rd_body {
        height: 1fr;
        padding: 1 2;
    }
    #rd_form {
        grid-size: 2 5;
        grid-gutter: 1 0;
        padding: 0 1;
    }
    .lbl {
        height: 1;
        content-align: left middle;
    }
    .val {
        height: 1;
    }
    #rd_actions {
        height: 3;
        content-align: center middle;
        padding: 0 1;
    }
    #rd_log {
        height: 8;
        border: solid $accent;
        margin: 1 1;
        padding: 0 1;
    }
    #rd_footer {
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
        # cached RFQ dict
        self._rfq = {}

    def compose(self) -> ComposeResult:
        with Container():
            yield Static(f"[b][cyan]RFQ Details #{self.rfq_id}[/cyan][/b]", id="rd_header")
            with Vertical(id="rd_body"):
                with Grid(id="rd_form"):
                    # Left column labels
                    yield Static("Estimated Value ($):", classes="lbl")
                    self.in_value = Input(placeholder="e.g., 250000", classes="val", id="in_value")
                    yield Static("Competition Level (#bidders):", classes="lbl")
                    self.in_comp = Input(placeholder="e.g., 15", classes="val", id="in_comp")
                    yield Static("Technology Vertical:", classes="lbl")
                    self.in_tech = Input(placeholder="e.g., Enterprise Networking", classes="val", id="in_tech")
                    yield Static("OEM:", classes="lbl")
                    self.in_oem = Input(placeholder="e.g., Cisco", classes="val", id="in_oem")
                    yield Static("Contract Vehicle:", classes="lbl")
                    self.in_contract = Input(placeholder="e.g., SEWP, NASA SEWP V", classes="val", id="in_contract")

                    # Right column
                    yield Static("Customer:", classes="lbl")
                    self.in_customer = Input(placeholder="e.g., AFCENT", classes="val", id="in_customer")
                    yield Static("Deadline (ISO):", classes="lbl")
                    self.in_deadline = Input(placeholder="YYYY-MM-DD or full ISO", classes="val", id="in_deadline")
                    yield Static("Has Previous Contract:", classes="lbl")
                    self.cb_prev = Checkbox(value=False, classes="val", id="cb_prev")
                    yield Static("RFQ Type (optional):", classes="lbl")
                    self.in_type = Input(placeholder="e.g., RFI, MRR, renewal", classes="val", id="in_type")
                    yield Static("Subject (read-only):", classes="lbl")
                    self.in_subject = Input(placeholder="", classes="val", id="in_subject")

                with Horizontal(id="rd_actions"):
                    yield Button("Save Attributes", id="btn_save", variant="primary")
                    yield Button("Re-run Rules", id="btn_rules")
                    yield Button("Re-run Analyze (AI)", id="btn_analyze")
                    yield Button("Edit Guidance", id="btn_guidance")
                    yield Button("Close", id="btn_close")

                self.log = Static("", id="rd_log")
                yield self.log

            yield Static("[dim]Tip: Update fields then Save, or re-run Rules/Analyze to refresh scoring and guidance.[/dim]", id="rd_footer")

    async def on_mount(self) -> None:
        await self._load_rfq()

    async def _load_rfq(self) -> None:
        # Call MCP tool 'rfq_list_pending' (status=all) and select matching RFQ
        data = self._call_tool_json("rfq_list_pending", {"status": "all"})
        rfqs = (data.get("rfqs") if isinstance(data, dict) else []) or []
        found = None
        for r in rfqs:
            try:
                if int(r.get("id")) == self.rfq_id:
                    found = r
                    break
            except Exception:
                continue
        if not found:
            self._write_log(f"[red]RFQ #{self.rfq_id} not found[/red]")
            return

        self._rfq = found
        # Populate
        self.in_subject.value = str(found.get("subject", ""))[:120]
        self.in_subject.disabled = True
        self.in_value.value = self._num_to_str(found.get("estimated_value", ""))
        self.in_comp.value = self._num_to_str(found.get("competition_level", ""))
        self.in_tech.value = str(found.get("tech_vertical", "") or "")
        self.in_oem.value = str(found.get("oem", "") or "")
        self.in_contract.value = str(found.get("contract_vehicle", "") or "")
        self.in_customer.value = str(found.get("customer", "") or "")
        self.in_deadline.value = str(found.get("deadline", "") or "")
        self.cb_prev.value = bool(found.get("has_previous_contract", 0))

        score = found.get("rfq_score", None)
        reco = found.get("rfq_recommendation", "")
        self._write_log(f"[cyan]Loaded.[/cyan] Score: [b]{score if score is not None else '—'}[/b]  Reco: [b]{reco or '—'}[/b]")

    def _num_to_str(self, v) -> str:
        try:
            if v is None or v == "":
                return ""
            if isinstance(v, (int, float)):
                return str(int(v)) if float(v).is_integer() else str(v)
            s = str(v).strip()
            return s
        except Exception:
            return ""

    def _write_log(self, msg: str) -> None:
        try:
            prev = self.log.renderable or ""
        except Exception:
            prev = ""
        text = (prev + ("\n" if prev else "") + msg).strip()
        self.log.update(text)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid == "btn_close":
            self.dismiss(True)
            return
        if bid == "btn_save":
            self._save_attributes()
            return
        if bid == "btn_rules":
            self._rerun_rules()
            return
        if bid == "btn_analyze":
            self._rerun_analyze()
            return
        if bid == "btn_guidance":
            try:
                self.app.push_screen(GuidanceScreen())
            except Exception as e:
                self._write_log(f"[red]Failed to open Guidance: {e}[/red]")
            return

    # --- Tool calls ---
    def _call_tool_json(self, tool_name: str, tool_args: dict, timeout: int = 120) -> dict:
        """Call MCP bridge and parse JSON."""
        import subprocess
        from pathlib import Path
        try:
            script_dir = Path(__file__).resolve().parent.parent.parent / "mcp"
            bridge = script_dir / "bridge.mjs"
            proc = subprocess.run(
                ["npx", "tsx", str(bridge), tool_name, json.dumps(tool_args)],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            if proc.returncode != 0:
                self._write_log(f"[red]Tool error:[/red] {proc.stderr.strip()}")
                return {}
            out = proc.stdout.strip()
            return json.loads(out) if out else {}
        except Exception as e:
            self._write_log(f"[red]Bridge error:[/red] {e}")
            return {}

    def _save_attributes(self) -> None:
        args = {
            "rfq_id": self.rfq_id,
            "estimated_value": self._parse_int(self.in_value.value),
            "competition_level": self._parse_int(self.in_comp.value),
            "tech_vertical": (self.in_tech.value or "").strip() or None,
            "oem": (self.in_oem.value or "").strip() or None,
            "contract_vehicle": (self.in_contract.value or "").strip() or None,
            "customer": (self.in_customer.value or "").strip() or None,
            "deadline": (self.in_deadline.value or "").strip() or None,
            "has_previous_contract": bool(self.cb_prev.value),
        }
        res = self._call_tool_json("rfq_set_attributes", args)
        ok = isinstance(res, dict) and "content" in res
        self._write_log("[green]Saved attributes[/green]" if ok else "[red]Save failed[/red]")
        # Refresh local view after save by reloading row (and score from rfq_calculate_score path)
        self._load_rfq_noawait()

    def _rerun_rules(self) -> None:
        args = {"rfq_id": self.rfq_id, "rfq_type": (self.in_type.value or "").strip() or None}
        res = self._call_tool_json("rfq_apply_rules", args)
        if not res:
            self._write_log("[red]Rules run failed[/red]")
            return
        self._write_log("[green]Rules re-applied[/green]")
        self._load_rfq_noawait()

    def _rerun_analyze(self) -> None:
        args = {"rfq_id": self.rfq_id, "use_ai": True}
        res = self._call_tool_json("rfq_analyze", args)
        if not res:
            self._write_log("[red]AI analyze failed[/red]")
            return
        self._write_log("[green]AI analyze completed[/green]")
        self._load_rfq_noawait()

    def _parse_int(self, s: str):
        try:
            s = (s or "").strip().replace(",", "")
            if s == "":
                return None
            return int(float(s))
        except Exception:
            return None

    def _load_rfq_noawait(self):
        try:
            # fire and forget
            import asyncio
            asyncio.create_task(self._load_rfq())
        except Exception:
            pass