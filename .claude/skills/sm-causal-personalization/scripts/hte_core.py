"""HTE validation contract for the investment dashboard.

The investment engine turns cell-level tau estimates into spend and profit.
This module answers the separate question: which tau estimates are backed by
holdout validation strongly enough to be called "validated" in the UI?

Pure stdlib and domain-agnostic by design.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

_HERE = Path(__file__).parent

try:
    import investment_charts as _charts
except ImportError:
    try:
        from . import investment_charts as _charts
    except ImportError:
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location("investment_charts", _HERE / "investment_charts.py")
        _charts = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(_charts)


def _is_num(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _compute_curve_auuc(curve: list[dict]) -> float | None:
    """Approximate AUUC above the random baseline from percent-scaled points."""
    points = sorted(
        [
            (float(row["targeted_pct"]), float(row["cumulative_lift_pct"]))
            for row in curve
            if _is_num(row.get("targeted_pct")) and _is_num(row.get("cumulative_lift_pct"))
        ],
        key=lambda p: p[0],
    )
    if len(points) < 2:
        return None
    area = 0.0
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        random_y1 = x1
        random_y2 = x2
        area += ((y1 - random_y1) + (y2 - random_y2)) / 2.0 * (x2 - x1)
    return round(area / 10000.0, 4)


def _compute_interval_coverage(decile_calibration: list[dict]) -> float | None:
    """Empirical coverage of the model's tau intervals on holdout deciles:
    the share of deciles whose observed lift falls inside [tau_lo, tau_hi].
    Returns None when the decile rows carry no interval bounds."""
    rows = [
        r for r in decile_calibration
        if _is_num(r.get("tau_lo")) and _is_num(r.get("tau_hi")) and _is_num(r.get("observed_lift"))
    ]
    if not rows:
        return None
    covered = sum(1 for r in rows
                  if float(r["tau_lo"]) <= float(r["observed_lift"]) <= float(r["tau_hi"]))
    return round(covered / len(rows), 4)


def _passes_gate(ref: dict, min_auuc: float, max_calibration_mae: float,
                 min_interval_coverage: float | None = None,
                 fallback_coverage: float | None = None) -> bool:
    """Three gates, all mandatory when configured: rank quality (AUUC),
    magnitude calibration (MAE), and — when min_interval_coverage is set —
    interval honesty (empirical coverage of the model's own uncertainty
    intervals on holdout). The third gate exists because overconfident
    intervals are the dominant failure mode: CausalDS (arXiv 2607.08093)
    measured nominal 95% ATE intervals covering only 20-71% empirically
    across every frontier model tested."""
    auuc = ref.get("qini_auuc")
    mae = ref.get("calibration_mae")
    if not _is_num(auuc) or not _is_num(mae):
        return False
    if float(auuc) < min_auuc or float(mae) > max_calibration_mae:
        return False
    if min_interval_coverage is not None:
        coverage = ref.get("interval_coverage")
        if not _is_num(coverage):
            coverage = fallback_coverage
        if not _is_num(coverage) or float(coverage) < min_interval_coverage:
            return False
    return True


def build_hte_summary(validation: dict | None, cells: list[dict]) -> dict:
    """Normalize the optional HTE validation block into dashboard-ready state."""
    if not validation:
        return {
            "status": "missing",
            "method": "",
            "holdout_n": 0,
            "validated_cell_ids": set(),
            "validation_refs": [],
            "charts": {
                "qini": {"status": "missing"},
                "decile_calibration": {"status": "missing"},
                "tau_distribution": _charts.hte_tau_distribution_spec(_distribution_from_cells(cells)),
            },
        }

    min_auuc = float(validation.get("min_auuc", 0.0))
    max_mae = float(validation.get("max_calibration_mae", 1.0))
    min_coverage = validation.get("min_interval_coverage")
    min_coverage = float(min_coverage) if _is_num(min_coverage) else None
    # a ref without its own interval_coverage falls back to the coverage
    # computed from the shared decile_calibration rows (single-model case)
    fallback_coverage = _compute_interval_coverage(validation.get("decile_calibration", []))
    refs = []
    validated_cell_ids: set[str] = set()
    for ref in validation.get("validation_refs", []):
        out = dict(ref)
        if not _is_num(out.get("interval_coverage")) and fallback_coverage is not None:
            out["interval_coverage"] = fallback_coverage
        out["passes_gate"] = _passes_gate(ref, min_auuc, max_mae, min_coverage, fallback_coverage)
        if out["passes_gate"]:
            for cell_id in ref.get("cells", []):
                validated_cell_ids.add(str(cell_id))
        refs.append(out)

    curve = validation.get("qini_curve", [])
    auuc = validation.get("qini_auuc")
    if not _is_num(auuc):
        ref_auucs = [float(r["qini_auuc"]) for r in refs if _is_num(r.get("qini_auuc"))]
        auuc = round(sum(ref_auucs) / len(ref_auucs), 4) if ref_auucs else _compute_curve_auuc(curve)

    return {
        "status": validation.get("status", "available"),
        "method": validation.get("method", ""),
        "holdout_n": validation.get("holdout_n", 0),
        "min_auuc": min_auuc,
        "max_calibration_mae": max_mae,
        "min_interval_coverage": min_coverage,
        "validated_cell_ids": validated_cell_ids,
        "validation_refs": refs,
        "charts": {
            "qini": _charts.hte_qini_spec(curve, auuc),
            "decile_calibration": _charts.hte_decile_calibration_spec(
                validation.get("decile_calibration", [])),
            "tau_distribution": _charts.hte_tau_distribution_spec(
                validation.get("tau_distribution") or _distribution_from_cells(cells)),
        },
    }


def annotate_cells_with_hte_validation(cells: list[dict], validation: dict | None) -> list[dict]:
    """Return copied cells with an internal _hte_validated flag for the engine."""
    summary = build_hte_summary(validation, cells)
    validated_ids = summary["validated_cell_ids"]
    annotated = []
    for cell in cells:
        out = dict(cell)
        ref = out.get("validation_ref")
        out["_hte_validated"] = bool(ref and out.get("id") in validated_ids)
        annotated.append(out)
    return annotated


def serializable_summary(summary: dict) -> dict:
    """Convert set fields before embedding in dashboard JSON."""
    out = dict(summary)
    out["validated_cell_ids"] = sorted(summary.get("validated_cell_ids", set()))
    return out


def _distribution_from_cells(cells: list[dict]) -> list[dict]:
    bins = [
        {"bucket": "<=0", "share": 0.0, "_count": 0},
        {"bucket": "0-1%", "share": 0.0, "_count": 0},
        {"bucket": "1-3%", "share": 0.0, "_count": 0},
        {"bucket": ">3%", "share": 0.0, "_count": 0},
    ]
    for cell in cells:
        tau = cell.get("tau_hat")
        if not _is_num(tau):
            continue
        tau = float(tau)
        if tau <= 0:
            idx = 0
        elif tau <= 0.01:
            idx = 1
        elif tau <= 0.03:
            idx = 2
        else:
            idx = 3
        bins[idx]["_count"] += 1
    total = sum(b["_count"] for b in bins) or 1
    out = []
    for b in bins:
        out.append({"bucket": b["bucket"], "share": round(b["_count"] / total, 4)})
    return out
