#!/usr/bin/env python3
"""Rendering tests for audience cards (ref 18) — report + dashboard, en + zh."""
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


gen = _load("generate_report")
dd = _load("dashboard_data")
dr = _load("dashboard_render")
aud_schema = _load("audience_schema")


def _card(**overrides):
    base = {
        "id": "d2",
        "name": "Comparison shoppers who researched the premium tier",
        "causal_role": "persuadable",
        "dimensions": {"funnel_state": "comparing", "price_sensitivity": "pays for proof"},
        "sizing": {
            "country_reachable": {"value": 2400000, "grade": "B", "source": "reach planner"},
            "category_or_intent_share": {"value": 0.18, "grade": "C", "source": "keyword volume"},
            "activation_match_rate": {"value": 0.6, "grade": "C", "source": "proxy fit"},
            "eligibility_rate": {"value": 0.9, "grade": "B", "source": "shipping coverage"},
            "persuadable_share": {"value": 0.3, "grade": "D", "source": "prior holdout",
                                  "needed_from": "fresh holdout"},
        },
        "reach": [
            {"platform": "Search", "proxy": "competitor + category queries", "match_quality": "high"},
            {"platform": "Social", "proxy": "broad category interest", "match_quality": "medium",
             "what_leaks": "includes already-loyal sure-things"},
        ],
        "suppression": "exclude recent purchasers",
        "measurement": "geo holdout on the search arm",
        "weakest_assumption": "the 18% share is a keyword proxy, not measured",
    }
    base.update(overrides)
    return base


def _cfg(lang="en", **extra):
    cfg = {"meta": {"lang": lang, "product": "Demo", "market": "Test"},
           "audience_cards": [_card()]}
    cfg.update(extra)
    return cfg


# ── document report section ───────────────────────────────────────────────

def test_report_section_shows_the_computed_reachable_number_and_worst_grade():
    html = gen.s_audience_cards(_cfg("en"))
    assert "233,280" in html            # 2.4M × .18 × .6 × .9
    assert "Reachable pool" in html
    # worst grade of the reach chain (B,C,C,B) is C
    assert 'background:#b8860b">C<' in html or ">C<" in html


def test_report_section_shows_persuadable_only_from_the_causal_chain():
    html = gen.s_audience_cards(_cfg("en"))
    assert "69,984" in html             # 233,280 × .30
    assert "Of which persuadable" in html


def test_report_section_localizes_to_zh():
    html = gen.s_audience_cards(_cfg("zh"))
    assert "可达盘子" in html
    assert "其中可说服" in html
    assert "会漏进谁" in html
    assert "Reachable pool" not in html


def test_report_section_absent_when_no_cards():
    assert gen.s_audience_cards({"meta": {"lang": "en"}}) == ""


def test_report_section_flags_unknown_persuadable():
    card = _card()
    del card["sizing"]["persuadable_share"]
    html = gen.s_audience_cards({"meta": {"lang": "en"}, "audience_cards": [card]})
    assert "Persuadable share unknown" in html
    assert "69,984" not in html


# ── dashboard data + render ───────────────────────────────────────────────

def test_dashboard_data_computes_and_carries_cards():
    data = dd.build_dashboard_data(_cfg("en"))
    cards = data["audience_cards"]
    assert len(cards) == 1
    assert cards[0]["reachable_text"] == "233,280"
    assert cards[0]["worst_grade"] == "C"
    assert cards[0]["persuadable_text"] == "69,984"


def test_dashboard_render_includes_audience_section_in_ch3():
    data = dd.build_dashboard_data(_cfg("zh"))
    html = dr.render_dashboard(data)
    assert 'id="audience"' in html
    assert "可达盘子" in html
    assert "aud-role-persuadable" in html


def test_category_dashboard_also_renders_audience_cards():
    cfg = {"report_type": "category_portfolio",
           "meta": {"lang": "en", "category": "X", "market": "Y"},
           "portfolio": [], "audience_cards": [_card()]}
    html = dr.render_dashboard(dd.build_dashboard_data(cfg))
    assert 'id="audience"' in html
    assert "233,280" in html


def test_malformed_card_fails_the_dashboard_build():
    cfg = {"meta": {"lang": "en"}, "audience_cards": [_card(causal_role="bogus")]}
    try:
        dd.build_dashboard_data(cfg)
    except aud_schema.AudienceConfigError:
        pass
    else:
        raise AssertionError("expected AudienceConfigError on a bad card")


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
