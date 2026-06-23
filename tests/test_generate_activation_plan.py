#!/usr/bin/env python3
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEN_PATH = ROOT / "skills" / "audience-activation" / "scripts" / "generate_activation_plan.py"

spec = importlib.util.spec_from_file_location("generate_activation_plan", GEN_PATH)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def sample_input(**overrides):
    data = {
        "country": "Hungary",
        "audience": "people interested in cycling",
    }
    data.update(overrides)
    return data


def test_hungary_cycling_generates_all_required_channels():
    plan = gen.generate_plan(sample_input())
    markdown = gen.render_markdown(plan)
    for channel in gen.REQUIRED_CHANNELS:
        assert channel in markdown, channel


def test_hungary_cycling_includes_budget_allocation():
    markdown = gen.render_markdown(gen.generate_plan(sample_input()))
    assert "## 4. Budget Allocation" in markdown
    assert "| budget level | Google Search |" in markdown
    assert "| low |" in markdown
    assert "| medium |" in markdown
    assert "| high |" in markdown
    assert "%" in markdown


def test_hungary_cycling_includes_roi_scores_with_confidence():
    markdown = gen.render_markdown(gen.generate_plan(sample_input()))
    assert "relative ROI score" in markdown
    assert "confidence" in markdown
    assert "planning estimate" in markdown.lower()
    assert "assumption note" in markdown.lower()


def test_purchase_goal_prioritizes_search_and_retargeting():
    plan = gen.generate_plan(sample_input(goal="purchase", first_party_data="website_visitors"))
    priorities = {row["channel"]: row["execution_priority"] for row in plan["channel_priority_map"]}
    assert priorities["Google Search"] == "High"
    assert priorities["CRM / retargeting"] == "High"
    budget = plan["budget_allocation"]["medium"]
    assert budget["Google Search"] >= budget["YouTube / video"]
    assert budget["CRM / retargeting"] >= budget["Display / programmatic / contextual"]


def test_unknown_budget_uses_percentages_not_fake_currency():
    markdown = gen.render_markdown(gen.generate_plan(sample_input(budget_level="unknown")))
    assert "%" in markdown
    for fake_currency in ["€", "$", "HUF", "USD", "EUR"]:
        assert fake_currency not in markdown


if __name__ == "__main__":
    tests = [name for name in globals() if name.startswith("test_")]
    failures = 0
    for name in tests:
        try:
            globals()[name]()
            print(f"PASS {name}")
        except Exception as exc:
            failures += 1
            print(f"FAIL {name}: {exc}")
    raise SystemExit(1 if failures else 0)
