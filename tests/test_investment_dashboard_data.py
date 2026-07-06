#!/usr/bin/env python3
"""Tests for mmm_bridge.py and dashboard_data.py's investment wiring."""
from __future__ import annotations

import copy
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


mmm_bridge = _load("mmm_bridge")
schema = _load("investment_schema")
data_mod = _load("dashboard_data")


# ── mmm_bridge ────────────────────────────────────────────────────────────────

def test_mmm_bridge_accepts_provided_summary_without_pymc_marketing():
    cfg = {"mmm": {"mode": "provided_summary",
           "channel_contribution": [{"channel": "Search", "contribution": 1200}],
           "posterior_roas": [{"channel": "Search", "mean": 2.1, "lo": 1.4, "hi": 3.0}],
           "adstock_curves": [], "saturation_curves": [],
           "optimized_channel_budget": [{"channel": "Search", "budget": 10000}],
           "lift_calibration": []}}
    out = mmm_bridge.build_mmm_summary(cfg)
    assert out["status"] == "available"
    assert out["posterior_roas"][0]["channel"] == "Search"


def test_mmm_bridge_reports_missing_when_no_mmm_config():
    out = mmm_bridge.build_mmm_summary({})
    assert out["status"] == "missing"
    assert "macro channel calibration" in out["blocks"]


def test_mmm_bridge_reports_deferred_for_pymc_marketing_mode():
    out = mmm_bridge.build_mmm_summary({"mmm": {"mode": "pymc_marketing"}})
    assert out["status"] == "deferred"
    assert "macro channel calibration" in out["blocks"]


def test_mmm_bridge_missing_summary_fields_default_to_empty_lists():
    out = mmm_bridge.build_mmm_summary({"mmm": {"mode": "provided_summary"}})
    assert out["status"] == "available"
    assert out["channel_contribution"] == []
    assert out["posterior_roas"] == []


# ── dashboard_data investment wiring (Task 6) ────────────────────────────────

_CELL = {
    "id": "be3_search", "sku": "BE3", "module": "search", "channel": "Google Search",
    "tau_hat": 0.025, "tau_source": "randomized_hte", "validation_ref": "be3_search_holdout",
    "measurement_gate": "holdout",
    "reachable_population": 10000, "unit_margin": 120, "max_spend": 3000,
    "saturation_k": 0.001, "readiness": 1.0,
    "owner": "Digital commerce",
    "flight": "2026-Q3 weeks 1-4",
    "kpi": "Incremental paid-search orders",
    "measurement": "Geo holdout by county",
    "stop_rule": "Pause if week-2 marginal ROI drops below 1.2x",
    "why": "Highest validated uplift cell in the portfolio.",
}


def _category_cfg(**plan_overrides):
    plan = {"currency": "RON", "planning_period": "2026-Q3", "total_budget": 4000,
            "required_mroi": 1.2, "budget_step": 1000,
            "modules": [{"id": "search", "label": "Search"}], "cells": [dict(_CELL)],
            "hte_validation": {
                "status": "available",
                "method": "DR learner on randomized holdout",
                "holdout_n": 24000,
                "min_auuc": 0.15,
                "max_calibration_mae": 0.02,
                "validation_refs": [
                    {"id": "be3_search_holdout", "cells": ["be3_search"], "learner": "dr_learner",
                     "qini_auuc": 0.26, "calibration_mae": 0.01, "policy_value_ipw": 12000}
                ],
                "qini_curve": [
                    {"targeted_pct": 0, "cumulative_lift_pct": 0},
                    {"targeted_pct": 50, "cumulative_lift_pct": 73},
                    {"targeted_pct": 100, "cumulative_lift_pct": 100},
                ],
                "decile_calibration": [
                    {"decile": 1, "predicted_tau": 0.041, "observed_lift": 0.039, "audience_pct": 10}
                ],
                "tau_distribution": [{"bucket": "1-3%", "share": 1.0}],
            }}
    plan.update(plan_overrides)
    return {
        "report_type": "category_portfolio",
        "meta": {"product": "Test Portfolio", "market": "Testland"},
        "portfolio": [{"sku": "BE3", "verdict": "grow"}],
        "investment_plan": plan,
        "mmm": {
            "mode": "provided_summary",
            "channel_contribution": [{"channel": "Search", "contribution": 1200}],
            "posterior_roas": [{"channel": "Search", "mean": 2.0, "lo": 1.5, "hi": 2.5}],
            "adstock_curves": [{"channel": "Search", "points": [
                {"spend": 0, "response": 0}, {"spend": 1000, "response": 0.7}
            ]}],
            "saturation_curves": [{"channel": "Search", "points": [
                {"spend": 0, "response": 0}, {"spend": 3000, "response": 0.9}
            ]}],
            "optimized_channel_budget": [{"channel": "Search", "budget": 4000}],
            "lift_calibration": [{"channel": "Search", "predicted": 0.05, "observed": 0.047}],
        },
    }


def test_category_config_with_investment_plan_builds_investment_dashboard_data():
    data = data_mod.build_dashboard_data(_category_cfg())
    assert data["kind"] == "category_portfolio"
    assert data["investment"]["answer"]["recommended_spend"] > 0
    assert data["investment"]["charts"]["frontier"]["profit_panel"]["title"]
    assert data["investment"]["charts"]["budget_matrix"]["y_axis"] == ["BE3"]
    assert data["investment"]["hte"]["status"] == "available"
    assert data["investment"]["charts"]["hte"]["qini"]["status"] == "available"
    assert data["investment"]["charts"]["mmm"]["posterior_roas"]["status"] == "available"


def test_investment_dashboard_data_includes_activation_cards_with_operating_details():
    data = data_mod.build_dashboard_data(_category_cfg())
    cards = data["investment"]["activation_cards"]
    assert cards
    assert cards[0]["owner"] == "Digital commerce"
    assert cards[0]["measurement"] == "Geo holdout by county"
    assert cards[0]["stop_rule"].startswith("Pause")


def test_category_config_without_investment_plan_is_unaffected():
    # regression: existing category dashboards must render exactly as before —
    # this key must be absent (not an empty dict) so callers can tell the
    # capability was never invoked
    cfg = {"report_type": "category_portfolio", "meta": {}, "portfolio": []}
    data = data_mod.build_dashboard_data(cfg)
    assert data.get("investment") is None


def test_investment_plan_with_invalid_schema_raises_config_error():
    cfg = _category_cfg(modules=[{"id": "discount"}])
    try:
        data_mod.build_dashboard_data(cfg)
    except schema.InvestmentConfigError as e:
        assert "discount" in str(e)
        return
    raise AssertionError("expected InvestmentConfigError for forbidden lever")


def test_investment_excludes_exit_verdict_sku_from_allocation():
    cfg = _category_cfg()
    cfg["portfolio"][0]["verdict"] = "exit"
    try:
        data_mod.build_dashboard_data(cfg)
    except schema.InvestmentConfigError as e:
        assert "exit" in str(e)
        return
    raise AssertionError("expected InvestmentConfigError for exit-verdict cell")


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
