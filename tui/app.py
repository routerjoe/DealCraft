"""DealCraft MCP TUI - Main application."""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Footer, Header

from tui.panels.ai import AIPanel
from tui.panels.contracts import ContractsPanel
from tui.panels.forecast import ForecastPanel
from tui.panels.metrics import MetricsPanel
from tui.panels.oems import OEMPanel
from tui.theme import DEALCRAFT_LIGHT


class DealCraftTUI(App):
    """DealCraft MCP Terminal UI."""

    # Shared state for request tracking
    last_request_id: str = "N/A"
    last_latency_ms: float = 0.0

    CSS = """
    Screen {
        background: $surface;
    }

    .panel-title {
        text-style: bold;
        color: $primary;
        padding: 1;
    }

    .help-text {
        color: $secondary;
        text-style: italic;
        padding-bottom: 1;
    }

    #oem-panel {
        border: solid $primary;
        height: 1fr;
        min-width: 30;
    }

    #contract-panel {
        border: solid $secondary;
        height: 1fr;
        min-width: 30;
    }

    #ai-panel {
        border: solid $accent;
        height: 1fr;
        min-width: 40;
    }

    #metrics-panel {
        border: solid $warning;
        height: 1fr;
        min-width: 35;
    }

    #forecast-panel {
        border: solid $success;
        height: 1fr;
        min-width: 50;
    }

    DataTable {
        height: 1fr;
    }

    #guidance-output {
        height: 1fr;
    }

    #add-oem-modal, #add-contract-modal, #edit-contract-modal {
        align: center middle;
        background: $surface;
        border: solid $primary;
        width: 60;
        height: auto;
        padding: 2;
    }

    #modal-title {
        text-style: bold;
        color: $primary;
        padding-bottom: 1;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("?", "help", "Help"),
    ]

    def __init__(self, api_base: str = "http://localhost:8000") -> None:
        """Initialize the TUI app."""
        super().__init__()
        self.api_base = api_base
        self.design = DEALCRAFT_LIGHT

    def compose(self) -> ComposeResult:
        """Compose the main UI layout."""
        yield Header()

        with Horizontal():
            with Container(id="oem-panel"):
                yield OEMPanel(self.api_base)

            with Container(id="contract-panel"):
                yield ContractsPanel(self.api_base)

            with Container(id="forecast-panel"):
                yield ForecastPanel(self.api_base)

            with Container(id="ai-panel"):
                yield AIPanel(self.api_base)

            with Container(id="metrics-panel"):
                yield MetricsPanel(self.api_base)

        footer = Footer()
        yield footer

    def update_request_info(self, request_id: str, latency_ms: float) -> None:
        """Update footer with request tracking info."""
        self.last_request_id = request_id
        self.last_latency_ms = latency_ms
        self.sub_title = f"req_id: {request_id} | latency: {latency_ms:.2f}ms"

    def action_help(self) -> None:
        """Show help notification."""
        help_text = """
        OEM Panel: A=Add, T=Toggle, ↑↓=Threshold, D=Delete, R=Refresh
        Contract Panel: C=Add, S=Toggle, E=Edit, X=Delete, R=Refresh
        Forecast Panel: F=Refresh, Y=Cycle FY, E=Export CSV, O=Export Obsidian
        AI Panel: G=Generate, I=Switch Model
        Metrics Panel: M=Refresh, P=Toggle Auto-refresh
        Global: Q=Quit, ?=Help
        """
        self.notify(help_text, title="Keyboard Shortcuts", severity="information")


def main() -> None:
    """Run the TUI application."""
    app = DealCraftTUI()
    app.title = "DealCraft MCP"
    app.sub_title = "Sales Automation Terminal UI"
    app.run()


if __name__ == "__main__":
    main()
