#!/usr/bin/env python3
import copy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".claude" / "skills" / "sm-causal-personalization" / "scripts"
DATA_PATH = SCRIPTS / "dashboard_data.py"
REPORT_PATH = SCRIPTS / "generate_report.py"
SKU_CONFIG = ROOT / ".claude" / "skills" / "sm-causal-personalization" / "examples" / "sample-sku-en-config.json"
CAT_CONFIG = ROOT / ".claude" / "skills" / "sm-causal-personalization" / "examples" / "aurora-airpurifier-category-config.json"


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


data_mod = _load_module("dashboard_data", DATA_PATH)
rpt = _load_module("generate_report", REPORT_PATH)


def _config(path):
    cfg = json.loads(path.read_text(encoding="utf-8"))
    rpt.validate_and_resolve(cfg.get("numbers", {}))
    return cfg


def test_sku_config_builds_dashboard_data():
    data = data_mod.build_dashboard_data(_config(SKU_CONFIG))
    assert data["kind"] == "sku"
    assert data["meta"]["product"] == "Vela BrewPro B1"
    assert data["overview"]["verdict"] == "conditional"
    assert data["kpis"]
    assert any(c["name"].startswith("Search") for c in data["channels"])
    assert any(t["id"] == "A1" for t in data["treatments"])
    assert data["evidence"]["missing"]
    derived = {row["id"]: row for row in data["evidence"]["derived"]}
    assert derived["unit_margin"]["value_text"] == "2,797 CZK"


def test_category_config_builds_portfolio_dashboard_data():
    data = data_mod.build_dashboard_data(_config(CAT_CONFIG))
    assert data["kind"] == "category_portfolio"
    assert data["meta"]["product"] == "Aurora Air Purifiers"
    assert data["portfolio"]["verdict_counts"]["grow"] == 3
    assert len(data["portfolio"]["tiers"]) == 3
    assert len(data["portfolio"]["diagnosis"]) == 6
    assert any(row["sku"] == "Aurora A3" for row in data["portfolio"]["skus"])


def test_missing_numbers_stay_missing():
    data = data_mod.build_dashboard_data(_config(SKU_CONFIG))
    missing = {row["id"]: row for row in data["evidence"]["missing"]}
    assert "search_cpc" in missing
    assert missing["search_cpc"]["value"] is None
    assert "Keyword Planner" in missing["search_cpc"]["needed_from"]


def test_demo_config_has_readable_fallbacks():
    cfg = copy.deepcopy(rpt.DEMO_CONFIG)
    rpt.validate_and_resolve(cfg.get("numbers", {}))
    data = data_mod.build_dashboard_data(cfg)
    assert data["meta"]["product"] == "DemoProduct"
    assert data["heatmap"]["columns"]
    assert data["heatmap"]["rows"]
    first = data["heatmap"]["columns"][0]
    assert first["id"] and first["label"]
    # a grid inferred from verdicts must say so — it is not real data
    assert data["heatmap"]["synthetic"] is True


def test_real_heatmap_scores_are_used_not_synthesized():
    # regression: the dashboard used to ignore cfg["heatmap"] and fabricate
    # grades from channel verdicts, violating the no-invented-numbers stance
    cfg = copy.deepcopy(rpt.DEMO_CONFIG)
    cfg["heatmap"] = {
        "channels": ["Search", "Social"],
        "dimensions": ["D1", "D2"],
        "dim_labels": {"D1": "Battery pain", "D2": "Android users"},
        "scores": {"Search": {"D1": "H", "D2": "T"}, "Social": {"D1": "A", "D2": "N"}},
    }
    rpt.validate_and_resolve(cfg.get("numbers", {}))
    data = data_mod.build_dashboard_data(cfg)
    hm = data["heatmap"]
    assert hm["synthetic"] is False
    assert [c["label"] for c in hm["columns"]] == ["Battery pain", "Android users"]
    by_name = {r["channel_name"]: r["grades"] for r in hm["rows"]}
    assert by_name["Search"] == ["H", "T"]
    assert by_name["Social"] == ["A", "N"]


def test_budget_rows_reach_the_dashboard():
    # regression: budgets read cfg["budget"] but the real schema field is
    # budget_rows, so the dashboard budget panel was always empty
    cfg = copy.deepcopy(rpt.DEMO_CONFIG)
    cfg["budget_rows"] = [
        {"phase": "P1", "item": "Search pilot", "budget_id": "price", "condition": "gate clears"},
        {"phase": "P2", "item": "Scale", "budget_display": "unsized", "condition": "checkpoint"},
    ]
    rpt.validate_and_resolve(cfg.get("numbers", {}))
    data = data_mod.build_dashboard_data(cfg)
    assert len(data["budgets"]) == 2
    assert data["budgets"][0]["budget_text"].startswith("100")
    assert data["budgets"][1]["budget_text"] == "unsized"


def test_dashboard_speaks_the_config_language():
    cfg = copy.deepcopy(rpt.DEMO_CONFIG)
    cfg["meta"]["lang"] = "zh"
    rpt.validate_and_resolve(cfg.get("numbers", {}))
    data = data_mod.build_dashboard_data(cfg)
    assert data["strings"]["ch1_question"] == "这钱到底花不花？"
    assert data["strings"]["grade_A"] == "别碰"
    assert data["chapter_answers"]["ch1"].startswith("先不花")
    # dimension fields follow the real schema
    cfg["dimensions"] = [{"id": "D1", "name": "电池焦虑", "mechanism": "十天续航",
                          "proxy": "关键词", "entry_score": "4/5",
                          "verdict": "Retain", "resolution_status": "open"}]
    data = data_mod.build_dashboard_data(cfg)
    dim = data["dimensions"][0]
    assert dim["label"] == "电池焦虑" and dim["logic"] == "十天续航"
    assert dim["entry_score"] == "4/5" and dim["status"] == "open"


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
