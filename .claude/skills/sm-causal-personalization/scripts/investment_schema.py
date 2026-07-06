"""Investment-plan validation (ref 06 policy-nbt, ref 17 category-portfolio).

Pure stdlib — no numpy/pandas. This module owns the contract for
`cfg["investment_plan"]`: which levers/modules are allowed, what every cell
must carry depending on its `tau_source`, and the one hard cross-check that
keeps SKU-level investment decisions honest against the category-portfolio
verdict that was already decided upstream (ref 17): a SKU verdicted
`harvest`/`exit` can never enter the allocation, no matter how it scores.

Domain-agnostic by design: nothing here names a brand, category, country, or
currency. Any product line in any market validates against the exact same
rules — only the config differs.

See references/06-policy-nbt.md and the investment-dashboard plan for the
full data contract.
"""

from __future__ import annotations

from typing import Any

ALLOWED_MODULES = {
    "category_brand", "search", "retail_media", "paid_social_video",
    "creator_review", "pdp_content", "retail_activation",
    "pr_reviews", "crm_retention", "measurement",
}
FORBIDDEN_LEVERS = {"discount", "coupon", "rebate", "price_subsidy"}

TAU_SOURCES = {"randomized_hte", "modeled_hte", "mmm_calibrated_prior", "expert_assumption", "missing"}

# verdicts that permanently exclude a SKU from investment_plan.cells,
# regardless of any priority score (ref 17: a Grow verdict is the gate,
# not a suggestion)
EXCLUDED_VERDICTS = {"harvest", "exit"}

_NUMERIC_CELL_FIELDS = ("reachable_population", "unit_margin", "max_spend", "saturation_k")


def _is_num(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def validate_investment_plan(cfg: dict) -> list[str]:
    """Validate cfg["investment_plan"]. Returns a list of error strings;
    empty list means valid. Absent investment_plan is not an error — the
    capability is opt-in."""
    plan = cfg.get("investment_plan")
    if not plan:
        return []
    errors: list[str] = []

    modules = plan.get("modules")
    cells = plan.get("cells")
    if not isinstance(modules, list) or not modules:
        errors.append("investment_plan.modules must be a non-empty list")
    if not isinstance(cells, list) or not cells:
        errors.append("investment_plan.cells must be a non-empty list")

    for module in modules or []:
        mid = str(module.get("id", ""))
        if mid in FORBIDDEN_LEVERS:
            errors.append(f"forbidden lever in investment_plan.modules: {mid}")
        elif mid and mid not in ALLOWED_MODULES:
            errors.append(f"unknown investment module: {mid}")

    for key in ("total_budget", "required_mroi"):
        val = plan.get(key)
        if val is not None and (not _is_num(val) or val < 0):
            errors.append(f"investment_plan.{key} must be a non-negative number")

    verdict_by_sku = {p.get("sku"): p.get("verdict") for p in cfg.get("portfolio", [])}

    declared_modules = {str(m.get("id", "")) for m in modules or []}

    for cell in cells or []:
        cid = cell.get("id", "<no id>")
        sku = cell.get("sku")

        module = cell.get("module")
        if module in FORBIDDEN_LEVERS:
            errors.append(f"{cid}: forbidden lever in cell.module: {module}")
        elif module not in ALLOWED_MODULES:
            errors.append(f"{cid}: unknown investment module: {module!r}")
        elif module not in declared_modules:
            errors.append(
                f"{cid}: module '{module}' is not declared in investment_plan.modules")

        verdict = verdict_by_sku.get(sku)
        if verdict in EXCLUDED_VERDICTS:
            errors.append(
                f"{cid}: sku '{sku}' is verdicted '{verdict}' in portfolio — "
                f"excluded SKUs may not appear in investment_plan.cells")

        if "confidence" in cell:
            errors.append(
                f"{cid}: 'confidence' must not be set on a cell — it is computed "
                f"from tau_source/readiness/measurement_gate (see investment_engine.confidence_badge)")

        tau_source = cell.get("tau_source")
        if tau_source not in TAU_SOURCES:
            errors.append(f"{cid}: tau_source must be one of {sorted(TAU_SOURCES)}, got {tau_source!r}")
        elif tau_source == "randomized_hte" and not cell.get("validation_ref"):
            errors.append(f"{cid}: tau_source='randomized_hte' requires a validation_ref")
        elif tau_source == "expert_assumption" and not cell.get("tau_basis"):
            errors.append(f"{cid}: tau_source='expert_assumption' requires a 'tau_basis' string")
        elif tau_source == "missing":
            if "tau_hat" in cell:
                errors.append(f"{cid}: tau_source='missing' must not carry a tau_hat value — that is a guess")
            if not cell.get("needed_from"):
                errors.append(f"{cid}: tau_source='missing' requires 'needed_from'")

        if tau_source != "missing" and not _is_num(cell.get("tau_hat")):
            errors.append(f"{cid}: tau_hat must be numeric unless tau_source='missing'")

        for field in _NUMERIC_CELL_FIELDS:
            val = cell.get(field)
            if val is not None and (not _is_num(val) or val < 0):
                errors.append(f"{cid}: {field} must be a non-negative number")

    return errors


class InvestmentConfigError(Exception):
    """Raised by the build-time wrapper when validate_investment_plan finds errors."""


def validate_or_raise(cfg: dict) -> None:
    errors = validate_investment_plan(cfg)
    if errors:
        raise InvestmentConfigError(
            "Investment-plan contract violations:\n  - " + "\n  - ".join(errors))
