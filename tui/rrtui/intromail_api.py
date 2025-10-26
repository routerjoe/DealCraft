"""
IntroMail API Bridge - Connect TUI to IntroMail MCP tools
Provides Python interface to IntroMail analyzer and draft generation
"""
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional


def _get_mcp_bridge() -> Path:
    """Get the MCP bridge script path."""
    script_dir = Path(__file__).resolve().parent.parent.parent / "mcp"
    return script_dir / "bridge.mjs"


def _call_mcp_tool(tool_name: str, args: Dict[str, Any], timeout: int = 60) -> Dict[str, Any]:
    """Call an MCP tool via the bridge."""
    bridge = _get_mcp_bridge()

    try:
        result = subprocess.run(
            ["npx", "tsx", str(bridge), tool_name, json.dumps(args)],
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if result.returncode != 0:
            return {"success": False, "error": result.stderr or "Tool execution failed"}

        try:
            response = json.loads(result.stdout.strip())
            return {"success": True, "data": response}
        except json.JSONDecodeError:
            return {"success": False, "error": "Invalid JSON response"}

    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Tool timed out after {timeout}s"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def analyze_csv(
    csv_path: str, output_dir: Optional[str] = None, config_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze a campaign CSV and rank contacts with scores.

    Args:
        csv_path: Path to the input CSV file
        output_dir: Optional output directory (defaults to ~/RedRiver/campaigns/analyzer_results)
        config_path: Optional custom config path

    Returns:
        Dict with success status and analysis results
    """
    args = {"csv_path": csv_path}
    if output_dir:
        args["output_dir"] = output_dir
    if config_path:
        args["config_path"] = config_path

    return _call_mcp_tool("intromail_analyzer", args, timeout=120)


def generate_intros(
    csv_path: str,
    subject_template: Optional[str] = None,
    body_template_path: Optional[str] = None,
    attachment_path: Optional[str] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Generate Outlook draft intro emails from a CSV.

    Args:
        csv_path: Path to the CSV file with contacts
        subject_template: Optional subject template with {{company}} placeholder
        body_template_path: Optional path to body template file
        attachment_path: Optional path to attachment (e.g., linecard)
        dry_run: If True, validate inputs without creating drafts

    Returns:
        Dict with success status and generation results
    """
    args = {"csv_path": csv_path, "dry_run": dry_run}
    if subject_template:
        args["subject_template"] = subject_template
    if body_template_path:
        args["body_template_path"] = body_template_path
    if attachment_path:
        args["attachment_path"] = attachment_path

    return _call_mcp_tool("intromail_intros", args, timeout=300)


def get_campaign_results_dir() -> Path:
    """Get the default campaign results directory."""
    home = Path.home()
    return home / "RedRiver" / "campaigns" / "analyzer_results"


def list_analyzed_csvs() -> list[Dict[str, Any]]:
    """
    List all analyzed CSV files in the results directory.

    Returns:
        List of dicts with file info (name, path, modified_time, size)
    """
    results_dir = get_campaign_results_dir()
    if not results_dir.exists():
        return []

    files = []
    for csv_file in results_dir.glob("*_analyzed.csv"):
        stat = csv_file.stat()
        files.append(
            {
                "name": csv_file.name,
                "path": str(csv_file),
                "modified": stat.st_mtime,
                "size": stat.st_size,
            }
        )

    # Sort by modification time, newest first
    files.sort(key=lambda x: x["modified"], reverse=True)
    return files


def get_sample_contacts_path() -> Optional[str]:
    """Get the sample contacts CSV path if it exists."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    sample_path = (
        repo_root
        / "future features"
        / "IntroMail"
        / "IntroMail Creation"
        / "samples"
        / "sample_contacts.csv"
    )
    return str(sample_path) if sample_path.exists() else None


def get_default_template_path() -> Optional[str]:
    """Get the default email template path if it exists."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    template_path = repo_root / "templates" / "intro_email.txt"
    return str(template_path) if template_path.exists() else None
