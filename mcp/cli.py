#!/usr/bin/env python3
# mcp/cli.py — Extended CLI for Red River MCP
# Adds subcommands used by the TUI: bidboard get, rfq process, rfq analyze, rfq clean-declined, status --json

import argparse, json, sys, time, subprocess, os
from pathlib import Path

# --- Helpers: progress bar, percent, subject clip for TUI-friendly logs ---
def _progress_bar(i: int, n: int, width: int = 24) -> str:
    try:
        if n <= 0:
            return "[" + ("-" * width) + "]"
        filled = int(round((i / n) * width))
        filled = min(max(filled, 0), width)
        return "[" + ("#" * filled) + ("-" * (width - filled)) + "]"
    except Exception:
        return "[" + ("-" * width) + "]"

def _percent(i: int, n: int) -> int:
    try:
        return 0 if n <= 0 else int((i / n) * 100)
    except Exception:
        return 0

def _clip_subject(s: str, max_len: int = 50) -> str:
    try:
        s = str(s or "")
    except Exception:
        s = ""
    return s if len(s) <= max_len else (s[: max_len - 1] + "…")

def _normalize_reco(s: str) -> str:
    """Normalize recommendation strings like 'NO-GO - Auto-Decline' to GO | NO-GO | REVIEW | PENDING."""
    try:
        t = str(s or "").strip().upper()
    except Exception:
        t = ""
    if t.startswith("NO GO") or t.startswith("NO-GO"):
        return "NO-GO"
    if t.startswith("GO"):
        return "GO"
    if t.startswith("REVIEW"):
        return "REVIEW"
    if t == "" or t == "PENDING":
        return "PENDING"
    if "NO-GO" in t or "NO GO" in t:
        return "NO-GO"
    if "GO" in t:
        return "GO"
    return "PENDING"

def current_status() -> dict:
    # Replace these mocks with live signals from your MCP runtime
    return {
        "mcp": {"running": True, "queue": 0, "uptime": "00:42:03"},
        "watchers": {
            "outlook_rfq":   {"state": "online", "last_run": "2025-10-17T12:58:03Z"},
            "fleeting_notes":{"state": "warn",   "last_run": "2025-10-17T12:56:00Z"},
            "radar":         {"state": "online", "last_run": "2025-10-17T12:50:40Z"},
            "govly_sync":    {"state": "off"}
        },
        "providers": {
            "claude": {"online": True, "p95_ms": 390},
            "gpt5":   {"online": True, "p95_ms": 320},
            "gemini": {"online": True, "p95_ms": 340}
        },
        "pipeline": {"emails": 18, "rfqs": 11, "go": 3, "pending": 2},
        "router": "SIMPLE (Claude-only)"
    }

def cmd_status(args):
    data = current_status()
    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print("MCP:", "ONLINE" if data["mcp"]["running"] else "ERROR")
        print("Queue:", data["mcp"]["queue"], "Uptime:", data["mcp"]["uptime"])
        print("Providers: Claude, GPT-5, Gemini")
    return 0

def cmd_bidboard_get(args):
    """
    Get bid board emails from Outlook using the real TypeScript implementation.
    """
    print(f"Retrieving emails from Outlook folder: '{args.folder}'...")

    # Call the real Outlook tool
    result = _call_mcp_tool("outlook_get_bid_board_emails", {
        "limit": 50,
        "unread_only": False,
        "scan_window": 500,
        "newest_first": True
    })

    if not result:
        print("Failed to retrieve emails.")
        return 1

    emails = result.get("emails", []) or []
    count = int(result.get("count", len(emails)) or 0)

    # Explicit progress-friendly message for the TUI
    print(f"{count} emails found")

    # Count emails with attachments and unread status using correct fields
    with_attachments = sum(1 for e in emails if int(e.get("attachments", 0) or 0) > 0)
    unread = sum(1 for e in emails if not bool(e.get("read", False)))

    print(f"  • Emails with attachments: {with_attachments}")
    print(f"  • Unread emails: {unread}")

    return 0

