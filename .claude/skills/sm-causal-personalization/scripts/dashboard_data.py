#!/usr/bin/env python3
"""Normalize existing report configs into interactive dashboard data.

Shares the semantic layer (report_semantics) with the document renderer, so
the cockpit and the document speak the same operator language: five reader
questions, plain verdict words, and real config data — the heatmap comes from
cfg["heatmap"] when present (a synthetic fallback is labelled as such), the
budget table reads the real budget_rows field, and dimension fields match the
actual schema (name / mechanism / entry_score / verdict / resolution_status).
"""

from __future__ import annotations

from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Dict, List

_HERE = Path(__file__).parent

def _local_import(name: str):
    """Three-tier import used throughout this package's scripts: plain
    (installed side by side), package-relative (smcp), or by file path
    (loaded via importlib, e.g. from the test suite).

    Registers into sys.modules under its real name so a module defining an
    exception class (e.g. investment_schema.InvestmentConfigError) is loaded
    exactly once per process — an `except module.SomeError` in another file
    that loads "the same" module via a second spec_from_file_location call
    would otherwise see a distinct, non-matching class object."""
    import sys
    if name in sys.modules:
        return sys.modules[name]
    try:
        return __import__(name)
    except ImportError:
        try:
            return __import__(f"{__package__}.{name}", fromlist=[name])
        except (ImportError, TypeError):
            import importlib.util as _ilu
            spec = _ilu.spec_from_file_location(name, _HERE / f"{name}.py")
            mod = _ilu.module_from_spec(spec)
            sys.modules[name] = mod
            spec.loader.exec_module(mod)
            return mod


_sem = _local_import("report_semantics")
_inv_schema = _local_import("investment_schema")
_inv_engine = _local_import("investment_engine")
_inv_charts = _local_import("investment_charts")
_mmm_bridge = _local_import("mmm_bridge")
_hte_core = _local_import("hte_core")
_aud_schema = _local_import("audience_schema")


def build_dashboard_data(cfg: Dict[str, Any]) -> Dict[str, Any]:
    if cfg.get("report_type") == "category_portfolio":
        return _build_category_dashboard(cfg)
    return _build_sku_dashboard(cfg)


def _meta(cfg: Dict[str, Any]) -> Dict[str, Any]:
    meta = cfg.get("meta", {})
    return {
        "product": meta.get("product") or meta.get("category") or "Untitled",
        "market": meta.get("market", "Unknown market"),
        "brand": meta.get("brand", ""),
        "category": meta.get("category", ""),
        "date": meta.get("date", ""),
        "lang": meta.get("lang", "en"),
    }


def _value_text(row: Dict[str, Any]) -> str:
    value = row.get("value")
    if value is None:
        return "Missing"
    if isinstance(value, list):
        return " - ".join(_format_scalar(v, row) for v in value)
    return _format_scalar(value, row)


def _format_scalar(value: Any, row: Dict[str, Any]) -> str:
    if isinstance(value, (int, float)):
        decimals = int(row.get("decimals", 1 if isinstance(value, float) else 0))
        if row.get("pct"):
            return f"{_format_number(value * 100, decimals)}%"
        text = _format_number(value, decimals)
        unit = row.get("unit")
        return f"{text} {unit}" if unit else text
    return str(value)


def _format_number(value: Any, decimals: int) -> str:
    places = max(decimals, 0)
    quant = Decimal("1") if places == 0 else Decimal("1").scaleb(-places)
    rounded = Decimal(str(value)).quantize(quant, rounding=ROUND_HALF_UP)
    text = f"{rounded:,.{places}f}"
    return text.rstrip("0").rstrip(".") if places else text


def _number_row(number_id: str, row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": number_id,
        "label": row.get("label", number_id),
        "value": row.get("value"),
        "value_text": _value_text(row),
        "provenance": row.get("provenance", "unknown"),
        "basis": row.get("basis", ""),
        "note": row.get("note", ""),
        "needed_from": row.get("needed_from", ""),
        "cost_to_get": row.get("cost_to_get", ""),
        "blocks": row.get("blocks", []),
        "source_url": row.get("source_url", ""),
        "source_label": row.get("source_label", ""),
        "accessed": row.get("accessed", ""),
    }


