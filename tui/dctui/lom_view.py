from textual import events
from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import DataTable, Static

from . import rfq_api as rfq_api


class LOMModal(ModalScreen):
    """Inline LOM viewer for a selected RFQ (stubbed to rfq_api.lom_open)."""

    def __init__(self, rfq_id: str):
        super().__init__()
        self.rfq_id = rfq_id
        self.table = DataTable()

    def compose(self) -> ComposeResult:
        yield Container(Static(f"[b]LOM — RFQ {self.rfq_id}[/b]   (Esc to close)"))
        self.table.add_columns(
            "Line#",
            "Part#",
            "Description",
            "Qty",
            "Unit$",
            "Ext$",
            "OEM",
            "Contract",
            "TAA",
            "EPEAT",
        )
        yield self.table

    def on_mount(self) -> None:
        try:
            rows = rfq_api.lom_open(self.rfq_id)  # returns list[dict]
            for r in rows:
                self.table.add_row(
                    str(r.get("line", "")),
                    str(r.get("part", "")),
                    str(r.get("desc", "")),
                    str(r.get("qty", "")),
                    str(r.get("unit", "")),
                    str(r.get("ext", "")),
                    str(r.get("oem", "")),
                    str(r.get("contract", "")),
                    str(r.get("taa", "")),
                    str(r.get("epeat", "")),
                )
        except Exception as e:
            self.app.push_screen(MessageModal(f"LOM error: {e!r}"))

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
