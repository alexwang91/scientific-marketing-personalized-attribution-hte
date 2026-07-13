"""Audience-card validation + sizing math (ref 18 audience-card).

Pure stdlib — no numpy/pandas. This module owns the contract for
`cfg["audience_cards"]`: how an audience is defined (20 dimensions), sized (a
four-layer chain, never one number), reached (per-platform proxy + match
quality), and graded (A/B/C/D, which map onto the skill's sourced/assumed/
derived/missing provenance states — ref 16).

Two honesty rules are made mechanical here, mirroring investment_schema's
abstention gates:
  1. A stated persuadable size needs a causal source — you cannot claim who is
     persuadable from platform data alone (ref 05).
  2. A precise share carrying a D grade must name `needed_from` — never hide a
     D-grade assumption inside a precise percentage (ref 18).

The reachable-size and persuadable-size numbers are DERIVED from the chain by
`compute_sizing` — a card may not set them as raw input (same rule as a cell's
computed confidence badge).

Domain-agnostic by design: nothing here names a brand, category, country, or
currency. Any audience in any market validates against the exact same rules.

See references/18-audience-card.md for the full data contract.
"""

from __future__ import annotations

from typing import Any

# dimension 20 of the audience card — the one that decides budget (ref 05)
CAUSAL_ROLES = {"persuadable", "sure_thing", "lost_cause", "sleeping_dog", "unknown"}

# audience-size confidence grades == provenance states applied to size (ref 16)
GRADES = {"A", "B", "C", "D"}

# how well a platform control expresses the causal segment (ref 42)
MATCH_QUALITIES = {"high", "medium", "low", "unavailable"}

# the four-layer sizing chain, in narrowing order (ref 18). country_reachable is
# an absolute count; the rest are shares in [0, 1] that narrow it.
COUNT_FACTOR = "country_reachable"
SHARE_FACTORS = ("category_or_intent_share", "activation_match_rate", "eligibility_rate")
# persuadable_share is a share too, but it sizes the persuadable pool, not the
# reachable pool — kept separate so an unknown causal read doesn't zero the reach
PERSUADABLE_FACTOR = "persuadable_share"
SIZING_FACTORS = (COUNT_FACTOR, *SHARE_FACTORS, PERSUADABLE_FACTOR)

# numbers the renderer computes — a card may not supply them as raw input
_DERIVED_FIELDS = ("reachable_target_size", "expected_persuadable", "worst_grade")

# worst-first ordering so the whole chain inherits its weakest link's grade
_GRADE_BADNESS = {"A": 0, "B": 1, "C": 2, "D": 3}