def cmd_rfq_process(args):
    """
    Process RFQ emails with streaming progress for the TUI.
    Prints:
      - "<N> emails found"
      - "Processing i of N — <subject>"
      - "[####------] 50% ✓ RFQ #<id> <status>"
    """
    try:
        limit = getattr(args, "limit", 50) if hasattr(args, "limit") else 50
    except Exception:
        limit = 50

    print("Fetching bid board emails...")
    emails_res = _call_mcp_tool("outlook_get_bid_board_emails", {
        "limit": limit,
        "unread_only": False,
        "scan_window": max(limit * 4, 500),
        "newest_first": True
    }, timeout=300)

    if not emails_res:
        print("Failed to fetch emails from Outlook.")
        return 1

    emails = emails_res.get("emails", []) or []
    total = min(len(emails), limit)
    print(f"{len(emails)} emails found")

    if total == 0:
        print("Nothing to process.")
        return 0

    processed_cnt = 0
    failed_cnt = 0

    for idx, e in enumerate(emails[:total], start=1):
        subj = _clip_subject(e.get("subject", ""))
        print(f"Processing {idx} of {total} — {subj}")

        try:
            res = _call_mcp_tool("rfq_process_email", {"email_id": e.get("id")}, timeout=300)
            if res:
                processed_cnt += 1
                rfq_id = res.get("rfq_id")
                status = res.get("status", "")
                bar = _progress_bar(idx, total)
                pct = _percent(idx, total)
                print(f"{bar} {idx}/{total} {pct}% ✓ RFQ #{rfq_id if rfq_id is not None else ''} {status}")
            else:
                failed_cnt += 1
                bar = _progress_bar(idx, total)
                pct = _percent(idx, total)
                print(f"{bar} {idx}/{total} {pct}% ✗ Failed processing email {e.get('id')}")
        except Exception as ex:
            failed_cnt += 1
            bar = _progress_bar(idx, total)
            pct = _percent(idx, total)
            print(f"{bar} {idx}/{total} {pct}% ✗ Error: {ex}")

    print("✓ RFQ batch processing complete")
    print(f"  • Total emails: {total}")
    print(f"  • Processed: {processed_cnt}")
    print(f"  • Failed: {failed_cnt}")

    return 0

