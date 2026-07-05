#!/usr/bin/env python3
"""Tests for investment-plan rendering in generate_report.py (document) and
dashboard_render.py (interactive cockpit) — both must produce real markup
(<svg>/<polyline>, a real .heatmap grid) for the frontier and budget-matrix
charts, not just spec-dict title strings. Also covers backward compat: a
category config without investment_plan must render unaffected in both."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".claude" / "skills" / "sm-causal-personalization" / "scripts"


def _load(name: str):
    # see other test files' identical helper: a module defining an exception
    # class (investment_schema.InvestmentConfigError) must be loaded exactly
    # once per process so `except module.SomeError` matches across loaders.
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


rpt = _load("generate_report")
dd = _load("dashboard_data")
dr = _load("dashboard_render")

_CELL = {
    "id": "be3_search", "sku": "BE3", "module": "search", "channel": "Google Search",
    "tau_hat": 0.025, "tau_source": "randomized_hte", "measurement_gate": "holdout",
    "reachable_population": 10000, "unit_margin": 120, "max_spend": 3000,
    "saturation_k": 0.001, "readiness": 1.0,
}


def _cfg(lang="en"):
    return {
        "report_type": "category_portfolio",
        "meta": {"product": "Test Portfolio", "market": "Testland", "lang": lang},
        "portfolio": [{"sku": "BE3", "verdict": "grow"}, {"sku": "AX1", "verdict": "exit"}],
        "investment_plan": {
            "currency": "RON", "planning_period": "2026-Q3", "total_budget": 4000,
            "required_mroi": 1.2, "budget_step": 1000,
            "modules": [{"id": "search", "label": "Search"}],
            "cells": [dict(_CELL)],
        },
    }


# ── generate_report.py (document report) ─────────────────────────────────────

def test_document_report_renders_all_five_investment_sections():
    html = rpt.generate_category_html(_cfg(), {})
    for sid in ("inv1", "inv2", "inv3", "inv4", "inv5"):
        assert f'id="{sid}"' in html, f"missing investment section {sid}"


def test_document_frontier_is_real_svg_not_a_spec_string():
    html = rpt.generate_category_html(_cfg(), {})
    assert "<svg" in html and "<polyline" in html


def test_document_budget_matrix_reuses_the_heatmap_css_grid():
    html = rpt.generate_category_html(_cfg(), {})
    assert 'class="heatmap"' in html
    assert "inv-conf-dot" in html


def test_document_report_without_investment_plan_has_no_investment_sections():
    cfg = {"report_type": "category_portfolio", "meta": {}, "portfolio": []}
    html = rpt.generate_category_html(cfg, {})
    for sid in ("inv1", "inv2", "inv3", "inv4", "inv5"):
        assert f'id="{sid}"' not in html


def test_document_ch1_answer_states_the_investment_verdict():
    html = rpt.generate_category_html(_cfg(), {})
    idx = html.index('id="ch1"')
    ch1_chunk = html[idx:idx + 4000]
    assert "RON" in ch1_chunk


def test_document_report_renders_in_zh_with_investment_labels():
    html = rpt.generate_category_html(_cfg(lang="zh"), {})
    assert "预算花在哪" in html
    assert "钱越花越多" in html


# ── dashboard_render.py (interactive cockpit) ─────────────────────────────────

def test_dashboard_renders_all_investment_sections():
    data = dd.build_dashboard_data(_cfg())
    html = dr.render_dashboard(data)
    for sid in ("invest-kpis", "invest-never-funded", "invest-frontier",
               "invest-matrix", "invest-tasks", "invest-confidence"):
        assert f'id="{sid}"' in html, f"missing dashboard section {sid}"


def test_dashboard_frontier_is_real_svg():
    data = dd.build_dashboard_data(_cfg())
    html = dr.render_dashboard(data)
    assert "<svg" in html and "<polyline" in html


def test_dashboard_budget_matrix_reuses_heatmap_grid():
    data = dd.build_dashboard_data(_cfg())
    html = dr.render_dashboard(data)
    assert "class='heatmap'" in html
    assert "inv-conf-dot" in html


def test_dashboard_without_investment_plan_has_no_investment_sections():
    cfg = {"report_type": "category_portfolio", "meta": {}, "portfolio": []}
    data = dd.build_dashboard_data(cfg)
    assert data.get("investment") is None
    html = dr.render_dashboard(data)
    for sid in ("invest-kpis", "invest-frontier", "invest-matrix"):
        assert f'id="{sid}"' not in html


def test_dashboard_never_funded_lists_confidence_blocked_cell():
    # a second, distinct SKU (still grow/hold) whose evidence is missing —
    # schema requires tau_source='missing' cells to carry no tau_hat and to
    # name needed_from; the engine then blocks it on computed confidence.
    # (An excluded-verdict cell can't reach this codepath at all: schema
    # validation rejects harvest/exit-sku cells before the engine ever runs.)
    cfg = _cfg()
    cfg["portfolio"].append({"sku": "4G5", "verdict": "hold"})
    cfg["investment_plan"]["cells"].append({
        "id": "g5_search", "sku": "4G5", "module": "search", "channel": "Google Search",
        "tau_source": "missing", "needed_from": "local pilot",
        "reachable_population": 10000, "unit_margin": 120, "max_spend": 3000,
        "saturation_k": 0.001, "readiness": 1.0,
    })
    data = dd.build_dashboard_data(cfg)
    html = dr.render_dashboard(data)
    idx = html.index('id="invest-never-funded"')
    chunk = html[idx:idx + 2000]
    assert "4G5" in chunk


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
