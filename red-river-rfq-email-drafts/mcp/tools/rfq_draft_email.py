# mcp/tools/rfq_draft_email.py
"""
Run: 
  python mcp/tools/rfq_draft_email.py --json rfq.json
  python mcp/tools/rfq_draft_email.py --sample

Embed as an MCP tool that accepts RFQ fields and creates two Outlook Draft emails via AppleScript.
"""

import os, json, argparse, subprocess, pathlib
from dataclasses import dataclass, asdict
from typing import List, Optional

SCRIPT_PATH = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "create_rfq_drafts.applescript"

@dataclass
class RFQ:
    customer: str
    command: str
    oem: str
    rfq_id: str
    contract_vehicle: str
    due_date: str
    est_value: float
    poc_name: str
    poc_email: str
    folder_path: str
    attachments: Optional[List[str]] = None

def run_osascript_with_json(payload: dict) -> str:
    if not SCRIPT_PATH.exists():
        raise FileNotFoundError(f"AppleScript not found at {SCRIPT_PATH}")
    json_arg = json.dumps(payload, ensure_ascii=False)
    cmd = ["osascript", str(SCRIPT_PATH), json_arg]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"osascript failed: {result.stderr.strip()}")
    return result.stdout.strip()

def create_rfq_drafts(rfq: RFQ) -> str:
    payload = asdict(rfq)
    return run_osascript_with_json(payload)

def _sample_rfq() -> RFQ:
    return RFQ(
        customer="AFCENT",
        command="AFCENT",
        oem="Cisco",
        rfq_id="361235",
        contract_vehicle="SEWP V",
        due_date="2025-10-12",
        est_value=701430.00,
        poc_name="Ms. Preston",
        poc_email="ms.preston@example.mil",
        folder_path="/Users/jonolan/RedRiver/RFQs/361235/",
        attachments=["/Users/jonolan/RedRiver/RFQs/attachments/361235_Cisco_SOW.pdf"],
    )

def main():
    import sys
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", help="Path to RFQ JSON file")
    parser.add_argument("--sample", action="store_true", help="Use a built-in sample payload")
    args = parser.parse_args()

    try:
        if args.sample:
            rfq = _sample_rfq()
            print(create_rfq_drafts(rfq))
            return

        if not args.json:
            parser.error("Provide --json or --sample")
        with open(args.json, "r") as f:
            data = json.load(f)
        rfq = RFQ(**data)
        print(create_rfq_drafts(rfq))
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    print(main() or "")
