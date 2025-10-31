import json
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path


def _py():
    return shutil.which("python3") or shutil.which("python") or sys.executable


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


def _run(args, timeout=60):
    cmd = [_py(), "-u", _cli()] + args
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    subprocess.check_call(cmd, timeout=timeout, env=env)


def _run_with_output(args, timeout=60):
    """Run command and return Popen object for output streaming."""
    cmd = [_py(), "-u", _cli()] + args
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, env=env)


def get_emails():
    _run(["bidboard", "get"], timeout=30)


def process_rfqs():
    _run(["rfq", "process"], timeout=60)


def analyze_rfqs():
    _run(["rfq", "analyze"], timeout=60)


def get_emails_with_output():
    """Get emails with output streaming."""
    return _run_with_output(["bidboard", "get"], timeout=30)


def process_rfqs_with_output():
    """Process RFQs with output streaming."""
    return _run_with_output(["rfq", "process"], timeout=60)


def analyze_rfqs_with_output():
    """Analyze RFQs with output streaming."""
    return _run_with_output(["rfq", "analyze"], timeout=60)


def get_rfq_email_id(rfq_id: int) -> str | None:
    """Lookup the Outlook email_id for a given RFQ id directly from SQLite."""
    try:
        dbp = _db_path()
        conn = sqlite3.connect(dbp)
        cur = conn.cursor()
        row = cur.execute("SELECT email_id FROM rfqs WHERE id = ?", (int(rfq_id),)).fetchone()
        return str(row[0]) if row and row[0] else None
    except Exception:
        return None


def process_single_email(email_id: str):
    """Process a single Outlook email by id to download attachments and record them in DB."""
    return _call_tool_json("rfq_process_email", {"email_id": email_id}, timeout=300)


def cleanup_rfq_with_output(rfq_id: int, delete_from_outlook: bool = False):
    """Cleanup a single RFQ by id (only allowed for NO-GO); streams CLI output."""
    args = ["rfq", "clean-declined", "--ids", str(rfq_id)]
    if delete_from_outlook:
        args.append("--delete-from-outlook")
    return _run_with_output(args, timeout=60)


# --- MCP bridge helpers for config editing ---
def _call_tool_json(tool_name: str, tool_args: dict, timeout: int = 60):
    """Call an MCP tool directly via bridge and return parsed JSON."""
    import json
    import subprocess
    from pathlib import Path

    script_dir = Path(__file__).resolve().parent.parent.parent / "mcp"
    bridge = script_dir / "bridge.mjs"
    try:
        proc = subprocess.run(
            ["npx", "tsx", str(bridge), tool_name, json.dumps(tool_args)],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except Exception as e:
        return {"success": False, "error": f"bridge_exec_error: {e}"}
    if proc.returncode != 0:
        return {"success": False, "error": proc.stderr.strip() or "bridge_nonzero_exit"}
    try:
        out = proc.stdout.strip()
        return json.loads(out) if out else {"success": False, "error": "empty_output"}
    except Exception as e:
        return {"success": False, "error": f"json_parse_error: {e}", "raw": proc.stdout.strip()}


def _db_path() -> str:
    """Resolve the sqlite file path used by the TS layer."""
    base = os.environ.get("SQLITE_DB_PATH")
    if base:
        return base
    rr = os.environ.get("RED_RIVER_BASE_DIR")
    if rr:
        return f"{rr.rstrip('/')}/data/rfq_tracking.db"
    # Fallback to HOME/RedRiver/data
    home = os.path.expanduser("~")
    return f"{home}/RedRiver/data/rfq_tracking.db"


def _ensure_config_tables(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    # Minimal schemas to support guidance edits
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS config_oem_tracking (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      oem_name TEXT UNIQUE NOT NULL,
      currently_authorized INTEGER DEFAULT 0,
      business_case_threshold INTEGER,
      notes TEXT,
      updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )"""
    )
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS config_contract_vehicles (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      vehicle_name TEXT UNIQUE NOT NULL,
      supported INTEGER DEFAULT 1,
      notes TEXT,
      updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )"""
    )
    conn.commit()


def config_list_oems():
    """Return OEM config from DB (authorization, thresholds, notes). Falls back to direct sqlite if bridge fails."""
    res = _call_tool_json("rfq_config_list_oems", {})
    if isinstance(res, dict) and ("items" in res):
        return res
    # Fallback: read from sqlite directly
    try:
        dbp = _db_path()
        conn = sqlite3.connect(dbp)
        _ensure_config_tables(conn)
        cur = conn.cursor()
        rows = cur.execute(
            "SELECT oem_name, currently_authorized, COALESCE(business_case_threshold, NULL), COALESCE(notes, NULL) FROM config_oem_tracking ORDER BY lower(oem_name)"
        ).fetchall()
        items = []
        for name, auth, thr, notes in rows:
            items.append(
                {
                    "oem_name": name,
                    "authorized": bool(int(auth or 0)),
                    "business_case_threshold": thr,
                    "notes": notes,
                }
            )
        return {"items": items}
    except Exception:
        return {"items": []}


def config_set_oem_authorized(oem_name: str, authorized: bool, business_case_threshold: int | None = None):
    """Update OEM authorization flag (and optional threshold). Uses Node bridge, falls back to sqlite on failure."""
    args = {"oem_name": oem_name, "authorized": bool(authorized)}
    if business_case_threshold is not None:
        args["business_case_threshold"] = int(business_case_threshold)
    res = _call_tool_json("rfq_config_set_oem_authorized", args)
    # If bridge succeeded, it returns a dict (possibly nested 'content'); also respect an explicit success:false
    if (
        isinstance(res, dict)
        and (res.get("success", True) is not False)
        and (("updated" in res) or ("content" in res) or ("oem_name" in res))
    ):
        return res
    # Fallback: direct sqlite update
    try:
        name = (oem_name or "").strip()
        if not name:
            return {"success": False, "error": "empty_oem_name"}
        dbp = _db_path()
        conn = sqlite3.connect(dbp)
        _ensure_config_tables(conn)
        cur = conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO config_oem_tracking (oem_name, currently_authorized) VALUES (?, 0)",
            (name,),
        )
        if business_case_threshold is not None:
            cur.execute(
                "UPDATE config_oem_tracking SET currently_authorized=?, business_case_threshold=?, updated_at=CURRENT_TIMESTAMP WHERE lower(trim(oem_name))=lower(trim(?))",
                (1 if authorized else 0, int(business_case_threshold), name),
            )
        else:
            cur.execute(
                "UPDATE config_oem_tracking SET currently_authorized=?, updated_at=CURRENT_TIMESTAMP WHERE lower(trim(oem_name))=lower(trim(?))",
                (1 if authorized else 0, name),
            )
        conn.commit()
        row = cur.execute(
            "SELECT oem_name, currently_authorized, business_case_threshold FROM config_oem_tracking WHERE lower(trim(oem_name))=lower(trim(?)) LIMIT 1",
            (name,),
        ).fetchone()
        if row:
            return {
                "updated": True,
                "oem_name": row[0],
                "authorized": bool(int(row[1] or 0)),
                "business_case_threshold": row[2],
            }
        return {
            "updated": True,
            "oem_name": name,
            "authorized": bool(authorized),
            "business_case_threshold": business_case_threshold,
        }
    except Exception as e:
        return {"success": False, "error": f"sqlite_update_error: {e}"}


