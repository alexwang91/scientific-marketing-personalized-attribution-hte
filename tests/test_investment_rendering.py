#!/usr/bin/env python3
"""Tests for investment-plan rendering in generate_report.py (document) and
dashboard_render.py (interactive cockpit) — both must produce real markup
(<svg>/<polyline>, a real .heatmap grid) for the frontier and budget-matrix
charts, not just spec-dict title strings. Also covers backward compat: a
category config without investment_plan must render unaffected in both."""
from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".claude" / "skills" / "sm-causal-personalization" / "scripts"
REPORT_PATH = SCRIPTS / "generate_report.py"


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


def test_every_chapter_answer_banner_mentions_its_own_investment_section():
    # regression: chapters 2-5 each gained an investment section (frontier /
    # matrix / activation cards / confidence+MMM) but their auto-generated
    # one-line "Short answer" banner used to only describe the pre-existing
    # portfolio-diagnosis content — silently ignoring the investment content
    # now also inside that same chapter. Each banner must say something
    # about what was actually added to its own chapter.
    html = rpt.generate_category_html(_cfg(), {})
    banners = dict(re.findall(
        r'<div class="chapter-head" id="(ch\d)">.*?<div class="ch-answer">(.*?)</div>',
        html, re.S))
    assert "frontier" in banners["ch2"]
    assert "budget matrix" in banners["ch3"]
    assert "activation" in banners["ch4"]
    assert "MMM" in banners["ch5"] or "validated test" in banners["ch5"]


def test_ch5_confidence_counts_only_funded_cells_not_the_full_candidate_set():
    # regression: the ch5 banner claims "of the funded budget", so its
    # validated/mmm/assumption counts must come from what actually got
    # funded (answer["allocation"]) — not inv["charts"]["confidence"],
    # which (correctly, for the section it drives) spans every eligible
    # cell whether or not it cleared the ROI floor. Construct a second,
    # confidence-"validated" cell whose ROI never clears required_mroi:
    # it's eligible (not "blocked"), so it inflates the all-cells count,
    # but must NOT inflate the ch5 banner's funded-only count.
    cfg = _cfg()
    cfg["investment_plan"]["cells"].append({
        "id": "be3_search_lowroi", "sku": "BE3", "module": "search", "channel": "Google Search",
        "tau_hat": 0.0001, "tau_source": "randomized_hte", "measurement_gate": "holdout",
        "reachable_population": 100, "unit_margin": 1, "max_spend": 2000,
        "saturation_k": 0.0001, "readiness": 1.0,
    })
    inv = rpt._get_investment_view(cfg)
    all_cells_validated = inv["charts"]["confidence"]["validated"]
    funded_validated = sum(1 for r in inv["answer"]["allocation"] if r["confidence"] == "validated")
    assert all_cells_validated == 2, "the low-ROI cell should still count as validated confidence"
    assert funded_validated == 1, "but only the cell that actually got funded should count as funded"

    banners = dict(re.findall(
        r'<div class="chapter-head" id="(ch\d)">.*?<div class="ch-answer">(.*?)</div>',
        rpt.generate_category_html(cfg, {}), re.S))
    assert "1 cell(s) rest on a validated test" in banners["ch5"]


def test_ch4_investment_overlay_does_not_imply_a_false_subset_of_grow_skus():
    # regression: an earlier phrasing said "N of those are funded moves"
    # right after a sentence naming only the Grow-verdicted SKUs — but N
    # (funded SKU x module cells) can exceed the Grow SKU count, which
    # reads as a nonsensical subset claim ("6 of those 3").
    html = rpt.generate_category_html(_cfg(), {})
    idx = html.index('id="ch4"')
    ch4_chunk = html[idx:idx + 2000]
    assert "of those" not in ch4_chunk


def test_document_report_renders_in_zh_with_investment_labels():
    html = rpt.generate_category_html(_cfg(lang="zh"), {})
    assert "预算花在哪" in html
    assert "钱越花越多" in html


def test_cli_validate_only_catches_a_malformed_investment_plan():
    # regression: --validate-only used to only check the numbers{} provenance
    # contract, silently printing "Config valid" for a config whose
    # investment_plan would fail InvestmentConfigError at actual build time.
    cfg = _cfg()
    cfg["investment_plan"]["modules"] = [{"id": "discount"}]
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(cfg, f)
        path = f.name
    proc = subprocess.run(
        [sys.executable, str(REPORT_PATH), "--config", path, "--validate-only"],
        capture_output=True, text=True)
    assert proc.returncode == 2, proc.stdout
    assert "discount" in proc.stderr


def test_cli_validate_only_passes_a_well_formed_investment_plan():
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(_cfg(), f)
        path = f.name
    proc = subprocess.run(
        [sys.executable, str(REPORT_PATH), "--config", path, "--validate-only"],
        capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert "Config valid" in proc.stderr


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
