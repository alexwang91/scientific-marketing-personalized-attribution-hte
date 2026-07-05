#!/usr/bin/env python3
"""Tests for investment_schema.py and investment_engine.py — pure stdlib,
no numpy/pandas required (mirrors generate_report.py's dependency posture)."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".claude" / "skills" / "sm-causal-personalization" / "scripts"


def _load(name: str):
    # register into sys.modules under its real name: a module that defines
    # an exception class (e.g. investment_schema.InvestmentConfigError) must
    # be loaded exactly once per process, or `except module.SomeError` in a
    # second loader (e.g. dashboard_data.py's own internal import) would
    # compare against a distinct, non-matching class object.
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


schema = _load("investment_schema")
engine = _load("investment_engine")


# ── Genericity: the engine must never hardcode a brand/category/country/
#    currency name. Mechanically checked, not just reviewed — covers both
#    real customer data ever discussed (never committed, per the Local-Only
#    Rule) and this repo's own fictional example brands (which belong only
#    in examples/*.json, not in the reusable engine). ────────────────────────

ENGINE_MODULES = (
    "investment_schema", "investment_engine", "investment_charts",
    "mmm_bridge", "svg_charts",
)

_BANNED_TERMS = (
    # real-world product/brand names ever discussed for this capability —
    # must never leak into the committed, reusable engine
    "cloudlink", "huawei", "watch fit", "router", "romania",
    # this repo's own fictional example brands/categories/markets — belong
    # only in examples/*.json, never in the domain-agnostic engine itself
    "vela", "brewpro", "czech", "aurora", "air purifier", "poland",
)

_BANNED_CURRENCY_CODES = ("CZK", "PLN", "RON", "HUF")


def test_engine_modules_contain_no_hardcoded_example_domain_terms():
    import re
    for name in ENGINE_MODULES:
        text = (SCRIPTS / f"{name}.py").read_text(encoding="utf-8")
        lower = text.lower()
        for term in _BANNED_TERMS:
            assert term not in lower, f"{name}.py hardcodes domain term {term!r}"
        for code in _BANNED_CURRENCY_CODES:
            assert not re.search(rf"\b{code}\b", text), \
                f"{name}.py hardcodes currency code {code!r}"


def _cell(**overrides):
    base = {
        "id": "c1", "sku": "BE3", "module": "search", "channel": "Search",
        "tau_hat": 0.02, "tau_source": "randomized_hte", "measurement_gate": "holdout",
        "reachable_population": 10000, "unit_margin": 120, "max_spend": 3000,
        "saturation_k": 0.001, "readiness": 1.0,
    }
    base.update(overrides)
    return base


# ── investment_schema ────────────────────────────────────────────────────────

def test_investment_plan_requires_cells_and_modules_when_present():
    cfg = {"investment_plan": {"total_budget": 100000, "required_mroi": 1.2}}
    errors = schema.validate_investment_plan(cfg)
    assert "investment_plan.modules must be a non-empty list" in errors
    assert "investment_plan.cells must be a non-empty list" in errors


def test_absent_investment_plan_is_not_an_error():
    assert schema.validate_investment_plan({}) == []


def test_forbidden_discount_lever_is_rejected():
    cfg = {"investment_plan": {"total_budget": 100000, "required_mroi": 1.2,
           "modules": [{"id": "discount", "label": "Discount"}], "cells": [_cell()]}}
    errors = schema.validate_investment_plan(cfg)
    assert any("discount" in e for e in errors)


def test_unknown_module_id_is_rejected():
    cfg = {"investment_plan": {"modules": [{"id": "not_a_real_module"}], "cells": [_cell()]}}
    errors = schema.validate_investment_plan(cfg)
    assert any("unknown investment module" in e for e in errors)


def test_expert_assumption_requires_tau_basis():
    cfg = {"investment_plan": {"modules": [{"id": "search"}],
           "cells": [_cell(tau_source="expert_assumption", measurement_gate=None)]}}
    errors = schema.validate_investment_plan(cfg)
    assert any("tau_basis" in e for e in errors)


def test_missing_tau_source_must_not_carry_tau_hat_and_needs_needed_from():
    cfg = {"investment_plan": {"modules": [{"id": "search"}],
           "cells": [_cell(tau_source="missing")]}}
    errors = schema.validate_investment_plan(cfg)
    assert any("must not carry a tau_hat" in e for e in errors)
    assert any("needed_from" in e for e in errors)


def test_missing_tau_source_with_needed_from_and_no_tau_hat_is_valid():
    cell = _cell(tau_source="missing", needed_from="local pilot")
    del cell["tau_hat"]
    cfg = {"investment_plan": {"modules": [{"id": "search"}], "cells": [cell]}}
    assert schema.validate_investment_plan(cfg) == []


def test_raw_confidence_field_is_rejected():
    cfg = {"investment_plan": {"modules": [{"id": "search"}],
           "cells": [_cell(confidence="high")]}}
    errors = schema.validate_investment_plan(cfg)
    assert any("must not be set on a cell" in e for e in errors)


def test_cell_referencing_exit_or_harvest_verdict_sku_is_rejected():
    cfg = {"portfolio": [{"sku": "AX1", "verdict": "exit"}],
           "investment_plan": {"modules": [{"id": "search"}],
           "cells": [_cell(id="c1", sku="AX1")]}}
    errors = schema.validate_investment_plan(cfg)
    assert any("AX1" in e and "exit" in e for e in errors)

    cfg["portfolio"][0]["verdict"] = "harvest"
    errors = schema.validate_investment_plan(cfg)
    assert any("AX1" in e and "harvest" in e for e in errors)


def test_grow_and_hold_verdict_skus_are_accepted():
    for verdict in ("grow", "hold"):
        cfg = {"portfolio": [{"sku": "BE3", "verdict": verdict}],
               "investment_plan": {"modules": [{"id": "search"}], "cells": [_cell()]}}
        assert schema.validate_investment_plan(cfg) == []


def test_negative_numeric_fields_are_rejected():
    cfg = {"investment_plan": {"modules": [{"id": "search"}],
           "cells": [_cell(max_spend=-100)]}}
    errors = schema.validate_investment_plan(cfg)
    assert any("max_spend" in e for e in errors)


def test_validate_or_raise_raises_investment_config_error():
    cfg = {"investment_plan": {"total_budget": 100, "required_mroi": 1.2,
           "modules": [{"id": "discount"}], "cells": []}}
    try:
        schema.validate_or_raise(cfg)
    except schema.InvestmentConfigError as e:
        assert "discount" in str(e)
        return
    raise AssertionError("expected InvestmentConfigError")


# ── investment_engine: cell math ──────────────────────────────────────────────

def test_response_units_saturates_with_spend():
    cell = {"tau_hat": 0.02, "reachable_population": 10000, "saturation_k": 0.001}
    low = engine.response_units(cell, 100)
    high = engine.response_units(cell, 10000)
    assert low > 0
    assert high > low
    assert high <= 200  # can never exceed reachable_population * tau_hat


def test_expand_budget_steps_computes_declining_marginal_roi():
    cell = _cell()
    steps = engine.expand_budget_steps([cell], 1000)
    assert len(steps) == 3
    assert steps[0]["marginal_roi"] > steps[1]["marginal_roi"] > steps[2]["marginal_roi"]


def test_confidence_badge_matches_rules():
    assert engine.confidence_badge(_cell(tau_source="randomized_hte", measurement_gate="g")) == "validated"
    assert engine.confidence_badge(_cell(tau_source="randomized_hte", measurement_gate=None)) == "assumption_grade"
    assert engine.confidence_badge(_cell(tau_source="mmm_calibrated_prior")) == "mmm_calibrated"
    assert engine.confidence_badge(_cell(tau_source="expert_assumption")) == "assumption_grade"
    assert engine.confidence_badge(_cell(tau_source="missing")) == "blocked"
    assert engine.confidence_badge(_cell(readiness=0.1)) == "blocked"


# ── investment_engine: allocation / frontier ─────────────────────────────────

def test_filter_investable_cells_excludes_harvest_and_exit():
    cells = [_cell(id="c1", sku="AX1"), _cell(id="c2", sku="BE3")]
    eligible, blocked = engine.filter_investable_cells(cells, {"AX1": "exit", "BE3": "grow"})
    assert [c["id"] for c in eligible] == ["c2"]
    assert blocked[0]["reason"] == "excluded verdict"


def test_filter_investable_cells_excludes_blocked_confidence():
    cells = [_cell(id="c1", tau_source="missing", tau_hat=None, needed_from="x")]
    eligible, blocked = engine.filter_investable_cells(cells, {})
    assert eligible == []
    assert blocked[0]["reason"] == "confidence blocked"


def test_allocator_funds_highest_mroi_steps_first_and_stops_at_threshold():
    cells = [
        _cell(id="be3_search", sku="BE3", tau_hat=0.025),
        _cell(id="ax1_search", sku="AX1", tau_hat=0.002, unit_margin=30),
    ]
    result = engine.optimize_investment(cells, total_budget=4000, budget_step=1000, required_mroi=1.2)
    assert result["recommended_spend"] <= 4000
    assert any(r["sku"] == "BE3" for r in result["allocation"])
    assert all(r["sku"] != "AX1" for r in result["allocation"])
    assert result["lambda_star"] >= 1.2


def test_lambda_star_equals_marginal_roi_of_last_funded_step():
    cells = [_cell(id="c1", max_spend=5000)]
    result = engine.optimize_investment(cells, total_budget=100000, budget_step=1000, required_mroi=0.1)
    last_step_roi = min(s["marginal_roi"] for s in result["funded_steps"])
    assert abs(result["lambda_star"] - last_step_roi) < 1e-9


def test_optimizer_never_funds_below_required_mroi_even_with_budget_left():
    cells = [_cell(id="c1", tau_hat=0.002, unit_margin=30, max_spend=3000)]
    result = engine.optimize_investment(cells, total_budget=100000, budget_step=1000, required_mroi=5.0)
    assert result["recommended_spend"] == 0
    assert result["lambda_star"] == 0.0


def test_score_skus_only_ranks_grow_and_hold_rows():
    rows = [
        {"sku": "A1", "verdict": "grow", "revenue_potential": 0.9, "margin_contribution": 0.9,
         "strategic_importance": 0.9, "channel_availability": 0.9, "competitive_advantage": 0.9,
         "inventory_readiness": 0.9},
        {"sku": "EXIT1", "verdict": "exit", "revenue_potential": 1.0, "margin_contribution": 1.0,
         "strategic_importance": 1.0, "channel_availability": 1.0, "competitive_advantage": 1.0,
         "inventory_readiness": 1.0},
    ]
    scored = engine.score_skus(rows)
    assert [r["sku"] for r in scored] == ["A1"]
    assert scored[0]["priority_tier"] in {"A1", "A2", "B", "C", "D"}


if __name__ == "__main__":
    tests = [name for name in sorted(globals()) if name.startswith("test_")]
    failures = 0
    for name in tests:
        try:
            globals()[name]()
            print(f"PASS {name}")
        except Exception as exc:
            failures += 1
            print(f"FAIL {name}: {exc}")
    raise SystemExit(1 if failures else 0)