def config_list_contracts():
    """Return supported contract vehicles. Falls back to sqlite when Node bridge fails."""
    res = _call_tool_json("rfq_config_list_contracts", {})
    if isinstance(res, dict) and (res.get("success", True) is not False) and ("items" in res):
        return res
    try:
        dbp = _db_path()
        conn = sqlite3.connect(dbp)
        _ensure_config_tables(conn)
        cur = conn.cursor()
        rows = cur.execute(
            "SELECT vehicle_name, supported, COALESCE(notes, NULL) FROM config_contract_vehicles ORDER BY lower(vehicle_name)"
        ).fetchall()
        items = [{"vehicle_name": n, "supported": bool(int(s or 0)), "notes": notes} for (n, s, notes) in rows]
        return {"items": items}
    except Exception as e:
        return {"success": False, "error": f"sqlite_read_error: {e}", "items": []}


def config_upsert_contract(vehicle_name: str, supported: bool = True, notes: str | None = None):
    """Insert or update a supported contract vehicle row."""
    args = {"vehicle_name": vehicle_name, "supported": bool(supported)}
    if notes:
        args["notes"] = notes
    return _call_tool_json("rfq_config_upsert_contract", args)


def _out(args, timeout=60):
    cmd = [_py(), "-u", _cli()] + args
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    return subprocess.check_output(cmd, timeout=timeout, env=env)


def _run_json(args, timeout=60):
    raw = _out(args, timeout)
    text = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else str(raw)
    try:
        return json.loads(text)
    except Exception:
        return {}


def _fixtures_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures"


def _load_fixture(name: str):
    p = _fixtures_dir() / name
    if p.exists():
        try:
            with p.open("r") as f:
                return json.load(f)
        except Exception:
            return {"items": []}
    return {"items": []}


def list_rfqs(status: str = "all"):
    """
    Returns a list of RFQ dicts suitable for populating the TUI table.
    Uses `mcp rfq list --status=... --json`. Falls back to fixtures on error.
    """
    data = None
    try:
        data = _run_json(["rfq", "list", "--status", status, "--json"], timeout=60)
    except Exception:
        data = None

    if not data:
        data = _load_fixture("rfqs.json")

    items = []
    if isinstance(data, dict) and "items" in data:
        items = data.get("items") or []
    elif isinstance(data, list):
        items = data

    out = []
    for r in items:
        if not isinstance(r, dict):
            continue
        out.append(
            {
                "id": r.get("id", ""),
                "subject": r.get("subject", ""),
                "rfq_type": r.get("rfq_type", ""),
                "rfq_score": r.get("rfq_score", ""),
                "rfq_recommendation": r.get("rfq_recommendation", ""),
            }
        )
    return out


