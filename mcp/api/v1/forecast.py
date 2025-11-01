"""
Forecast Hub Engine - Phase 5
Generates AI-driven forecasts with intelligent scoring for opportunities.
Features:
- Multi-factor opportunity scoring (OEM alignment, partner fit, etc.)
- Confidence intervals
- FY-based forecasting (FY25/26/27)
- Export to Obsidian and CSV
- Win probability modeling
"""

import csv
import json
import statistics
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Header, HTTPException, Response
from pydantic import BaseModel, Field

from mcp.core.scoring import scorer

router = APIRouter(prefix="/v1/forecast", tags=["forecast"])

# Paths
FORECAST_FILE = Path("data/forecast.json")
STATE_FILE = Path("data/state.json")
OBSIDIAN_BASE = Path("obsidian/40 Projects/Opportunities")


# ============================================================================
# Models
# ============================================================================


class ForecastRequest(BaseModel):
    """Request to generate forecasts for opportunities."""

    opportunity_ids: Optional[List[str]] = Field(default=None, description="Specific opportunity IDs to forecast. If None, forecast all.")
    model: str = Field(default="gpt-5-thinking", description="AI model to use for forecasting")
    confidence_threshold: int = Field(default=50, description="Minimum confidence score (0-100) to include in summary")


class ForecastData(BaseModel):
    """Forecast data for a single opportunity with intelligent scoring."""

    model_config = {"populate_by_name": True}  # Allow both field name and alias

    opportunity_id: str
    opportunity_name: str
    projected_amount_FY25: float
    projected_amount_FY26: float
    projected_amount_FY27: float
    confidence_score: int  # 0-100 (legacy field)
    reasoning: str
    generated_at: str  # ISO 8601
    llm_model: str = Field(alias="model_used", description="AI model used for forecast generation")

    # Phase 5: Intelligent Scoring Fields
    win_prob: float = Field(default=0.0, description="Win probability (0-100)")
    score_raw: float = Field(default=0.0, description="Raw composite score (0-100)")
    score_scaled: float = Field(default=0.0, description="Scaled score (0-100)")
    oem_alignment_score: float = Field(default=0.0, description="OEM strategic alignment")
    partner_fit_score: float = Field(default=0.0, description="Partner ecosystem fit")
    contract_vehicle_score: float = Field(default=0.0, description="Contract vehicle priority")
    govly_relevance_score: float = Field(default=0.0, description="Govly/federal relevance")

    # Confidence interval
    confidence_interval: Optional[Dict[str, float]] = Field(default=None, description="Statistical confidence bounds")


class ForecastSummary(BaseModel):
    """Summary of all forecasts."""

    total_opportunities: int
    total_projected_FY25: float
    total_projected_FY26: float
    total_projected_FY27: float
    avg_confidence: float
    high_confidence_count: int  # >= 75
    medium_confidence_count: int  # 50-74
    low_confidence_count: int  # < 50
    last_updated: str


# ============================================================================
# Forecast Persistence
# ============================================================================


def load_forecasts() -> Dict[str, ForecastData]:
    """Load forecasts from data/forecast.json."""
    if not FORECAST_FILE.exists():
        return {}
    try:
        with open(FORECAST_FILE, "r") as f:
            data = json.load(f)
            return {k: ForecastData(**v) for k, v in data.items()}
    except (json.JSONDecodeError, ValueError):
        return {}


def save_forecasts(forecasts: Dict[str, ForecastData]) -> None:
    """Save forecasts to data/forecast.json with atomic write."""
    FORECAST_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp_file = FORECAST_FILE.with_suffix(".tmp")
    try:
        with open(temp_file, "w") as f:
            json.dump({k: v.model_dump(by_alias=True) for k, v in forecasts.items()}, f, indent=2, default=str)
        temp_file.replace(FORECAST_FILE)
    except Exception as e:
        if temp_file.exists():
            temp_file.unlink()
        raise e


