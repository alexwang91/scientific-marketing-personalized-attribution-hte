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


def test_category_dashboard_html_contains_portfolio_sections():
    html = _html(CAT_CONFIG)
    for marker in ["Portfolio Verdict", "Tier Map", "Diagnosis Lenses", "SKU Matrix"]:
        assert marker in html, marker
    assert "Aurora A3" in html
    assert "L1" in html


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
