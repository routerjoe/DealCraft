from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, status
from pydantic import BaseModel, Field, field_validator

router = APIRouter(prefix="/v1", tags=["obsidian"])


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
    # Base dir for tests / local usage
    base_dir = Path("obsidian/30 Hub/Opportunities")
    base_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{payload.id} - {_sanitize_title_for_filename(payload.title)}.md"
    path = base_dir / filename

    content = render_markdown(payload)
    path.write_text(content, encoding="utf-8")

    return {"path": str(path), "created": True}
