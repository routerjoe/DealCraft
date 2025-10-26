from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, status
from pydantic import BaseModel, Field, validator

router = APIRouter()


# --- Models ----------------------------------------------------------------


class OpportunityIn(BaseModel):
    id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    customer: str = Field(..., min_length=1)
    oem: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0)
    stage: str = Field(..., min_length=1)
    close_date: str = Field(..., min_length=1)  # YYYY-MM-DD
    source: str = Field(..., min_length=1)
    tags: Optional[List[str]] = None

    @validator("close_date")
    def _validate_close_date(cls, v: str) -> str:
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v or ""):
            raise ValueError("close_date must be YYYY-MM-DD")
        return v

    @validator("id", "title", "customer", "oem", "stage", "source")
    def _no_empty(cls, v: str) -> str:
        if (v or "").strip() == "":
            raise ValueError("field cannot be empty")
        return v.strip()


# --- Helpers ---------------------------------------------------------------

SAFE_CHARS = re.compile(r"[^a-zA-Z0-9._ -]+")


def safe_filename(s: str) -> str:
    s = SAFE_CHARS.sub("-", s.strip())
    s = re.sub(r"\s+", " ", s)
    return s.replace("/", "-").replace("\\", "-")


def render_markdown(data: OpportunityIn) -> str:
    # Default tags if not provided
    tags = data.tags if data.tags is not None else ["opportunity", "30-hub"]

    # YAML block-style frontmatter
    frontmatter = (
        [
            "---",
            f"id: {data.id}",  # unquoted to satisfy test expectation
            f'title: "{data.title}"',
            f"customer: {data.customer}",
            f'oem: "{data.oem}"',
            f"amount: {data.amount:.2f}",
            f'stage: "{data.stage}"',
            f'close_date: "{data.close_date}"',
            f'source: "{data.source}"',
            "type: opportunity",
            "tags:",
        ]
        + [f"- {t}" for t in tags]
        + [
            "---",
            "",
        ]
    )

    body = [
        f"# {data.title}",
        "",
        "## Summary",
        f"- **Customer:** {data.customer}",
        f"- **OEM:** {data.oem}",
        f"- **Amount:** ${data.amount:,.2f}",
        f"- **Stage:** {data.stage}",
        f"- **Close Date:** {data.close_date}",
        f"- **Source:** {data.source}",
        "",
        "## Notes",
        "- ",
        "",
    ]

    return "\n".join(frontmatter + body)


# --- Endpoint --------------------------------------------------------------


@router.post("/obsidian/opportunity", status_code=status.HTTP_201_CREATED)
def create_opportunity_note(payload: OpportunityIn):
    base_dir = Path("obsidian") / "30 Hub" / "Opportunities"
    base_dir.mkdir(parents=True, exist_ok=True)

    fname = f"{payload.id} - {safe_filename(payload.title)}.md"
    path = base_dir / fname

    content = render_markdown(payload)
    path.write_text(content, encoding="utf-8")

    return {
        "created": True,
        "path": str(path),
        "id": payload.id,
        "title": payload.title,
    }
