#!/usr/bin/env python3
"""Tests for the investment dashboard's HTE core contract."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".claude" / "skills" / "sm-causal-personalization" / "scripts"


def _load(name: str):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


schema = _load("investment_schema")
engine = _load("investment_engine")
hte_core = _load("hte_core")


def _cell(**overrides):
    base = {
        "id": "be3_search",
        "sku": "BE3",
        "module": "search",
        "channel": "Search",
        "tau_hat": 0.026,
        "tau_source": "randomized_hte",
        "validation_ref": "be3_search_holdout",
        "measurement_gate": "geo_holdout",
        "reachable_population": 12000,
        "unit_margin": 120,
        "max_spend": 4000,
        "saturation_k": 0.001,
        "readiness": 1.0,
    }
    base.update(overrides)
    return base


def _hte_validation():
    return {
        "status": "available",
        "method": "DR learner on randomized holdout",
        "holdout_n": 24000,
        "min_auuc": 0.15,
        "max_calibration_mae": 0.02,
        "validation_refs": [
            {
                "id": "be3_search_holdout",
                "cells": ["be3_search"],
                "learner": "dr_learner",
                "qini_auuc": 0.27,
                "calibration_mae": 0.011,
                "policy_value_ipw": 18200,
            }
        ],
        "qini_curve": [
            {"targeted_pct": 0, "cumulative_lift_pct": 0},
            {"targeted_pct": 20, "cumulative_lift_pct": 38},
            {"targeted_pct": 40, "cumulative_lift_pct": 62},
            {"targeted_pct": 60, "cumulative_lift_pct": 78},
            {"targeted_pct": 80, "cumulative_lift_pct": 91},
            {"targeted_pct": 100, "cumulative_lift_pct": 100},
        ],
        "decile_calibration": [
            {"decile": 1, "predicted_tau": 0.052, "observed_lift": 0.049, "audience_pct": 10},
            {"decile": 2, "predicted_tau": 0.039, "observed_lift": 0.037, "audience_pct": 10},
            {"decile": 3, "predicted_tau": 0.026, "observed_lift": 0.025, "audience_pct": 10},
        ],
        "tau_distribution": [
            {"bucket": "<=0", "share": 0.18},
            {"bucket": "0-1%", "share": 0.22},
            {"bucket": "1-3%", "share": 0.35},
            {"bucket": ">3%", "share": 0.25},
        ],
    }


def test_schema_requires_randomized_hte_cells_to_name_a_validation_ref():
    cfg = {
        "portfolio": [{"sku": "BE3", "verdict": "grow"}],
        "investment_plan": {
            "modules": [{"id": "search"}],
            "cells": [_cell(validation_ref=None)],
        },
    }
    errors = schema.validate_investment_plan(cfg)
    assert any("validation_ref" in e for e in errors)


def test_hte_summary_marks_validated_refs_and_returns_chart_specs():
    summary = hte_core.build_hte_summary(_hte_validation(), [_cell()])
    assert summary["status"] == "available"
    assert summary["method"] == "DR learner on randomized holdout"
    assert summary["validated_cell_ids"] == {"be3_search"}
    assert summary["validation_refs"][0]["passes_gate"] is True
    assert summary["charts"]["qini"]["points"][1] == (20, 38)
    assert summary["charts"]["decile_calibration"]["rows"][0]["predicted_tau"] == 0.052
    assert summary["charts"]["tau_distribution"]["bins"][2]["bucket"] == "1-3%"


def test_hte_validation_controls_validated_confidence_badge():
    cells = hte_core.annotate_cells_with_hte_validation([_cell()], _hte_validation())
    assert cells[0]["_hte_validated"] is True
    assert engine.confidence_badge(cells[0]) == "validated"

    no_validation = hte_core.annotate_cells_with_hte_validation([_cell()], {})
    assert no_validation[0]["_hte_validated"] is False
    assert engine.confidence_badge(no_validation[0]) == "assumption_grade"


# ── third gate: interval coverage (CausalDS arXiv 2607.08093 — nominal 95%
#    intervals covered only 20-71% empirically; overconfidence is the norm) ──

def test_interval_coverage_gate_rejects_overconfident_refs():
    hv = _hte_validation()
    hv["min_interval_coverage"] = 0.85
    hv["validation_refs"][0]["interval_coverage"] = 0.62  # overconfident intervals
    summary = hte_core.build_hte_summary(hv, [_cell()])
    assert summary["validation_refs"][0]["passes_gate"] is False
    assert summary["validated_cell_ids"] == set()


def test_interval_coverage_gate_passes_honest_refs():
    hv = _hte_validation()
    hv["min_interval_coverage"] = 0.85
    hv["validation_refs"][0]["interval_coverage"] = 0.9
    summary = hte_core.build_hte_summary(hv, [_cell()])
    assert summary["validation_refs"][0]["passes_gate"] is True
    assert summary["validated_cell_ids"] == {"be3_search"}


def test_interval_coverage_gate_requires_coverage_evidence_when_configured():
    # min_interval_coverage set but no coverage supplied anywhere -> the ref
    # cannot prove its intervals are honest -> gate fails
    hv = _hte_validation()
    hv["min_interval_coverage"] = 0.85
    summary = hte_core.build_hte_summary(hv, [_cell()])
    assert summary["validation_refs"][0]["passes_gate"] is False


def test_interval_coverage_falls_back_to_decile_bounds():
    hv = _hte_validation()
    hv["min_interval_coverage"] = 0.6
    # 2 of 3 deciles covered -> fallback coverage 0.6667 >= 0.6 -> passes
    hv["decile_calibration"] = [
        {"decile": 1, "predicted_tau": 0.052, "observed_lift": 0.049, "tau_lo": 0.045, "tau_hi": 0.06},
        {"decile": 2, "predicted_tau": 0.039, "observed_lift": 0.037, "tau_lo": 0.035, "tau_hi": 0.044},
        {"decile": 3, "predicted_tau": 0.026, "observed_lift": 0.010, "tau_lo": 0.02, "tau_hi": 0.032},
    ]
    summary = hte_core.build_hte_summary(hv, [_cell()])
    assert summary["validation_refs"][0]["interval_coverage"] == round(2 / 3, 4)
    assert summary["validation_refs"][0]["passes_gate"] is True


def test_without_min_interval_coverage_the_old_two_gates_still_apply():
    # backward compat: configs that never set min_interval_coverage keep the
    # original AUUC + calibration behaviour
    summary = hte_core.build_hte_summary(_hte_validation(), [_cell()])
    assert summary["validation_refs"][0]["passes_gate"] is True
    assert summary["min_interval_coverage"] is None


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
