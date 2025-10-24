from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Header, Footer, DataTable
from textual.containers import Container, Vertical, Horizontal, VerticalScroll
from rich.text import Text
from rich.console import Console
from rich.markup import render
import asyncio
import time
import re
from datetime import datetime
from . import rfq_api
from .lom_view import LOMModal
from .artifacts_view import ArtifactsModal
from .guidance_modal import CleanupModal
from .guidance_screen import GuidanceScreen
from .rfq_details_modal import RFQDetailsModal

class RFQManagementScreen(Screen):
    """Comprehensive RFQ Management screen with workflow and RFQ operations."""
    
    # Override parent bindings to show only RFQ-specific actions
    BINDINGS = [
        ("escape,q", "app.pop_screen", "Back"),
        ("enter", "open_details", "Open Details"),
        ("g", "get_emails", "Get Emails"),
        ("p", "process_rfqs", "Process"),
        ("a", "analyze_rfqs", "Analyze"),
        ("i", "gen_internal_email", "Internal Email"),
        ("o", "gen_oem_email", "OEM Email"),
        ("l", "view_lom", "LOM"),
        ("f", "view_artifacts", "Artifacts"),
        ("d", "download_attachments", "Download Attachments"),
        ("e", "edit_guidance", "Guidance"),
        ("x", "cleanup_selected", "Cleanup NO-GO"),
        ("r", "run_workflow", "Full Workflow"),
    ]
    
    CSS = """
    #rfqm_workflow {
        height: 6;
        padding: 1;
        border: round cyan;
        margin: 0 0 1 0;
    }
    
    #rfqm_table {
        height: 12;
        border: round cyan;
        margin: 0 0 1 0;
    }
    
    #rfqm_log_container {
        height: 1fr;
        border: round cyan;
    }
    
    #rfqm_log {
        padding: 1;
    }
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._operation_running = False
        self._log_lines = []
        # Progress state for streaming operations
        self._current_stage = None  # "Get Emails" | "Process RFQs" | "Analyze RFQs" | None
        self._progress_current = 0
        self._progress_total = 0
        self._progress_message = ""
        
        
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static(id="rfqm_workflow")
        self.table = DataTable(id="rfqm_table")
        yield self.table
        with VerticalScroll(id="rfqm_log_container"):
            yield Static(id="rfqm_log")
        yield Footer()
    
    async def on_mount(self):
        """Initialize the RFQ management screen."""
        self._log_widget = self.query_one("#rfqm_log", Static)
        self._workflow_widget = self.query_one("#rfqm_workflow", Static)
        
        # Setup table
        self.table.add_columns("ID", "Opportunity", "Type", "Score", "Reco")
        
        # Load initial data
        await self.refresh_rfqs()
        self.update_workflow_panel()
        
        self._write_log("[b][cyan]RFQ Management: Get, Process, and Analyze[/cyan][/b]")
        self._write_log("[cyan]Ready. Select an action above or press 'r' for full workflow.[/cyan]")
        self._write_log("[dim]🤖 AI-powered analysis uses Claude/ChatGPT/Gemini for GO/NO-GO recommendations.[/dim]")
        self._write_log("")
    
    def _write_log(self, message: str):
        """Write a line to the log with Rich markup support."""
        self._log_lines.append(message)
        # Keep last 500 lines
        if len(self._log_lines) > 500:
            self._log_lines = self._log_lines[-500:]
        self._log_widget.update("\n".join(self._log_lines))
        # Auto-scroll log view to the bottom as new lines stream in
        try:
            container = self.query_one("#rfqm_log_container", VerticalScroll)
            container.scroll_end(animate=False)
        except Exception:
            pass
    
    def update_workflow_panel(self):
        """Update the workflow action panel (shows live progress when available)."""
        content = [
            "[b][cyan]Workflow:[/cyan][/b]  [yellow][g][/yellow] Get  |  [yellow][p][/yellow] Process  |  [yellow][a][/yellow] Analyze (AI)  |  [yellow][r][/yellow] Full Workflow",
            "[dim]Get = metadata only (no downloads). Use 'd' on a selected RFQ to download now, or 'p' Process to download for all.[/dim]",
            "",
        ]
        # Insert progress line if an operation is running
        if self._current_stage:
            if self._progress_total > 0:
                pct = int((self._progress_current / max(1, self._progress_total)) * 100)
                bar = self._mk_progress_bar(self._progress_current, self._progress_total, 24)
                msg = f"[b]{self._current_stage}[/b]  {bar} {self._progress_current}/{self._progress_total} {pct}%"
            else:
                # For "Get Emails", we may only know the found count
                msg = f"[b]{self._current_stage}[/b]  {self._progress_message}".strip()
            content.append(msg)
            content.append("")
        content.append("[b][cyan]Actions:[/cyan][/b]  [yellow][i][/yellow] Internal Email  |  [yellow][o][/yellow] OEM Email  |  [yellow][l][/yellow] LOM  |  [yellow][f][/yellow] Artifacts  |  [yellow][d][/yellow] Download Attachments  |  [yellow][e][/yellow] Guidance  |  [yellow][x][/yellow] Cleanup  |  [yellow][q][/yellow] Back")
        self._workflow_widget.update("\n".join(content))
    
    # Progress helpers
    def _mk_progress_bar(self, i: int, n: int, width: int = 24) -> str:
        if n <= 0:
            return "[" + "-" * width + "]"
        filled = int((i / n) * width)
        filled = min(max(filled, 0), width)
        return "[" + "#" * filled + "-" * (width - filled) + "]"

    def _set_stage(self, name: str):
        self._current_stage = name
        self._progress_current = 0
        self._progress_total = 0
        self._progress_message = ""
        self.update_workflow_panel()

    def _clear_progress(self):
        self._current_stage = None
        self._progress_current = 0
        self._progress_total = 0
        self._progress_message = ""
        self.update_workflow_panel()

    def _update_progress_from_line(self, line: str):
        """Parse CLI output lines to update progress in the workflow panel."""
        try:
            s = (line or "").strip()
        except Exception:
            s = ""
        if not s:
            return

        # Detect "N emails found"
        m = re.match(r"^(\d+)\s+emails\s+found\b", s, re.IGNORECASE)
        if m:
            total = int(m.group(1))
            self._progress_total = total
            self._progress_current = 0
            self._progress_message = f"{total} emails found"
            # For Get stage, no per-item steps; still show count
            self.update_workflow_panel()
            return

        # Detect "Found N pending RFQs" (Analyze stage)
        m = re.match(r"^Found\s+(\d+)\s+pending\s+RFQs\b", s, re.IGNORECASE)
        if m:
            total = int(m.group(1))
            self._progress_total = total
            self._progress_current = 0
            # No message needed; header will render bar 0/N 0%
            self.update_workflow_panel()
            return

        # Detect "Processing i of N — ..."
        m = re.match(r"^Processing\s+(\d+)\s+of\s+(\d+)\b", s, re.IGNORECASE)
        if m:
            cur = int(m.group(1)); total = int(m.group(2))
            self._progress_current = cur
            self._progress_total = total
            self.update_workflow_panel()
            return

        # Detect "Analyzing pending RFQs..."
        if re.match(r"^Analyzing\s+pending\s+RFQs\.\.\.", s, re.IGNORECASE):
            self._progress_message = "Analyzing pending RFQs..."
            self.update_workflow_panel()
            return

        # Detect "No pending RFQs found."
        if re.match(r"^No\s+pending\s+RFQs\s+found\.", s, re.IGNORECASE):
            self._progress_total = 0
            self._progress_current = 0
            self._progress_message = "No pending RFQs found."
            self.update_workflow_panel()
            return

        # Detect "Analyzing i of N — ..."
        m = re.match(r"^Analyzing\s+(\d+)\s+of\s+(\d+)\b", s, re.IGNORECASE)
        if m:
            cur = int(m.group(1)); total = int(m.group(2))
            self._progress_current = cur
            self._progress_total = total
            self.update_workflow_panel()
            return

        # Detect progress bar lines: "[####------] i/N PCT%"
        m = re.match(r"^\[[#\-]+\]\s+(\d+)\/(\d+)\s+(\d+)%", s)
        if m:
            cur = int(m.group(1)); total = int(m.group(2))
            self._progress_current = cur
            self._progress_total = total
            self.update_workflow_panel()
            return

    async def refresh_rfqs(self):
        """Refresh the RFQ table."""
        try:
            rfqs = rfq_api.list_rfqs("all")
            self.table.clear()
            for r in rfqs:
                self.table.add_row(
                    str(r.get("id", "")),
                    str(r.get("subject", ""))[:40],  # Truncate long subjects
                    str(r.get("rfq_type", "")),
                    str(r.get("rfq_score", "")),
                    str(r.get("rfq_recommendation", "")),
                )
        except Exception as e:
            self._write_log(f"[red]❌ Error refreshing RFQs: {e}[/red]")
    
    def _selected_rfq_id(self) -> str:
        """Get the currently selected RFQ ID from table."""
        try:
            row = self.table.cursor_row
            if row is not None:
                return str(self.table.get_row(row)[0])
        except Exception:
            pass
        return "0"
    
    async def action_get_emails(self):
        """Get emails from bid board."""
        if self._operation_running:
            return
        await self._run_operation("Get Emails", rfq_api.get_emails_with_output)
    
    async def action_process_rfqs(self):
        """Process RFQs."""
        if self._operation_running:
            return
        await self._run_operation("Process RFQs", rfq_api.process_rfqs_with_output)
    
    async def action_analyze_rfqs(self):
        """Analyze RFQs."""
        if self._operation_running:
            return
        await self._run_operation("Analyze RFQs", rfq_api.analyze_rfqs_with_output)
    
    async def action_download_attachments(self):
        """Download attachments for the selected RFQ now (single email re-process)."""
        if self._operation_running:
            return
        rfq_id = self._selected_rfq_id()
        if rfq_id == "0":
            self._write_log("[yellow]⚠️  Please select an RFQ from the table first.[/yellow]")
            return
        try:
            self._write_log(f"\n[b][cyan]📎 Downloading attachments for RFQ #{rfq_id}[/cyan][/b]")
            # Resolve email_id directly from SQLite for reliability
            email_id = rfq_api.get_rfq_email_id(int(rfq_id))
            if not email_id:
                self._write_log("[red]❌ Unable to resolve email_id for selected RFQ[/red]")
                return
            # Process just this email (idempotent; inserts any missing attachments)
            res = await asyncio.to_thread(rfq_api.process_single_email, email_id)
            if isinstance(res, dict):
                att = res.get("attachments", []) or []
                self._write_log(f"[green]✅ Downloaded {len(att)} attachment(s) into {res.get('email_id','')}[/green]")
            else:
                self._write_log("[green]✅ Attachments downloaded[/green]")
            await self.refresh_rfqs()
        except Exception as e:
            self._write_log(f"[red]❌ Download failed: {e}[/red]")
    
    async def action_run_workflow(self):
        """Run the complete workflow: Get → Process → Analyze."""
        if self._operation_running:
            return
        await self._run_full_workflow()
    
    async def action_view_lom(self):
        """View LOM for selected RFQ."""
        rfq_id = self._selected_rfq_id()
        if rfq_id == "0":
            self._write_log("[yellow]⚠️  Please select an RFQ from the table first.[/yellow]")
            return
        self.app.push_screen(LOMModal(rfq_id))
    
    async def action_gen_internal_email(self):
        """Generate internal RFQ email draft."""
        rfq_id = self._selected_rfq_id()
        if rfq_id == "0":
            self._write_log("[yellow]⚠️  Please select an RFQ from the table first.[/yellow]")
            return
        
        self._write_log(f"\n[b][cyan]📧 Generating Internal Email for RFQ #{rfq_id}[/cyan][/b]")
        
        try:
            # Call the create_rfq_drafts tool
            result = await asyncio.to_thread(
                self._call_tool,
                "create_rfq_drafts",
                {"rfq_id": int(rfq_id)}
            )
            
            if result and result.get("success"):
                self._write_log(f"[green]✅ Internal email draft created in Outlook[/green]")
                self._write_log(f"[dim]Subject: {result.get('subject', 'N/A')}[/dim]")
            else:
                error = result.get("error", "Unknown error") if result else "Failed to generate"
                self._write_log(f"[red]❌ Failed: {error}[/red]")
                
        except Exception as e:
            self._write_log(f"[red]❌ Error generating internal email: {e}[/red]")
    
    async def action_gen_oem_email(self):
        """Generate OEM registration email draft."""
        rfq_id = self._selected_rfq_id()
        if rfq_id == "0":
            self._write_log("[yellow]⚠️  Please select an RFQ from the table first.[/yellow]")
            return
        
        self._write_log(f"\n[b][cyan]📧 Generating OEM Registration Email for RFQ #{rfq_id}[/cyan][/b]")
        
        try:
            # Call the rfq_draft_oem_registration tool
            result = await asyncio.to_thread(
                self._call_tool,
                "rfq_draft_oem_registration",
                {"rfq_id": int(rfq_id)}
            )
            
            if result and result.get("success"):
                self._write_log(f"[green]✅ OEM registration email draft created in Outlook[/green]")
                self._write_log(f"[dim]OEM: {result.get('oem', 'N/A')}[/dim]")
            else:
                error = result.get("error", "Unknown error") if result else "Failed to generate"
                self._write_log(f"[red]❌ Failed: {error}[/red]")
                
        except Exception as e:
            self._write_log(f"[red]❌ Error generating OEM email: {e}[/red]")
    
    async def action_view_artifacts(self):
        """View artifacts for selected RFQ."""
        rfq_id = self._selected_rfq_id()
        if rfq_id == "0":
            self._write_log("[yellow]⚠️  Please select an RFQ from the table first.[/yellow]")
            return
        self.app.push_screen(ArtifactsModal(rfq_id))

    async def action_open_details(self):
        """Open RFQ Details modal for selected RFQ."""
        rfq_id = self._selected_rfq_id()
        if rfq_id == "0":
            self._write_log("[yellow]⚠️  Please select an RFQ from the table first.[/yellow]")
            return
        try:
            self.app.push_screen(RFQDetailsModal(int(rfq_id)))
        except Exception as e:
            self._write_log(f"[red]❌ Failed to open Details: {e}[/red]")

    async def action_edit_guidance(self):
        """Open Guidance editor (OEM authorization + supported contracts)."""
        try:
            self.app.push_screen(GuidanceScreen())
        except Exception as e:
            self._write_log(f"[red]❌ Failed to open Guidance: {e}[/red]")

    async def action_cleanup_selected(self):
        """Cleanup selected RFQ (backend enforces NO-GO only) with confirmation modal."""
        rfq_id = self._selected_rfq_id()
        if rfq_id == "0":
            self._write_log("[yellow]⚠️  Please select an RFQ from the table first.[/yellow]")
            return
        try:
            self.app.push_screen(CleanupModal(int(rfq_id)))
        except Exception as e:
            self._write_log(f"[red]❌ Cleanup modal failed: {e}[/red]")
    
    def _call_tool(self, tool_name: str, tool_args: dict):
        """Call an MCP tool via the bridge."""
        import subprocess, json
        from pathlib import Path
        
        script_dir = Path(__file__).resolve().parent.parent.parent / "mcp"
        bridge = script_dir / "bridge.mjs"
        
        result = subprocess.run(
            ['npx', 'tsx', str(bridge), tool_name, json.dumps(tool_args)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            return {"success": False, "error": result.stderr}
        
        try:
            return json.loads(result.stdout.strip())
        except:
            return {"success": False, "error": "Invalid response"}
    
    
    async def _run_operation(self, name: str, func):
        """Run a single operation."""
        self._operation_running = True
        start_time = time.time()

        # Update header with stage
        self._set_stage(name)

        self._write_log(f"\n[b][yellow]{'─' * 80}[/yellow][/b]")
        self._write_log(f"[b][cyan]📋 {name}[/cyan][/b]")
        self._write_log(f"[dim]🕐 {datetime.now().strftime('%H:%M:%S')}[/dim]\n")

        try:
            result = await asyncio.to_thread(self._execute_command, func)

            if result["success"]:
                elapsed = time.time() - start_time
                self._write_log(f"\n[green]✅ {name} completed ({elapsed:.1f}s)[/green]")
                await self.refresh_rfqs()
            else:
                self._write_log(f"\n[red]❌ {name} failed: {result['error']}[/red]")

        except Exception as e:
            self._write_log(f"\n[red]❌ Error: {e}[/red]")

        finally:
            # Clear progress display
            self._clear_progress()
            self._operation_running = False
    
    async def _run_full_workflow(self):
        """Run the complete Get → Process → Analyze workflow."""
        self._operation_running = True
        start_time = time.time()

        self._write_log(f"\n[b][cyan]{'═' * 80}[/cyan][/b]")
        self._write_log(f"[b][cyan]🚀 FULL RFQ WORKFLOW[/cyan][/b]")
        self._write_log(f"[dim]🕐 {datetime.now().strftime('%H:%M:%S')}[/dim]")
        self._write_log(f"[b][cyan]{'═' * 80}[/cyan][/b]\n")

        steps = [
            ("Get Emails", rfq_api.get_emails_with_output),
            ("Process RFQs", rfq_api.process_rfqs_with_output),
            ("Analyze RFQs", rfq_api.analyze_rfqs_with_output)
        ]

        all_success = True
        for step_idx, (step_name, step_func) in enumerate(steps, 1):
            self._write_log(f"[b][yellow]{'─' * 80}[/yellow][/b]")
            self._write_log(f"[b][cyan]📍 Step {step_idx}/3: {step_name}[/cyan][/b]")
            self._write_log(f"[dim]🕐 {datetime.now().strftime('%H:%M:%S')}[/dim]\n")

            # Set stage for header progress
            self._set_stage(step_name)
            
            try:
                result = await asyncio.to_thread(self._execute_command, step_func)
                
                if result["success"]:
                    self._write_log(f"\n[green]✅ {step_name} completed[/green]\n")
                else:
                    self._write_log(f"\n[red]❌ {step_name} failed: {result['error']}[/red]\n")
                    all_success = False
                    
            except Exception as e:
                self._write_log(f"\n[red]❌ {step_name} error: {e}[/red]\n")
                all_success = False
            finally:
                self._clear_progress()

        # Workflow complete
        elapsed = time.time() - start_time
        self._write_log(f"[b][cyan]{'═' * 80}[/cyan][/b]")

        if all_success:
            self._write_log(f"[b][green]✅ Full RFQ Workflow Completed Successfully![/green][/b]")
        else:
            self._write_log(f"[b][yellow]⚠️  Workflow Completed with Errors[/yellow][/b]")

        self._write_log(f"[dim]⏱️  Total time: {elapsed:.2f}s[/dim]\n")

        # Refresh RFQ table
        await self.refresh_rfqs()

        self._operation_running = False
    
    def _execute_command(self, func):
        """Execute a command and capture output."""
        try:
            proc = func()
            
            if proc and hasattr(proc, 'stdout'):
                for line in iter(proc.stdout.readline, ''):
                    if not line:
                        break
                    ln = line.rstrip()
                    self.app.call_from_thread(self._write_log, ln)
                    self.app.call_from_thread(self._update_progress_from_line, ln)
                
                returncode = proc.wait()
                
                if returncode == 0:
                    return {"success": True}
                else:
                    return {"success": False, "error": f"Exit code {returncode}"}
            else:
                return {"success": True}
                
        except Exception as e:
            return {"success": False, "error": str(e)}