def _is_num(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _factor_errors(cid: str, factor: str, spec: Any, is_share: bool) -> list[str]:
    """Validate one sizing factor: {value, grade, source, [needed_from]}."""
    errs: list[str] = []
    if not isinstance(spec, dict):
        return [f"{cid}: sizing.{factor} must be an object with value/grade/source"]
    value = spec.get("value")
    if value is not None:
        if not _is_num(value) or value < 0:
            errs.append(f"{cid}: sizing.{factor}.value must be a non-negative number")
        elif is_share and value > 1:
            errs.append(f"{cid}: sizing.{factor}.value is a share and must be ≤ 1, got {value}")
    grade = spec.get("grade")
    if grade not in GRADES:
        errs.append(f"{cid}: sizing.{factor}.grade must be one of {sorted(GRADES)}, got {grade!r}")
    if not spec.get("source"):
        errs.append(f"{cid}: sizing.{factor} requires a 'source' (where the number came from)")
    # the honesty rule: a precise D-grade number must say what would firm it up
    if grade == "D" and value is not None and not spec.get("needed_from"):
        errs.append(
            f"{cid}: sizing.{factor} is grade D with a precise value {value} but no "
            f"'needed_from' — never hide a D-grade assumption inside a precise number (ref 18)")
    return errs


def validate_audience_cards(cfg: dict) -> list[str]:
    """Validate cfg["audience_cards"]. Returns a list of error strings; empty
    means valid. Absent audience_cards is not an error — the section is opt-in."""
    cards = cfg.get("audience_cards")
    if cards is None:
        return []
    errors: list[str] = []
    if not isinstance(cards, list) or not cards:
        return ["audience_cards must be a non-empty list when present"]

    seen_ids: set[str] = set()
    for card in cards:
        cid = str(card.get("id") or card.get("name") or "<no id>")
        if not card.get("name"):
            errors.append(f"{cid}: audience card requires a 'name'")
        cid_key = card.get("id")
        if cid_key:
            if cid_key in seen_ids:
                errors.append(f"{cid}: duplicate audience card id {cid_key!r}")
            seen_ids.add(cid_key)

        role = card.get("causal_role")
        if role is not None and role not in CAUSAL_ROLES:
            errors.append(
                f"{cid}: causal_role must be one of {sorted(CAUSAL_ROLES)}, got {role!r}")

        for field in _DERIVED_FIELDS:
            if field in card:
                errors.append(
                    f"{cid}: '{field}' is derived from the sizing chain and must not be set "
                    f"on the card (see audience_schema.compute_sizing)")

        sizing = card.get("sizing")
        if sizing is not None:
            if not isinstance(sizing, dict):
                errors.append(f"{cid}: sizing must be an object")
            else:
                if COUNT_FACTOR in sizing:
                    errors += _factor_errors(cid, COUNT_FACTOR, sizing[COUNT_FACTOR], is_share=False)
                for factor in SHARE_FACTORS:
                    if factor in sizing:
                        errors += _factor_errors(cid, factor, sizing[factor], is_share=True)
                if PERSUADABLE_FACTOR in sizing:
                    spec = sizing[PERSUADABLE_FACTOR]
                    errors += _factor_errors(cid, PERSUADABLE_FACTOR, spec, is_share=True)
                    # can't state a persuadable NUMBER without a causal read
                    if isinstance(spec, dict) and _is_num(spec.get("value")) and not spec.get("source"):
                        errors.append(
                            f"{cid}: a stated persuadable_share needs a causal 'source' "
                            f"(holdout / uplift) — persuadable is not a platform field (ref 05)")

        reach = card.get("reach")
        if reach is not None:
            if not isinstance(reach, list):
                errors.append(f"{cid}: reach must be a list of platform proxies")
            else:
                for r in reach:
                    plat = r.get("platform", "<no platform>")
                    if not r.get("proxy"):
                        errors.append(f"{cid}/{plat}: reach entry requires a 'proxy'")
                    mq = r.get("match_quality")
                    if mq not in MATCH_QUALITIES:
                        errors.append(
                            f"{cid}/{plat}: match_quality must be one of {sorted(MATCH_QUALITIES)}, got {mq!r}")
                    elif mq in ("medium", "low") and not r.get("what_leaks"):
                        errors.append(
                            f"{cid}/{plat}: match_quality '{mq}' requires 'what_leaks' — "
                            f"say what the proxy lets in (e.g. sure-things) (ref 18)")

    return errors


def worst_grade(grades: list[str]) -> str | None:
    """The weakest (worst) grade in a chain — a chain is only as sound as its
    weakest multiplier."""
    present = [g for g in grades if g in _GRADE_BADNESS]
    if not present:
        return None
    return max(present, key=lambda g: _GRADE_BADNESS[g])


def compute_sizing(card: dict) -> dict:
    """Derive the reachable and persuadable pool sizes from the sizing chain,
    plus the chain's inherited (worst) grade. Returns a dict with:
      reachable_target_size, expected_persuadable, worst_grade,
      persuadable_known (bool), factors (ordered [(name, value, grade), ...]).
    Missing factors are skipped honestly: no country_reachable -> size is None
    (can't size); no persuadable_share value -> persuadable is unknown."""
    sizing = card.get("sizing") or {}
    factors: list[tuple[str, float | None, str | None]] = []
    grades: list[str] = []

    reach_val: float | None = None
    count_spec = sizing.get(COUNT_FACTOR)
    if isinstance(count_spec, dict) and _is_num(count_spec.get("value")):
        reach_val = float(count_spec["value"])
        factors.append((COUNT_FACTOR, reach_val, count_spec.get("grade")))
        if count_spec.get("grade"):
            grades.append(count_spec["grade"])

    for factor in SHARE_FACTORS:
        spec = sizing.get(factor)
        if isinstance(spec, dict) and _is_num(spec.get("value")):
            factors.append((factor, float(spec["value"]), spec.get("grade")))
            if spec.get("grade"):
                grades.append(spec["grade"])
            if reach_val is not None:
                reach_val *= float(spec["value"])

    persuadable_known = False
    expected_persuadable: float | None = None
    p_spec = sizing.get(PERSUADABLE_FACTOR)
    if isinstance(p_spec, dict) and _is_num(p_spec.get("value")):
        persuadable_known = True
        # persuadable is a separate derivation on top of the reachable pool; its
        # grade rides on the persuadable number, not on the reachable badge, so
        # it is NOT folded into worst_grade (which stamps the reachable chain)
        factors.append((PERSUADABLE_FACTOR, float(p_spec["value"]), p_spec.get("grade")))
        if reach_val is not None:
            expected_persuadable = reach_val * float(p_spec["value"])

    return {
        "reachable_target_size": reach_val,
        "expected_persuadable": expected_persuadable,
        "persuadable_known": persuadable_known,
        "worst_grade": worst_grade(grades),
        "factors": factors,
    }


class AudienceConfigError(Exception):
    """Raised by the build-time wrapper when validate_audience_cards finds errors."""


def validate_or_raise(cfg: dict) -> None:
    errors = validate_audience_cards(cfg)
    if errors:
        raise AudienceConfigError(
            "Audience-card contract violations:\n  - " + "\n  - ".join(errors))
