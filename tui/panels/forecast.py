"""Forecast panel for TUI - Phase 5."""

import time

import httpx
from textual.app import ComposeResult
from textual.widgets import DataTable, Label, Static


class ForecastPanel(Static):
    """Forecast panel displaying opportunity forecasts and win probabilities."""

    def __init__(self, api_base: str) -> None:
        """Initialize Forecast panel."""
        super().__init__()
        self.api_base = api_base
        self.auto_refresh = True
        self.current_fy = "all"  # Can be "all", "25", "26", "27"

    def compose(self) -> ComposeResult:
        """Compose the panel layout."""
        yield Label("📊 Forecast Hub - Opportunity Forecasts", classes="panel-title")
        yield Label("F:Refresh | Y:Cycle FY | E:Export CSV | O:Export Obsidian", classes="help-text")

        yield Label("Loading forecasts...", id="forecast-summary")

        table = DataTable(id="forecast-table")
        table.add_columns("Rank", "Opportunity", "Win %", "FY25", "FY26", "FY27", "OEM", "Partner", "Vehicle")
        yield table

    async def on_mount(self) -> None:
        """Load forecasts when panel mounts."""
        await self.refresh_forecasts()

    async def refresh_forecasts(self) -> None:
        """Refresh forecast data from API."""
        summary_label = self.query_one("#forecast-summary", Label)
        summary_label.update("Refreshing forecasts...")

        try:
            start_time = time.time()

            # Determine which endpoint to call
            if self.current_fy == "all":
                endpoint = f"{self.api_base}/v1/forecast/top?limit=20&sort_by=win_prob"
            else:
                endpoint = f"{self.api_base}/v1/forecast/FY{self.current_fy}"

            async with httpx.AsyncClient() as client:
                response = await client.get(endpoint)
                response.raise_for_status()
                latency_ms = (time.time() - start_time) * 1000
                request_id = response.headers.get("X-Request-ID", "N/A")

                data = response.json()

                # Extract forecasts from response
                if self.current_fy == "all":
                    forecasts = data.get("top_deals", [])
                    total_count = data.get("total_available", 0)
                else:
                    forecasts = data.get("forecasts", [])
                    total_count = data.get("total_opportunities", 0)
                    total_projected = data.get("total_projected", 0)

                # Update summary
                if self.current_fy == "all":
                    summary = f"Viewing: All Forecasts (Top 20) | " f"Total Opportunities: {total_count} | " f"Sorted by: Win Probability"
                else:
                    summary = (
                        f"Viewing: FY{self.current_fy} | "
                        f"Total Opportunities: {total_count} | "
                        f"Total Projected: ${total_projected:,.0f}"
                    )
                summary_label.update(summary)

                # Update table
                table = self.query_one("#forecast-table", DataTable)
                table.clear()

                if not forecasts:
                    table.add_row("", "No forecasts available", "", "", "", "", "", "", "")
                else:
                    for idx, forecast in enumerate(forecasts[:20], 1):
                        # Truncate long names
                        opp_name = forecast.get("opportunity_name", "Unknown")[:30]

                        # Format amounts
                        fy25 = forecast.get("projected_amount_FY25", 0)
                        fy26 = forecast.get("projected_amount_FY26", 0)
                        fy27 = forecast.get("projected_amount_FY27", 0)

                        # Format scores
                        win_prob = forecast.get("win_prob", 0)
                        oem_score = forecast.get("oem_alignment_score", 0)
                        partner_score = forecast.get("partner_fit_score", 0)
                        vehicle_score = forecast.get("contract_vehicle_score", 0)

                        table.add_row(
                            str(idx),
                            opp_name,
                            f"{win_prob:.1f}%",
                            f"${fy25:,.0f}",
                            f"${fy26:,.0f}",
                            f"${fy27:,.0f}",
                            f"{oem_score:.0f}",
                            f"{partner_score:.0f}",
                            f"{vehicle_score:.0f}",
                        )

                # Update request tracking
                self.app.update_request_info(request_id, latency_ms)
                self.app.notify("Forecasts refreshed", severity="success")

        except Exception as e:
            summary_label.update(f"Error loading forecasts: {str(e)}")
            self.app.notify(f"Failed to refresh forecasts: {str(e)}", severity="error")

    async def cycle_fiscal_year(self) -> None:
        """Cycle through fiscal year views."""
        fy_cycle = ["all", "25", "26", "27"]
        current_index = fy_cycle.index(self.current_fy)
        next_index = (current_index + 1) % len(fy_cycle)
        self.current_fy = fy_cycle[next_index]

        fy_display = f"FY{self.current_fy}" if self.current_fy != "all" else "All FYs"
        self.app.notify(f"Viewing: {fy_display}", severity="information")
        await self.refresh_forecasts()

    async def export_csv(self) -> None:
        """Export forecasts to CSV."""
        try:
            fy_param = f"?fiscal_year={self.current_fy}" if self.current_fy != "all" else ""
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_base}/v1/forecast/export/csv{fy_param}")
                response.raise_for_status()

                # Save to exports directory
                from pathlib import Path

                exports_dir = Path("exports")
                exports_dir.mkdir(exist_ok=True)

                filename = f"forecast_FY{self.current_fy}.csv" if self.current_fy != "all" else "forecast_all.csv"
                filepath = exports_dir / filename

                filepath.write_text(response.text)

                self.app.notify(f"Exported to: {filepath}", severity="success")

        except Exception as e:
            self.app.notify(f"Export failed: {str(e)}", severity="error")

    async def export_obsidian(self) -> None:
        """Export forecasts to Obsidian dashboard."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.api_base}/v1/forecast/export/obsidian")
                response.raise_for_status()

                data = response.json()
                path = data.get("path", "Unknown")
                count = data.get("opportunities_exported", 0)

                self.app.notify(f"Exported {count} opportunities to {path}", severity="success")

        except Exception as e:
            self.app.notify(f"Obsidian export failed: {str(e)}", severity="error")

    def toggle_auto_refresh(self) -> None:
        """Toggle auto-refresh mode."""
        self.auto_refresh = not self.auto_refresh
        status = "enabled" if self.auto_refresh else "disabled"
        self.app.notify(f"Auto-refresh {status}", severity="information")

    async def on_key(self, event) -> None:
        """Handle key presses."""
        if event.key == "f":
            await self.refresh_forecasts()
        elif event.key == "y":
            await self.cycle_fiscal_year()
        elif event.key == "e":
            await self.export_csv()
        elif event.key == "o":
            await self.export_obsidian()
        elif event.key == "p":
            self.toggle_auto_refresh()
