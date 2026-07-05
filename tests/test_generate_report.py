#!/usr/bin/env python3
"""Tests for generate_report.py — provenance contract, formula safety, rendering.

Stdlib-only: generate_report.py has no third-party dependencies.
"""
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = (ROOT / ".claude" / "skills" / "sm-causal-personalization"
               / "scripts" / "generate_report.py")

spec = importlib.util.spec_from_file_location("generate_report", REPORT_PATH)
rpt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rpt)


def _assumed(value, basis="test"):
    return {"provenance": "assumed", "basis": basis, "value": value}


def _derived(formula, inputs):
    return {"provenance": "derived", "formula": formula, "inputs": inputs}


def _raises_config_error(numbers, needle):
    try:
        rpt.validate_and_resolve(numbers)
    except rpt.ConfigError as exc:
        assert needle in str(exc), f"expected {needle!r} in: {exc}"
        return
    raise AssertionError(f"expected ConfigError containing {needle!r}")


def test_valid_formula_resolves():
    numbers = {
        "price": _assumed(100),
        "margin": _assumed(0.3),
        "unit_margin": _derived("price * margin", ["price", "margin"]),
    }
    rpt.validate_and_resolve(numbers)
    assert numbers["unit_margin"]["value"] == 30.0


def test_power_operator_rejected():
    # regression: '**' passed the old character-level check, so a formula like
    # 9**9**9 hung the build computing a 370-million-digit number
    numbers = {"a": _assumed(9), "boom": _derived("a**a**a", ["a"])}
    _raises_config_error(numbers, "unsupported syntax")


def test_attribute_chain_rejected():
    # regression: dots + identifiers + parens all passed the old character check,
    # opening an eval sandbox escape via attribute chains
    numbers = {
        "x": _assumed(1),
        "evil": _derived("().__class__.__base__.__subclasses__()", ["x"]),
    }
    _raises_config_error(numbers, "unsupported syntax")


def test_function_call_rejected():
    numbers = {"a": _assumed(2), "b": _derived("min(a, a)", ["a"])}
    _raises_config_error(numbers, "unsupported syntax")


def test_formula_identifier_must_be_listed_in_inputs():
    numbers = {"a": _assumed(2), "b": _derived("a * ghost", ["a"])}
    _raises_config_error(numbers, "'ghost' not listed in inputs")


def test_circular_derivation_raises():
    numbers = {
        "a": _derived("b + 1", ["b"]),
        "b": _derived("a + 1", ["a"]),
    }
    _raises_config_error(numbers, "circular derivation")


def test_interval_propagation_via_corners():
    numbers = {
        "cpc": _assumed([0.3, 1.2]),
        "cvr": _assumed([0.01, 0.03]),
        "cac": _derived("cpc / cvr", ["cpc", "cvr"]),
    }
    rpt.validate_and_resolve(numbers)
    assert numbers["cac"]["value"] == [10.0, 120.0]


def test_derived_from_missing_is_missing():
    numbers = {
        "cpc": {"provenance": "missing", "needed_from": "Keyword Planner"},
        "cvr": _assumed(0.02),
        "cac": _derived("cpc / cvr", ["cpc", "cvr"]),
    }
    rpt.validate_and_resolve(numbers)
    assert numbers["cac"]["value"] is None


def test_missing_number_must_not_carry_value():
    numbers = {"x": {"provenance": "missing", "needed_from": "somewhere", "value": 5}}
    _raises_config_error(numbers, "must NOT carry a value")


def test_unknown_horizon_is_build_error():
    # regression: decisions with a typo'd horizon were silently dropped
    cfg = copy.deepcopy(rpt.DEMO_CONFIG)
    cfg["decision_memo"]["decisions"][0]["horizon"] = "Now"  # wrong case
    try:
        rpt.generate_html(cfg)
    except rpt.ConfigError as exc:
        assert "horizon" in str(exc)
        return
    raise AssertionError("expected ConfigError for unknown horizon")


def test_rejected_options_render_as_never_do_in_chapter1():
    # regression: rejected_options silently disappeared when s_actions was removed;
    # they now render as the "Never do" section closing chapter 1 (the call page)
    html = rpt.generate_html(copy.deepcopy(rpt.DEMO_CONFIG))
    assert 'id="rej"' in html
    assert "Never do" in html
    assert "Influencer hero spend" in html
    assert html.index('id="rej"') < html.index('id="s2"'), "never-do must live in chapter 1"


def test_demo_report_renders_all_core_sections():
    html = rpt.generate_html(copy.deepcopy(rpt.DEMO_CONFIG))
    for marker in ["Decision Memo", "The Math", "cac-chart", "derivation"]:
        assert marker in html, f"missing {marker!r}"


