from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Static, Button, Log
from textual.containers import Container, Vertical, Horizontal
import asyncio
import subprocess
import time
from datetime import datetime

class OperationModal(ModalScreen):
    """Modal that shows MCP operation progress with real-time output."""
    
    CSS = """
    OperationModal {
        align: center middle;
    }
    
    OperationModal > Container {
        width: 90;
        height: 30;
        border: thick $accent;
        background: $surface;
    }
    
    #op_header {
        dock: top;
        height: 3;
        background: $accent;
        padding: 0 1;
        content-align: center middle;
    }
    
    #op_status {
        dock: top;
        height: 3;
        padding: 0 1;
    }
    
    #op_log {
        height: 1fr;
        border: solid $accent-lighten-1;
        margin: 1 1;
    }
    
    #op_footer {
        dock: bottom;
        height: 3;
        align: center middle;
    }
    
    Button {
        margin: 0 1;
    }
    """
    
    def __init__(self, operation_name: str, command_func, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.operation_name = operation_name
        self.command_func = command_func
        self._is_running = False
        self._success = False
        self._start_time = None
        
    def compose(self) -> ComposeResult:
        with Container():
            yield Static(f"[b]{self.operation_name}[/b]", id="op_header")
            yield Static(id="op_status")
            yield Log(id="op_log", auto_scroll=True)
            with Horizontal(id="op_footer"):
                yield Button("Close", id="close_btn", variant="primary", disabled=True)
    
    async def on_mount(self):
        """Start the operation when modal opens."""
        self._log_widget = self.query_one("#op_log", Log)
        self._status_widget = self.query_one("#op_status", Static)
        self._close_btn = self.query_one("#close_btn", Button)
        
        # Start the operation
        await self.run_operation()
    
    async def run_operation(self):
        """Execute the operation and capture output."""
        self._is_running = True
        self._start_time = time.time()
        self.update_status("running", "Operation in progress...")
        
        self._log_widget.write_line(f"[cyan]Starting {self.operation_name}...[/cyan]")
        self._log_widget.write_line(f"[dim]Time: {datetime.now().strftime('%H:%M:%S')}[/dim]")
        self._log_widget.write_line("")
        
        try:
            # Run the command function in a thread to avoid blocking
            result = await asyncio.to_thread(self._execute_command)
            
            if result["success"]:
                elapsed = time.time() - self._start_time
                self._log_widget.write_line("")
                self._log_widget.write_line(f"[green]✓ Operation completed successfully![/green]")
                self._log_widget.write_line(f"[dim]Elapsed time: {elapsed:.2f}s[/dim]")
                self.update_status("success", f"Completed in {elapsed:.1f}s")
                self._success = True
            else:
                self._log_widget.write_line("")
                self._log_widget.write_line(f"[red]✗ Operation failed[/red]")
                self._log_widget.write_line(f"[red]{result['error']}[/red]")
                self.update_status("error", f"Failed: {result['error']}")
                
        except Exception as e:
            self._log_widget.write_line("")
            self._log_widget.write_line(f"[red]✗ Unexpected error: {e}[/red]")
            self.update_status("error", f"Error: {e.__class__.__name__}")
        
        finally:
            self._is_running = False
            self._close_btn.disabled = False
    
    def _execute_command(self):
        """Execute the command and capture output line by line."""
        try:
            # Call the command function which should return a Popen object
            proc = self.command_func()
            
            # Stream output line by line
            if proc and hasattr(proc, 'stdout'):
                for line in iter(proc.stdout.readline, ''):
                    if not line:
                        break
                    # Write to the log widget (will be called from main thread via call_from_thread)
                    self.app.call_from_thread(self._log_widget.write_line, line.rstrip())
                
                # Wait for completion
                returncode = proc.wait()
                
                if returncode == 0:
                    return {"success": True, "output": ""}
                else:
                    return {"success": False, "error": f"Exit code {returncode}"}
            else:
                # Fallback for functions that don't return Popen
                result = proc if proc else None
                return {"success": True, "output": ""}
                
        except subprocess.CalledProcessError as e:
            return {"success": False, "error": f"Exit code {e.returncode}"}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Operation timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def update_status(self, state: str, message: str):
        """Update the status display."""
        if state == "running":
            icon = "[yellow]⟳[/yellow]"
        elif state == "success":
            icon = "[green]✓[/green]"
        elif state == "error":
            icon = "[red]✗[/red]"
        else:
            icon = "[dim]○[/dim]"
        
        self._status_widget.update(f"{icon} {message}")
    
    def on_button_pressed(self, event: Button.Pressed):
        """Handle close button."""
        if event.button.id == "close_btn":
            self.dismiss(self._success)