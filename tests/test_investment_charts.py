#!/usr/bin/env python3
"""Tests for investment_charts.py — pure stdlib chart-spec generation."""
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


charts = _load("investment_charts")


def test_investment_answer_kpis_has_six_cards_with_tone():
    summary = {"recommended_spend": 91000, "incremental_units": 692,
               "incremental_gross_profit": 213800, "net_profit": 122800,
               "roi": 2.35, "lambda_star": 1.3}
    kpis = charts.investment_answer_kpis(summary, currency="RON")
    ids = {k["id"] for k in kpis}
    assert ids == {"spend", "units", "gross_profit", "net_profit", "roi", "lambda_star"}
    roi_kpi = next(k for k in kpis if k["id"] == "roi")
    assert roi_kpi["tone"] == "good"  # roi >= 1.0


def test_investment_answer_kpis_tone_is_bad_for_negative_roi():
    kpis = charts.investment_answer_kpis({"roi": -0.5, "net_profit": -100})
    roi_kpi = next(k for k in kpis if k["id"] == "roi")
    assert roi_kpi["tone"] == "bad"


def test_frontier_chart_has_two_single_axis_panels_not_dual_axis():
    frontier = [
        {"spend": 1000, "incremental_gross_profit": 2500, "marginal_roi": 2.5},
        {"spend": 2000, "incremental_gross_profit": 4200, "marginal_roi": 1.7},
    ]
    spec = charts.frontier_chart_spec(frontier, cutoff_spend=2000)
    assert spec["profit_panel"]["title"] and spec["roi_panel"]["title"]
    assert "series" not in spec  # no combined dual-axis series list
    assert spec["profit_panel"]["points"] == [(1000, 2500), (2000, 4200)]
    assert spec["roi_panel"]["cutoff_spend"] == 2000


def test_budget_matrix_contains_sku_and_module_axes_plus_confidence():
    allocation = [{"sku": "BE3", "module": "search", "spend": 1000, "roi": 2.2,
                  "confidence": "validated"}]
    spec = charts.budget_matrix_spec(allocation)
    assert spec["x_axis"] == ["search"]
    assert spec["y_axis"] == ["BE3"]
    assert spec["cells"][0]["confidence"] == "validated"


def test_budget_matrix_preserves_first_seen_axis_order():
    allocation = [
        {"sku": "BE3", "module": "search", "spend": 1, "roi": 1, "confidence": "validated"},
        {"sku": "4G5", "module": "retail_activation", "spend": 1, "roi": 1, "confidence": "assumption_grade"},
        {"sku": "BE3", "module": "retail_media", "spend": 1, "roi": 1, "confidence": "mmm_calibrated"},
    ]
    spec = charts.budget_matrix_spec(allocation)
    assert spec["x_axis"] == ["search", "retail_activation", "retail_media"]
    assert spec["y_axis"] == ["BE3", "4G5"]


def test_confidence_strip_counts_by_computed_badge():
    cells = [{"tau_source": "randomized_hte", "measurement_gate": "g", "_hte_validated": True},
             {"tau_source": "expert_assumption"}, {"tau_source": "missing"}]
    spec = charts.confidence_strip_spec(cells)
    assert spec["validated"] == 1
    assert spec["assumption_grade"] == 1
    assert spec["blocked"] == 1
    assert spec["mmm_calibrated"] == 0


def test_hte_chart_specs_are_real_dashboard_inputs():
    qini = charts.hte_qini_spec([
        {"targeted_pct": 0, "cumulative_lift_pct": 0},
        {"targeted_pct": 50, "cumulative_lift_pct": 74},
        {"targeted_pct": 100, "cumulative_lift_pct": 100},
    ], auuc=0.24)
    assert qini["status"] == "available"
    assert qini["points"] == [(0, 0), (50, 74), (100, 100)]
    assert qini["random_baseline"] == [(0, 0), (100, 100)]
    assert qini["auuc"] == 0.24

    deciles = charts.hte_decile_calibration_spec([
        {"decile": 1, "predicted_tau": 0.04, "observed_lift": 0.038},
        {"decile": 2, "predicted_tau": 0.03, "observed_lift": 0.028},
    ])
    assert deciles["rows"][0]["gap"] == 0.002

    distribution = charts.hte_tau_distribution_spec([
        {"bucket": "0-1%", "share": 0.4},
        {"bucket": "1-3%", "share": 0.6},
    ])
    assert distribution["bins"][1]["share"] == 0.6


def test_mmm_chart_specs_render_from_provided_summary_not_deferred():
    contribution = charts.mmm_contribution_spec([
        {"channel": "Search", "contribution": 1200},
        {"channel": "Retail media", "contribution": 2400},
    ])
    assert contribution["status"] == "available"
    assert contribution["bars"][0]["channel"] == "Retail media"

    adstock = charts.adstock_saturation_spec([
        {"channel": "Search", "points": [{"spend": 0, "response": 0}, {"spend": 1000, "response": 0.7}]}
    ])
    assert adstock["panels"][0]["points"] == [(0, 0), (1000, 0.7)]

    roas = charts.posterior_roas_spec([
        {"channel": "Search", "mean": 2.1, "lo": 1.4, "hi": 3.0}
    ])
    assert roas["intervals"][0]["mean"] == 2.1

    lift = charts.lift_calibration_spec([
        {"channel": "Search", "predicted": 0.05, "observed": 0.047}
    ])
    assert lift["points"][0] == (0.05, 0.047)


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