def cmd_rfq_analyze(args):
    """
    Call the real TypeScript MCP tools to analyze RFQs with AI.
    Adds streaming percent/progress output for the TUI.
    """
    use_ai = getattr(args, "use_ai", None)
    ai_provider = getattr(args, "ai_provider", None)

    # Check if we should use AI from env
    if use_ai is None:
        use_ai = os.getenv("RFQ_AI_ENABLED", "true").lower() == "true"

    if ai_provider is None:
        ai_provider = os.getenv("RFQ_AI_DEFAULT_PROVIDER", "claude")

    print(f"[AI Analysis] Provider: {ai_provider if use_ai else 'disabled'}", flush=True)
    print("Analyzing pending RFQs...", flush=True)

    # Call the TypeScript rfq_list_pending tool to get pending RFQs
    pending_rfqs = _call_mcp_tool("rfq_list_pending", {})

    if not pending_rfqs or "rfqs" not in pending_rfqs:
        print("Found 0 pending RFQs", flush=True)
        print("No pending RFQs found.", flush=True)
        return 0

    rfqs = pending_rfqs.get("rfqs", []) or []
    total = len(rfqs)
    print(f"Found {total} pending RFQs", flush=True)

    if total == 0:
        return 0

    analyzed_count = 0
    go_count = 0
    nogo_count = 0
    review_count = 0
    pending_count = 0

    # Analyze each pending RFQ with progress
    for idx, rfq in enumerate(rfqs, start=1):
        rfq_id = rfq.get("id")
        if not rfq_id:
            continue

        subject = _clip_subject(rfq.get("subject", "Unknown"))
        bar = _progress_bar(idx - 1, total)
        pct = _percent(idx - 1, total)
        print(f"{bar} {idx-1}/{total} {pct}%", flush=True)
        print(f"Analyzing {idx} of {total} — RFQ #{rfq_id}: {subject}", flush=True)

        # Call rfq_analyze with AI parameters
        analysis = _call_mcp_tool("rfq_analyze", {
            "rfq_id": rfq_id,
            "use_ai": use_ai,
            "ai_provider": ai_provider if use_ai else None
        })

        if analysis:
            analyzed_count += 1
            # score is an object { score, recommendation } in TS response
            score_obj = analysis.get("score", {}) or {}
            if not isinstance(score_obj, dict):
                score_obj = {}
            # Fallback: some AI-enhanced responses may expose a top-level rule_based_score
            if "score" not in score_obj and "rule_based_score" in analysis:
                try:
                    score_obj["score"] = int(analysis.get("rule_based_score") or 0)
                except Exception:
                    score_obj["score"] = analysis.get("rule_based_score")
            score_val = score_obj.get("score", 0)
            reco = score_obj.get("recommendation", "PENDING")
            
            # Tally recommendation: prefer AI recommendation when enabled/available
            raw_reco = None
            if use_ai and "ai_analysis" in analysis:
                try:
                    raw_reco = analysis["ai_analysis"].get("go_nogo_recommendation")
                except Exception:
                    raw_reco = reco
            else:
                raw_reco = reco

            norm = _normalize_reco(raw_reco)
            if norm == "GO":
                go_count += 1
            elif norm == "NO-GO":
                nogo_count += 1
            elif norm == "REVIEW":
                review_count += 1
            else:
                pending_count += 1
            
            # Per-item completion line with progress bar
            bar_done = _progress_bar(idx, total)
            pct_done = _percent(idx, total)
            # Include AI Strategic Fit when available to distinguish rule vs AI scores
            sf_val = None
            try:
                if "ai_analysis" in analysis:
                    sf_val = analysis["ai_analysis"].get("strategic_fit_score")
            except Exception:
                sf_val = None
            summary_line = f"{bar_done} {idx}/{total} {pct_done}% ✓ Score: {score_val} | Recommendation: {reco}"
            if sf_val is not None:
                summary_line += f" | SF: {sf_val}/100"
                # Also show combined average of rule-based Score and AI Strategic Fit
                avg_val = None
                try:
                    avg_val = int(round((float(score_val or 0) + float(sf_val or 0)) / 2.0))
                except Exception:
                    avg_val = None
                if avg_val is not None:
                    summary_line += f" | AVG: {avg_val}/100"
            print(summary_line, flush=True)
            
            # Show AI analysis if available
            if use_ai and "ai_analysis" in analysis:
                ai = analysis["ai_analysis"]
                rec = ai.get('go_nogo_recommendation')
                conf = ai.get('confidence_level')
                sf_raw = ai.get('strategic_fit_score')
                wp_raw = ai.get('estimated_win_probability')

                # Safe display formatting (avoid "None%" etc.)
                try:
                    sf_disp = f"{int(round(float(sf_raw))):d}/100"
                except Exception:
                    sf_disp = "—"
                try:
                    wp_disp = "—" if wp_raw is None else f"{int(round(float(wp_raw))):d}%"
                except Exception:
                    wp_disp = "—"

                print(f"    AI Recommendation: {rec}", flush=True)
                print(f"    AI Confidence: {conf}", flush=True)
                print(f"    Strategic Fit: {sf_disp}", flush=True)
                print(f"    Win Probability: {wp_disp}", flush=True)

                insights = ai.get('key_insights', [])
                if insights:
                    print(f"    Key Insights:", flush=True)
                    for insight in insights[:2]:  # Show first 2
                        print(f"      • {insight}", flush=True)
        else:
            # Per-item failure still advances progress
            bar_done = _progress_bar(idx, total)
            pct_done = _percent(idx, total)
            print(f"{bar_done} {idx}/{total} {pct_done}% ✗ Analysis failed or no result", flush=True)

    print(f"\n{'='*60}", flush=True)
    print(f"RFQ Analysis Summary", flush=True)
    print(f"Total analyzed: {analyzed_count}", flush=True)
    # Compute pending fallback if none was tallied explicitly
    if pending_count == 0:
        pending_count = max(0, analyzed_count - go_count - nogo_count - review_count)
    print(f"Recommendations: [green]{go_count} GO[/green] | [red]{nogo_count} NO-GO[/red] | [yellow]{review_count} REVIEW[/yellow] | [dim]{pending_count} Pending[/dim]", flush=True)
    if use_ai:
        print(f"AI Provider: {ai_provider}", flush=True)
    print(f"{'='*60}", flush=True)

    return 0