def _numbers(cfg: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {
        number_id: _number_row(number_id, row)
        for number_id, row in cfg.get("numbers", {}).items()
    }


def _kpis(cfg: Dict[str, Any], numbers: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    ids = cfg.get("kpi_strip") or list(numbers.keys())[:4]
    return [numbers[number_id] for number_id in ids if number_id in numbers]


def _overview(cfg: Dict[str, Any], numbers: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    memo = cfg.get("decision_memo", {})
    decisions = memo.get("decisions", [])
    top_now = next((d.get("text", "") for d in decisions if d.get("horizon") == "now"), "")
    missing = [row for row in numbers.values() if row["provenance"] == "missing"]
    top_blocker = missing[0]["label"] if missing else memo.get("weakest_point", "")
    return {
        "verdict": memo.get("verdict", "undetermined"),
        "thesis": memo.get("thesis", ""),
        "top_action": top_now,
        "top_blocker": top_blocker,
        "weakest_point": memo.get("weakest_point", ""),
        "overturn_conditions": memo.get("overturn_conditions", []),
        "decisions": decisions,
    }


def _channels(cfg: Dict[str, Any], numbers: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    channels = []
    for idx, row in enumerate(cfg.get("channel_screen", []), 1):
        estimate_id = row.get("cac_estimate")
        channels.append({
            "id": f"CH{idx:02d}",
            "name": row.get("channel", f"Channel {idx}"),
            "verdict": row.get("verdict", "undetermined"),
            "reasoning": row.get("reasoning", ""),
            "cac_estimate_id": estimate_id,
            "cac_estimate": numbers.get(estimate_id, {}) if estimate_id else {},
        })
    return channels


def _treatments(cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    treatments = []
    for idx, row in enumerate(cfg.get("actions", []), 1):
        treatment_id = row.get("id") or f"A{idx}"
        treatments.append({
            "id": treatment_id,
            "label": _short(row.get("action", treatment_id)),
            "action": row.get("action", ""),
            "mechanism": row.get("mechanism", ""),
            "guardrail": row.get("guardrail", ""),
            "test": row.get("test", ""),
            "gate": row.get("gate", ""),
            "blocked_by": row.get("blocked_by", []),
        })
    return treatments


def _challenges(cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [{
        "id": row.get("id", f"C{idx}"),
        "target": row.get("target", ""),
        "question": row.get("question", ""),
        "status": row.get("status", "open"),
        "evidence_needed": row.get("evidence_needed", ""),
    } for idx, row in enumerate(cfg.get("challenges", []), 1)]


def _dimensions(cfg: Dict[str, Any], treatments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    raw = cfg.get("dimensions") or cfg.get("d_dimensions") or []
    if raw:
        # field names follow the real config schema; older aliases kept as fallbacks
        return [{
            "id": row.get("id", f"D{idx}"),
            "label": row.get("name") or row.get("label") or row.get("dimension") or f"D{idx}",
            "status": row.get("resolution_status", row.get("status", "open")),
            "verdict": row.get("verdict", ""),
            "entry_score": row.get("entry_score", ""),
            "logic": row.get("mechanism") or row.get("logic") or row.get("reasoning", ""),
            "proxy": row.get("proxy", ""),
            "post_treatment_check": row.get("post_treatment_check", ""),
            "post_treatment_note": row.get("post_treatment_note", ""),
            "treatment_ids": row.get("treatment_ids", []),
        } for idx, row in enumerate(raw, 1)]
    fallback = []
    for idx, treatment in enumerate(treatments[:5], 1):
        fallback.append({
            "id": f"D{idx}",
            "label": _short(treatment["label"], 28),
            "status": "open",
            "verdict": "",
            "entry_score": "",
            "logic": treatment.get("mechanism", ""),
            "proxy": treatment.get("gate", ""),
            "treatment_ids": [treatment["id"]],
        })
    return fallback or [{
        "id": "D1",
        "label": "Decision blocker",
        "status": "open",
        "verdict": "",
        "entry_score": "",
        "logic": "Needs data",
        "proxy": "",
        "treatment_ids": [],
    }]


def _heatmap(cfg: Dict[str, Any], channels: List[Dict[str, Any]],
             dimensions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Real heatmap from cfg["heatmap"] when present. The synthetic fallback
    (derived mechanically from channel verdicts) is labelled synthetic so the
    UI can say so — a fabricated-looking grid presented as data would violate
    the provenance stance of this repo."""
    hm = cfg.get("heatmap")
    if hm and hm.get("channels") and hm.get("dimensions"):
        label_map = hm.get("dim_labels", {})
        dim_logic = {d["id"]: d for d in dimensions}
        columns = [{
            "id": d,
            "label": label_map.get(d, d),
            "logic": dim_logic.get(d, {}).get("logic", ""),
            "proxy": dim_logic.get(d, {}).get("proxy", ""),
        } for d in hm["dimensions"]]
        rows = [{
            "channel_id": ch,
            "channel_name": ch,
            "grades": [hm.get("scores", {}).get(ch, {}).get(d, "N") for d in hm["dimensions"]],
        } for ch in hm["channels"]]
        return {"columns": columns, "rows": rows, "synthetic": False}

    rows = []
    for channel in channels:
        verdict = channel.get("verdict")
        grades = []
        for idx, _dimension in enumerate(dimensions):
            if verdict == "not-viable":
                grade = "A" if idx == 0 else "N"
            elif verdict == "viable":
                grade = "H" if idx == 0 else "T"
            elif verdict == "role-only":
                grade = "S" if idx == 0 else "N"
            else:
                grade = "T" if idx == 0 else "N"
            grades.append(grade)
        rows.append({"channel_id": channel["id"],
                     "channel_name": channel.get("name", channel["id"]),
                     "grades": grades})
    return {"columns": dimensions, "rows": rows, "synthetic": True}


def _evidence(numbers: Dict[str, Dict[str, Any]], cfg: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "sourced": [row for row in numbers.values() if row["provenance"] == "sourced"],
        "assumed": [row for row in numbers.values() if row["provenance"] == "assumed"],
        "derived": [row for row in numbers.values() if row["provenance"] == "derived"],
        "missing": [row for row in numbers.values() if row["provenance"] == "missing"],
        "facts": cfg.get("facts", []),
    }


def _budget_rows(cfg: Dict[str, Any], numbers: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for r in cfg.get("budget_rows", []):
        bid = r.get("budget_id")
        spec = numbers.get(bid, {}) if bid else {}
        rows.append({
            "phase": r.get("phase", ""),
            "item": r.get("item", ""),
            "budget_text": spec.get("value_text") or r.get("budget_display", "—"),
            "provenance": spec.get("provenance", ""),
            "condition": r.get("condition", ""),
        })
    return rows


_AUD_SHARE_FACTORS = {"category_or_intent_share", "activation_match_rate",
                      "eligibility_rate", "persuadable_share"}


def _aud_fmt(name: str, value: Any) -> str:
    if value is None:
        return "—"
    if name in _AUD_SHARE_FACTORS:
        pct = value * 100
        return f"{pct:.0f}%" if (pct == 0 or pct >= 1) else f"{pct:.1f}%"
    return f"{value:,.0f}"


def _audience_cards_view(cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Normalize cfg["audience_cards"] into dashboard-ready cards (ref 18):
    each card's four-layer sizing chain is computed here (derived, never raw),
    and its labels/grades resolved through the operator string pack. Empty list
    when the section was never invoked. Raises AudienceConfigError on a
    malformed card — same build-fails-hard posture as the investment plan."""
    cards = cfg.get("audience_cards")
    if not cards:
        return []
    _aud_schema.validate_or_raise(cfg)
    out: List[Dict[str, Any]] = []
    for card in cards:
        comp = _aud_schema.compute_sizing(card)
        role = card.get("causal_role")
        reach_factors = []
        persuadable_grade = None
        for name, val, grade in comp["factors"]:
            if name == "persuadable_share":
                persuadable_grade = grade
                continue
            reach_factors.append({
                "name": name,
                "label": _sem.S(cfg, "aud_factor_" + name),
                "value_text": _aud_fmt(name, val),
                "grade": grade,
            })
        reach = []
        for r in card.get("reach") or []:
            mq = r.get("match_quality", "")
            reach.append({
                "platform": r.get("platform", ""),
                "proxy": r.get("proxy", ""),
                "match_quality": mq,
                "match_label": _sem.S(cfg, "aud_mq_" + mq) if mq else "",
                "what_leaks": r.get("what_leaks", ""),
            })
        reachable = comp["reachable_target_size"]
        persuadable = comp["expected_persuadable"]
        out.append({
            "id": card.get("id"),
            "name": card.get("name", ""),
            "causal_role": role,
            "role_label": _sem.S(cfg, "aud_role_" + role) if role else "",
            "dimensions": [str(v) for v in (card.get("dimensions") or {}).values()],
            "factors": reach_factors,
            "reachable_target_size": reachable,
            "reachable_text": f"{reachable:,.0f}" if reachable is not None else "",
            "worst_grade": comp["worst_grade"],
            "persuadable_known": comp["persuadable_known"],
            "persuadable_text": f"{persuadable:,.0f}" if persuadable is not None else "",
            "persuadable_grade": persuadable_grade,
            "reach": reach,
            "suppression": card.get("suppression", ""),
            "measurement": card.get("measurement", ""),
            "weakest_assumption": card.get("weakest_assumption", ""),
        })
    return out


def _strings(cfg: Dict[str, Any]) -> Dict[str, str]:
    """UI vocabulary for the renderer, in the config's language."""
    keys = [
        "ch1_title", "ch1_question", "ch2_title", "ch2_question",
        "ch3_title", "ch3_question", "ch4_title", "ch4_question",
        "ch5_title", "ch5_question", "ch_answer_label",
        "kill_line_word", "blocked_word", "gate_word", "owner_word", "due_word",
        "never_do_heading", "prov_legend", "heatmap_caption",
        "task_cards_heading", "toc_title", "why_now_label",
        "inv_ch1_heading", "inv_kpi_spend", "inv_kpi_units", "inv_kpi_gross_profit",
        "inv_kpi_net_profit", "inv_kpi_roi", "inv_kpi_lambda_star",
        "inv_never_funded_heading", "inv_never_funded_empty",
        "inv_reason_excluded_verdict", "inv_reason_confidence_blocked",
        "inv_th_sku", "inv_th_module", "inv_th_reason", "inv_th_spend", "inv_th_roi",
        "inv_th_confidence", "inv_frontier_heading", "inv_frontier_profit_title",
        "inv_frontier_roi_title", "inv_frontier_caption", "inv_matrix_heading",
        "inv_matrix_caption", "inv_matrix_empty", "inv_tasks_heading",
        "inv_confidence_heading", "inv_confidence_validated", "inv_confidence_mmm_calibrated",
        "inv_confidence_assumption_grade", "inv_confidence_blocked",
        "inv_mmm_heading", "inv_mmm_available", "inv_mmm_deferred", "inv_mmm_missing",
        "inv_qini_missing", "inv_th_measurement",
        "verdict_grow", "verdict_hold", "verdict_harvest", "verdict_exit",
        "dash_hero_portfolio", "dash_top_action", "dash_top_blocker",
        "dash_detail_title", "dash_detail_empty_title", "dash_detail_empty_hint",
        "dash_tiers_title", "dash_tiers_sub", "dash_diag_title", "dash_diag_sub",
        "dash_skus_title", "dash_skus_sub", "dash_handoff_title", "dash_handoff_sub",
        "dash_evidence_title", "dash_evidence_sub", "dash_economics_title", "dash_economics_sub",
        "dash_channels_title", "dash_channels_sub", "dash_dimensions_title", "dash_dimensions_sub",
        "dash_heatmap_title", "dash_suppression_title", "dash_suppression_sub",
        "dash_treatments_title", "dash_treatments_sub", "dash_budgets_title", "dash_budgets_sub",
        "dash_gates_sub", "dash_challenges_title", "dash_challenges_sub",
        "dash_map_title", "dash_map_sub", "dash_measurement_title",
        "inv_th_kpi", "inv_hte_heading", "inv_hte_sub", "inv_hte_gate_title", "inv_hte_gate_note",
        "inv_th_auuc", "inv_th_decile", "inv_th_predicted_tau", "inv_th_observed_lift",
        "inv_th_gap", "inv_th_tau_bucket", "inv_th_share", "inv_mmm_sub",
        "inv_th_contribution", "inv_th_roas", "inv_mmm_adstock", "inv_mmm_saturation",
        "inv_mmm_lift_calibration",
        "inv_limits_heading", "inv_limits_intro", "inv_limits_blocked_line",
        "inv_csv_heading", "inv_csv_hint", "inv_csv_download", "inv_csv_copy",
        "stance_invest", "stance_test", "stance_hold", "stance_fix",
        "inv_frontier_by_group", "inv_frontier_group_sub",
        "dash_tiers_drill_hint", "tier_spend_word", "tier_sku_count_word",
        "cat_bridge_ch1", "cat_bridge_ch2", "cat_bridge_ch3", "cat_bridge_ch4", "cat_bridge_ch5",
        "dash_4p_product", "dash_4p_price", "dash_4p_place", "dash_4p_promotion",
        "post_treatment_warn",
        "aud_heading", "aud_intro", "aud_role_word", "aud_who_word", "aud_size_word",
        "aud_reachable_word", "aud_persuadable_word", "aud_persuadable_unknown",
        "aud_grade_word", "aud_worst_grade_note", "aud_reach_word",
        "aud_th_platform", "aud_th_proxy", "aud_th_match", "aud_th_leaks",
        "aud_suppression_word", "aud_measurement_word", "aud_weakest_word",
        "aud_grade_legend", "aud_caption", "dash_audience_title", "dash_audience_sub",
    ]
    out = {k: _sem.S(cfg, k) for k in keys}
    for code in ("H", "T", "S", "N", "A"):
        out[f"grade_{code}"] = _sem.grade_label(cfg, code)
    for v in ("viable", "not-viable", "undetermined", "role-only"):
        out[f"verdict_{v}"] = _sem.verdict_word(cfg, v)
    return out


def _build_sku_dashboard(cfg: Dict[str, Any]) -> Dict[str, Any]:
    numbers = _numbers(cfg)
    treatments = _treatments(cfg)
    challenges = _challenges(cfg)
    channels = _channels(cfg, numbers)
    dimensions = _dimensions(cfg, treatments)
    raw_numbers = cfg.get("numbers", {})
    return {
        "kind": "sku",
        "meta": _meta(cfg),
        "strings": _strings(cfg),
        "chapter_answers": _sem.chapter_answers(cfg, raw_numbers),
        "overview": _overview(cfg, numbers),
        "kpis": _kpis(cfg, numbers),
        "economics": {
            "derivations": [
                numbers[number_id]
                for number_id in cfg.get("derivations", [])
                if number_id in numbers
            ],
            "sensitivity": cfg.get("sensitivity", []),
        },
        "channels": channels,
        "dimensions": dimensions,
        "heatmap": _heatmap(cfg, channels, dimensions),
        "audience_cards": _audience_cards_view(cfg),
        "treatments": treatments,
        "budgets": _budget_rows(cfg, numbers),
        "gates": cfg.get("execution_gates", []),
        "suppression": cfg.get("suppression_rules", []),
        "measurement": cfg.get("measurement_plan", {}),
        "checklist": cfg.get("checklist", []),
        "h_main": cfg.get("h_main_breakdown", []),
        "plays": cfg.get("priority_plays", []),
        "challenges": challenges,
        "tests": cfg.get("test_plan", []),
        "rejected_options": cfg.get("rejected_options", []),
        "evidence": _evidence(numbers, cfg),
    }


def build_investment_view(cfg: Dict[str, Any]) -> Dict[str, Any] | None:
    """Normalize cfg["investment_plan"] into dashboard-ready allocation +
    chart data. Returns None when the capability was never invoked (no
    investment_plan) — category dashboards without it are unaffected.

    Raises investment_schema.InvestmentConfigError on a malformed plan (same
    build-fails-hard posture as generate_report.py's provenance contract)."""
    plan = cfg.get("investment_plan")
    if not plan:
        return None
    _inv_schema.validate_or_raise(cfg)

    raw_cells = plan["cells"]
    hte_summary = _hte_core.build_hte_summary(plan.get("hte_validation"), raw_cells)
    cells = _hte_core.annotate_cells_with_hte_validation(raw_cells, plan.get("hte_validation"))

    verdict_by_sku = {p.get("sku"): p.get("verdict") for p in cfg.get("portfolio", [])}
    eligible, blocked = _inv_engine.filter_investable_cells(cells, verdict_by_sku)
    summary = _inv_engine.optimize_investment(
        eligible, plan["total_budget"], plan["budget_step"], plan["required_mroi"],
        plan.get("required_mroi_by_confidence"))
    mmm = _mmm_bridge.build_mmm_summary(cfg)

    # optional accountability fields on cells flow through to the activation
    # cards: who owns the move, how it's measured, and the stop rule
    card_fields = ("owner", "measurement", "stop_rule")
    meta_by_key: Dict[tuple, Dict[str, str]] = {}
    for cell in plan["cells"]:
        key = (cell.get("sku"), cell.get("module"))
        if key not in meta_by_key and any(cell.get(f) for f in card_fields):
            meta_by_key[key] = {f: cell[f] for f in card_fields if cell.get(f)}
    for row in summary["allocation"]:
        row.update(meta_by_key.get((row["sku"], row["module"]), {}))

    currency = plan.get("currency", "")
    frontier = _inv_engine.expand_budget_steps(eligible, plan["budget_step"])
    frontier.sort(key=lambda s: -s["marginal_roi"])
    cumulative, cum_spend, running = [], 0.0, 0.0
    for step in frontier:
        cum_spend += step["step_spend"]
        running += step["marginal_gross_profit"]
        cumulative.append({"spend": cum_spend, "incremental_gross_profit": running,
                           "marginal_roi": step["marginal_roi"]})

    module_labels = {str(m.get("id", "")): m.get("label") or str(m.get("id", ""))
                     for m in plan.get("modules", [])}

    return {
        "answer": summary,
        "blocked": blocked,
        "mmm": mmm,
        "hte": _hte_core.serializable_summary(hte_summary),
        "module_labels": module_labels,
        "limits": _investment_limits_view(cfg, plan, summary, blocked, hte_summary, module_labels),
        "activation_cards": _investment_activation_cards(cfg, summary["allocation"], eligible, currency),
        "charts": {
            "kpis": _inv_charts.investment_answer_kpis(summary, currency),
            "frontier": _inv_charts.frontier_chart_spec(cumulative, summary["recommended_spend"]),
            "frontier_groups": _frontier_by_group(cfg, eligible, summary, plan),
            "budget_matrix": _inv_charts.budget_matrix_spec(summary["allocation"]),
            "confidence": _inv_charts.confidence_strip_spec(cells),
            "hte": hte_summary["charts"],
            "mmm": {
                "contribution": _inv_charts.mmm_contribution_spec(mmm.get("channel_contribution", [])),
                "adstock": _inv_charts.adstock_saturation_spec(mmm.get("adstock_curves", [])),
                "saturation": _inv_charts.adstock_saturation_spec(mmm.get("saturation_curves", [])),
                "posterior_roas": _inv_charts.posterior_roas_spec(mmm.get("posterior_roas", [])),
                "lift_calibration": _inv_charts.lift_calibration_spec(mmm.get("lift_calibration", [])),
            },
        },
        "currency": currency,
    }


def _investment_activation_cards(cfg: Dict[str, Any], allocation: list[dict],
                                 cells: list[dict], currency: str) -> list[dict]:
    by_key = {(c.get("sku"), c.get("module")): c for c in cells}
    module_labels = {str(m.get("id", "")): m.get("label") or str(m.get("id", ""))
                     for m in cfg.get("investment_plan", {}).get("modules", [])}
    cards = []
    for row in allocation:
        cell = by_key.get((row.get("sku"), row.get("module")), {})
        cards.append({
            "sku": row.get("sku", ""),
            "module": row.get("module", ""),
            "module_label": module_labels.get(row.get("module"), row.get("module", "")),
            "channel": row.get("channel", cell.get("channel", "")),
            "spend": row.get("spend", 0.0),
            "currency": currency,
            "roi": row.get("roi", 0.0),
            "units": row.get("units", 0.0),
            "gross_profit": row.get("gross_profit", 0.0),
            "confidence": row.get("confidence", "assumption_grade"),
            "owner": cell.get("owner") or _sem.S(cfg, "inv_default_owner"),
            "flight": cell.get("flight") or _sem.S(cfg, "inv_default_flight"),
            "kpi": cell.get("kpi") or _sem.S(cfg, "inv_default_kpi"),
            "measurement": cell.get("measurement", cell.get("measurement_gate", "")),
            "stop_rule": cell.get("stop_rule") or _sem.S(cfg, "inv_default_stop_rule"),
            "why": cell.get("why") or _sem.S(cfg, "inv_default_why"),
        })
    return cards


def _sku_group_map(cfg: Dict[str, Any]) -> Dict[str, str]:
    """sku -> business-line label. price_tiers.your_skus wins; portfolio.tier
    fills the gaps (using the tier id verbatim when no price_tiers entry names it)."""
    label_by_tier = {str(t.get("id", "")): t.get("label") or str(t.get("id", ""))
                     for t in cfg.get("price_tiers", [])}
    out: Dict[str, str] = {}
    for t in cfg.get("price_tiers", []):
        for sku in t.get("your_skus", []):
            out[sku] = t.get("label") or str(t.get("id", ""))
    for p in cfg.get("portfolio", []):
        sku = p.get("sku")
        if sku and sku not in out:
            tier = str(p.get("tier", ""))
            out[sku] = label_by_tier.get(tier, tier)
    return out


def _frontier_by_group(cfg: Dict[str, Any], eligible: list[dict], summary: dict,
                       plan: Dict[str, Any]) -> list[dict]:
    """The overall frontier, split by business line (tier). One mini panel per
    group: cumulative gross profit as that group's spend grows, plus how much
    of it the overall allocation actually funded."""
    group_of = _sku_group_map(cfg)
    funded_by_group: Dict[str, float] = {}
    for row in summary.get("allocation", []):
        g = group_of.get(row.get("sku"), "")
        funded_by_group[g] = funded_by_group.get(g, 0.0) + float(row.get("spend", 0.0))

    cells_by_group: Dict[str, list] = {}
    for cell in eligible:
        g = group_of.get(cell.get("sku"), "")
        cells_by_group.setdefault(g, []).append(cell)

    groups = []
    for g, cells in cells_by_group.items():
        steps = _inv_engine.expand_budget_steps(cells, plan.get("budget_step", 0) or 0)
        steps.sort(key=lambda s: -s["marginal_roi"])
        points, cum_spend, running = [], 0.0, 0.0
        for step in steps:
            cum_spend += step["step_spend"]
            running += step["marginal_gross_profit"]
            points.append((cum_spend, running))
        groups.append({
            "label": g or "—",
            "points": points,
            "funded": funded_by_group.get(g, 0.0),
            "cells": len(cells),
        })
    groups.sort(key=lambda r: -r["funded"])
    return groups


_CSV_COLUMNS = (
    "sku", "module", "channel", "tau_hat", "tau_source", "validation_ref",
    "measurement_gate", "reachable_population", "unit_margin", "max_spend",
    "saturation_k", "readiness", "owner", "flight", "kpi", "measurement",
    "stop_rule", "why",
)


def _csv_field(value: Any) -> str:
    text = "" if value is None else str(value)
    if any(c in text for c in (",", '"', "\n")):
        text = '"' + text.replace('"', '""') + '"'
    return text


def _investment_limits_view(cfg: Dict[str, Any], plan: Dict[str, Any], summary: dict,
                            blocked: list[dict], hte_summary: dict,
                            module_labels: Dict[str, str] | None = None) -> Dict[str, Any]:
    """What limits this run + the exact CSV to fill so the next run computes.
    The template is pre-filled with every cell (funded or not); blank fields
    are precisely the data being requested."""
    allocation = summary.get("allocation", [])
    module_labels = module_labels or {}
    assumption = sum(1 for r in allocation if r.get("confidence") == "assumption_grade")
    lines = [",".join(_CSV_COLUMNS)]
    for cell in plan.get("cells", []):
        lines.append(",".join(_csv_field(cell.get(col)) for col in _CSV_COLUMNS))
    return {
        "funded": len(allocation),
        "assumption": assumption,
        "blocked": [{"sku": b.get("sku", ""),
                     "module": module_labels.get(b.get("module"), b.get("module", "")),
                     "reason": b.get("reason", "")} for b in blocked],
        "holdout_n": hte_summary.get("holdout_n", 0),
        "csv": "\r\n".join(lines),
    }


def _tier_drill(cfg: Dict[str, Any], investment: Dict[str, Any] | None) -> list[dict]:
    """Tier -> SKU -> plays/funded-spend drill-down for the play chapter."""
    by_sku = {p.get("sku"): p for p in cfg.get("portfolio", [])}
    spend_by_sku: Dict[str, list] = {}
    module_labels = (investment or {}).get("module_labels", {})
    for row in (investment or {}).get("answer", {}).get("allocation", []):
        spend_by_sku.setdefault(row.get("sku"), []).append({
            "module": module_labels.get(row.get("module"), row.get("module", "")),
            "spend": float(row.get("spend", 0.0)),
            "roi": float(row.get("roi", 0.0)),
        })
    group_of = _sku_group_map(cfg)
    tiers = []
    for t in cfg.get("price_tiers", []):
        label = t.get("label") or str(t.get("id", ""))
        skus = []
        for sku_name in t.get("your_skus", []):
            p = by_sku.get(sku_name, {})
            modules = spend_by_sku.get(sku_name, [])
            skus.append({
                "sku": sku_name,
                "verdict": p.get("verdict", ""),
                "note": p.get("note", ""),
                "fourP": p.get("fourP", {}),
                "spend": sum(m["spend"] for m in modules),
                "modules": sorted(modules, key=lambda m: -m["spend"]),
            })
        skus.sort(key=lambda s: -s["spend"])
        tiers.append({
            "label": label,
            "trend": t.get("trend", ""),
            "audience": t.get("audience", ""),
            "force": t.get("force", ""),
            "channel_fit": t.get("channel_fit", ""),
            "spend": sum(s["spend"] for s in skus),
            "skus": skus,
        })
    # portfolio SKUs whose tier has no price_tiers entry still deserve a row
    leftover = [p for p in cfg.get("portfolio", [])
                if p.get("sku") not in group_of or group_of.get(p.get("sku")) not in
                {t["label"] for t in tiers}]
    if leftover:
        skus = []
        for p in leftover:
            modules = spend_by_sku.get(p.get("sku"), [])
            skus.append({
                "sku": p.get("sku", ""), "verdict": p.get("verdict", ""),
                "note": p.get("note", ""), "fourP": p.get("fourP", {}),
                "spend": sum(m["spend"] for m in modules),
                "modules": sorted(modules, key=lambda m: -m["spend"]),
            })
        tiers.append({"label": "—", "trend": "", "audience": "", "force": "",
                      "channel_fit": "", "spend": sum(s["spend"] for s in skus),
                      "skus": skus})
    return tiers


def _build_category_dashboard(cfg: Dict[str, Any]) -> Dict[str, Any]:
    numbers = _numbers(cfg)
    portfolio = cfg.get("portfolio", [])
    investment = build_investment_view(cfg)
    answers = _sem.category_chapter_answers(cfg, cfg.get("numbers", {}))
    if investment:
        # same per-chapter investment overlay the document report appends —
        # the dashboard banner must state the budget verdict too
        for ch_id, suffix in _sem.investment_chapter_answers(cfg, investment).items():
            answers[ch_id] = answers[ch_id] + suffix
    return {
        "kind": "category_portfolio",
        "meta": _meta(cfg),
        "strings": _strings(cfg),
        "chapter_answers": answers,
        "audience_cards": _audience_cards_view(cfg),
        "overview": {
            "verdict": "portfolio",
            "thesis": cfg.get("_note", ""),
            "top_action": _category_top_action(portfolio),
            "top_blocker": _category_top_blocker(numbers),
            "weakest_point": "",
            "overturn_conditions": [],
            "decisions": [],
        },
        "kpis": _portfolio_kpis(cfg, portfolio, numbers),
        "economics": {"derivations": [], "sensitivity": []},
        "channels": [],
        "dimensions": [],
        "heatmap": {"columns": [], "rows": []},
        "treatments": [],
        "budgets": [],
        "plays": [],
        "challenges": [],
        "tests": [],
        "rejected_options": [],
        "evidence": _evidence(numbers, cfg),
        "portfolio": {
            "tiers": cfg.get("price_tiers", []),
            "tier_drill": _tier_drill(cfg, investment),
            "diagnosis": cfg.get("diagnosis", []),
            "skus": portfolio,
            "verdict_counts": dict(Counter(row.get("verdict", "unknown") for row in portfolio)),
        },
        "investment": investment,
    }


def _portfolio_kpis(cfg: Dict[str, Any], portfolio: List[Dict[str, Any]],
                    numbers: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    counts = Counter(row.get("verdict", "unknown") for row in portfolio)
    kpis = [
        {
            "id": "sku_count",
            "label": _sem.S(cfg, "dash_kpi_skus"),
            "value": len(portfolio),
            "value_text": str(len(portfolio)),
            "provenance": "derived",
        },
        {
            "id": "grow_count",
            "label": _sem.S(cfg, "dash_kpi_grow"),
            "value": counts.get("grow", 0),
            "value_text": str(counts.get("grow", 0)),
            "provenance": "derived",
        },
        {
            "id": "exit_count",
            "label": _sem.S(cfg, "dash_kpi_exit"),
            "value": counts.get("exit", 0),
            "value_text": str(counts.get("exit", 0)),
            "provenance": "derived",
        },
    ]
    missing = [row for row in numbers.values() if row["provenance"] == "missing"]
    if missing:
        kpis.append({
            "id": "missing_count",
            "label": _sem.S(cfg, "dash_kpi_missing"),
            "value": len(missing),
            "value_text": str(len(missing)),
            "provenance": "missing",
        })
    return kpis


def _category_top_action(portfolio: List[Dict[str, Any]]) -> str:
    grow = [row.get("sku", "") for row in portfolio if row.get("verdict") == "grow"]
    return "Deep-dive Grow SKUs: " + ", ".join(grow[:3]) if grow else "No Grow SKU selected"


def _category_top_blocker(numbers: Dict[str, Dict[str, Any]]) -> str:
    missing = [row for row in numbers.values() if row["provenance"] == "missing"]
    return missing[0]["label"] if missing else "No missing number registered"


def _short(text: str, limit: int = 36) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[:limit - 3].rstrip() + "..."
