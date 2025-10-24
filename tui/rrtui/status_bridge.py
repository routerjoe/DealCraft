
import os, json, subprocess, shutil, sys
from pathlib import Path

def _py(): return shutil.which("python3") or shutil.which("python") or sys.executable

def _cli():
    env = os.environ.get("RR_MCP_CLI")
    if env:
        return env
    # Search upwards for repo-root mcp/cli.py
    here = Path(__file__).resolve().parent
    cur = here
    for _ in range(5):
        cand = cur / "mcp" / "cli.py"
        if cand.exists():
            return str(cand)
        cur = cur.parent
    # Fallback: relative; may still resolve if CWD is repo root
    return "mcp/cli.py"

def _fixtures_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures"

def _load_fixture(name: str) -> dict:
    p = _fixtures_dir() / name
    if p.exists():
        try:
            with p.open("r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _normalize_status(d: dict) -> dict:
    d = d or {}
    mcp = d.get("mcp", {}) or {}
    watchers = d.get("watchers", {}) or {}
    providers = d.get("providers", {}) or {}
    pipeline = d.get("pipeline", {}) or {}
    router = d.get("router", "SIMPLE Claude-only")
    # watchers
    def _st(name: str):
        v = watchers.get(name, {}) or {}
        s = v.get("state") or "off"
        return {"state": s}
    watchers_n = {
        "outlook_rfq": _st("outlook_rfq"),
        "fleeting_notes": _st("fleeting_notes"),
        "radar": _st("radar"),
        "govly_sync": _st("govly_sync"),
    }
    # providers
    def _prov(name: str):
        v = providers.get(name, {}) or {}
        return {
            "online": bool(v.get("online", False)),
            "p95_ms": v.get("p95_ms", None),
        }
    providers_n = {
        "claude": _prov("claude"),
        "gpt5": _prov("gpt5"),
        "gemini": _prov("gemini"),
    }
    return {
        "mcp": {
            "running": bool(mcp.get("running", False)),
            "uptime": mcp.get("uptime", "—"),
            "queue": int(mcp.get("queue", 0) or 0),
        },
        "watchers": watchers_n,
        "providers": providers_n,
        "pipeline": {
            "emails": int(pipeline.get("emails", 0) or 0),
            "rfqs": int(pipeline.get("rfqs", 0) or 0),
            "go": int(pipeline.get("go", 0) or 0),
            "pending": int(pipeline.get("pending", 0) or 0),
        },
        "router": str(router),
    }

def get_status() -> dict:
    try:
        out = subprocess.check_output([_py(), _cli(), "status", "--json"], timeout=10)
        data = json.loads(out.decode("utf-8"))
        return _normalize_status(data)
    except Exception:
        try:
            data = _load_fixture("status.json")
            return _normalize_status(data)
        except Exception:
            return _normalize_status({})
