"""
IntroMail Management Screen
Handles campaign analysis and intro email generation
"""
import asyncio
import time
from datetime import datetime
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Header, Input, Static

from . import intromail_api


class IntroMailScreen(Screen):
    """IntroMail campaign management screen with analyzer and draft generation."""

    BINDINGS = [
        ("escape,q", "app.pop_screen", "Back"),
        ("a", "analyze_csv", "Analyze CSV"),
        ("g", "generate_drafts", "Generate Drafts"),
        ("s", "select_csv", "Select CSV"),
        ("r", "refresh_campaigns", "Refresh"),
    ]

    CSS = """
    #im_actions {
        height: 8;
        padding: 1;
        border: round cyan;
        margin: 0 0 1 0;
    }

    #im_input_container {
        height: 5;
        border: round cyan;
        margin: 0 0 1 0;
        padding: 1;
    }

    #im_table {
        height: 10;
        border: round cyan;
        margin: 0 0 1 0;
    }

    #im_log_container {
        height: 1fr;
        border: round cyan;
    }

    #im_log {
        padding: 1;
    }

    .input_row {
        height: 1;
        margin: 0 0 1 0;
    }

    Input {
        width: 3fr;
    }

    Button {
        width: 1fr;
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._operation_running = False
        self._log_lines = []
        self._current_csv_path = ""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static(id="im_actions")

        with Vertical(id="im_input_container"):
            with Horizontal(classes="input_row"):
                yield Input(placeholder="CSV file path...", id="csv_input")
                yield Button("Browse", id="browse_btn", variant="primary")
            with Horizontal(classes="input_row"):
                yield Input(placeholder="Subject template (optional)", id="subject_input")

        self.table = DataTable(id="im_table")
        yield self.table

        with VerticalScroll(id="im_log_container"):
            yield Static(id="im_log")

        yield Footer()

    async def on_mount(self):
        """Initialize the IntroMail screen."""
        self._log_widget = self.query_one("#im_log", Static)
        self._actions_widget = self.query_one("#im_actions", Static)
        self._csv_input = self.query_one("#csv_input", Input)
        self._subject_input = self.query_one("#subject_input", Input)

        # Setup table
        self.table.add_columns("Campaign File", "Modified", "Size")

        # Load initial data
        await self.refresh_campaigns()
        self.update_actions_panel()

        self._write_log("[b][cyan]IntroMail Campaign Manager[/cyan][/b]")
        self._write_log("[cyan]Analyze contacts and generate personalized intro emails[/cyan]")
        self._write_log("")

        # Set default paths if available
        sample_csv = intromail_api.get_sample_contacts_path()
        if sample_csv:
            self._csv_input.value = sample_csv
            self._current_csv_path = sample_csv
            self._write_log(f"[dim]📄 Sample CSV loaded: {Path(sample_csv).name}[/dim]")

    def _write_log(self, message: str):
        """Write a line to the log with Rich markup support."""
        self._log_lines.append(message)
        # Keep last 500 lines
        if len(self._log_lines) > 500:
            self._log_lines = self._log_lines[-500:]
        self._log_widget.update("\n".join(self._log_lines))

    def update_actions_panel(self):
        """Update the actions panel."""
        content = [
            "[b][cyan]IntroMail Workflow[/cyan][/b]",
            "",
            "[yellow][a][/yellow] Analyze CSV → Score & prioritize contacts",
            "[yellow][g][/yellow] Generate Drafts → Create Outlook intro emails",
            "[yellow][s][/yellow] Select CSV → Choose campaign file",
            "[yellow][r][/yellow] Refresh → Update campaign list",
            "[yellow][q][/yellow] Back → Return to dashboard",
        ]
        self._actions_widget.update("\n".join(content))

    async def refresh_campaigns(self):
        """Refresh the campaigns table with analyzed CSV files."""
        try:
            campaigns = intromail_api.list_analyzed_csvs()
            self.table.clear()

            for campaign in campaigns:
                # Format size
                size_kb = campaign["size"] / 1024
                size_str = f"{size_kb:.1f} KB"

                # Format modified time
                mod_time = datetime.fromtimestamp(campaign["modified"])
                time_str = mod_time.strftime("%Y-%m-%d %H:%M")

                self.table.add_row(campaign["name"], time_str, size_str)

            if not campaigns:
                self._write_log(
                    "[dim]No analyzed campaigns found yet. Analyze a CSV to get started.[/dim]"
                )

        except Exception as e:
            self._write_log(f"[red]❌ Error loading campaigns: {e}[/red]")

    def _selected_campaign(self) -> str:
        """Get the currently selected campaign file path."""
        try:
            row = self.table.cursor_row
            if row is not None:
                filename = self.table.get_row(row)[0]
                results_dir = intromail_api.get_campaign_results_dir()
                return str(results_dir / filename)
        except Exception:
            pass
        return ""

    async def on_button_pressed(self, event):
        """Handle button presses."""
        if event.button.id == "browse_btn":
            await self.action_select_csv()

    async def on_input_changed(self, event):
        """Handle input changes."""
        if event.input.id == "csv_input":
            self._current_csv_path = event.value

    async def action_select_csv(self):
        """Select a CSV file from the table or use the current input."""
        selected = self._selected_campaign()
        if selected:
            self._csv_input.value = selected
            self._current_csv_path = selected
            self._write_log(f"[green]✓[/green] Selected: {Path(selected).name}")
        else:
            self._write_log(
                "[yellow]⚠️  Please select a campaign from the table or enter a path[/yellow]"
            )

    async def action_analyze_csv(self):
        """Analyze a CSV file and score contacts."""
        if self._operation_running:
            return

        csv_path = self._current_csv_path or self._csv_input.value
        if not csv_path:
            self._write_log("[yellow]⚠️  Please enter or select a CSV file path[/yellow]")
            return

        if not Path(csv_path).exists():
            self._write_log(f"[red]❌ File not found: {csv_path}[/red]")
            return

        await self._run_analyze(csv_path)

    async def action_generate_drafts(self):
        """Generate Outlook draft emails from analyzed CSV."""
        if self._operation_running:
            return

        csv_path = self._current_csv_path or self._csv_input.value
        if not csv_path:
            self._write_log("[yellow]⚠️  Please enter or select a CSV file path[/yellow]")
            return

        if not Path(csv_path).exists():
            self._write_log(f"[red]❌ File not found: {csv_path}[/red]")
            return

        # Get optional subject template
        subject = self._subject_input.value or None

        await self._run_generate(csv_path, subject)

    async def action_refresh_campaigns(self):
        """Refresh the campaign list."""
        await self.refresh_campaigns()
        self._write_log("[green]✓[/green] Campaign list refreshed")

    async def _run_analyze(self, csv_path: str):
        """Run CSV analysis operation."""
        self._operation_running = True
        start_time = time.time()

        self._write_log(f"\n[b][yellow]{'─' * 80}[/yellow][/b]")
        self._write_log("[b][cyan]📊 Analyzing Campaign CSV[/cyan][/b]")
        self._write_log(f"[dim]📄 Input: {Path(csv_path).name}[/dim]")
        self._write_log(f"[dim]🕐 {datetime.now().strftime('%H:%M:%S')}[/dim]\n")

        try:
            self._write_log("Processing contacts...")
            result = await asyncio.to_thread(intromail_api.analyze_csv, csv_path)

            if result.get("success"):
                elapsed = time.time() - start_time
                data = result.get("data", {})

                # Parse the response content
                if "content" in data and len(data["content"]) > 0:
                    import json

                    response_text = data["content"][0].get("text", "{}")
                    response_data = json.loads(response_text)

                    if response_data.get("ok"):
                        summary = response_data.get("summary", {})
                        totals = summary.get("totals", {})
                        output_path = summary.get("output", "")

                        self._write_log(f"\n[green]✅ Analysis Complete ({elapsed:.1f}s)[/green]")
                        self._write_log("[b]Results:[/b]")
                        self._write_log(f"  • Total contacts: {totals.get('rows', 0)}")
                        self._write_log(
                            f"  • High priority: [green]{totals.get('high', 0)}[/green]"
                        )
                        self._write_log(
                            f"  • Medium priority: [yellow]{totals.get('medium', 0)}[/yellow]"
                        )
                        self._write_log(f"  • Low priority: [dim]{totals.get('low', 0)}[/dim]")
                        self._write_log(f"[dim]📁 Output: {Path(output_path).name}[/dim]")

                        # Auto-select the output file
                        self._csv_input.value = output_path
                        self._current_csv_path = output_path
                    else:
                        self._write_log(
                            f"[yellow]⚠️  {response_data.get('message', 'Analysis completed')}[/yellow]"
                        )

                await self.refresh_campaigns()
            else:
                error = result.get("error", "Unknown error")
                self._write_log(f"\n[red]❌ Analysis failed: {error}[/red]")

        except Exception as e:
            self._write_log(f"\n[red]❌ Error: {e}[/red]")

        finally:
            self._operation_running = False

    async def _run_generate(self, csv_path: str, subject_template: str = None):
        """Run draft generation operation."""
        self._operation_running = True
        start_time = time.time()

        self._write_log(f"\n[b][yellow]{'─' * 80}[/yellow][/b]")
        self._write_log("[b][cyan]📧 Generating Intro Email Drafts[/cyan][/b]")
        self._write_log(f"[dim]📄 Input: {Path(csv_path).name}[/dim]")
        if subject_template:
            self._write_log(f"[dim]📝 Subject: {subject_template}[/dim]")
        self._write_log(f"[dim]🕐 {datetime.now().strftime('%H:%M:%S')}[/dim]\n")

        try:
            self._write_log("Creating Outlook drafts...")
            self._write_log("[dim]This may take a moment...[/dim]")

            result = await asyncio.to_thread(
                intromail_api.generate_intros,
                csv_path,
                subject_template=subject_template,
                body_template_path=intromail_api.get_default_template_path(),
            )

            if result.get("success"):
                elapsed = time.time() - start_time
                data = result.get("data", {})

                # Parse the response content
                if "content" in data and len(data["content"]) > 0:
                    import json

                    response_text = data["content"][0].get("text", "{}")
                    response_data = json.loads(response_text)

                    if response_data.get("ok"):
                        message = response_data.get("message", "Completed")
                        self._write_log(
                            f"\n[green]✅ Draft Generation Complete ({elapsed:.1f}s)[/green]"
                        )
                        self._write_log(f"[b]{message}[/b]")
                        self._write_log(
                            "[dim]Check your Outlook Drafts folder for the intro emails[/dim]"
                        )
                    else:
                        self._write_log(
                            f"[yellow]⚠️  {response_data.get('message', 'Generation completed')}[/yellow]"
                        )
            else:
                error = result.get("error", "Unknown error")
                self._write_log(f"\n[red]❌ Generation failed: {error}[/red]")

        except Exception as e:
            self._write_log(f"\n[red]❌ Error: {e}[/red]")

        finally:
            self._operation_running = False
