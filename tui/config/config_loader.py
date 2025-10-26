from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

try:
    import yaml  # type: ignore
except Exception:
    yaml = None

DEFAULTS: Dict[str, Any] = {
    "providers": {
        "claude": {
            "enabled": True,
            "model": "claude-3-5-sonnet-latest",
            "p95_warn_ms": 600,
            "p95_error_ms": 1500,
        },
        "gpt5": {
            "enabled": True,
            "model": "gpt-5-thinking",
            "p95_warn_ms": 600,
            "p95_error_ms": 1500,
        },
        "gemini": {
            "enabled": True,
            "model": "gemini-1.5-pro-latest",
            "p95_warn_ms": 600,
            "p95_error_ms": 1500,
        },
    },
    "router": {"order": ["claude", "gpt5", "gemini"], "sticky_provider": False, "max_retries": 2},
    "ui": {
        "theme": "light",
        "refresh_sec": 2,
        "stats_refresh_sec": 10,
        "provider_history_len": 60,
        "show_provider_p95": True,
    },
}


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)  # type: ignore
        else:
            out[k] = v
    return out


def load_settings(settings_path: str | Path = "config/settings.yaml") -> Dict[str, Any]:
    cfg = dict(DEFAULTS)
    p = Path(settings_path)
    if p.exists() and yaml:
        try:
            with p.open("r") as f:
                file_cfg = yaml.safe_load(f) or {}
            cfg = _deep_merge(cfg, file_cfg)
        except Exception:
            pass

    # ENV overrides (keys masked to 'set'/'***' for UI)
    for prov, env_var in (
        ("claude", "ANTHROPIC_API_KEY"),
        ("gpt5", "OPENAI_API_KEY"),
        ("gemini", "GOOGLE_API_KEY"),
    ):
        key = os.getenv(env_var, "")
        cfg["providers"][prov]["api_key"] = "set" if key else "***"

    order_env = os.getenv("MCP_ROUTER_ORDER")
    if order_env:
        cfg["router"]["order"] = [x.strip() for x in order_env.split(",") if x.strip()] or cfg["router"]["order"]

    warn = os.getenv("MCP_P95_WARN_MS")
    err = os.getenv("MCP_P95_ERROR_MS")
    for name in ("claude", "gpt5", "gemini"):
        if warn:
            cfg["providers"][name]["p95_warn_ms"] = int(warn)
        if err:
            cfg["providers"][name]["p95_error_ms"] = int(err)

    return cfg


def save_settings(cfg: Dict[str, Any], settings_path: str | Path = "config/settings.yaml") -> None:
    p = Path(settings_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if yaml:
        with p.open("w") as f:
            yaml.safe_dump(cfg, f, sort_keys=False)
    else:
        with p.open("w") as f:
            f.write(json.dumps(cfg, indent=2))


if __name__ == "__main__":
    from pprint import pprint

    pprint(load_settings())
