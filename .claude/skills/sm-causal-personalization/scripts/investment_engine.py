"""HTE-to-profit cell math + budget-frontier allocation engine (ref 06 policy-nbt).

Pure stdlib — no numpy/pandas. `dashboard_data.py` (which imports this module)
is deliberately stdlib-only so the report/dashboard pipeline never requires a
scientific-Python install; see `generate_report.py`'s own no-third-party-deps
posture and `tests/test_causal_scripts.py`, which skips itself when numpy is
absent.

This module mirrors `policy_budget.py`'s allocation *algorithm shape* — sort
by marginal ROI descending, fund a prefix of the budget, stop at the first
step that fails the ROI floor or exceeds the budget, `lambda_star` = marginal
ROI of the last funded step — without importing it. `policy_budget.py` is for
per-user IPW policy value on real randomized holdout data (needs numpy); this
module is for business-planning cells with a point `tau_hat` estimate and no
holdout required. Same algorithm, two dependency tiers.

Domain-agnostic by design: no brand, category, country, or currency name
appears here. A cell is just `sku` / `module` / `channel` keys from whatever
config is supplied — swapping to a different portfolio never touches this file.

See investment_schema.py for what every cell must carry, and
references/06-policy-nbt.md for the underlying budget-constraint math.
"""

from __future__ import annotations

import math
from typing import Any

MIN_READINESS = 0.5

# confidence tiers, least to most trustworthy — used to pick the conservative
# (weakest) badge when several cells roll up into one allocation row
_CONFIDENCE_RANK = {"blocked": 0, "assumption_grade": 1, "mmm_calibrated": 2, "validated": 3}

_SKU_TIER_WEIGHTS = {
    "revenue_potential": 0.25,
    "margin_contribution": 0.20,
    "strategic_importance": 0.20,
    "channel_availability": 0.15,
    "competitive_advantage": 0.10,
    "inventory_readiness": 0.10,
}

# SKU verdicts (from the category-portfolio diagnostic, ref 17) that may
# still receive investment — harvest/exit are excluded everywhere in this engine
INVESTABLE_VERDICTS = {"grow", "hold"}


def response_units(cell: dict, spend: float) -> float:
    """Saturating response curve: reach * tau_hat * (1 - e^-k*spend).
    Never exceeds reach * tau_hat regardless of spend."""
    tau = float(cell["tau_hat"])
    reach = float(cell["reachable_population"])
    k = float(cell.get("saturation_k", 0.0001))
    return reach * tau * (1.0 - math.exp(-k * spend))


def expand_budget_steps(cells: list[dict], default_step: float) -> list[dict]:
    """Expand every cell into fixed-size spend steps, each carrying its own
    marginal gross profit and marginal ROI. A cell may override the shared
    step size via its own `spend_step`."""
    steps: list[dict] = []
    for cell in cells:
        step = float(cell.get("spend_step") or default_step)
        max_spend = float(cell.get("max_spend", 0.0))
        margin = float(cell["unit_margin"])
        if step <= 0 or max_spend <= 0:
            continue
        badge = confidence_badge(cell)
        spend = 0.0
        while spend + step <= max_spend:
            units_before = response_units(cell, spend)
            units_after = response_units(cell, spend + step)
            before = units_before * margin
            after = units_after * margin
            steps.append({
                "cell_id": cell.get("id"),
                "sku": cell.get("sku"),
                "module": cell.get("module"),
                "channel": cell.get("channel"),
                "confidence": badge,
                "step_spend": step,
                "marginal_units": units_after - units_before,
                "marginal_gross_profit": after - before,
                "marginal_roi": (after - before) / step,
            })
            spend += step
    return steps


def confidence_badge(cell: dict) -> str:
    """Computed from the cell's own fields — never a raw config input
    (investment_schema.py rejects a 'confidence' field in the config).

    - blocked:          tau_source == "missing", or readiness below the floor
    - validated:        randomized_hte + a measurement_gate is in place
    - mmm_calibrated:   mmm_calibrated_prior
    - assumption_grade: everything else (modeled_hte or randomized_hte
                        without a gate, or expert_assumption)
    """
    tau_source = cell.get("tau_source")
    readiness = cell.get("readiness", 1.0)
    if tau_source == "missing" or readiness is None or readiness < MIN_READINESS:
        return "blocked"
    if tau_source == "randomized_hte" and cell.get("measurement_gate"):
        return "validated"
    if tau_source == "mmm_calibrated_prior":
        return "mmm_calibrated"
    return "assumption_grade"


