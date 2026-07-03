#!/usr/bin/env python3
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "skills" / "audience-activation" / "scripts" / "validate_activation_plan.py"
GEN_PATH = ROOT / "skills" / "audience-activation" / "scripts" / "generate_activation_plan.py"

v_spec = importlib.util.spec_from_file_location("validate_activation_plan", VALIDATOR_PATH)
validator = importlib.util.module_from_spec(v_spec)
v_spec.loader.exec_module(validator)

g_spec = importlib.util.spec_from_file_location("generate_activation_plan", GEN_PATH)
gen = importlib.util.module_from_spec(g_spec)
g_spec.loader.exec_module(gen)


def valid_markdown():
    return gen.render_markdown(gen.generate_plan({
        "country": "Hungary",
        "audience": "people interested in cycling",
        "goal": "purchase",
    }))


def test_validator_rejects_missing_required_sections():
    bad = valid_markdown().replace("## 4. Budget Allocation", "## 4. Removed")
    errors = validator.validate_markdown(bad)
    assert any("missing required section" in e for e in errors), errors


def test_validator_rejects_deterministic_targeting_claims():
    bad = valid_markdown() + "\nThis plan can deterministically reach every person interested in cycling.\n"
    errors = validator.validate_markdown(bad)
    assert any("deterministic" in e for e in errors), errors


def test_validator_rejects_roi_without_assumption_note():
    bad = valid_markdown().replace("assumption note", "removed note")
    errors = validator.validate_markdown(bad)
    assert any("assumption note" in e.lower() for e in errors), errors


def test_high_priority_row_mentioning_channel_is_not_skipped():
    # regression: rows whose cells contain the word "channel" (e.g. "omni-channel")
    # were treated as header rows, so a missing execution spec went undetected
    md = valid_markdown().replace(
        "| Google Search | conversion | Local-language intent keywords",
        "| Google Search | conversion | omni-channel intent keywords")
    assert "Google Search" in validator.high_priority_channels(md), \
        "Google Search dropped from high-priority list"
    bad = md.replace("### Google Search", "### Removed Spec")
    errors = validator.validate_markdown(bad)
    assert any("execution spec" in e and "Google Search" in e for e in errors), errors


def test_high_priority_channels_matches_generated_plan():
    plan = gen.generate_plan({
        "country": "Hungary",
        "audience": "people interested in cycling",
        "goal": "purchase",
        "first_party_data": "website_visitors",
    })
    expected = sorted(r["channel"] for r in plan["channel_priority_map"]
                      if r["execution_priority"] == "High")
    parsed = sorted(validator.high_priority_channels(gen.render_markdown(plan)))
    assert parsed == expected, (parsed, expected)


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
