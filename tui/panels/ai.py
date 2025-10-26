"""AI Guidance panel for TUI."""

import time

import httpx
from textual.app import ComposeResult
from textual.widgets import Label, Static, TextArea


class AIPanel(Static):
    """AI Guidance panel with text display and key bindings."""

    def __init__(self, api_base: str) -> None:
        """Initialize AI panel."""
        super().__init__()
        self.api_base = api_base
        self.current_model = "gpt-5-thinking"
        self.available_models = []

    def compose(self) -> ComposeResult:
        """Compose the panel layout."""
        yield Label("AI Guidance", classes="panel-title")
        yield Label("G:Generate | I:Switch Model", classes="help-text")
        yield Label(f"Current Model: {self.current_model}", id="current-model")

        guidance_area = TextArea(id="guidance-output")
        guidance_area.text = "Press 'G' to generate AI guidance for current RFQ"
        yield guidance_area

    async def on_mount(self) -> None:
        """Load available models when panel mounts."""
        await self.load_models()

    async def load_models(self) -> None:
        """Load available AI models from API."""
        try:
            start_time = time.time()
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_base}/v1/ai/models")
                response.raise_for_status()
                latency_ms = (time.time() - start_time) * 1000
                request_id = response.headers.get("X-Request-ID", "N/A")
                self.app.update_request_info(request_id, latency_ms)

                self.available_models = response.json()

                # Set current model to first one if not set
                if self.current_model not in self.available_models and self.available_models:
                    self.current_model = self.available_models[0]
                    self.query_one("#current-model", Label).update(f"Current Model: {self.current_model}")
        except Exception as e:
            self.app.notify(f"Failed to load models: {str(e)}", severity="error")

    async def generate_guidance(self) -> None:
        """Generate AI guidance using current OEMs, contracts, and model."""
        guidance_area = self.query_one("#guidance-output", TextArea)
        guidance_area.text = "Generating guidance..."

        try:
            # Fetch current OEMs and contracts
            async with httpx.AsyncClient() as client:
                oems_response = await client.get(f"{self.api_base}/v1/oems")
                oems_response.raise_for_status()
                oems = oems_response.json()

                contracts_response = await client.get(f"{self.api_base}/v1/contracts")
                contracts_response.raise_for_status()
                contracts = contracts_response.json()

                # Generate guidance
                payload = {
                    "oems": [{"name": o["name"], "authorized": o["authorized"]} for o in oems],
                    "contracts": [{"name": c["name"], "supported": c["supported"]} for c in contracts],
                    "rfq_text": "Sample RFQ for demonstration",
                    "model": self.current_model,
                }

                start_time = time.time()
                response = await client.post(f"{self.api_base}/v1/ai/guidance", json=payload)
                response.raise_for_status()
                latency_ms = (time.time() - start_time) * 1000
                request_id = response.headers.get("X-Request-ID", "N/A")

                result = response.json()

                # Format guidance output
                output = f"Model: {self.current_model}\n\n"
                output += f"SUMMARY:\n{result['summary']}\n\n"
                output += "RECOMMENDED ACTIONS:\n"
                for action in result["actions"]:
                    output += f"  • {action}\n"
                output += "\nIDENTIFIED RISKS:\n"
                for risk in result["risks"]:
                    output += f"  ⚠ {risk}\n"

                guidance_area.text = output

                # Update request tracking in footer
                self.app.update_request_info(request_id, latency_ms)

                self.app.notify("Guidance generated successfully", severity="success")
        except Exception as e:
            guidance_area.text = f"Error generating guidance: {str(e)}"
            self.app.notify(f"Failed to generate guidance: {str(e)}", severity="error")

    async def switch_model(self) -> None:
        """Switch to next available AI model."""
        if not self.available_models:
            await self.load_models()

        if self.available_models:
            # Find current model index and switch to next
            try:
                current_idx = self.available_models.index(self.current_model)
                next_idx = (current_idx + 1) % len(self.available_models)
                self.current_model = self.available_models[next_idx]
            except ValueError:
                # Current model not in list, use first
                self.current_model = self.available_models[0]

            self.query_one("#current-model", Label).update(f"Current Model: {self.current_model}")
            self.app.notify(f"Switched to {self.current_model}", severity="information")

    async def on_key(self, event) -> None:
        """Handle key presses."""
        if event.key == "g":
            await self.generate_guidance()
        elif event.key == "i":
            await self.switch_model()
