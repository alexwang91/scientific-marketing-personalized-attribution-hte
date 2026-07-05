"""Chart-data specs for the investment dashboard (ref 06, ref 12 §five-chapter spine).

Pure stdlib. Returns plain, JSON-serializable dicts consumed by both
`dashboard_render.py` (inline SVG / CSS heatmap grid) and `generate_report.py`
(the document report). Phase 1 implements 4 charts; the 4 MMM curve charts are
stubbed (`{"status": "deferred"}`) until Phase 2 wires a live macro-calibration
source — see mmm_bridge.py's own phase split.

Domain-agnostic: every function takes generic sku/module/spend/roi/confidence
keys from whatever config produced them — no brand/category/country name
appears here.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

_HERE = Path(__file__).parent

try:
    from investment_engine import confidence_badge
except ImportError:
    try:
        from .investment_engine import confidence_badge
    except ImportError:
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location("investment_engine", _HERE / "investment_engine.py")
        _mod = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
        confidence_badge = _mod.confidence_badge


def investment_answer_kpis(summary: dict, currency: str = "") -> list[dict]:
    """KPI cards for chapter 1 — spend, incremental units/profit, net profit,
    ROI, and the cutoff (lambda_star). Tone follows ROI vs. break-even (1.0),
    not vs. required_mroi — a card at exactly the hurdle is still "good"."""
    roi = summary.get("roi", 0.0)
    tone = "good" if roi >= 1.0 else ("warn" if roi > 0 else "bad")
    return [
        {"id": "spend", "label_key": "kpi_spend", "value": summary.get("recommended_spend", 0.0),
         "unit": currency, "tone": "neutral"},
        {"id": "units", "label_key": "kpi_units", "value": summary.get("incremental_units", 0.0),
         "unit": "", "tone": "neutral"},
        {"id": "gross_profit", "label_key": "kpi_gross_profit",
         "value": summary.get("incremental_gross_profit", 0.0), "unit": currency, "tone": "neutral"},
        {"id": "net_profit", "label_key": "kpi_net_profit", "value": summary.get("net_profit", 0.0),
         "unit": currency, "tone": tone},
        {"id": "roi", "label_key": "kpi_roi", "value": round(roi, 2), "unit": "x", "tone": tone},
        {"id": "lambda_star", "label_key": "kpi_lambda_star",
         "value": round(summary.get("lambda_star", 0.0), 2), "unit": "x", "tone": "neutral"},
    ]


def frontier_chart_spec(frontier: list[dict], cutoff_spend: float) -> dict:
    """Two single-axis panels — spend vs. cumulative profit, spend vs. marginal
    ROI — never a combined dual-axis chart (two measures of different scale
    get two charts, per the dataviz 'one axis' rule)."""
    profit_points = [
        (r["spend"], r.get("incremental_gross_profit", r.get("cumulative_gross_profit", 0.0)))
        for r in frontier
    ]
    roi_points = [(r["spend"], r["marginal_roi"]) for r in frontier]
    return {
        "profit_panel": {"title": "Cumulative gross profit", "points": profit_points,
                         "cutoff_spend": cutoff_spend},
        "roi_panel": {"title": "Marginal ROI", "points": roi_points, "cutoff_spend": cutoff_spend},
    }


def budget_matrix_spec(allocation: list[dict]) -> dict:
    """SKU (rows) x module (columns) budget matrix. Spend encodes a sequential
    ramp (magnitude); confidence is a secondary encoding (a dot), never folded
    into the same hue as spend."""
    x_axis: list[str] = []
    y_axis: list[str] = []
    for row in allocation:
        if row["module"] not in x_axis:
            x_axis.append(row["module"])
        if row["sku"] not in y_axis:
            y_axis.append(row["sku"])
    cells = [{
        "sku": row["sku"], "module": row["module"],
        "spend": row.get("spend", 0.0), "roi": row.get("roi", 0.0),
        "confidence": row.get("confidence", "assumption_grade"),
    } for row in allocation]
    return {"x_axis": x_axis, "y_axis": y_axis, "cells": cells}


def confidence_strip_spec(cells: list[dict]) -> dict:
    """Counts by computed confidence badge — never a raw input, see
    investment_engine.confidence_badge."""
    counts = {"validated": 0, "mmm_calibrated": 0, "assumption_grade": 0, "blocked": 0}
    for cell in cells:
        badge = confidence_badge(cell)
        counts[badge] = counts.get(badge, 0) + 1
    return counts


# ── Deferred to Phase 2 — signatures fixed now so mmm_bridge.py's output
#    shape is stable when a live macro-calibration source lands ─────────────

def mmm_contribution_spec(channel_contribution: list[dict]) -> dict:
    return {"status": "deferred"}


def adstock_saturation_spec(curves: list[dict]) -> dict:
    return {"status": "deferred"}


def posterior_roas_spec(posterior_roas: list[dict]) -> dict:
    return {"status": "deferred"}


def lift_calibration_spec(lift_calibration: list[dict]) -> dict:
    return {"status": "deferred"}
