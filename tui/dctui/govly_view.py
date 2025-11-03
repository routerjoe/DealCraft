"""
Govly/Radar Opportunity Viewer Screen
Displays opportunities from webhook ingestion (state.json)
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Static

from . import govly_api


class GovlyViewerScreen(Screen):
    """Govly & Radar opportunity viewer screen."""

    INHERIT_BINDINGS = False  # Don't inherit parent app bindings

    BINDINGS = [
        ("escape,q", "app.pop_screen", "Back"),
        ("g", "show_govly", "Govly"),
        ("r", "show_radar", "Radar"),
        ("a", "show_all", "All"),
        ("f", "refresh", "Refresh"),
        ("s", "sync_now", "Sync Now"),
    ]

    CSS = """
    #govly_header {
        height: 5;
        padding: 1;
        border: round cyan;
        margin-bottom: 1;
    }

    #govly_table {
        height: 1fr;
        border: round green;
        margin-bottom: 1;
    }

    #govly_status {
        height: 3;
        border: round yellow;
        padding: 1;
    }
    """

    def __init__(self, initial_filter="all", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_filter = initial_filter  # all, govly, radar

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static(id="govly_header")
        self.table = DataTable(id="govly_table")
        yield self.table
        yield Static(id="govly_status")
        yield Footer()

    async def on_mount(self):
        """Initialize the Govly viewer screen."""
        # Setup table columns
        self.table.add_columns("ID", "Title", "Source", "Amount", "Agency", "Status")

        # Load initial data
        await self.refresh_opportunities()

    async def refresh_opportunities(self):
        """Load and display opportunities based on current filter."""
        # Clear table
        self.table.clear()

        # Get opportunities
        if self.current_filter == "govly":
            opps = govly_api.get_govly_opportunities()
        elif self.current_filter == "radar":
            opps = govly_api.get_radar_opportunities()
        else:  # all
            opps = govly_api.load_opportunities()

        # Update header
        stats = govly_api.get_opportunity_stats()
        header = self.query_one("#govly_header", Static)
        header.update(
            f"[b][cyan]Govly/Radar Opportunities[/cyan][/b]\n"
            f"Total: [b]{stats['total']}[/b]  |  Govly: [b]{stats['govly']}[/b]  |  "
            f"Radar: [b]{stats['radar']}[/b]  |  Triage: [b]{stats['triage']}[/b]\n"
            f"Filter: [b yellow]{self.current_filter.upper()}[/b yellow]  |  "
            f"Showing: [b]{len(opps)}[/b] opportunities"
        )

        # Populate table
        for opp in opps:
            opp_id = opp.get("id", "")
            title = opp.get("title", opp.get("name", "—"))
            source = opp.get("source", "unknown").upper()
            amount = opp.get("estimated_amount") or opp.get("amount") or 0
            amount_str = f"${amount:,.0f}" if amount else "—"
            agency = opp.get("agency", "—") or "—"
            status = "⚠ Triage" if opp.get("triage") else "✓ Processed"

            self.table.add_row(
                str(opp_id)[:25],
                str(title)[:45],
                source,
                amount_str,
                str(agency)[:15],
                status,
            )

        # Update status bar
        status_bar = self.query_one("#govly_status", Static)
        status_bar.update(
            "[b][cyan]Actions:[/cyan][/b] [g] Govly Only  |  [r] Radar Only  |  "
            "[a] All  |  [f] Refresh  |  [s] Sync Now  |  [q] Back\n"
            "[dim]Webhook-ingested and API-synced opportunities from Govly.com and Radar[/dim]"
        )

    async def action_show_govly(self):
        """Filter to show only Govly opportunities."""
        self.current_filter = "govly"
        await self.refresh_opportunities()

    async def action_show_radar(self):
        """Filter to show only Radar opportunities."""
        self.current_filter = "radar"
        await self.refresh_opportunities()

    async def action_show_all(self):
        """Show all opportunities."""
        self.current_filter = "all"
        await self.refresh_opportunities()

    async def action_refresh(self):
        """Refresh opportunity list."""
        await self.refresh_opportunities()

    async def action_sync_now(self):
        """Trigger immediate Govly API sync."""
        try:
            # Import here to avoid circular dependencies
            from mcp.services.govly_sync import get_service

            service = get_service()
            if not service:
                self.app.notify("Govly sync service not running. Start it first.", severity="warning", timeout=3)
                return

            # Show syncing notification
            self.app.notify("Syncing with Govly API...", timeout=2)

            # Trigger sync in background
            import asyncio

            result = await asyncio.to_thread(service.sync_now)

            # Show result
            if result.get("success"):
                new_count = result.get("new_opportunities", 0)
                if new_count > 0:
                    self.app.notify(f"✓ Sync complete: {new_count} new opportunities", severity="information", timeout=5)
                else:
                    self.app.notify("✓ Sync complete: No new opportunities", severity="information", timeout=3)

                # Refresh view to show new opportunities
                await self.refresh_opportunities()
            else:
                error = result.get("error", "Unknown error")
                self.app.notify(f"Sync failed: {error}", severity="error", timeout=5)

        except Exception as e:
            self.app.notify(f"Sync error: {e}", severity="error", timeout=5)
