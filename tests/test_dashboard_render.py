#!/usr/bin/env python3
import importlib.util
import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".claude" / "skills" / "sm-causal-personalization" / "scripts"
REPORT_PATH = SCRIPTS / "generate_report.py"
DATA_PATH = SCRIPTS / "dashboard_data.py"
RENDER_PATH = SCRIPTS / "dashboard_render.py"
SKU_CONFIG = ROOT / ".claude" / "skills" / "sm-causal-personalization" / "examples" / "sample-sku-en-config.json"
CAT_CONFIG = ROOT / ".claude" / "skills" / "sm-causal-personalization" / "examples" / "aurora-airpurifier-category-config.json"


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


rpt = _load_module("generate_report", REPORT_PATH)
data_mod = _load_module("dashboard_data", DATA_PATH)
render_mod = _load_module("dashboard_render", RENDER_PATH)


def _html(path):
    cfg = json.loads(path.read_text(encoding="utf-8"))
    rpt.validate_and_resolve(cfg.get("numbers", {}))
    return render_mod.render_dashboard(data_mod.build_dashboard_data(cfg))


def test_sku_dashboard_html_contains_core_sections():
    html = _html(SKU_CONFIG)
    for marker in ["<!doctype html>", "decision-dashboard", "Economics", "Channel Screen", "Treatment Gates", "Evidence Ledger"]:
        assert marker in html, marker
    assert "Vela BrewPro B1" in html
    assert "Search" in html
    assert "2,797 CZK" in html
    assert "<strong>Unit margin</strong>\n  <span>Needs data</span>" not in html
    assert "__PLACEHOLDER__" not in html


def test_sku_dashboard_renders_dimensions_and_measurement_plan():
    # regression: dashboard_data.py has always built data["dimensions"] and
    # data["measurement"] from cfg["dimensions"]/cfg["measurement_plan"], but
    # dashboard_render.py had no _dimensions()/_measurement() renderer at
    # all — the D-dimension table and measurement plan silently never
    # appeared in the interactive cockpit for any single-SKU report.
    cfg = copy.deepcopy(rpt.DEMO_CONFIG)
    cfg["dimensions"] = [{
        "id": "D1", "name": "Existing dead-zone complainers", "mechanism": "Has an unmet pain point",
        "proxy": "Search intent for coverage-problem terms", "entry_score": "5/5",
        "verdict": "Retain", "resolution_status": "open",
    }]
    cfg["measurement_plan"] = {
        "maturity": "L0", "primary_metric": "Incremental CAC per channel",
        "secondary_metrics": ["PDP conversion rate"],
        "scale_up_rule": "Scale once holdout confirms CAC under ceiling",
        "pause_rule": "Pause if incremental CAC exceeds 2x ceiling for 7 days",
        "gcg_design": "Hold out 25% of spend as a global control group",
    }
    rpt.validate_and_resolve(cfg.get("numbers", {}))
    html = render_mod.render_dashboard(data_mod.build_dashboard_data(cfg))
    assert 'id="dimensions"' in html
    assert "Existing dead-zone complainers" in html
    assert 'id="measurement"' in html
    assert "Incremental CAC per channel" in html
    assert "Hold out 25%" in html


def test_category_dashboard_html_contains_portfolio_sections():
    html = _html(CAT_CONFIG)
    for marker in ["Portfolio Verdict", "Tier Map", "Diagnosis Lenses", "SKU Matrix"]:
        assert marker in html, marker
    assert "Aurora A3" in html
    assert "L1" in html


def test_category_dashboard_follows_the_five_question_spine():
    # regression: the category dashboard used to be a flat stack of sections
    # with no chapter bands and no one-line answers — the reading line
    # (call → why → play → execution → receipts) existed only in the
    # document report. Now both renderers share it.
    html = _html(CAT_CONFIG)
    assert html.count('class="chapter-band section"') == 5
    for ch in ("ch1", "ch2", "ch3", "ch4", "ch5"):
        assert f'id="{ch}"' in html, f"missing chapter band {ch}"
    # reading order: the call before the why before the receipts
    assert html.index('id="ch1"') < html.index('id="ch2"') < html.index('id="ch5"')
    # ch1's answer carries the investment verdict (aurora has investment_plan)
    ch1_chunk = html[html.index('id="ch1"'):html.index('id="ch2"')]
    assert "PLN" in ch1_chunk
    # diagnosis lives in ch2, tier map + skus in ch3, activation cards in ch4
    assert html.index('id="ch2"') < html.index('id="diagnosis"') < html.index('id="ch3"')
    assert html.index('id="ch3"') < html.index('id="tiers"') < html.index('id="ch4"')
    assert html.index('id="ch4"') < html.index('id="invest-tasks"') < html.index('id="ch5"')


