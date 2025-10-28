"""Metrics & Latency Monitor panel for TUI."""

import time

import httpx
from textual.app import ComposeResult
from textual.widgets import DataTable, Label, Static


class MetricsPanel(Static):
    """Metrics panel displaying system performance and accuracy tracking."""

    def __init__(self, api_base: str) -> None:
        """Initialize Metrics panel."""
        super().__init__()
        self.api_base = api_base
        self.auto_refresh = True

    def compose(self) -> ComposeResult:
        """Compose the panel layout."""
        yield Label("Metrics & Performance", classes="panel-title")
        yield Label("M:Refresh | P:Toggle Auto-refresh", classes="help-text")

        yield Label("Loading metrics...", id="metrics-summary")

        table = DataTable(id="metrics-table")
        table.add_columns("Metric", "Value")
        yield table

    async def on_mount(self) -> None:
        """Load metrics when panel mounts."""
        await self.refresh_metrics()

    async def refresh_metrics(self) -> None:
        """Refresh metrics data from API."""
        summary_label = self.query_one("#metrics-summary", Label)
        summary_label.update("Refreshing metrics...")

        try:
            start_time = time.time()
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_base}/v1/metrics")
                response.raise_for_status()
                latency_ms = (time.time() - start_time) * 1000
                request_id = response.headers.get("X-Request-ID", "N/A")

                data = response.json()

                # Update summary
                latency = data.get("latency", {})
                accuracy = data.get("accuracy_confusion", {})

                summary = (
                    f"Avg Latency: {latency.get('avg_latency_ms', 0):.1f}ms | "
                    f"P95: {latency.get('p95_latency_ms', 0):.1f}ms | "
                    f"Requests (7d): {data.get('request_volume_last_7d', 0)} | "
                    f"Total: {data.get('request_volume_total', 0)}"
                )
                summary_label.update(summary)

                # Update table
                table = self.query_one("#metrics-table", DataTable)
                table.clear()

                # Latency metrics
                table.add_row("Avg Latency", f"{latency.get('avg_latency_ms', 0):.2f} ms")
                table.add_row("P95 Latency", f"{latency.get('p95_latency_ms', 0):.2f} ms")
                table.add_row("P99 Latency", f"{latency.get('p99_latency_ms', 0):.2f} ms")
                table.add_row("Min Latency", f"{latency.get('min_latency_ms', 0):.2f} ms")
                table.add_row("Max Latency", f"{latency.get('max_latency_ms', 0):.2f} ms")

                # Request volume
                table.add_row("", "")  # Spacer
                table.add_row("Requests (7d)", str(data.get("request_volume_last_7d", 0)))
                table.add_row("Total Requests", str(data.get("request_volume_total", 0)))

                # Accuracy
                table.add_row("", "")  # Spacer
                table.add_row("Accuracy: Correct", str(accuracy.get("correct", 0)))
                table.add_row("Accuracy: Incorrect", str(accuracy.get("incorrect", 0)))
                table.add_row("Accuracy: Unknown", str(accuracy.get("unknown", 0)))

                # Calculate accuracy percentage
                total_accuracy = sum(accuracy.values())
                if total_accuracy > 0:
                    correct_pct = (accuracy.get("correct", 0) / total_accuracy) * 100
                    table.add_row("Accuracy Rate", f"{correct_pct:.1f}%")

                # Top endpoints by latency
                endpoints = data.get("endpoints", {})
                if endpoints:
                    table.add_row("", "")  # Spacer
                    table.add_row("Top Endpoints", "Avg Latency")

                    # Sort by average latency
                    sorted_endpoints = sorted(endpoints.items(), key=lambda x: x[1].get("avg_latency_ms", 0), reverse=True)[:5]  # Top 5

                    for endpoint, stats in sorted_endpoints:
                        endpoint_name = endpoint.split("/")[-1] if "/" in endpoint else endpoint
                        avg_lat = stats.get("avg_latency_ms", 0)
                        count = stats.get("request_count", 0)
                        table.add_row(f"  {endpoint_name}", f"{avg_lat:.1f}ms ({count})")

                # Update request tracking
                self.app.update_request_info(request_id, latency_ms)
                self.app.notify("Metrics refreshed", severity="success")

        except Exception as e:
            summary_label.update(f"Error loading metrics: {str(e)}")
            self.app.notify(f"Failed to refresh metrics: {str(e)}", severity="error")

    def toggle_auto_refresh(self) -> None:
        """Toggle auto-refresh mode."""
        self.auto_refresh = not self.auto_refresh
        status = "enabled" if self.auto_refresh else "disabled"
        self.app.notify(f"Auto-refresh {status}", severity="information")

    async def on_key(self, event) -> None:
        """Handle key presses."""
        if event.key == "m":
            await self.refresh_metrics()
        elif event.key == "p":
            self.toggle_auto_refresh()