def filter_investable_cells(cells: list[dict],
                            verdict_by_sku: dict[str, str]) -> tuple[list[dict], list[dict]]:
    """Split cells into (eligible, blocked-with-reason). Two hard gates, checked
    in order: the portfolio verdict (harvest/exit never invest, regardless of
    score), then computed confidence (blocked confidence never invests)."""
    eligible: list[dict] = []
    blocked: list[dict] = []
    for cell in cells:
        verdict = verdict_by_sku.get(cell.get("sku"))
        if verdict is not None and verdict not in INVESTABLE_VERDICTS:
            blocked.append({**cell, "reason": "excluded verdict"})
            continue
        if confidence_badge(cell) == "blocked":
            blocked.append({**cell, "reason": "confidence blocked"})
            continue
        eligible.append(cell)
    return eligible, blocked


def optimize_investment(cells: list[dict], total_budget: float, budget_step: float,
                        required_mroi: float) -> dict:
    """Fund steps in descending marginal-ROI order; stop at the first step
    that falls below required_mroi or would exceed the budget (same prefix
    rule as policy_budget.allocate's cumsum-based cutoff — not skip-ahead).
    lambda_star = marginal ROI of the last funded step, 0.0 if none funded."""
    steps = sorted(expand_budget_steps(cells, budget_step), key=lambda s: -s["marginal_roi"])

    funded_steps: list[dict] = []
    spend_used = 0.0
    for step in steps:
        if step["marginal_roi"] < required_mroi:
            break
        if spend_used + step["step_spend"] > total_budget:
            break
        funded_steps.append(step)
        spend_used += step["step_spend"]

    lambda_star = min((s["marginal_roi"] for s in funded_steps), default=0.0)
    return summarize_allocation(funded_steps, spend_used, lambda_star)


def summarize_allocation(funded_steps: list[dict], spend_used: float, lambda_star: float) -> dict:
    """Aggregate funded steps by (sku, module) into the allocation table, plus
    the top-line investment answer (spend, profit, ROI, cutoff)."""
    by_key: dict[tuple, dict] = {}
    for s in funded_steps:
        key = (s["sku"], s["module"])
        row = by_key.setdefault(key, {
            "sku": s["sku"], "module": s["module"], "channel": s.get("channel"),
            "spend": 0.0, "units": 0.0, "gross_profit": 0.0, "confidence": s["confidence"],
        })
        row["spend"] += s["step_spend"]
        row["units"] += s["marginal_units"]
        row["gross_profit"] += s["marginal_gross_profit"]
        # conservative rollup: show the weakest confidence among grouped steps
        if _CONFIDENCE_RANK.get(s["confidence"], 0) < _CONFIDENCE_RANK.get(row["confidence"], 0):
            row["confidence"] = s["confidence"]

    allocation = []
    for row in by_key.values():
        row["roi"] = (row["gross_profit"] / row["spend"]) if row["spend"] else 0.0
        allocation.append(row)
    allocation.sort(key=lambda r: -r["spend"])

    total_profit = sum(s["marginal_gross_profit"] for s in funded_steps)
    total_units = sum(s["marginal_units"] for s in funded_steps)
    return {
        "recommended_spend": spend_used,
        "incremental_units": total_units,
        "incremental_gross_profit": total_profit,
        "net_profit": total_profit - spend_used,
        "roi": (total_profit / spend_used) if spend_used else 0.0,
        "lambda_star": lambda_star,
        "allocation": allocation,
        "funded_steps": funded_steps,
    }


def _assign_sku_tier(score: float, row: dict) -> str:
    if score >= 0.80 and float(row.get("strategic_importance", 0)) >= 0.80:
        return "A1"
    if score >= 0.65 and float(row.get("revenue_potential", 0)) >= 0.65:
        return "A2"
    if score >= 0.55 and float(row.get("margin_contribution", 0)) >= 0.70:
        return "B"
    if float(row.get("channel_availability", 0)) >= 0.80:
        return "C"
    return "D"


def score_skus(rows: list[dict]) -> list[dict]:
    """Priority-tier SKUs already verdicted grow/hold (ref 17's gate) —
    harvest/exit rows never enter this ranking at all, regardless of score,
    matching investment_schema.py's cell-level exclusion."""
    scored = []
    for row in rows:
        if row.get("verdict") not in INVESTABLE_VERDICTS:
            continue
        score = sum(float(row.get(k, 0.0)) * w for k, w in _SKU_TIER_WEIGHTS.items())
        out = dict(row)
        out["priority_score"] = round(score, 4)
        out["priority_tier"] = _assign_sku_tier(score, row)
        scored.append(out)
    return sorted(scored, key=lambda r: -r["priority_score"])