def load_state() -> Dict[str, Any]:
    """Load state from data/state.json."""
    if not STATE_FILE.exists():
        return {"opportunities": [], "actions": []}
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        return {"opportunities": [], "actions": []}


def get_opportunities() -> List[Dict[str, Any]]:
    """Get all opportunities from state.json."""
    state = load_state()
    return state.get("opportunities", [])


# ============================================================================
# Forecast Generation
# ============================================================================


def generate_forecast_for_opportunity(opp: Dict[str, Any], model: str = "gpt-5-thinking") -> ForecastData:
    """
    Generate forecast for a single opportunity with intelligent scoring.
    Phase 5: Integrates multi-factor scoring engine.
    """
    opp_id = opp.get("id", "unknown")
    opp_name = opp.get("name", opp.get("title", "Unknown Opportunity"))
    current_amount = float(opp.get("amount", opp.get("est_amount", 0)))
    close_date_str = opp.get("close_date", opp.get("est_close", ""))
    stage = opp.get("stage", "Unknown")

    # Parse close date to determine FY
    try:
        close_date = datetime.fromisoformat(close_date_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        from datetime import timezone

        close_date = datetime.now(timezone.utc)

    # FY distribution logic
    from datetime import timezone

    fy26_start = datetime(2025, 10, 1, tzinfo=timezone.utc)
    fy27_start = datetime(2026, 10, 1, tzinfo=timezone.utc)

    if close_date < fy26_start:
        fy25_amount = current_amount * 0.8
        fy26_amount = current_amount * 0.15
        fy27_amount = current_amount * 0.05
        confidence = 85
    elif close_date < fy27_start:
        fy25_amount = current_amount * 0.1
        fy26_amount = current_amount * 0.75
        fy27_amount = current_amount * 0.15
        confidence = 75
    else:
        fy25_amount = current_amount * 0.05
        fy26_amount = current_amount * 0.2
        fy27_amount = current_amount * 0.75
        confidence = 65

    # Phase 9: Calculate enhanced intelligent scores with reasoning
    scores = scorer.calculate_composite_score(opp, include_reasoning=True)
    confidence_interval = scorer.calculate_confidence_interval(scores["win_prob"], current_amount, stage)

    # Build detailed reasoning
    reasoning_parts = [f"Forecast based on close_date ({close_date_str}). Amount: ${current_amount:,.2f}."]

    # Add score reasoning if available
    if "score_reasoning" in scores:
        reasoning_parts.append("Scoring breakdown:")
        reasoning_parts.extend(scores["score_reasoning"])

    reasoning_parts.append(f"Distributed across FY25-27 based on fiscal alignment (Stage: {stage}).")

    reasoning = " ".join(reasoning_parts)

    return ForecastData(
        opportunity_id=opp_id,
        opportunity_name=opp_name,
        projected_amount_FY25=round(fy25_amount, 2),
        projected_amount_FY26=round(fy26_amount, 2),
        projected_amount_FY27=round(fy27_amount, 2),
        confidence_score=confidence,
        reasoning=reasoning,
        generated_at=datetime.utcnow().isoformat() + "Z",
        model_used=model,
        # Phase 5 scoring fields
        win_prob=scores["win_prob"],
        score_raw=scores["score_raw"],
        score_scaled=scores["score_scaled"],
        oem_alignment_score=scores["oem_alignment_score"],
        partner_fit_score=scores["partner_fit_score"],
        contract_vehicle_score=scores["contract_vehicle_score"],
        govly_relevance_score=scores["govly_relevance_score"],
        confidence_interval=confidence_interval,
    )


def update_opportunity_with_forecast(opp: Dict[str, Any], forecast: ForecastData) -> Dict[str, Any]:
    """Add forecast fields to opportunity."""
    opp["forecast"] = {
        "projected_amount_FY25": forecast.projected_amount_FY25,
        "projected_amount_FY26": forecast.projected_amount_FY26,
        "projected_amount_FY27": forecast.projected_amount_FY27,
        "confidence_score": forecast.confidence_score,
        "generated_at": forecast.generated_at,
    }
    return opp


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/run", response_model=Dict[str, Any])
async def run_forecast(request: ForecastRequest, x_request_id: str = Header(default="unknown")) -> Dict[str, Any]:
    """
    Generate forecasts for opportunities.
    POST /v1/forecast/run

    Request body:
    {
        "opportunity_ids": ["opp-1", "opp-2"],  # optional
        "model": "gpt-5-thinking",
        "confidence_threshold": 50
    }

    Returns:
    {
        "request_id": "uuid",
        "forecasts_generated": 5,
        "forecasts": [...]
    }
    """
    start_time = datetime.utcnow()

    try:
        # Load existing forecasts
        forecasts = load_forecasts()

        # Get opportunities
        opportunities = get_opportunities()

        # Filter by IDs if provided
        if request.opportunity_ids:
            opportunities = [o for o in opportunities if o.get("id") in request.opportunity_ids]

        # Generate forecasts
        new_forecasts = []
        for opp in opportunities:
            forecast = generate_forecast_for_opportunity(opp, request.model)
            forecasts[forecast.opportunity_id] = forecast
            new_forecasts.append(forecast)

        # Save forecasts
        save_forecasts(forecasts)

        # Update opportunities in state with forecast fields
        state = load_state()
        updated = False
        for i, opp in enumerate(state.get("opportunities", [])):
            if opp.get("id") in forecasts:
                state["opportunities"][i] = update_opportunity_with_forecast(opp, forecasts[opp.get("id")])
                updated = True

        # Save updated state if any opportunities were updated
        if updated:
            from mcp.core.store import write_json

            write_json(str(STATE_FILE), state)

        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        return {
            "request_id": x_request_id,
            "forecasts_generated": len(new_forecasts),
            "forecasts": [f.model_dump(by_alias=True) for f in new_forecasts],
            "latency_ms": round(latency_ms, 2),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all", response_model=Dict[str, Any])
async def get_all_forecasts(x_request_id: str = Header(default="unknown")) -> Dict[str, Any]:
    """
    Get all forecasts.
    GET /v1/forecast/all

    Returns:
    {
        "total": 10,
        "forecasts": [...]
    }
    """
    try:
        forecasts = load_forecasts()

        return {
            "request_id": x_request_id,
            "total": len(forecasts),
            "forecasts": [f.model_dump(by_alias=True) for f in forecasts.values()],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/FY{fiscal_year}", response_model=Dict[str, Any])
async def get_forecasts_by_fy(fiscal_year: int, x_request_id: str = Header(default="unknown")) -> Dict[str, Any]:
    """
    Get forecasts for a specific fiscal year.
    GET /v1/forecast/FY25

    Returns forecasts with projected amounts for the specified FY.
    """
    try:
        forecasts = load_forecasts()

        # Filter forecasts with significant amounts in the requested FY
        fy_key = f"projected_amount_FY{fiscal_year}"
        fy_forecasts = []

        for forecast in forecasts.values():
            forecast_dict = forecast.model_dump(by_alias=True)
            if fy_key in forecast_dict and forecast_dict[fy_key] > 0:
                fy_forecasts.append(forecast_dict)

        # Sort by projected amount for this FY (descending)
        fy_forecasts.sort(key=lambda x: x.get(fy_key, 0), reverse=True)

        # Calculate total for this FY
        total_fy = sum(f.get(fy_key, 0) for f in fy_forecasts)

        return {
            "request_id": x_request_id,
            "fiscal_year": f"FY{fiscal_year}",
            "total_opportunities": len(fy_forecasts),
            "total_projected": round(total_fy, 2),
            "forecasts": fy_forecasts,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top", response_model=Dict[str, Any])
async def get_top_forecasts(
    limit: int = 10, sort_by: str = "win_prob", fiscal_year: Optional[int] = None, x_request_id: str = Header(default="unknown")
) -> Dict[str, Any]:
    """
    Get top forecasts ranked by various criteria.
    GET /v1/forecast/top?limit=10&sort_by=win_prob&fiscal_year=25

    sort_by options:
    - win_prob: Win probability
    - score_raw: Raw composite score
    - projected_amount: Total projected amount across all FYs
    - FY25, FY26, FY27: Specific FY amounts

    Returns:
    {
        "top_deals": [...],
        "sort_criteria": "win_prob",
        "limit": 10
    }
    """
    try:
        forecasts = load_forecasts()

        if not forecasts:
            return {
                "request_id": x_request_id,
                "top_deals": [],
                "sort_criteria": sort_by,
                "limit": limit,
            }

        forecast_list = [f.model_dump(by_alias=True) for f in forecasts.values()]

        # Determine sort key
        if sort_by in ["FY25", "FY26", "FY27"]:
            sort_key = f"projected_amount_{sort_by}"
        elif sort_by == "projected_amount":
            # Calculate total projected amount
            for f in forecast_list:
                f["total_projected"] = (
                    f.get("projected_amount_FY25", 0) + f.get("projected_amount_FY26", 0) + f.get("projected_amount_FY27", 0)
                )
            sort_key = "total_projected"
        else:
            sort_key = sort_by

        # Sort by specified criteria (descending)
        forecast_list.sort(key=lambda x: x.get(sort_key, 0), reverse=True)

        # Apply limit
        top_deals = forecast_list[:limit]

        return {
            "request_id": x_request_id,
            "top_deals": top_deals,
            "sort_criteria": sort_by,
            "limit": limit,
            "total_available": len(forecast_list),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/csv")
async def export_forecasts_csv(fiscal_year: Optional[int] = None, x_request_id: str = Header(default="unknown")) -> Response:
    """
    Export forecasts to CSV format.
    GET /v1/forecast/export/csv?fiscal_year=25

    If fiscal_year is provided, exports only that FY's data.
    Otherwise, exports all forecasts with all FY columns.
    """
    try:
        forecasts = load_forecasts()

        if not forecasts:
            raise HTTPException(status_code=404, detail="No forecasts available to export")

        # Prepare CSV data
        import io

        output = io.StringIO()

        # Define columns
        if fiscal_year:
            fieldnames = [
                "opportunity_id",
                "opportunity_name",
                f"projected_amount_FY{fiscal_year}",
                "win_prob",
                "confidence_score",
                "oem_alignment_score",
                "partner_fit_score",
                "contract_vehicle_score",
                "govly_relevance_score",
                "generated_at",
            ]
        else:
            fieldnames = [
                "opportunity_id",
                "opportunity_name",
                "projected_amount_FY25",
                "projected_amount_FY26",
                "projected_amount_FY27",
                "total_projected",
                "win_prob",
                "confidence_score",
                "oem_alignment_score",
                "partner_fit_score",
                "contract_vehicle_score",
                "govly_relevance_score",
                "confidence_interval_lower",
                "confidence_interval_upper",
                "generated_at",
                "model_used",
            ]

        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()

        for forecast in forecasts.values():
            row = forecast.model_dump(by_alias=True)

            # Add calculated fields
            if not fiscal_year:
                row["total_projected"] = (
                    row.get("projected_amount_FY25", 0) + row.get("projected_amount_FY26", 0) + row.get("projected_amount_FY27", 0)
                )

                # Flatten confidence interval
                ci = row.get("confidence_interval", {})
                if ci:
                    row["confidence_interval_lower"] = ci.get("lower_bound", 0)
                    row["confidence_interval_upper"] = ci.get("upper_bound", 0)

            writer.writerow(row)

        # Prepare response
        output.seek(0)
        filename = f"forecast_FY{fiscal_year}.csv" if fiscal_year else "forecast_all.csv"

        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "X-Request-ID": x_request_id,
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export/obsidian", response_model=Dict[str, Any])
async def export_forecasts_obsidian(x_request_id: str = Header(default="unknown")) -> Dict[str, Any]:
    """
    Export forecasts to Obsidian Forecast Dashboard.
    POST /v1/forecast/export/obsidian

    Creates/updates: obsidian/50 Dashboards/Forecast Dashboard.md

    Returns:
    {
        "path": "obsidian/50 Dashboards/Forecast Dashboard.md",
        "opportunities_exported": 10,
        "total_FY25": 1000000,
        "total_FY26": 2000000,
        "total_FY27": 500000
    }
    """
    try:
        forecasts = load_forecasts()

        if not forecasts:
            raise HTTPException(status_code=404, detail="No forecasts available to export")

        # Calculate summary statistics
        forecast_list = list(forecasts.values())
        total_fy25 = sum(f.projected_amount_FY25 for f in forecast_list)
        total_fy26 = sum(f.projected_amount_FY26 for f in forecast_list)
        total_fy27 = sum(f.projected_amount_FY27 for f in forecast_list)
        avg_win_prob = statistics.mean([f.win_prob for f in forecast_list]) if forecast_list else 0

        # Sort by win probability (descending)
        sorted_forecasts = sorted(forecast_list, key=lambda x: x.win_prob, reverse=True)

        # Create dashboard content
        dashboard_lines = [
            "---",
            "title: Forecast Dashboard",
            "type: dashboard",
            "tags:",
            "  - forecast",
            "  - dashboard",
            "  - 50-hub",
            f"updated: {datetime.utcnow().isoformat()}Z",
            "---",
            "",
            "# 📊 Forecast Dashboard",
            "",
            f"**Last Updated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            "",
            "## Summary",
            "",
            f"- **Total Opportunities:** {len(forecast_list)}",
            f"- **Average Win Probability:** {avg_win_prob:.1f}%",
            "",
            "### Projected Revenue by Fiscal Year",
            "",
            "| Fiscal Year | Projected Amount | Opportunity Count |",
            "|-------------|------------------|-------------------|",
            f"| **FY25** | ${total_fy25:,.2f} | {sum(1 for f in forecast_list if f.projected_amount_FY25 > 0)} |",
            f"| **FY26** | ${total_fy26:,.2f} | {sum(1 for f in forecast_list if f.projected_amount_FY26 > 0)} |",
            f"| **FY27** | ${total_fy27:,.2f} | {sum(1 for f in forecast_list if f.projected_amount_FY27 > 0)} |",
            f"| **Total** | ${total_fy25 + total_fy26 + total_fy27:,.2f} | {len(forecast_list)} |",
            "",
            "## Top Opportunities by Win Probability",
            "",
            "| Rank | Opportunity | Win Prob | FY25 | FY26 | FY27 | Scores (OEM/Partner/Vehicle) |",
            "|------|-------------|----------|------|------|------|------------------------------|",
        ]

        # Add top 20 opportunities
        for idx, forecast in enumerate(sorted_forecasts[:20], 1):
            opp_name = forecast.opportunity_name[:40]  # Truncate long names
            dashboard_lines.append(
                f"| {idx} | {opp_name} | {forecast.win_prob:.1f}% | "
                f"${forecast.projected_amount_FY25:,.0f} | "
                f"${forecast.projected_amount_FY26:,.0f} | "
                f"${forecast.projected_amount_FY27:,.0f} | "
                f"{forecast.oem_alignment_score:.0f}/{forecast.partner_fit_score:.0f}/{forecast.contract_vehicle_score:.0f} |"
            )

        dashboard_lines.extend(
            [
                "",
                "## Confidence Distribution",
                "",
                f"- **High Confidence (≥75%):** {sum(1 for f in forecast_list if f.win_prob >= 75)} opportunities",
                f"- **Medium Confidence (50-74%):** {sum(1 for f in forecast_list if 50 <= f.win_prob < 75)} opportunities",
                f"- **Low Confidence (<50%):** {sum(1 for f in forecast_list if f.win_prob < 50)} opportunities",
                "",
                "## OEM Heat Map (Top 5)",
                "",
            ]
        )

        # Group by OEM alignment score and show top performers
        high_oem = sorted([f for f in forecast_list if f.oem_alignment_score >= 85], key=lambda x: x.oem_alignment_score, reverse=True)[:5]

        if high_oem:
            dashboard_lines.append("| Opportunity | OEM Score | Win Prob | Total Projected |")
            dashboard_lines.append("|-------------|-----------|----------|-----------------|")
            for f in high_oem:
                total_proj = f.projected_amount_FY25 + f.projected_amount_FY26 + f.projected_amount_FY27
                dashboard_lines.append(
                    f"| {f.opportunity_name[:40]} | {f.oem_alignment_score:.0f} | " f"{f.win_prob:.1f}% | ${total_proj:,.0f} |"
                )
        else:
            dashboard_lines.append("*No high OEM alignment opportunities at this time*")

        dashboard_lines.extend(
            [
                "",
                "---",
                "",
                "*This dashboard is auto-generated by the Forecast Hub Engine.*",
                "*Scores are calculated using multi-factor analysis including OEM alignment, "
                "partner fit, contract vehicle priority, and Govly relevance.*",
                "",
            ]
        )

        # Write to Obsidian
        dashboard_path = Path("obsidian/50 Dashboards")
        dashboard_path.mkdir(parents=True, exist_ok=True)

        dashboard_file = dashboard_path / "Forecast Dashboard.md"
        dashboard_file.write_text("\n".join(dashboard_lines), encoding="utf-8")

        return {
            "request_id": x_request_id,
            "path": str(dashboard_file),
            "opportunities_exported": len(forecast_list),
            "total_FY25": round(total_fy25, 2),
            "total_FY26": round(total_fy26, 2),
            "total_FY27": round(total_fy27, 2),
            "dashboard_updated": True,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary", response_model=ForecastSummary)
async def get_forecast_summary(confidence_threshold: int = 50, x_request_id: str = Header(default="unknown")) -> ForecastSummary:
    """
    Get summary of all forecasts.
    GET /v1/forecast/summary?confidence_threshold=50

    Returns:
    {
        "total_opportunities": 10,
        "total_projected_FY25": 500000,
        "total_projected_FY26": 750000,
        "total_projected_FY27": 250000,
        "avg_confidence": 75.5,
        "high_confidence_count": 6,
        "medium_confidence_count": 3,
        "low_confidence_count": 1,
        "last_updated": "2025-10-28T17:30:00Z"
    }
    """
    try:
        forecasts = load_forecasts()

        if not forecasts:
            return ForecastSummary(
                total_opportunities=0,
                total_projected_FY25=0,
                total_projected_FY26=0,
                total_projected_FY27=0,
                avg_confidence=0,
                high_confidence_count=0,
                medium_confidence_count=0,
                low_confidence_count=0,
                last_updated=datetime.utcnow().isoformat() + "Z",
            )

        # Filter by confidence threshold
        filtered = [f for f in forecasts.values() if f.confidence_score >= confidence_threshold]

        total_fy25 = sum(f.projected_amount_FY25 for f in filtered)
        total_fy26 = sum(f.projected_amount_FY26 for f in filtered)
        total_fy27 = sum(f.projected_amount_FY27 for f in filtered)
        avg_confidence = statistics.mean([f.confidence_score for f in filtered]) if filtered else 0

        high_conf = sum(1 for f in filtered if f.confidence_score >= 75)
        med_conf = sum(1 for f in filtered if 50 <= f.confidence_score < 75)
        low_conf = sum(1 for f in filtered if f.confidence_score < 50)

        return ForecastSummary(
            total_opportunities=len(filtered),
            total_projected_FY25=round(total_fy25, 2),
            total_projected_FY26=round(total_fy26, 2),
            total_projected_FY27=round(total_fy27, 2),
            avg_confidence=round(avg_confidence, 2),
            high_confidence_count=high_conf,
            medium_confidence_count=med_conf,
            low_confidence_count=low_conf,
            last_updated=datetime.utcnow().isoformat() + "Z",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