def test_report_has_five_chapter_banners_with_answers():
    html = rpt.generate_html(copy.deepcopy(rpt.DEMO_CONFIG))
    assert html.count('class="chapter-head"') == 5
    assert html.count('class="ch-answer"') == 5
    for ch in ("ch1", "ch2", "ch3", "ch4", "ch5"):
        assert f'id="{ch}"' in html, f"missing chapter {ch}"
    # reading order is the reader's question order
    assert html.index('id="ch1"') < html.index('id="ch2"') < html.index('id="ch5"')


def test_chapter_answers_bilingual_and_key_parallel():
    import importlib.util
    sem_path = REPORT_PATH.parent / "report_semantics.py"
    spec = importlib.util.spec_from_file_location("report_semantics_t", sem_path)
    sem = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sem)
    assert set(sem.OPERATOR_STRINGS["en"]) == set(sem.OPERATOR_STRINGS["zh"]), \
        "operator string packs must stay key-parallel"
    zh_cfg = {"meta": {"lang": "zh"}}
    assert sem.S(zh_cfg, "ch1_question") == "这钱到底花不花？"
    assert sem.grade_label(zh_cfg, "A") == "别碰"
    assert sem.verdict_word({"meta": {"lang": "en"}}, "not-viable").startswith("money-losing")


def test_task_card_merge_links_tests_and_plays():
    import importlib.util
    sem_path = REPORT_PATH.parent / "report_semantics.py"
    spec = importlib.util.spec_from_file_location("report_semantics_t2", sem_path)
    sem = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sem)
    cfg = {
        "actions": [{"id": "A1", "action": "x"}, {"id": "A2", "action": "y"}],
        "test_plan": [{"name": "T1", "card": "A2"}, {"name": "T2"}],
        "priority_plays": [{"play": "P1", "card": "A2", "why_now": "w"},
                           {"play": "P2", "action": "loose"}],
    }
    merged = sem.merge_task_cards(cfg)
    assert [c["id"] for c in merged["cards"]] == ["A2", "A1"], "play rank orders cards"
    assert merged["cards"][0]["tests"][0]["name"] == "T1"
    assert merged["cards"][0]["play"]["why_now"] == "w"
    assert [t["name"] for t in merged["loose_tests"]] == ["T2"]
    assert len(merged["loose_plays"]) == 1


def test_old_config_without_new_fields_still_renders():
    # backward compat: a config with no card/owner/due/chapter_answers renders fine
    cfg = copy.deepcopy(rpt.DEMO_CONFIG)
    html = rpt.generate_html(cfg)
    assert 'class="chapter-head"' in html and "cac-chart" in html


def test_category_portfolio_uses_the_same_five_chapter_spine():
    # regression: category_portfolio used to render its own independent 6-section
    # layout (c0-c4 + evidence) instead of the ch1-ch5 spine the single-SKU
    # report uses — one report_type should not mean two different structures
    cfg = {
        "report_type": "category_portfolio",
        "meta": {"product": "Demo Category", "market": "Testland"},
        "portfolio": [
            {"sku": "S1", "verdict": "grow", "fourP": {}},
            {"sku": "S2", "verdict": "exit", "fourP": {}},
        ],
        "diagnosis": [{"lens": "L1", "title": "T1", "severity": "critical",
                       "evidence_grade": "hypothesis", "finding": "f", "implication": "i",
                       "recommendation": "r"}],
        "price_tiers": [],
        "numbers": {"x": {"provenance": "assumed", "basis": "b", "value": 1}},
    }
    html = rpt.generate_html(cfg)
    for ch in ("ch1", "ch2", "ch3", "ch4", "ch5"):
        assert f'id="{ch}"' in html, f"category report missing chapter {ch}"
    assert html.count('class="chapter-head"') == 5
    # severity capped to the evidence grade (hypothesis) shows in ch2's answer,
    # not the raw uncapped "critical" count
    assert "1 critical" not in html.split('id="ch2"')[1].split('id="ch3"')[0]


def test_embed_echarts_inlines_local_js():
    html = rpt.generate_html(copy.deepcopy(rpt.DEMO_CONFIG),
                             echarts_js="/*local echarts*/")
    assert "/*local echarts*/" in html
    assert "cdn.jsdelivr.net" not in html


def test_validate_only_without_numbers_key_exits_cleanly():
    # regression: --validate-only crashed with KeyError when cfg had no "numbers"
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump({"meta": {"product": "X"}}, f)
        path = f.name
    proc = subprocess.run(
        [sys.executable, str(REPORT_PATH), "--config", path, "--validate-only"],
        capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert "Config valid" in proc.stderr


def test_demo_dashboard_format_renders():
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        path = f.name
    proc = subprocess.run(
        [sys.executable, str(REPORT_PATH), "--demo", "--format", "dashboard", "--output", path],
        capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    html = Path(path).read_text(encoding="utf-8")
    assert "decision-dashboard" in html
    assert "DemoProduct" in html


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
