
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, DataTable
from textual.containers import Horizontal, Container
from textual.reactive import reactive
from datetime import datetime
import asyncio, os, subprocess, time
from pathlib import Path
try:
    from dotenv import load_dotenv, find_dotenv
except Exception:
    load_dotenv = None
    find_dotenv = None

from config.config_loader import load_settings
from . import status_bridge as status_bridge
from . import rfq_api as rfq_api
from .lom_view import LOMModal
from .artifacts_view import ArtifactsModal
from .analytics_view import AnalyticsModal
from .settings_view import SettingsView
from .operation_modal import OperationModal
from .rfq_management_view import RFQManagementScreen
from .rfq_details_modal import RFQDetailsModal
from .intromail_view import IntroMailScreen

# Load .env values (repo root and tui/.env) without requiring shell sourcing
def _load_env():
    if load_dotenv:
        try:
            repo_root = Path(__file__).resolve().parents[2]
            tui_root = Path(__file__).resolve().parents[1]
            for p in (repo_root / ".env", tui_root / ".env"):
                if p.exists():
                    load_dotenv(p, override=False)
        except Exception:
            # Best-effort env load; continue silently if anything goes wrong
            pass

_load_env()

class Dashboard(App):
    CSS_PATH = str(Path(__file__).with_name("styles.tcss"))
    BINDINGS = [
        ("q","quit","Quit"),
        ("1","rfq_management","RFQ Emails"),
        ("2","govly","Govly"),
        ("3","intromail","IntroMail"),
        ("7","analytics","Analytics"),
        ("9","settings","Settings"),
        ("d","dark","Dark"),
        ("enter","open_selected","Open Details"),
        ("o","open_selected","Open Details"),
    ]

    last_update = reactive("—")
    toast = reactive("")

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container():
            with Horizontal(id="row"):
                yield Static(id="system", classes="panel")
                yield Static(id="providers", classes="panel")
            yield Static(id="funnel", classes="panel")
            yield Static(id="pipeline", classes="panel")
            self.table = DataTable(id="rfq_table", classes="panel")
            yield self.table
            yield Static(id="actions", classes="panel")
        yield Footer()

    async def on_mount(self):
        self.cfg = load_settings()
        # Apply theme
        self.dark = (self.cfg.get("ui", {}).get("theme", "light") == "dark")
        # Start refresh timer and keep handle for live updates
        self.refresh_timer = self.set_interval(self.cfg["ui"].get("refresh_sec", 2), self.refresh_status)
        self.table.add_columns("ID","Opportunity","Type","Score","Reco")
        # Stats cache for Funnel 30d
        self._stats_cache = None
        self._stats_ts = 0.0
        await self.refresh_status()

    async def refresh_status(self):
        s = status_bridge.get_status()
        self.last_update = datetime.now().strftime("%H:%M:%S")
        dot = lambda st: "[green]● ONLINE[/]" if st=="online" else "[yellow]● WARN[/]" if st=="warn" else "[red]● ERROR[/]" if st=="error" else "[dim]○ OFF[/]"

        sys = self.query_one("#system", Static)
        prv = self.query_one("#providers", Static)
        pip = self.query_one("#pipeline", Static)
        act = self.query_one("#actions", Static)

        mcp = s.get("mcp",{}); watchers = s.get("watchers",{})
        providers = s.get("providers",{}); pipe = s.get("pipeline",{})
        router = s.get("router","SIMPLE (Claude-only)")

        sys.update(
            f"[b][cyan]System[/cyan][/b]\n"
            f"MCP: {dot('online' if mcp.get('running') else 'error')}\n"
            f"Uptime: {mcp.get('uptime','—')}  Queue: {mcp.get('queue',0)}\n\n"
            f"[b][cyan]Watchers[/cyan][/b]\n" +
            "\n".join([f"• {label:<14} {dot(watchers.get(key,{}).get('state','off'))}" for key,label in [
                ("outlook_rfq","Outlook RFQ"),("fleeting_notes","Fleeting Notes"),("radar","Radar"),("govly_sync","Govly Sync")
            ]]) + f"\n\nRouting: {router}"
        )
        prv_lines = []
        for key,label in [("claude","Claude Runtime"),("gpt5","ChatGPT-5"),("gemini","Gemini")]:
            status = dot('online' if providers.get(key,{}).get('online') else 'error')
            p95 = providers.get(key,{}).get('p95_ms')
            p95_str = f"{p95} ms" if p95 is not None else "— ms"
            prv_lines.append(f"• {label:<14} {status}  p95 {p95_str:>7}")
        prv.update("[b][cyan]Providers[/cyan][/b]\n" + "\n".join(prv_lines))
        pip.update(
            f"[b][cyan]RFQ Pipeline Today[/cyan][/b]\n"
            f"Emails: {pipe.get('emails',0)}   RFQs: {pipe.get('rfqs',0)}   GO: {pipe.get('go',0)}   Pending: {pipe.get('pending',0)}\n"
            f"[i]Last update: {self.last_update}[/i]"
        )
        # Funnel 30d panel refresh (stats every ui.stats_refresh_sec)
        try:
            now = time.time()
            if (now - getattr(self, "_stats_ts", 0.0)) >= self.cfg.get("ui", {}).get("stats_refresh_sec", 10):
                self._stats_cache = rfq_api.rfq_stats("30d")
                self._stats_ts = now
            stats = self._stats_cache or {}
            funnel = (stats.get("funnel") if isinstance(stats, dict) else {}) or {}
            fun = self.query_one("#funnel", Static)
            fun.update(self._render_funnel(funnel))
        except Exception:
            try:
                fun = self.query_one("#funnel", Static)
                fun.update("[b][cyan]Funnel 30d[/cyan][/b]\n—")
            except Exception:
                pass
        # Table refresh: fetch RFQs and populate table (Top 10 GO by Score desc)
        try:
            rfqs = rfq_api.list_rfqs("all")
        except Exception:
            rfqs = []

        def _norm_reco(val: str) -> str:
            try:
                t = str(val or "").strip().upper()
            except Exception:
                t = ""
            if t.startswith("NO GO") or t.startswith("NO-GO") or "NO-GO" in t:
                return "NO-GO"
            if t.startswith("REVIEW"):
                return "REVIEW"
            if t.startswith("GO") or " GO" in t:
                return "GO"
            return "PENDING"

        def _parse_score(v) -> int:
            try:
                return int(str(v).strip() or "0")
            except Exception:
                return 0

        # Filter to GO only, sort by Score desc, and take Top 10
        gos = [r for r in (rfqs or []) if _norm_reco(r.get("rfq_recommendation","")) == "GO"]
        gos_sorted = sorted(gos, key=lambda r: _parse_score(r.get("rfq_score","0")), reverse=True)[:10]

        self.table.clear()
        for r in gos_sorted:
            self.table.add_row(
                str(r.get("id","")),
                str(r.get("subject","")),
                str(r.get("rfq_type","")),
                str(r.get("rfq_score","")),
                str(r.get("rfq_recommendation","")),
            )

        act.update(
            "[b][cyan]Actions[/cyan][/b]  [1] RFQ Emails  [2] Govly  [3] IntroMail  [7] Analytics  [9] Settings  (d) Dark  (q) Quit\n"
            "[dim]RFQ Table: Top 10 GO opportunities (Score desc). Use Enter or 'o' to open details.[/dim]\n"
            f"{self.toast}"
        )

    def _render_funnel(self, funnel: dict) -> str:
        """Render a 30d funnel with horizontal bars scaled to max."""
        order = [
            ("received", "Received"),
            ("validated", "Validated"),
            ("registered", "Registered"),
            ("quoted", "Quoted"),
            ("submitted", "Submitted"),
            ("awarded", "Awarded"),
        ]
        vals = [int((funnel or {}).get(k, 0) or 0) for k, _ in order]
        max_v = max(vals) if vals else 0
        width = 40
        out = "[b][cyan]Funnel 30d[/cyan][/b]\n"
        for (key, label), v in zip(order, vals):
            bar_len = int(v / max_v * width) if max_v else 0
            bar = "[green]" + ("█" * bar_len) + "[/green]"
            out += f"{label:<10} [b]{v:>4}[/b]  {bar}\n"
        
        # Add conversion rate at bottom if we have data
        if max_v > 0 and len(vals) == 6:
            received = vals[0]
            awarded = vals[5]
            if received > 0:
                conversion = (awarded / received) * 100
                out += f"\n[dim]Conversion: {conversion:.1f}% ({awarded}/{received})[/dim]"
        
        return out.rstrip()

    def _selected_rfq_id(self) -> str:
        try:
            row = self.table.cursor_row
            if row is not None:
                rid = self.table.get_row(row)[0]
                return str(rid)
        except Exception:
            pass
        return "0"

    async def action_rfq_management(self):
        """Open the comprehensive RFQ Management screen."""
        self.push_screen(RFQManagementScreen())

    def apply_settings(self, cfg: dict) -> None:
        # Merge new settings
        self.cfg = cfg or self.cfg
        # Apply theme
        try:
            theme = (self.cfg.get("ui", {}).get("theme", "light"))
            self.dark = (theme == "dark")
        except Exception:
            pass
        # Reset refresh timer
        try:
            if hasattr(self, "refresh_timer") and self.refresh_timer:
                try:
                    self.refresh_timer.stop()
                except Exception:
                    pass
            interval = self.cfg.get("ui", {}).get("refresh_sec", 2)
            self.refresh_timer = self.set_interval(interval, self.refresh_status)
        except Exception:
            pass

    async def action_settings(self):
        try:
            self.push_screen(SettingsView(self.cfg))
        except Exception:
            self.toast = "Settings failed to open"

    async def action_govly(self):
        """Govly integration - Coming Soon"""
        self.toast = "[yellow]⚠ Govly feature not yet implemented[/yellow]"
        await self.refresh_status()
    
    async def action_intromail(self):
        """Open the IntroMail campaign management screen."""
        self.push_screen(IntroMailScreen())
    
    async def action_analytics(self):
        self.push_screen(AnalyticsModal())

    async def action_open_selected(self):
        """Open RFQ Details modal for the selected RFQ."""
        rid = self._selected_rfq_id()
        if rid == "0":
            self.toast = "[yellow]⚠ Select an RFQ in the table first[/yellow]"
            await self.refresh_status()
            return
        self.push_screen(RFQDetailsModal(int(rid)))

    async def action_dark(self):
        self.dark = not self.dark

    
if __name__ == "__main__":
    Dashboard().run()