def _call_mcp_tool(tool_name: str, tool_args: dict, timeout: int = 120):
    """
    Call a TypeScript MCP tool via the bridge.mjs script using tsx.
    This directly executes the tool handlers from the TypeScript codebase.
    """
    try:
        # Find paths
        script_dir = Path(__file__).resolve().parent
        project_root = script_dir.parent
        bridge_script = script_dir / "bridge.mjs"
        
        if not bridge_script.exists():
            print(f"Bridge script not found: {bridge_script}", file=sys.stderr)
            return None
        
        # Call the bridge script using npx tsx
        result = subprocess.run(
            ['npx', 'tsx', str(bridge_script), tool_name, json.dumps(tool_args)],
            capture_output=True,
            text=True,
            cwd=str(project_root),
            timeout=timeout
        )
        
        if result.returncode != 0:
            print(f"Tool execution failed: {result.stderr}", file=sys.stderr)
            return None
        
        # Parse JSON output
        output = result.stdout.strip()
        if output:
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                # Not JSON - might be formatted text output
                return {"output": output}
        
        return None
            
    except subprocess.TimeoutExpired:
        print(f"Tool {tool_name} timed out", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error calling MCP tool {tool_name}: {e}", file=sys.stderr)
        return None

def cmd_rfq_list(args):
    """
    List RFQs for the TUI using the real MCP tool (rfq_list_pending).
    Emits JSON compatible with the TUI's expectations.
    """
    status = getattr(args, "status", "all")

    # Pull from TS MCP tool (reads the actual SQLite DB)
    data = _call_mcp_tool("rfq_list_pending", {"status": status})
    rfqs = []
    if data and isinstance(data, dict):
        rfqs = data.get("rfqs") or []

    # Normalize into the TUI table's expected items shape
    items = []
    for r in rfqs:
        try:
            items.append({
                "id": r.get("id"),
                "subject": r.get("subject") or "",
                "customer": r.get("customer") or "",
                "oem": r.get("oem") or "",
                "rfq_type": r.get("rfq_type") or "",
                "rfq_score": r.get("rfq_score") if r.get("rfq_score") is not None else "",
                "rfq_recommendation": r.get("rfq_recommendation") or "",
                "attachments_count": r.get("attachments_count") if r.get("attachments_count") is not None else None,
                "received_date": r.get("received_date") or r.get("processed_date") or r.get("created_at") or "",
            })
        except Exception:
            # Skip malformed rows defensively
            pass

    out = {"status": status, "count": len(items), "items": items}
    if getattr(args, "json", True):
        print(json.dumps(out, indent=2))
    else:
        print(f"RFQs: {len(items)}")
    return 0

def cmd_rfq_clean_declined(args):
    """Cleanup NO-GO RFQs by ID; optionally delete Outlook emails first."""
    ids_str = getattr(args, "ids", "") or ""
    parts = [p.strip() for p in ids_str.split(",") if p.strip()]
    rfq_ids = []
    for p in parts:
        try:
            rfq_ids.append(int(p))
        except Exception:
            pass

    if not rfq_ids:
        print("No valid RFQ IDs provided (use --ids '1,2,3').", flush=True)
        return 1

    res = _call_mcp_tool("rfq_cleanup_declined", {
        "rfq_ids": rfq_ids,
        "delete_from_outlook": bool(getattr(args, "delete_from_outlook", False))
    })
    if not res:
        print("Cleanup failed (no response).", flush=True)
        return 1

    cleaned_count = res.get("cleaned_count", 0)
    print("Cleaned NO-GO RFQs from system.", flush=True)
    print(f"deleted_from_outlook: {'true' if getattr(args, 'delete_from_outlook', False) else 'false'}", flush=True)
    print(f"IDs: {', '.join(map(str, rfq_ids))}", flush=True)
    print(json.dumps(res, indent=2), flush=True)
    return 0

def cmd_rfq_stats(args):
    window = getattr(args, "window", "30d")
    if window == "7d":
        funnel = {"received": 12, "validated": 11, "registered": 10, "quoted": 9, "submitted": 8, "awarded": 6}
        by_day = [
            {"date": "2025-10-12", "received": 2, "awarded": 1},
            {"date": "2025-10-13", "received": 1, "awarded": 0},
            {"date": "2025-10-14", "received": 2, "awarded": 1},
            {"date": "2025-10-15", "received": 2, "awarded": 1},
            {"date": "2025-10-16", "received": 1, "awarded": 1},
            {"date": "2025-10-17", "received": 3, "awarded": 1},
            {"date": "2025-10-18", "received": 1, "awarded": 1},
        ]
    elif window == "90d":
        funnel = {"received": 120, "validated": 112, "registered": 107, "quoted": 101, "submitted": 98, "awarded": 90}
        by_day = []
    else:
        funnel = {"received": 42, "validated": 39, "registered": 37, "quoted": 34, "submitted": 33, "awarded": 31}
        by_day = [
            {"date": "2025-10-12", "received": 2, "awarded": 1},
            {"date": "2025-10-13", "received": 1, "awarded": 0},
            {"date": "2025-10-14", "received": 4, "awarded": 3},
            {"date": "2025-10-15", "received": 5, "awarded": 1},
            {"date": "2025-10-16", "received": 3, "awarded": 2},
            {"date": "2025-10-17", "received": 8, "awarded": 3},
            {"date": "2025-10-18", "received": 3, "awarded": 2},
        ]
    data = {"window": window, "funnel": funnel}
    if by_day:
        data["by_day"] = by_day
    if getattr(args, "json", False):
        print(json.dumps(data, indent=2))
    else:
        print(f"Window: {window}")
        print("Funnel:", ", ".join([f"{k}={v}" for k, v in funnel.items()]))
    return 0

def cmd_analytics_oem(args):
    window = getattr(args, "window", "30d")
    scale = 1.0 if window == "30d" else 0.25 if window == "7d" else 3.0
    base = [
        {"oem": "Cisco", "occurrences": 12, "total": 250000, "avg_competition": 0.42, "status": "High-value mix"},
        {"oem": "Dell", "occurrences": 9, "total": 180000, "avg_competition": 0.38, "status": "Steady"},
        {"oem": "HPE", "occurrences": 7, "total": 140000, "avg_competition": 0.45, "status": "Competitive"},
        {"oem": "Nutanix", "occurrences": 5, "total": 120000, "avg_competition": 0.35, "status": "Growing"},
        {"oem": "Palo Alto", "occurrences": 4, "total": 90000, "avg_competition": 0.30, "status": "Security push"},
    ]
    items = []
    for r in base:
        items.append({
            "oem": r["oem"],
            "occurrences": max(1, int(r["occurrences"] * scale)),
            "total": int(r["total"] * scale),
            "avg_competition": float(r["avg_competition"]),
            "status": r["status"],
        })
    data = {"window": window, "currency": "USD", "items": items}
    if getattr(args, "json", False):
        print(json.dumps(data, indent=2))
    else:
        print(f"OEM analytics {window}: {len(items)} items")
    return 0

def main():
    parser = argparse.ArgumentParser(prog="mcp")
    sub = parser.add_subparsers(dest="cmd")

    p_status = sub.add_parser("status", help="Show MCP status")
    p_status.add_argument("--json", action="store_true", help="Emit JSON")
    p_status.set_defaults(func=cmd_status)

    p_get = sub.add_parser("bidboard", help="Bid board operations")
    get_sub = p_get.add_subparsers(dest="bid_cmd")

    p_get_fetch = get_sub.add_parser("get", help="Retrieve bid board emails")
    p_get_fetch.add_argument("--folder", default="Bid Board", help="Source folder/mailbox")
    p_get_fetch.set_defaults(func=cmd_bidboard_get)

    p_rfq = sub.add_parser("rfq", help="RFQ pipeline")
    rfq_sub = p_rfq.add_subparsers(dest="rfq_cmd")

    p_rfq_proc = rfq_sub.add_parser("process", help="Process RFQs")
    p_rfq_proc.add_argument("--limit", type=int, default=50, help="Maximum emails to process (default: 50)")
    p_rfq_proc.set_defaults(func=cmd_rfq_process)

    p_rfq_an = rfq_sub.add_parser("analyze", help="Analyze RFQs with AI")
    p_rfq_an.add_argument("--use-ai", action="store_true", default=None, help="Enable AI analysis (default: from .env)")
    p_rfq_an.add_argument("--ai-provider", choices=["claude", "openai", "gemini"], help="AI provider (default: from .env)")
    p_rfq_an.set_defaults(func=cmd_rfq_analyze)

    p_rfq_list = rfq_sub.add_parser("list", help="List RFQs for TUI")
    p_rfq_list.add_argument("--status", choices=["pending", "processed", "all"], default="all", help="Filter by status")
    p_rfq_list.add_argument("--json", action="store_true", help="Emit JSON")
    p_rfq_list.set_defaults(func=cmd_rfq_list)

    p_rfq_clean = rfq_sub.add_parser("clean-declined", help="Cleanup declined RFQs")
    p_rfq_clean.add_argument("--ids", required=True, help="Comma-separated RFQ IDs to clean (must be NO-GO)")
    p_rfq_clean.add_argument("--delete-from-outlook", action="store_true", help="Also delete Outlook emails (performed first)")
    p_rfq_clean.set_defaults(func=cmd_rfq_clean_declined)

    # New: rfq stats (funnel)
    p_rfq_stats = rfq_sub.add_parser("stats", help="Aggregate RFQ stats (funnel)")
    p_rfq_stats.add_argument("--window", choices=["7d","30d","90d"], default="30d", help="Time window")
    p_rfq_stats.add_argument("--json", action="store_true", help="Emit JSON")
    p_rfq_stats.set_defaults(func=cmd_rfq_stats)

    # New: analytics group (oem)
    p_analytics = sub.add_parser("analytics", help="Analytics endpoints")
    analytics_sub = p_analytics.add_subparsers(dest="analytics_cmd")
    p_analytics_oem = analytics_sub.add_parser("oem", help="OEM analytics")
    p_analytics_oem.add_argument("--window", choices=["7d","30d","90d"], default="30d", help="Time window")
    p_analytics_oem.add_argument("--json", action="store_true", help="Emit JSON")
    p_analytics_oem.set_defaults(func=cmd_analytics_oem)

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    return args.func(args)

if __name__ == "__main__":
    sys.exit(main())
