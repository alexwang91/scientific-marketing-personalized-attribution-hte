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

try:
    import report_semantics as _sem
except ImportError:
    try:
        from . import report_semantics as _sem
    except ImportError:
        import importlib.util as _ilu
        _sem_spec = _ilu.spec_from_file_location("report_semantics", _HERE / "report_semantics.py")
        _sem = _ilu.module_from_spec(_sem_spec)
        _sem_spec.loader.exec_module(_sem)


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


def _strings(cfg: Dict[str, Any]) -> Dict[str, str]:
    """UI vocabulary for the renderer, in the config's language."""
    keys = [
        "ch1_title", "ch1_question", "ch2_title", "ch2_question",
        "ch3_title", "ch3_question", "ch4_title", "ch4_question",
        "ch5_title", "ch5_question", "ch_answer_label",
        "kill_line_word", "blocked_word", "gate_word", "owner_word", "due_word",
        "never_do_heading", "prov_legend", "heatmap_caption",
        "task_cards_heading", "toc_title",
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


def _build_category_dashboard(cfg: Dict[str, Any]) -> Dict[str, Any]:
    numbers = _numbers(cfg)
    portfolio = cfg.get("portfolio", [])
    return {
        "kind": "category_portfolio",
        "meta": _meta(cfg),
        "strings": _strings(cfg),
        "overview": {
            "verdict": "portfolio",
            "thesis": cfg.get("_note", ""),
            "top_action": _category_top_action(portfolio),
            "top_blocker": _category_top_blocker(numbers),
            "weakest_point": "",
            "overturn_conditions": [],
            "decisions": [],
        },
        "kpis": _portfolio_kpis(portfolio, numbers),
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
            "diagnosis": cfg.get("diagnosis", []),
            "skus": portfolio,
            "verdict_counts": dict(Counter(row.get("verdict", "unknown") for row in portfolio)),
        },
    }


def _portfolio_kpis(portfolio: List[Dict[str, Any]], numbers: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    counts = Counter(row.get("verdict", "unknown") for row in portfolio)
    kpis = [
        {
            "id": "sku_count",
            "label": "SKUs",
            "value": len(portfolio),
            "value_text": str(len(portfolio)),
            "provenance": "derived",
        },
        {
            "id": "grow_count",
            "label": "Grow",
            "value": counts.get("grow", 0),
            "value_text": str(counts.get("grow", 0)),
            "provenance": "derived",
        },
        {
            "id": "exit_count",
            "label": "Exit",
            "value": counts.get("exit", 0),
            "value_text": str(counts.get("exit", 0)),
            "provenance": "derived",
        },
    ]
    missing = [row for row in numbers.values() if row["provenance"] == "missing"]
    if missing:
        kpis.append({
            "id": "missing_count",
            "label": "Missing data",
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
