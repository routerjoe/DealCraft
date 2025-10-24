
from textual.app import ComposeResult
from textual.widgets import Static, DataTable
from textual.containers import Container
from textual.screen import ModalScreen
from textual import events
from . import rfq_api as rfq_api

class ArtifactsModal(ModalScreen):
    """Artifacts list for selected RFQ (stubbed to rfq_api.artifacts_list)."""

    def __init__(self, rfq_id: str):
        super().__init__()
        self.rfq_id = rfq_id
        self.table = DataTable()

    def compose(self) -> ComposeResult:
        yield Container(Static(f"[b]Artifacts — RFQ {self.rfq_id}[/b]   (Enter: open externally, Esc: close)"))
        self.table.add_columns("Name", "Type", "Size", "Path")
        yield self.table

    def on_mount(self) -> None:
        try:
            files = rfq_api.artifacts_list(self.rfq_id)  # returns list[dict]
            for f in files:
                self.table.add_row(f.get("name",""), f.get("type",""), str(f.get("size","")), f.get("path",""))
        except Exception as e:
            self.app.push_screen(MessageModal(f"Artifacts error: {e!r}"))

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.app.pop_screen()
        elif event.key == "enter":
            try:
                row = self.table.cursor_row
                if row is not None:
                    path = self.table.get_row(row)[3]
                    rfq_api.artifact_open(path)
            except Exception as e:
                self.app.push_screen(MessageModal(f"Open error: {e!r}"))

class MessageModal(ModalScreen):
    def __init__(self, message: str):
        super().__init__()
        self.message = message
    def compose(self) -> ComposeResult:
        yield Static(self.message + "\n\n(Esc to close)")
    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.app.pop_screen()
