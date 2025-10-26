from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, status
from pydantic import BaseModel, Field, field_validator

router = APIRouter(prefix="/v1", tags=["obsidian"])


# ---------------------------
# Federal FY Helper
# ---------------------------
def get_federal_fy(close_date_str: str) -> str:
    """
    Determine Federal Fiscal Year from close_date.

    Federal FY runs from Oct 1 (N-1) to Sep 30 (N).
    For example:
    - 2024-10-01 to 2025-09-30 is FY25
    - 2025-10-01 to 2026-09-30 is FY26

    Args:
        close_date_str: Date string in YYYY-MM-DD format

    Returns:
        FY folder name (e.g., "FY25") or "Triage" if date is invalid
    """
    try:
        date_obj = datetime.strptime(close_date_str, "%Y-%m-%d")
        # If month is Oct-Dec, FY is next calendar year
        # If month is Jan-Sep, FY is current calendar year
        if date_obj.month >= 10:
            fy_year = date_obj.year + 1
        else:
            fy_year = date_obj.year
        return f"FY{fy_year % 100:02d}"  # Last 2 digits (e.g., 2025 → 25)
    except (ValueError, AttributeError):
        return "Triage"


# ---------------------------
# Input Model + Validation
# ---------------------------
class OpportunityIn(BaseModel):
    id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    customer: str = Field(..., min_length=1)
    oem: str = Field(..., min_length=1)
    amount: float
    stage: str = Field(..., min_length=1)
    close_date: str = Field(..., min_length=1)  # YYYY-MM-DD
    source: str = Field(..., min_length=1)
    tags: Optional[List[str]] = None

    @field_validator("close_date")
    @classmethod
    def valid_date(cls, v: str) -> str:
        # Expect strict YYYY-MM-DD (no quotes in output)
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("close_date must be YYYY-MM-DD")
        return v

    @field_validator("id", "title", "customer", "oem", "stage", "source")
    @classmethod
    def non_empty(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("must be a non-empty string")
        return v

    @field_validator("amount")
    @classmethod
    def positive_amount(cls, v: float) -> float:
        if v is None or float(v) <= 0:
            raise ValueError("amount must be positive")
        return v


# ---------------------------
# Rendering helpers
# ---------------------------
def _sanitize_title_for_filename(title: str) -> str:
    # Replace path separators with dashes and tidy spaces
    safe = title.replace("/", "-").replace("\\", "-").strip()
    return " ".join(safe.split())


def render_markdown(data: OpportunityIn) -> str:
    """
    Produce content with YAML frontmatter that matches tests' expectations:
      - Unquoted scalars for: id, customer, oem, amount, stage, close_date, source
      - Block list for tags: `tags:\n- tag1\n- tag2`
      - Include `type: opportunity`
      - Add dashboard-friendly aliases: est_amount, est_close, oems, partners, contract_vehicle
    Markdown body requires: '**Amount:** $<number>.1f' (no commas).
    """
    # Default tags if none provided
    tags = data.tags if data.tags is not None else ["opportunity", "30-hub"]

    # Amount formatting:
    # - YAML: one decimal (e.g., 500000.0)
    # - Markdown: exactly one decimal and *no commas*
    amount_yaml = f"{float(data.amount):.1f}"
    amount_md = f"{float(data.amount):.1f}"

    frontmatter_lines = [
        "---",
        f"id: {data.id}",
        f'title: "{data.title}"',
        f"customer: {data.customer}",
        f"oem: {data.oem}",
        f"amount: {amount_yaml}",
        f"stage: {data.stage}",
        f"close_date: {data.close_date}",
        f"source: {data.source}",
        "type: opportunity",
        # Dashboard-friendly aliases (non-breaking additions)
        f"est_amount: {amount_yaml}",
        f"est_close: {data.close_date}",
        "oems:",
        f"  - {data.oem}",
        "partners: []",
        'contract_vehicle: ""',
        "tags:",
        *[f"- {t}" for t in tags],
        "---",
        "",
    ]

    body_lines = [
        f"# {data.title}",
        "",
        "## Summary",
        f"- **Customer:** {data.customer}",
        f"- **OEM:** {data.oem}",
        f"- **Amount:** ${amount_md}",
        f"- **Stage:** {data.stage}",
        f"- **Expected Close:** {data.close_date}",
        f"- **Source:** {data.source}",
        "",
        "## Notes",
        "- ",
        "",
    ]

    return "\n".join(frontmatter_lines + body_lines)


# ---------------------------
# Endpoint
# ---------------------------
@router.post("/obsidian/opportunity", status_code=status.HTTP_201_CREATED)
def create_opportunity_note(payload: OpportunityIn):
    # Determine FY folder or Triage
    fy_folder = get_federal_fy(payload.close_date)

    # Base dir: obsidian/40 Projects/Opportunities/<FYxx|Triage>
    base_dir = Path("obsidian/40 Projects/Opportunities") / fy_folder
    base_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{payload.id} - {_sanitize_title_for_filename(payload.title)}.md"
    path = base_dir / filename

    content = render_markdown(payload)
    path.write_text(content, encoding="utf-8")

    return {"path": str(path), "created": True}
