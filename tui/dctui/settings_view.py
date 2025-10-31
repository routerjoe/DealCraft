from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Button, Checkbox, Input, Select, Static

try:
    import yaml  # type: ignore
except Exception:
    yaml = None

from config.config_loader import load_settings


class SettingsView(Screen):
    TITLE = "Settings"

    def __init__(self, initial: Dict[str, Any] | None = None) -> None:
        super().__init__()
        self._initial = initial or load_settings()

    def compose(self) -> ComposeResult:
        cfg = self._initial
        yield Static("Settings", id="title")

        # Providers section
        yield Static("Providers", id="providers_title")
        for name, label in [("claude", "Claude"), ("gpt5", "ChatGPT-5"), ("gemini", "Gemini")]:
            prov = cfg.get("providers", {}).get(name, {}) or {}
            row = Horizontal(
                Checkbox(
                    f"{label} enabled",
                    value=bool(prov.get("enabled", True)),
                    id=f"prov-{name}-enabled",
                ),
                Input(value=str(prov.get("model", "")), placeholder="model", id=f"prov-{name}-model"),
                Input(
                    value=str(prov.get("p95_warn_ms", 600)),
                    placeholder="p95 warn ms",
                    id=f"prov-{name}-warn",
                ),
                Input(
                    value=str(prov.get("p95_error_ms", 1500)),
                    placeholder="p95 error ms",
                    id=f"prov-{name}-err",
                ),
                Button(f"Test {label}", id=f"test-{name}"),
                Static("", id=f"test-{name}-result"),
            )
            yield row

        # Router section
        yield Static("Router", id="router_title")
        order_list = cfg.get("router", {}).get("order", ["claude", "gpt5", "gemini"])
        yield Horizontal(
            Input(value=",".join(order_list), placeholder="order (comma-separated)", id="router-order"),
            Checkbox(
                "Sticky provider",
                value=bool(cfg.get("router", {}).get("sticky_provider", False)),
                id="router-sticky",
            ),
            Input(
                value=str(cfg.get("router", {}).get("max_retries", 2)),
                placeholder="max retries",
                id="router-retries",
            ),
        )

        # UI section
        yield Static("UI", id="ui_title")
        theme = cfg.get("ui", {}).get("theme", "light")
        yield Horizontal(
            Select(options=[("Light", "light"), ("Dark", "dark")], value=theme, id="ui-theme"),
            Input(
                value=str(cfg.get("ui", {}).get("refresh_sec", 2)),
                placeholder="refresh sec",
                id="ui-refresh",
            ),
            Input(
                value=str(cfg.get("ui", {}).get("stats_refresh_sec", 10)),
                placeholder="stats refresh sec",
                id="ui-stats-refresh",
            ),
        )

        # Actions
        yield Horizontal(
            Button("Save", id="save", variant="success"),
            Button("Cancel", id="cancel", variant="warning"),
            Static("", id="status"),
        )

    def _int(self, s: str, default: int) -> int:
        try:
            return int(str(s).strip())
        except Exception:
            return default

    def _parse_order(self, s: str) -> List[str]:
        raw = [x.strip() for x in (s or "").split(",")]
        return [x for x in raw if x]

    def _test_connection(self, prov: str) -> str:
        env_map = {
            "claude": "ANTHROPIC_API_KEY",
            "gpt5": "OPENAI_API_KEY",
            "gemini": "GOOGLE_API_KEY",
        }
        env = env_map.get(prov, "")
        if env and os.getenv(env):
            return "OK (key set)"
        return "No key set"

    def _collect(self) -> Dict[str, Any]:
        # Providers
        providers: Dict[str, Any] = {}
        for name in ("claude", "gpt5", "gemini"):
            enabled = self.query_one(f"#prov-{name}-enabled", Checkbox).value
            model = self.query_one(f"#prov-{name}-model", Input).value
            warn = self._int(self.query_one(f"#prov-{name}-warn", Input).value, 600)
            err = self._int(self.query_one(f"#prov-{name}-err", Input).value, 1500)
            providers[name] = {
                "enabled": bool(enabled),
                "model": str(model),
                "p95_warn_ms": int(warn),
                "p95_error_ms": int(err),
            }

        # Router
        order = self._parse_order(self.query_one("#router-order", Input).value)
        sticky = self.query_one("#router-sticky", Checkbox).value
        retries = self._int(self.query_one("#router-retries", Input).value, 2)

        # UI
        theme = self.query_one("#ui-theme", Select).value or "light"
        refresh = self._int(self.query_one("#ui-refresh", Input).value, 2)
        stats_refresh = self._int(self.query_one("#ui-stats-refresh", Input).value, 10)

        # Preserve show_provider_p95 from initial if present
        show_p95 = bool(self._initial.get("ui", {}).get("show_provider_p95", True))

        return {
            "providers": providers,
            "router": {
                "order": order or ["claude", "gpt5", "gemini"],
                "sticky_provider": bool(sticky),
                "max_retries": int(retries),
            },
            "ui": {
                "theme": theme,
                "refresh_sec": int(refresh),
                "stats_refresh_sec": int(stats_refresh),
                "show_provider_p95": show_p95,
            },
        }

    def _save_yaml(self, cfg: Dict[str, Any]) -> None:
        from config.config_loader import save_settings

        base_dir = Path(__file__).resolve().parent.parent
        p = base_dir / "config" / "settings.yaml"
        save_settings(cfg, p)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid.startswith("test-"):
            prov = bid.split("-", 1)[1]
            self.query_one(f"#test-{prov}-result", Static).update(self._test_connection(prov))
            return
        if bid == "cancel":
            self.app.pop_screen()
            return
        if bid == "save":
            cfg = self._collect()
            try:
                self._save_yaml(cfg)
                # If app can apply live, notify it
                if hasattr(self.app, "apply_settings"):
                    try:
                        # type: ignore[attr-defined]
                        self.app.apply_settings(cfg)  # type: ignore
                    except Exception:
                        pass
                self.query_one("#status", Static).update("Saved")
                # Close after a tick
                self.app.pop_screen()
            except Exception as e:
                self.query_one("#status", Static).update(f"Save failed: {e.__class__.__name__}")
