
from textual.app import ComposeResult
from textual.widgets import Static, DataTable, Tabs
from textual.containers import Container
from textual.screen import ModalScreen
from textual import events
import re
from . import rfq_api as rfq_api

class AnalyticsModal(ModalScreen):
    """OEM analytics with 7/30/90 day windows (rfq_api.analytics_oem)."""

    def __init__(self):
        super().__init__()
        self.table = DataTable()
        self.window = "30d"

    def compose(self) -> ComposeResult:
        # Header with rich markup like other stages
        yield Container(Static("[b][cyan]OEM Analytics[/cyan][/b]  [dim](Esc to close)[/dim]", id="analytics_header"))
        yield Tabs("7d", "30d", "90d", id="tabs")
        # Table
        self.table.add_columns("OEM", "Occurrences", "Total $", "Avg Competition %", "Status")
        yield self.table
        # Summary panel with rich markdown-style output
        yield Static("", id="analytics_summary")

    def on_mount(self) -> None:
        self.refresh_table("30d")

    def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
        label = event.tab.label.plain
        self.refresh_table(label)

    def refresh_table(self, label: str):
        win = "7d" if label == "7d" else "90d" if label == "90d" else "30d"
        self.window = win
        try:
            rows = rfq_api.analytics_oem(win)  # list[dict]
            self.table.clear()
            for r in rows:
                self.table.add_row(
                    r.get("oem",""),
                    str(r.get("occurrences",0)),
                    str(r.get("total","$0")),
                    str(r.get("avg_competition","—")),
                    r.get("status","")
                )

            # Header with window and count (rich markup)
            header = (
                f"[b][cyan]OEM Analytics[/cyan][/b]  [dim](Esc to close)[/dim]\n"
                f"[dim]Window:[/dim] [yellow]{self.window}[/yellow]  |  "
                f"[dim]Top OEMs:[/dim] [yellow]{len(rows)}[/yellow]"
            )
            try:
                self.query_one("#analytics_header", Static).update(header)
            except Exception:
                pass

            # Compute summary metrics for markdown-style panel
            total_usd = 0.0
            total_occ = 0
            avg_comp_vals: list[float] = []
            for r in rows:
                # Parse money like "$250,000"
                t = str(r.get("total", "$0"))
                digits = re.sub(r"[^0-9.]", "", t)
                try:
                    total_usd += float(digits) if digits else 0.0
                except Exception:
                    pass

                # Occurrences
                try:
                    total_occ += int(r.get("occurrences", 0) or 0)
                except Exception:
                    pass

                # Avg competition like "42%"
                ac = str(r.get("avg_competition", "0%"))
                ac_d = re.sub(r"[^0-9.]", "", ac)
                try:
                    avg_comp_vals.append(float(ac_d) if ac_d else 0.0)
                except Exception:
                    pass

            avg_comp = round(sum(avg_comp_vals) / len(avg_comp_vals)) if avg_comp_vals else 0
            summary = (
                "[b][cyan]Summary[/cyan][/b]\n"
                f"• [b]Total:[/b] ${total_usd:,.0f}\n"
                f"• [b]Occurrences:[/b] {total_occ}\n"
                f"• [b]Avg Competition:[/b] {avg_comp}%"
            )
            try:
                self.query_one("#analytics_summary", Static).update(summary)
            except Exception:
                pass

        except Exception as e:
            self.app.push_screen(MessageModal(f"Analytics error: {e!r}"))

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.app.pop_screen()

class MessageModal(ModalScreen):
    def __init__(self, message: str):
        super().__init__()
        self.message = message
    def compose(self) -> ComposeResult:
        yield Static(self.message + "\n\n(Esc to close)")
    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.app.pop_screen()