# --- Extended stubs ---
def lom_open(rfq_id: str):
    """Return list of LOM line dicts. Replace with CLI call when available."""
    return [
        {
            "line": 1,
            "part": "C9300-48T-A",
            "desc": "Cisco Catalyst 9300 48-port",
            "qty": 4,
            "unit": "$5,200",
            "ext": "$20,800",
            "oem": "Cisco",
            "contract": "SEWP",
            "taa": "Y",
            "epeat": "Gold",
        },
        {
            "line": 2,
            "part": "SVC-C9300",
            "desc": "SmartNet 8x5xNBD",
            "qty": 4,
            "unit": "$600",
            "ext": "$2,400",
            "oem": "Cisco",
            "contract": "SEWP",
            "taa": "Y",
            "epeat": "-",
        },
    ]


def artifacts_list(rfq_id: str):
    return [
        {
            "name": f"RFQ_{rfq_id}.pdf",
            "type": "pdf",
            "size": 128_000,
            "path": f"./artifacts/RFQ_{rfq_id}.pdf",
        },
        {
            "name": f"SOW_{rfq_id}.docx",
            "type": "docx",
            "size": 256_000,
            "path": f"./artifacts/SOW_{rfq_id}.docx",
        },
    ]


def artifact_open(path: str):
    import os
    import platform
    import subprocess

    sysname = platform.system()
    if sysname == "Darwin":
        subprocess.Popen(["open", path])
    elif sysname == "Windows":
        os.startfile(path)  # type: ignore
    else:
        subprocess.Popen(["xdg-open", path])


def analytics_oem(window: str):
    """
    Load OEM analytics via CLI first (mcp analytics oem --window=... --json),
    falling back to fixtures analytics_oem_{window}.json (and 30d as final).
    Returns rows formatted for the TUI table.
    Input CLI/fixture shape:
      {
        "window": "30d",
        "currency": "USD",
        "items": [
          { "oem": "Cisco", "occurrences": 12, "total": 250000, "avg_competition": 0.42, "status": "High-value mix" }
        ]
      }
    Output (for table):
      [
        { "oem": "Cisco", "occurrences": 12, "total": "$250,000", "avg_competition": "42%", "status": "High-value mix" },
        ...
      ]
    """
    data = None
    try:
        data = _run_json(["analytics", "oem", "--window", window, "--json"], timeout=60)
    except Exception:
        data = None
    if not data or not isinstance(data, dict) or "items" not in data:
        # Fixture fallback(s)
        name = f"analytics_oem_{window}.json"
        data = _load_fixture(name)
        if not data or not isinstance(data, dict) or "items" not in data:
            data = _load_fixture("analytics_oem_30d.json")

    items = data.get("items", []) if isinstance(data, dict) else []
    norm = []
    for r in items if isinstance(items, list) else []:
        try:
            total_num = float(r.get("total", 0) or 0)
        except Exception:
            total_num = 0.0
        avg_comp = r.get("avg_competition", 0)
        try:
            avg_comp = float(avg_comp)
        except Exception:
            avg_comp = 0.0
        norm.append(
            {
                "oem": r.get("oem", ""),
                "occurrences": int(r.get("occurrences", 0) or 0),
                "total": f"${total_num:,.0f}",
                "avg_competition": f"{round(avg_comp * 100):d}%",
                "status": r.get("status", ""),
                "_total_num": total_num,
            }
        )

    # Sort by numeric total desc and limit Top 10
    norm.sort(key=lambda x: x.get("_total_num", 0.0), reverse=True)
    top = norm[:10]
    for r in top:
        r.pop("_total_num", None)
    return top


def rfq_stats(window: str = "30d"):
    """
    Return RFQ funnel stats for the given window.
    CLI-first: mcp rfq stats --window=... --json
    Fallback to fixtures: rfq_stats_{window}.json, then rfq_stats_30d.json.
    Shape:
      {
        "window": "30d",
        "funnel": {
           "received": int, "validated": int, "registered": int,
           "quoted": int, "submitted": int, "awarded": int
        },
        "by_day": [ { "date": "YYYY-MM-DD", "received": int, "awarded": int }, ... ]?
      }
    """
    data = None
    try:
        data = _run_json(["rfq", "stats", "--window", window, "--json"], timeout=60)
    except Exception:
        data = None

    if not data or not isinstance(data, dict) or "funnel" not in data:
        # Fixture fallback(s)
        name = f"rfq_stats_{window}.json"
        data = _load_fixture(name)
        if not data or "funnel" not in data:
            data = _load_fixture("rfq_stats_30d.json")

    if not isinstance(data, dict):
        data = {}

    fun = data.get("funnel", {}) or {}
    funnel = {
        "received": int(fun.get("received", 0) or 0),
        "validated": int(fun.get("validated", 0) or 0),
        "registered": int(fun.get("registered", 0) or 0),
        "quoted": int(fun.get("quoted", 0) or 0),
        "submitted": int(fun.get("submitted", 0) or 0),
        "awarded": int(fun.get("awarded", 0) or 0),
    }
    out = {
        "window": data.get("window", window),
        "funnel": funnel,
    }
    if isinstance(data.get("by_day"), list):
        out["by_day"] = data["by_day"]
    return out