def test_category_dashboard_zh_config_renders_localized_section_titles():
    # regression: section titles were hardcoded English, so a zh config
    # rendered a mixed-language dashboard ("Tier Map", "Diagnosis Lenses",
    # "Evidence Ledger" over Chinese content).
    cfg = json.loads(CAT_CONFIG.read_text(encoding="utf-8"))
    cfg["meta"]["lang"] = "zh"
    rpt.validate_and_resolve(cfg.get("numbers", {}))
    html = render_mod.render_dashboard(data_mod.build_dashboard_data(cfg))
    assert "价格带地图" in html
    assert "类目诊断" in html
    assert "证据台账" in html
    for english_leak in ("Tier Map", "Diagnosis Lenses", "SKU Matrix", "Evidence Ledger"):
        assert english_leak not in html, f"hardcoded English title leaked: {english_leak}"


def test_category_dashboard_sku_cards_are_ordered_grow_first():
    html = _html(CAT_CONFIG)
    skus_chunk = html[html.index('id="skus"'):html.index('id="handoff"')]
    # aurora: A3 is grow, A3 Plus is exit — grow must render before exit
    assert skus_chunk.index("Aurora A3") < skus_chunk.index("Aurora A3 Plus")


def test_investment_kpis_render_whole_numbers_not_false_precision():
    html = _html(CAT_CONFIG)
    kpi_chunk = html[html.index('id="invest-kpis"'):html.index('id="ch2"')]
    import re
    # money/units KPIs must not carry decimals; only roi/lambda keep 2 (x-suffixed)
    decimals = [m for m in re.findall(r'<strong>([\d,]+\.\d+)[^<]*</strong>', kpi_chunk)
                if not m.endswith("0")]
    for d in decimals:
        # any decimal value present must belong to an x-ratio card
        idx = kpi_chunk.index(d)
        assert "x" in kpi_chunk[idx:idx + len(d) + 4], f"false-precision KPI value: {d}"


def test_diagnosis_cards_show_invest_stance_badge_when_configured():
    cfg = json.loads(CAT_CONFIG.read_text(encoding="utf-8"))
    cfg["diagnosis"][0]["invest_stance"] = "invest"
    cfg["diagnosis"][1]["invest_stance"] = "fix"
    rpt.validate_and_resolve(cfg.get("numbers", {}))
    html = render_mod.render_dashboard(data_mod.build_dashboard_data(cfg))
    diag = html[html.index('id="diagnosis"'):html.index('id="invest-frontier"')]
    assert 'class="stance stance-invest"' in diag
    assert 'class="stance stance-fix"' in diag
    assert "Invest more" in diag
    assert "Fix first, then fund" in diag


def test_tier_map_is_a_drilldown_from_tier_to_sku_to_funded_modules():
    html = _html(CAT_CONFIG)
    tiers = html[html.index('id="tiers"'):html.index('id="skus"')]
    assert 'class="drill drill-tier"' in tiers
    assert 'class="drill drill-sku"' in tiers
    # a funded SKU's module spend rows appear inside its drill
    assert 'class="drill-module-row"' in tiers


def test_frontier_renders_per_business_line_panels():
    html = _html(CAT_CONFIG)
    frontier = html[html.index('id="invest-frontier"'):html.index('id="ch3"')]
    # aurora has entry/mid/premium tiers with eligible cells -> group panels
    assert 'class="inv-group-grid"' in frontier
    assert frontier.count('inv-panel-meta') >= 2


def test_ch5_sections_are_folded_shut_by_default():
    html = _html(CAT_CONFIG)
    ch5 = html[html.index('id="ch5"'):]
    assert ch5.count('<details class="fold section">') >= 3
    assert "<details open" not in ch5


def test_chapter_bands_carry_narrative_bridges():
    html = _html(CAT_CONFIG)
    assert html.count('class="ch-bridge"') == 5


def test_activation_cards_carry_owner_and_stop_rule_from_cells():
    cfg = json.loads(CAT_CONFIG.read_text(encoding="utf-8"))
    cfg["investment_plan"]["cells"][0]["owner"] = "Growth lead A"
    cfg["investment_plan"]["cells"][0]["stop_rule"] = "Stop below 1.3x marginal ROI"
    rpt.validate_and_resolve(cfg.get("numbers", {}))
    html = render_mod.render_dashboard(data_mod.build_dashboard_data(cfg))
    tasks_chunk = html[html.index('id="invest-tasks"'):]
    assert "Growth lead A" in tasks_chunk
    assert "Stop below 1.3x marginal ROI" in tasks_chunk


def test_dashboard_cli_demo_renders_to_file():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "dashboard.html"
        proc = subprocess.run(
            [sys.executable, str(REPORT_PATH), "--demo", "--format", "dashboard", "--output", str(out)],
            capture_output=True, text=True)
        assert proc.returncode == 0, proc.stderr
        html = out.read_text(encoding="utf-8")
        assert "DemoProduct" in html
        assert "decision-dashboard" in html
        assert "30 USD" in html
        assert "18 USD" in html


def test_dashboard_detail_payload_is_escaped():
    cfg = copy.deepcopy(rpt.DEMO_CONFIG)
    cfg["decision_memo"]["thesis"] = "</script><img src=x onerror=alert(1)>"
    rpt.validate_and_resolve(cfg.get("numbers", {}))
    html = render_mod.render_dashboard(data_mod.build_dashboard_data(cfg))
    assert "<img src=x" not in html
    assert "</script><img" not in html
    assert "\\u003c/script\\u003e" in html
    assert "escapeHtml(detail.text)" in html


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
