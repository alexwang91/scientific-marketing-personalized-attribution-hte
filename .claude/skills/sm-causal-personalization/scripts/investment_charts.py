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

def hte_qini_spec(qini_curve: list[dict], auuc: float | None = None) -> dict:
    points = [
        (row.get("targeted_pct"), row.get("cumulative_lift_pct"))
        for row in qini_curve
        if _is_num(row.get("targeted_pct")) and _is_num(row.get("cumulative_lift_pct"))
    ]
    if not points:
        return {"status": "missing", "points": [], "auuc": auuc}
    points = sorted(points, key=lambda p: p[0])
    return {
        "status": "available",
        "title": "Qini / AUUC",
        "points": points,
        "random_baseline": [(0, 0), (100, 100)],
        "auuc": auuc,
    }


def hte_decile_calibration_spec(deciles: list[dict]) -> dict:
    rows = []
    for row in deciles:
        predicted = row.get("predicted_tau")
        observed = row.get("observed_lift")
        if not _is_num(predicted) or not _is_num(observed):
            continue
        rows.append({
            "decile": row.get("decile"),
            "predicted_tau": predicted,
            "observed_lift": observed,
            "audience_pct": row.get("audience_pct"),
            "gap": round(float(predicted) - float(observed), 4),
        })
    return {"status": "available" if rows else "missing", "rows": rows}


def hte_tau_distribution_spec(distribution: list[dict]) -> dict:
    bins = [
        {"bucket": row.get("bucket", ""), "share": row.get("share", 0.0)}
        for row in distribution
        if row.get("bucket") is not None
    ]
    return {"status": "available" if bins else "missing", "bins": bins}


def mmm_contribution_spec(channel_contribution: list[dict]) -> dict:
    bars = [
        {"channel": row.get("channel", ""), "contribution": row.get("contribution", 0.0)}
        for row in channel_contribution
        if row.get("channel")
    ]
    bars.sort(key=lambda r: -float(r.get("contribution") or 0.0))
    return {"status": "available" if bars else "missing", "bars": bars}


def adstock_saturation_spec(curves: list[dict]) -> dict:
    panels = []
    for row in curves:
        points = _points(row.get("points", []), "spend", "response")
        if points:
            panels.append({"channel": row.get("channel", ""), "points": points})
    return {"status": "available" if panels else "missing", "panels": panels}


def posterior_roas_spec(posterior_roas: list[dict]) -> dict:
    intervals = []
    for row in posterior_roas:
        if not row.get("channel"):
            continue
        intervals.append({
            "channel": row.get("channel", ""),
            "mean": row.get("mean", 0.0),
            "lo": row.get("lo", 0.0),
            "hi": row.get("hi", 0.0),
        })
    intervals.sort(key=lambda r: -float(r.get("mean") or 0.0))
    return {"status": "available" if intervals else "missing", "intervals": intervals}


def lift_calibration_spec(lift_calibration: list[dict]) -> dict:
    points = _points(lift_calibration, "predicted", "observed")
    labels = [
        row.get("channel", "")
        for row in lift_calibration
        if _is_num(row.get("predicted")) and _is_num(row.get("observed"))
    ]
    return {"status": "available" if points else "missing", "points": points, "labels": labels}


def _points(rows: list[dict], x_key: str, y_key: str) -> list[tuple]:
    return [
        (row.get(x_key), row.get(y_key))
        for row in rows
        if _is_num(row.get(x_key)) and _is_num(row.get(y_key))
    ]


def _is_num(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)
