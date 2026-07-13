#!/usr/bin/env python3
"""Tests for the audience-card contract (ref 18 audience-card)."""
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


aud = _load("audience_schema")


def _card(**overrides):
    base = {
        "id": "d2_comparison",
        "name": "对比型买家（研究过高端产品、价格敏感但非只看折扣）",
        "causal_role": "persuadable",
        "dimensions": {"funnel_state": "comparing", "price_sensitivity": "pays for proof"},
        "sizing": {
            "country_reachable": {"value": 2400000, "grade": "B", "source": "reach planner"},
            "category_or_intent_share": {"value": 0.18, "grade": "C", "source": "keyword volume"},
            "activation_match_rate": {"value": 0.6, "grade": "C", "source": "proxy fit estimate"},
            "eligibility_rate": {"value": 0.9, "grade": "B", "source": "shipping coverage"},
        },
        "reach": [
            {"platform": "Search", "proxy": "competitor + category queries",
             "match_quality": "high"},
            {"platform": "Social", "proxy": "broad interest in the category",
             "match_quality": "medium", "what_leaks": "includes sure-things already loyal"},
        ],
        "suppression": "exclude recent purchasers",
        "measurement": "geo holdout on the search arm",
        "weakest_assumption": "the 18% category share is a keyword-volume proxy, not measured",
    }
    base.update(overrides)
    return base


def _cfg(*cards):
    return {"audience_cards": list(cards)}


# ── opt-in / basic shape ──────────────────────────────────────────────────

def test_absent_audience_cards_is_not_an_error():
    assert aud.validate_audience_cards({}) == []


def test_empty_list_is_an_error():
    assert aud.validate_audience_cards({"audience_cards": []})


def test_a_well_formed_card_validates_clean():
    assert aud.validate_audience_cards(_cfg(_card())) == []


def test_card_requires_a_name():
    errs = aud.validate_audience_cards(_cfg(_card(name="")))
    assert any("requires a 'name'" in e for e in errs)


def test_duplicate_ids_rejected():
    errs = aud.validate_audience_cards(_cfg(_card(), _card()))
    assert any("duplicate audience card id" in e for e in errs)


# ── causal role (dimension 20) ────────────────────────────────────────────

def test_unknown_causal_role_rejected():
    errs = aud.validate_audience_cards(_cfg(_card(causal_role="high_value")))
    assert any("causal_role must be one of" in e for e in errs)


def test_unknown_causal_role_is_a_valid_state():
    assert aud.validate_audience_cards(_cfg(_card(causal_role="unknown"))) == []


# ── derived fields may not be raw input ───────────────────────────────────

def test_derived_size_may_not_be_set_on_the_card():
    errs = aud.validate_audience_cards(_cfg(_card(reachable_target_size=999)))
    assert any("reachable_target_size" in e and "derived" in e for e in errs)


# ── sizing chain honesty ──────────────────────────────────────────────────

def test_sizing_factor_requires_a_source():
    card = _card()
    card["sizing"]["category_or_intent_share"] = {"value": 0.18, "grade": "C"}
    errs = aud.validate_audience_cards(_cfg(card))
    assert any("requires a 'source'" in e for e in errs)


def test_share_above_one_rejected():
    card = _card()
    card["sizing"]["activation_match_rate"] = {"value": 1.4, "grade": "C", "source": "x"}
    errs = aud.validate_audience_cards(_cfg(card))
    assert any("must be ≤ 1" in e for e in errs)


def test_d_grade_precise_share_needs_needed_from():
    card = _card()
    card["sizing"]["category_or_intent_share"] = {"value": 0.18, "grade": "D", "source": "guess"}
    errs = aud.validate_audience_cards(_cfg(card))
    assert any("grade D" in e and "needed_from" in e for e in errs)


def test_d_grade_precise_share_with_needed_from_is_ok():
    card = _card()
    card["sizing"]["category_or_intent_share"] = {
        "value": 0.18, "grade": "D", "source": "guess", "needed_from": "reach planner pull"}
    assert aud.validate_audience_cards(_cfg(card)) == []


def test_stated_persuadable_share_needs_a_causal_source():
    card = _card()
    # a persuadable number with no source is the classic "who is persuadable
    # from platform data" error
    card["sizing"]["persuadable_share"] = {"value": 0.3, "grade": "C"}
    errs = aud.validate_audience_cards(_cfg(card))
    assert any("causal 'source'" in e or "requires a 'source'" in e for e in errs)


# ── reach / match quality ─────────────────────────────────────────────────

def test_bad_match_quality_rejected():
    card = _card()
    card["reach"][0]["match_quality"] = "great"
    errs = aud.validate_audience_cards(_cfg(card))
    assert any("match_quality must be one of" in e for e in errs)


def test_medium_match_quality_requires_what_leaks():
    card = _card()
    card["reach"] = [{"platform": "Social", "proxy": "broad interest", "match_quality": "low"}]
    errs = aud.validate_audience_cards(_cfg(card))
    assert any("requires 'what_leaks'" in e for e in errs)


def test_reach_entry_requires_a_proxy():
    card = _card()
    card["reach"] = [{"platform": "Search", "match_quality": "high"}]
    errs = aud.validate_audience_cards(_cfg(card))
    assert any("requires a 'proxy'" in e for e in errs)


# ── compute_sizing (the derived numbers) ──────────────────────────────────

def test_compute_sizing_multiplies_the_chain_and_inherits_worst_grade():
    got = aud.compute_sizing(_card())
    # 2,400,000 × 0.18 × 0.6 × 0.9 = 233,280
    assert round(got["reachable_target_size"]) == 233280
    # no persuadable_share supplied -> unknown, expected None
    assert got["persuadable_known"] is False
    assert got["expected_persuadable"] is None
    # worst of B, C, C, B -> C
    assert got["worst_grade"] == "C"


def test_compute_sizing_uses_persuadable_share_when_present():
    card = _card()
    card["sizing"]["persuadable_share"] = {
        "value": 0.3, "grade": "D", "source": "prior holdout", "needed_from": "fresh holdout"}
    got = aud.compute_sizing(card)
    assert got["persuadable_known"] is True
    # 233,280 × 0.3 = 69,984
    assert round(got["expected_persuadable"]) == 69984
    # worst now includes D
    assert got["worst_grade"] == "D"


def test_compute_sizing_without_country_reachable_cannot_size():
    card = _card()
    del card["sizing"]["country_reachable"]
    got = aud.compute_sizing(card)
    assert got["reachable_target_size"] is None
    assert got["expected_persuadable"] is None


def test_compute_sizing_on_a_card_with_no_sizing_is_all_none():
    got = aud.compute_sizing({"name": "qualitative only"})
    assert got["reachable_target_size"] is None
    assert got["worst_grade"] is None
    assert got["factors"] == []


# ── validate_or_raise ─────────────────────────────────────────────────────

def test_validate_or_raise_raises_on_bad_config():
    try:
        aud.validate_or_raise(_cfg(_card(causal_role="bogus")))
    except aud.AudienceConfigError as exc:
        assert "causal_role" in str(exc)
    else:
        raise AssertionError("expected AudienceConfigError")


def test_validate_or_raise_silent_on_good_config():
    aud.validate_or_raise(_cfg(_card()))


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
