#!/usr/bin/env python3
"""Render normalized dashboard data as a single-file interactive HTML cockpit."""

from __future__ import annotations

import json
import re
import sys
from html import escape
from pathlib import Path
from typing import Any, Dict, Iterable

_HERE = Path(__file__).parent

try:
    import svg_charts as _svg
except ImportError:
    try:
        from . import svg_charts as _svg
    except ImportError:
        import importlib.util as _ilu
        if "svg_charts" in sys.modules:
            _svg = sys.modules["svg_charts"]
        else:
            _spec = _ilu.spec_from_file_location("svg_charts", _HERE / "svg_charts.py")
            _svg = _ilu.module_from_spec(_spec)
            sys.modules["svg_charts"] = _svg
            _spec.loader.exec_module(_svg)

_CONF_COLOR = {"validated": "#16a34a", "mmm_calibrated": "#2563eb",
               "assumption_grade": "#d97706", "blocked": "#9ca3af"}


def render_dashboard(data: Dict[str, Any]) -> str:
    payload = _script_json(data)
    title = f"{data['meta'].get('product', 'Dashboard')} · {data['meta'].get('market', '')}"
    if data.get("kind") == "category_portfolio":
        body = _render_category(data)
    else:
        body = _render_sku(data)
    return f"""<!doctype html>
<html lang="{_esc(data['meta'].get('lang', 'en'))}">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{_esc(title)}</title>
  <style>{_css()}</style>
</head>
<body>
<div class="decision-dashboard" data-kind="{_esc(data.get('kind', 'sku'))}">
  <nav class="rail" aria-label="Dashboard sections">
    <div class="rail-mark">SM</div>
    {_nav(data)}
  </nav>
  <main class="workspace">
    {body}
  </main>
  <aside class="detail-panel" id="detail-panel">
    <div class="eyebrow">{_esc(_s(data, "dash_detail_title", "Detail"))}</div>
    <h2 id="detail-title">{_esc(_s(data, "dash_detail_empty_title", "Select an item"))}</h2>
    <div id="detail-body"><p>{_esc(_s(data, "dash_detail_empty_hint", "Click a KPI, channel, heatmap cell, treatment, diagnosis, or evidence row to inspect its reasoning."))}</p></div>
  </aside>
</div>
<script>
const DASHBOARD_DATA = {payload};
{_js()}
</script>
</body>
</html>"""


def _render_sku(data: Dict[str, Any]) -> str:
    """Workspace order = the reader's five questions (report_semantics spine)."""
    s = data.get("strings", {})
    answers = data.get("chapter_answers", {})

    def ch(n: str) -> str:
        return _chapter_head(n, s.get(f"{n}_title", n), s.get(f"{n}_question", ""),
                             s.get("ch_answer_label", "Short answer"), answers.get(n, ""))

    return "\n".join([
        ch("ch1"),
        _hero(data, s.get("ch1_title", "The Call")),
        _never_do(data),
        ch("ch2"),
        _kpis(data),
        _economics(data),
        ch("ch3"),
        _channels(data),
        _dimensions(data),
        _audience_cards(data),
        _heatmap(data),
        _suppression(data),
        ch("ch4"),
        _treatments(data),
        _budgets(data),
        _checklist(data),
        ch("ch5"),
        _causal_map(data),
        _measurement(data),
        _challenges_section(data),
        _evidence(data),
    ])


def _chapter_head(ch_id: str, title: str, question: str, answer_label: str, answer: str,
                  bridge: str = "") -> str:
    answer_html = f'<p class="ch-ans"><b>{_esc(answer_label)}</b> {_esc(answer)}</p>' if answer else ""
    bridge_html = f'<p class="ch-bridge">{_esc(bridge)}</p>' if bridge else ""
    return f"""<section class="chapter-band section" id="{_esc(ch_id)}">
  <div class="eyebrow">{_esc(title)}</div>
  <h2>{_esc(question)}</h2>
  {answer_html}
  {bridge_html}
</section>"""


def _render_category(data: Dict[str, Any]) -> str:
    """Same five-question spine as _render_sku — the reading line is:
    ch1 the call (verdicts + investment answer) → ch2 the why (diagnosis +
    frontier, overall and by business line) → ch3 the play (tier→SKU drill,
    SKU verdicts, where the money lands) → ch4 execution (handoff + funded
    activation cards + the CSV data request) → ch5 evidence & risk, folded
    shut by default."""
    s = data.get("strings", {})
    answers = data.get("chapter_answers", {})
    inv = data.get("investment")

    def ch(n: str) -> str:
        return _chapter_head(n, s.get(f"{n}_title", n), s.get(f"{n}_question", ""),
                             s.get("ch_answer_label", "Short answer"), answers.get(n, ""),
                             bridge=s.get(f"cat_bridge_{n}", ""))

    parts = [
        ch("ch1"),
        _hero(data, _s(data, "dash_hero_portfolio", "Portfolio Verdict")),
        _kpis(data),
    ]
    if inv:
        parts.append(_investment_kpis(data, inv))
    parts += [ch("ch2"), _portfolio_diagnosis(data)]
    if inv:
        parts.append(_investment_frontier(data, inv))
    parts += [ch("ch3"), _portfolio_tiers(data), _portfolio_skus(data), _audience_cards(data)]
    if inv:
        parts.append(_investment_matrix(data, inv))
    parts += [ch("ch4"), _portfolio_handoff(data)]
    if inv:
        # execution ends with the data request: what to fill in (CSV) so the
        # next run computes — replaces the old never-funded card wall
        parts += [_investment_tasks(data, inv), _investment_limits(data, inv)]
    # evidence & risk: folded shut by default — open only what you need
    parts.append(ch("ch5"))
    parts.append(_fold(data, _evidence(data)))
    if inv:
        parts += [_fold(data, _investment_hte_core(data, inv)),
                  _fold(data, _investment_mmm(data, inv)),
                  _fold(data, _investment_confidence_mmm(data, inv))]
    return "\n".join(p for p in parts if p)


def _fold(data: Dict[str, Any], section_html: str) -> str:
    """Collapse a rendered section behind its own title — the section's h2
    becomes the clickable summary; everything else shows only when opened."""
    if not section_html:
        return ""
    m = re.search(r'<h2>(.*?)</h2>', section_html, re.S)
    title = m.group(1) if m else ""
    return f"""<details class="fold section">
  <summary>{title}</summary>
  {section_html}
</details>"""


def _s(data: Dict[str, Any], key: str, default: str = "") -> str:
    return data.get("strings", {}).get(key, default)


def _kpi_value_text(k: Dict[str, Any]) -> str:
    """Money and unit counts read as whole numbers — '13,802.48 units' is
    false precision when every input is an estimate; ratios keep 2 decimals."""
    v = k.get("value", 0)
    if not isinstance(v, (int, float)):
        return str(v)
    txt = f'{v:.2f}' if k.get("id") in ("roi", "lambda_star") else f'{v:,.0f}'
    return f'{txt} {k.get("unit", "")}'.strip()


def _investment_kpis(data: Dict[str, Any], inv: Dict[str, Any]) -> str:
    cards = []
    for k in inv.get("charts", {}).get("kpis", []):
        label = _s(data, "inv_" + k["label_key"], k["label_key"])
        text = _kpi_value_text(k)
        cards.append(f"""<button class="kpi-card tone-{_esc(k.get('tone','neutral'))}" data-detail='{_detail_json(label, text, k)}'>
  <span>{_esc(label)}</span>
  <strong>{_esc(text)}</strong>
</button>""")
    return f'<section class="kpi-strip section" id="invest-kpis">{"".join(cards)}</section>'


def _investment_limits(data: Dict[str, Any], inv: Dict[str, Any]) -> str:
    """What limits this run + the CSV to fill — replaces the never-funded
    card wall: state the constraint, name the blocked cells in one line each,
    and hand over the exact template that unlocks the next run."""
    limits = inv.get("limits") or {}
    intro = _s(data, "inv_limits_intro", "").format(
        funded=limits.get("funded", 0), assumption=limits.get("assumption", 0),
        blocked=len(limits.get("blocked", [])), holdout=limits.get("holdout_n", 0))
    blocked_html = ""
    if limits.get("blocked"):
        items = "".join(
            f'<li><strong>{_esc(b.get("sku",""))}</strong> · {_esc(b.get("module",""))}'
            f' — {_esc(_s(data, "inv_reason_excluded_verdict" if b.get("reason") == "excluded verdict" else "inv_reason_confidence_blocked", b.get("reason","")))}</li>'
            for b in limits["blocked"])
        blocked_html = (f'<p class="limits-blocked"><b>{_esc(_s(data, "inv_limits_blocked_line", "Not funded:"))}</b></p>'
                        f'<ul class="limits-blocked-list">{items}</ul>')
    csv_text = limits.get("csv", "")
    csv_html = f"""<div class="csv-box">
  <div class="csv-head">
    <strong>{_esc(_s(data, "inv_csv_heading", "CSV template"))}</strong>
    <span>
      <button class="pill" onclick="smcpCopyCsv()">{_esc(_s(data, "inv_csv_copy", "Copy"))}</button>
      <button class="pill" onclick="smcpDownloadCsv()">{_esc(_s(data, "inv_csv_download", "Download CSV"))}</button>
    </span>
  </div>
  <p class="csv-hint">{_esc(_s(data, "inv_csv_hint", ""))}</p>
  <pre id="smcp-csv-template">{_esc(csv_text)}</pre>
</div>"""
    body = f'<p class="limits-intro">{_esc(intro)}</p>{blocked_html}{csv_html}'
    return _section("invest-limits", _s(data, "inv_limits_heading", "What limits this report"),
                    "", [body])


def _investment_frontier(data: Dict[str, Any], inv: Dict[str, Any]) -> str:
    frontier = inv.get("charts", {}).get("frontier", {})
    profit = frontier.get("profit_panel", {})
    roi = frontier.get("roi_panel", {})
    panels = f"""<div class="inv-frontier-grid">
  <div class="inv-panel">
    <div class="inv-panel-title">{_esc(_s(data, "inv_frontier_profit_title", "Cumulative gross profit"))}</div>
    {_svg.line_panel(profit.get("points", []), profit.get("cutoff_spend"), "#4f46e5")}
  </div>
  <div class="inv-panel">
    <div class="inv-panel-title">{_esc(_s(data, "inv_frontier_roi_title", "Marginal ROI"))}</div>
    {_svg.line_panel(roi.get("points", []), roi.get("cutoff_spend"), "#0891b2")}
  </div>
</div>"""
    groups = inv.get("charts", {}).get("frontier_groups", [])
    group_html = ""
    if len(groups) > 1:
        currency = inv.get("currency", "")
        cells = ""
        for g in groups:
            cells += f"""<div class="inv-panel">
  <div class="inv-panel-title">{_esc(g.get("label", ""))}</div>
  <div class="inv-panel-meta">{_esc(_s(data, "tier_spend_word", "funded this cycle"))}: {g.get("funded", 0):,.0f} {_esc(currency)}</div>
  {_svg.line_panel(g.get("points", []), g.get("funded") or None, "#4f46e5", height=140)}
</div>"""
        group_html = f"""<h3 class="inv-subhead">{_esc(_s(data, "inv_frontier_by_group", "By business line"))}</h3>
<p class="inv-subhint">{_esc(_s(data, "inv_frontier_group_sub", ""))}</p>
<div class="inv-group-grid">{cells}</div>"""
    return _section("invest-frontier", _s(data, "inv_frontier_heading", "The budget-vs-return curve"),
                    _s(data, "inv_frontier_caption", ""), [panels + group_html])


def _investment_hte_core(data: Dict[str, Any], inv: Dict[str, Any]) -> str:
    hte = inv.get("hte", {})
    charts = inv.get("charts", {}).get("hte", {})
    qini = charts.get("qini", {})
    decile = charts.get("decile_calibration", {})
    distribution = charts.get("tau_distribution", {})
    gate_note = _s(data, "inv_hte_gate_note",
                   "Method: {method} · holdout n: {n}.").format(
        method=hte.get("method") or "missing", n=hte.get("holdout_n", 0))
    cards = [
        _wide_card(
            _s(data, "inv_hte_gate_title", "HTE validation gate"),
            gate_note,
            hte,
            extra=f'<span class="status">{_esc(hte.get("status", "missing"))}</span>',
        )
    ]
    if qini.get("status") == "available":
        cards.append(f"""<div class="wide-card">
  <strong>{_esc(_s(data, "inv_th_auuc", "Qini / AUUC"))}</strong>
  <span>AUUC: {_esc(qini.get('auuc', ''))}</span>
  {_svg.line_panel(qini.get("points", []), None, "#16a34a")}
</div>""")
    for row in decile.get("rows", [])[:4]:
        text = (f'{_s(data, "inv_th_predicted_tau", "Predicted tau")}: {row.get("predicted_tau", 0):.3f} · '
                f'{_s(data, "inv_th_observed_lift", "Observed lift")}: {row.get("observed_lift", 0):.3f} · '
                f'{_s(data, "inv_th_gap", "Gap")}: {row.get("gap", 0):.3f}')
        cards.append(_wide_card(f'{_s(data, "inv_th_decile", "Decile")} {row.get("decile", "")}', text, row))
    for row in distribution.get("bins", [])[:4]:
        share = float(row.get("share") or 0.0)
        cards.append(_wide_card(f'{_s(data, "inv_th_tau_bucket", "Tau bucket")} {row.get("bucket", "")}',
                                f'{_s(data, "inv_th_share", "Audience share")}: {share:.0%}', row))
    return _section("invest-hte", _s(data, "inv_hte_heading", "HTE Validation Core"),
                    _s(data, "inv_hte_sub", ""), cards)


def _investment_matrix(data: Dict[str, Any], inv: Dict[str, Any]) -> str:
    bm = inv.get("charts", {}).get("budget_matrix", {})
    x_axis, y_axis, cells = bm.get("x_axis", []), bm.get("y_axis", []), bm.get("cells", [])
    if not x_axis or not y_axis:
        return _section("invest-matrix", _s(data, "inv_matrix_heading", "Where the money lands"),
                        "", [_empty(_s(data, "inv_matrix_empty", "No allocation cleared the ROI floor."))])
    by_pos = {(c["sku"], c["module"]): c for c in cells}
    max_spend = max((c["spend"] for c in cells), default=0.0) or 1.0
    labels = inv.get("module_labels", {})
    head = (f"<div class='heat-head'>{_esc(_s(data, 'inv_th_sku', 'SKU'))}</div>"
            + "".join(f"<div class='heat-head'>{_esc(labels.get(m, m))}</div>" for m in x_axis))
    body = []
    for sku in y_axis:
        body.append(f"<div class='heat-channel'>{_esc(sku)}</div>")
        for mod in x_axis:
            cell = by_pos.get((sku, mod))
            if not cell:
                body.append("<div class='heat-cell'></div>")
                continue
            alpha = 0.18 + 0.72 * min(cell["spend"] / max_spend, 1.0)
            dot = _CONF_COLOR.get(cell["confidence"], "#9ca3af")
            detail = {"sku": sku, "module": mod, "spend": cell["spend"], "roi": cell["roi"],
                      "confidence": cell["confidence"]}
            body.append(
                f"<button class='heat-cell' style='background:rgba(79,70,229,{alpha:.2f})' "
                f"data-detail='{_detail_json(f'{sku} · {mod}', cell['confidence'], detail)}'>"
                f"{cell['spend']:,.0f}<span class='inv-conf-dot' style='background:{dot}'></span></button>")
    grid = f"<div class='heatmap' style='--cols:{len(x_axis)}'>{head}{''.join(body)}</div>"
    return _section("invest-matrix", _s(data, "inv_matrix_heading", "Where the money lands"),
                    _s(data, "inv_matrix_caption", ""), [grid])


def _investment_tasks(data: Dict[str, Any], inv: Dict[str, Any]) -> str:
    allocation = inv.get("activation_cards") or inv.get("answer", {}).get("allocation", [])
    currency = inv.get("currency", "")
    cards = []
    for row in allocation:
        conf = row.get("confidence", "assumption_grade")
        bits = [
            f'{_s(data, "inv_th_spend", "Spend")}: {row.get("spend", 0):,.0f} {row.get("currency", currency)}'.rstrip(),
            f'{_s(data, "inv_th_roi", "ROI")}: {row.get("roi", 0):.2f}x',
        ]
        if row.get("owner"):
            bits.append(f'{_s(data, "owner_word", "Owner")}: {row["owner"]}')
        if row.get("flight"):
            bits.append(f'{_s(data, "due_word", "Due")}: {row["flight"]}')
        if row.get("kpi"):
            bits.append(f'{_s(data, "inv_th_kpi", "KPI")}: {row["kpi"]}')
        if row.get("measurement"):
            bits.append(f'{_s(data, "inv_th_measurement", "Measurement")}: {row["measurement"]}')
        if row.get("stop_rule"):
            bits.append(f'{_s(data, "kill_line_word", "Stop-loss line")}: {row["stop_rule"]}')
        if row.get("why"):
            bits.append(f'{_s(data, "why_now_label", "Why now")}: {row["why"]}')
        bits.append(_s(data, f"inv_confidence_{conf}", conf))
        module_word = row.get("module_label") or row.get("module", "")
        cards.append(_wide_card(f'{row.get("sku","")} · {module_word}', " · ".join(bits), row,
                                extra=f'<span class="status">{_esc(conf)}</span>'))
    return _section("invest-tasks", _s(data, "inv_tasks_heading", "Activation cards"),
                    "", cards or [_empty("No funded rows.")])


def _investment_mmm(data: Dict[str, Any], inv: Dict[str, Any]) -> str:
    charts = inv.get("charts", {}).get("mmm", {})
    mmm = inv.get("mmm", {})
    cards = [_wide_card(
        _s(data, "inv_mmm_heading", "Macro channel calibration (MMM)"),
        _s(data, f"inv_mmm_{mmm.get('status', 'missing')}", _s(data, "inv_mmm_missing", "")),
        mmm,
        extra=f'<span class="status">{_esc(mmm.get("status", "missing"))}</span>',
    )]
    for row in charts.get("contribution", {}).get("bars", [])[:5]:
        cards.append(_wide_card(
            f'{_s(data, "inv_th_contribution", "Contribution")} · {row.get("channel", "")}',
            f"{row.get('contribution', 0):,.0f}",
            row,
        ))
    for row in charts.get("posterior_roas", {}).get("intervals", [])[:5]:
        cards.append(_wide_card(
            f'{_s(data, "inv_th_roas", "Posterior ROAS")} · {row.get("channel", "")}',
            f"{row.get('mean', 0):.2f}x ({row.get('lo', 0):.2f}-{row.get('hi', 0):.2f})",
            row,
        ))
    for panel in charts.get("adstock", {}).get("panels", [])[:2]:
        cards.append(f"""<div class="wide-card">
  <strong>{_esc(_s(data, "inv_mmm_adstock", "Adstock / response"))} · {_esc(panel.get('channel', ''))}</strong>
  {_svg.line_panel(panel.get("points", []), None, "#0891b2")}
</div>""")
    for panel in charts.get("saturation", {}).get("panels", [])[:2]:
        cards.append(f"""<div class="wide-card">
  <strong>{_esc(_s(data, "inv_mmm_saturation", "Saturation"))} · {_esc(panel.get('channel', ''))}</strong>
  {_svg.line_panel(panel.get("points", []), None, "#4f46e5")}
</div>""")
    lift = charts.get("lift_calibration", {})
    if lift.get("status") == "available":
        cards.append(f"""<div class="wide-card">
  <strong>{_esc(_s(data, "inv_mmm_lift_calibration", "Lift calibration"))}</strong>
  {_svg.line_panel(lift.get("points", []), None, "#d97706")}
</div>""")
    return _section("invest-mmm", _s(data, "inv_mmm_heading", "Macro channel calibration (MMM)"),
                    _s(data, "inv_mmm_sub", ""), cards)


def _investment_confidence_mmm(data: Dict[str, Any], inv: Dict[str, Any]) -> str:
    counts = inv.get("charts", {}).get("confidence", {})
    cards = [
        _wide_card(_s(data, f"inv_confidence_{k}", k), str(counts.get(k, 0)), {"count": counts.get(k, 0)})
        for k in ("validated", "mmm_calibrated", "assumption_grade", "blocked")
    ]
    mmm = inv.get("mmm", {})
    status = mmm.get("status", "missing")
    mmm_text = _s(data, f"inv_mmm_{status}", _s(data, "inv_mmm_missing"))
    cards.append(_wide_card(_s(data, "inv_mmm_heading", "Macro channel calibration (MMM)"), mmm_text, mmm))
    return _section("invest-confidence", _s(data, "inv_confidence_heading", "How much of this rests on solid evidence"),
                    _s(data, "inv_qini_missing", ""), cards)


def _hero(data: Dict[str, Any], label: str) -> str:
    meta = data["meta"]
    overview = data.get("overview", {})
    return f"""<section class="hero section" id="overview">
  <div>
    <div class="eyebrow">{_esc(label)}</div>
    <h1>{_esc(meta.get('product', 'Untitled'))} <span>{_esc(meta.get('market', ''))}</span></h1>
    <p>{_esc(overview.get('thesis', 'No thesis provided.'))}</p>
  </div>
  <div class="hero-actions">
    <button class="pill verdict" data-detail='{_detail_json("Verdict", overview.get("thesis", ""), overview)}'>{_esc(str(overview.get('verdict', 'undetermined')).upper())}</button>
    <button class="pill" data-detail='{_detail_json(_s(data, "dash_top_action", "Top action"), overview.get("top_action", ""), overview)}'>{_esc(_s(data, "dash_top_action", "Top action"))}</button>
    <button class="pill muted" data-detail='{_detail_json(_s(data, "dash_top_blocker", "Top blocker"), overview.get("top_blocker", ""), overview)}'>{_esc(_s(data, "dash_top_blocker", "Top blocker"))}</button>
  </div>
</section>"""


def _kpis(data: Dict[str, Any]) -> str:
    cards = []
    for row in data.get("kpis", []):
        text = row.get("note") or row.get("basis") or row.get("needed_from", "")
        cards.append(f"""<button class="kpi-card" data-detail='{_detail_json(row.get("label", ""), text, row)}'>
  <span>{_esc(row.get('label', 'Metric'))}</span>
  <strong>{_esc(str(row.get('value_text', row.get('value', ''))))}</strong>
  <em>{_esc(row.get('provenance', ''))}</em>
</button>""")
    return f'<section class="kpi-strip section" id="kpis">{"".join(cards)}</section>'


def _economics(data: Dict[str, Any]) -> str:
    rows = []
    for row in data.get("economics", {}).get("derivations", []):
        rows.append(_wide_card(row.get("label", row.get("id", "")), _number_text(row), row))
    for row in data.get("economics", {}).get("sensitivity", []):
        rows.append(_wide_card(row.get("change", "Sensitivity"), row.get("effect", ""), row))
    return _section(
        "economics",
        _s(data, "dash_economics_title", "Economics"),
        _s(data, "dash_economics_sub", "Unit economics, CAC ceiling, and sensitivity levers."),
        rows or [_empty("No economics rows available.")],
    )


def _channels(data: Dict[str, Any]) -> str:
    cards = []
    for channel in data.get("channels", []):
        cards.append(_wide_card(
            channel.get("name", ""),
            channel.get("reasoning", ""),
            channel,
            extra=f'<span class="status">{_esc(channel.get("verdict", ""))}</span>',
        ))
    return _section(
        "channels",
        _s(data, "dash_channels_title", "Channel Screen"),
        _s(data, "dash_channels_sub", "Which channels can be defended before spend is unlocked."),
        cards or [_empty("No channel screen available.")],
    )


def _causal_map(data: Dict[str, Any]) -> str:
    nodes = ["Product", "Economics", "Channel", "Dimension", "Treatment", "Measurement"]
    html = "".join(
        f'<button class="graph-node" data-detail=\'{_detail_json(n, "Layer in the causal decision chain.", {"layer": n})}\'>{_esc(n)}</button>'
        for n in nodes
    )
    return _section("map", _s(data, "dash_map_title", "Causal Map"),
                    _s(data, "dash_map_sub", "The dashboard keeps the reasoning sequence visible."), [f'<div class="graph">{html}</div>'])


def _dimensions(data: Dict[str, Any]) -> str:
    dims = data.get("dimensions", [])
    if not dims:
        return _section("dimensions", _s(data, "dash_dimensions_title", "D Dimension Table"), "", [_empty("No dimension table available.")])
    cards = []
    for d in dims:
        extra = f'<span class="status">{_esc(d.get("verdict",""))}</span>'
        if d.get("post_treatment_check") == "fail":
            extra = (f'<span class="stance stance-fix">'
                     f'{_esc(_s(data, "post_treatment_warn", "post-treatment proxy risk"))}</span> ') + extra
        cards.append(_wide_card(f'{d.get("id","")} · {d.get("label","")}', d.get("logic", ""), d,
                                extra=extra))
    return _section("dimensions", _s(data, "dash_dimensions_title", "D Dimension Table"),
                    _s(data, "dash_dimensions_sub", "Buyer characteristics that predict incremental response, within the channels above."), cards)


def _aud_grade_badge(grade: str | None) -> str:
    if not grade:
        return ""
    return f'<span class="aud-grade aud-grade-{_esc(grade)}">{_esc(grade)}</span>'


def _audience_cards(data: Dict[str, Any]) -> str:
    """Audience cards (ref 18): who exactly, how big the pool is (the four-layer
    sizing chain, graded), how to reach them (match quality), suppression,
    measurement, weakest assumption. Rendered inside chapter 3 (the play)."""
    cards = data.get("audience_cards", [])
    if not cards:
        return ""
    blocks = []
    for c in cards:
        role = c.get("causal_role")
        role_html = (f'<span class="aud-role aud-role-{_esc(role)}">{_esc(c.get("role_label", ""))}</span>'
                     if role else "")
        who = ""
        if c.get("dimensions"):
            chips = "".join(f'<span class="aud-chip">{_esc(v)}</span>' for v in c["dimensions"])
            who = f'<div class="aud-who">{_esc(_s(data, "aud_who_word", "Who they are"))}: {chips}</div>'
        chain = ""
        if c.get("factors"):
            parts = []
            for i, f in enumerate(c["factors"]):
                sep = " × " if i > 0 else ""
                parts.append(f'{sep}<span class="aud-factor"><span class="lab">{_esc(f["label"])}</span> '
                             f'<b>{_esc(f["value_text"])}</b>{_aud_grade_badge(f.get("grade"))}</span>')
            result = ""
            if c.get("reachable_text"):
                result = (f' = <span class="aud-result">{_esc(c["reachable_text"])}</span> '
                          f'<span class="lab" style="font-size:12px;color:var(--muted)">'
                          f'{_esc(_s(data, "aud_reachable_word", "Reachable pool"))}</span>'
                          f'{_aud_grade_badge(c.get("worst_grade"))}')
            chain = f'<div class="aud-chain">{"".join(parts)}{result}</div>'
        pers = ""
        if c.get("persuadable_known") and c.get("persuadable_text"):
            pers = (f'<div class="aud-persuadable"><span class="lab">'
                    f'{_esc(_s(data, "aud_persuadable_word", "Of which persuadable"))}:</span> '
                    f'<b>{_esc(c["persuadable_text"])}</b>{_aud_grade_badge(c.get("persuadable_grade"))}</div>')
        elif c.get("reachable_text"):
            pers = (f'<div class="aud-unknown">⚠ '
                    f'{_esc(_s(data, "aud_persuadable_unknown", "Persuadable share unknown"))}</div>')
        reach = ""
        if c.get("reach"):
            rows = "".join(
                f'<tr><td>{_esc(r["platform"])}</td><td>{_esc(r["proxy"])}</td>'
                f'<td>{_esc(r["match_label"])}</td><td>{_esc(r["what_leaks"])}</td></tr>'
                for r in c["reach"])
            reach = (f'<table class="aud-reach"><thead><tr>'
                     f'<th>{_esc(_s(data, "aud_th_platform", "Platform"))}</th>'
                     f'<th>{_esc(_s(data, "aud_th_proxy", "Proxy"))}</th>'
                     f'<th>{_esc(_s(data, "aud_th_match", "Match"))}</th>'
                     f'<th>{_esc(_s(data, "aud_th_leaks", "Leaks"))}</th></tr></thead>'
                     f'<tbody>{rows}</tbody></table>')

        def foot(key: str, default: str, val: str) -> str:
            return (f'<div><span class="lab">{_esc(_s(data, key, default))}:</span> {_esc(val)}</div>'
                    if val else "")
        footer = (foot("aud_suppression_word", "Exclude", c.get("suppression", ""))
                  + foot("aud_measurement_word", "How we'd measure it", c.get("measurement", ""))
                  + foot("aud_weakest_word", "Weakest assumption", c.get("weakest_assumption", "")))
        blocks.append(
            f'<div class="aud-card"><div class="aud-head">'
            f'<strong>{_esc(c.get("name", ""))}</strong>{role_html}</div>'
            f'{who}{chain}{pers}{reach}<div class="aud-foot">{footer}</div></div>')
    legend = f'<p class="aud-legend">{_esc(_s(data, "aud_grade_legend", ""))}</p>'
    cap = f'<p class="aud-legend">{_esc(_s(data, "aud_caption", ""))}</p>'
    body = (f'<div style="display:flex;flex-direction:column;gap:10px">{"".join(blocks)}</div>'
            f'{legend}{cap}')
    return f"""<section class="panel section" id="audience">
  <div class="section-head"><div><div class="eyebrow">audience</div><h2>{_esc(_s(data, "dash_audience_title", "Audience cards"))}</h2><p>{_esc(_s(data, "dash_audience_sub", ""))}</p></div></div>
  {body}
</section>"""


def _measurement(data: Dict[str, Any]) -> str:
    mp = data.get("measurement", {})
    if not mp:
        return ""
    rows = []
    if mp.get("primary_metric"):
        rows.append(_wide_card("Primary metric", mp["primary_metric"], mp))
    for m in mp.get("secondary_metrics", []):
        rows.append(_wide_card("Secondary metric", m, {"metric": m}))
    if mp.get("scale_up_rule"):
        rows.append(_wide_card("Scale-up rule", mp["scale_up_rule"], mp))
    if mp.get("pause_rule"):
        rows.append(_wide_card("Pause rule", mp["pause_rule"], mp))
    if mp.get("gcg_design"):
        rows.append(_wide_card("GCG design", mp["gcg_design"], mp))
    maturity = mp.get("maturity", "L0")
    return _section("measurement", f'{_s(data, "dash_measurement_title", "Measurement Plan")} · {_esc(maturity)}',
                    mp.get("hte_note", ""), rows or [_empty("No measurement plan available.")])


def _heatmap(data: Dict[str, Any]) -> str:
    heatmap = data.get("heatmap", {})
    columns = heatmap.get("columns", [])
    rows = heatmap.get("rows", [])
    s = data.get("strings", {})
    channels = {c["id"]: c for c in data.get("channels", [])}
    if not columns or not rows:
        return _section("heatmap", _s(data, "dash_heatmap_title", "Play matrix"), "", [_empty("No heatmap data available.")])

    head = "<div class='heat-head'>Channel</div>" + "".join(
        f"<div class='heat-head'>{_esc(c['id'])}<br><span>{_esc(c['label'])}</span></div>"
        for c in columns
    )
    body = []
    for row in rows:
        name = row.get("channel_name") or channels.get(row.get("channel_id"), {}).get("name", row.get("channel_id", ""))
        body.append(f"<div class='heat-channel'>{_esc(name)}</div>")
        for col, grade in zip(columns, row.get("grades", [])):
            word = s.get(f"grade_{grade}", grade)
            detail = {"channel": name, "dimension": col, "grade": f"{word} ({grade})"}
            cell_text = f"{word}: {col.get('label', '')}"
            body.append(
                f"<button class='heat-cell grade-{_esc(grade)}' "
                f"data-detail='{_detail_json(name, cell_text, detail)}'>"
                f"{_esc(word)}</button>"
            )
    caption = s.get("heatmap_caption", "")
    synthetic_note = ""
    if heatmap.get("synthetic"):
        synthetic_note = "<p class='synthetic-note'>Auto-inferred from channel verdicts — no real heatmap scores in the config yet.</p>"
    return _section(
        "heatmap",
        _s(data, "dash_heatmap_title", "Play matrix"),
        caption or "Click a cell to inspect the causal hypothesis, proxy, and validation action.",
        [f"<div class='heatmap' style='--cols:{len(columns)}'>{head}{''.join(body)}</div>{synthetic_note}"],
    )


def _never_do(data: Dict[str, Any]) -> str:
    rows = data.get("rejected_options", [])
    if not rows:
        return ""
    s = data.get("strings", {})
    cards = [_wide_card(r.get("option", ""), r.get("reason", ""), r) for r in rows]
    return _section("neverdo", s.get("never_do_heading", "Never do"),
                    "Refused moves and the reason each was refused.", cards)


def _suppression(data: Dict[str, Any]) -> str:
    rows = data.get("suppression", [])
    if not rows:
        return ""
    cards = [_wide_card(r.get("rule", ""), r.get("reason", ""), r,
                        extra=f'<span class="status">{_esc(r.get("dimension", ""))}</span>')
             for r in rows]
    return _section("suppression", _s(data, "dash_suppression_title", "Who NOT to touch"),
                    _s(data, "dash_suppression_sub", "Targeting these people burns money — exclusions are part of the play."), cards)


def _budgets(data: Dict[str, Any]) -> str:
    rows = data.get("budgets", [])
    if not rows:
        return ""
    cards = [_wide_card(f'{r.get("phase", "")} · {r.get("item", "")}',
                        f'{r.get("budget_text", "—")} — {r.get("condition", "")}', r)
             for r in rows]
    return _section("budgets", _s(data, "dash_budgets_title", "Budget release"),
                    _s(data, "dash_budgets_sub", "Money unlocks stage by stage; each line names its release condition."), cards)


def _checklist(data: Dict[str, Any]) -> str:
    items = data.get("checklist", [])
    gates = data.get("gates", [])
    if not items and not gates:
        return ""
    s = data.get("strings", {})
    cards = []
    for g in gates:
        cards.append(_wide_card(g.get("gate", ""), g.get("input_needed", ""), g,
                                extra=f'<span class="status">{_esc(g.get("status", ""))}</span>'))
    for i in items:
        cards.append(_wide_card(i.get("item", ""), "", i,
                                extra=f'<span class="status">{_esc(i.get("status", ""))}</span>'))
    return _section("gates", s.get("gate_word", "Release conditions"),
                    _s(data, "dash_gates_sub", "Everything that must land before budget unlocks."), cards)


def _challenges_section(data: Dict[str, Any]) -> str:
    rows = data.get("challenges", [])
    if not rows:
        return ""
    cards = [_wide_card(f'{c.get("id", "")} · {c.get("target", "")}', c.get("question", ""), c,
                        extra=f'<span class="status">{_esc(c.get("status", ""))}</span>')
             for c in rows]
    return _section("challenges", _s(data, "dash_challenges_title", "Self-critique"),
                    _s(data, "dash_challenges_sub", "Independent challenges to this analysis — open items block dependent spend."), cards)


def _treatments(data: Dict[str, Any]) -> str:
    cards = []
    for treatment in data.get("treatments", []):
        text = " · ".join(x for x in [
            treatment.get("mechanism"),
            treatment.get("test"),
            treatment.get("gate"),
        ] if x)
        cards.append(_wide_card(f"{treatment.get('id')} {treatment.get('label')}", text, treatment))
    return _section(
        "treatments",
        _s(data, "dash_treatments_title", "Treatment Gates"),
        _s(data, "dash_treatments_sub", "Every action carries mechanism, guardrail, test, and gate."),
        cards or [_empty("No treatment/action cards available.")],
    )


def _portfolio_tiers(data: Dict[str, Any]) -> str:
    drill = data.get("portfolio", {}).get("tier_drill", [])
    if not drill:
        cards = [
            _wide_card(t.get("label", ""), f"{t.get('trend', '')} · {t.get('audience', '')} · {t.get('channel_fit', '')}", t)
            for t in data.get("portfolio", {}).get("tiers", [])
        ]
        return _section("tiers", _s(data, "dash_tiers_title", "Tier Map"),
                        _s(data, "dash_tiers_sub", "Price tiers, audiences, forces, and channel fit."), cards)

    spend_word = _s(data, "tier_spend_word", "funded this cycle")
    sku_word = _s(data, "tier_sku_count_word", "SKU(s)")
    tiers_html = ""
    for t in drill:
        sku_rows = ""
        for sku in t.get("skus", []):
            verdict = str(sku.get("verdict", ""))
            verdict_word = _s(data, f"verdict_{verdict}", verdict)
            fourp = sku.get("fourP", {})
            fourp_rows = "".join(
                f'<div class="drill-fourp-row"><b>{_esc(_s(data, f"dash_4p_{key}", label))}</b>{_esc(fourp.get(key, "—"))}</div>'
                for key, label in (("product", "Product"), ("price", "Price"),
                                   ("place", "Place"), ("promotion", "Promotion"))
                if fourp.get(key))
            module_rows = "".join(
                f'<div class="drill-module-row"><span>{_esc(m.get("module", ""))}</span>'
                f'<span>{m.get("spend", 0):,.0f} · ROI {m.get("roi", 0):.2f}x</span></div>'
                for m in sku.get("modules", []))
            spend_badge = (f'<span class="drill-spend">{sku.get("spend", 0):,.0f}</span>'
                           if sku.get("spend") else "")
            sku_rows += f"""<details class="drill drill-sku">
  <summary><span class="status">{_esc(verdict_word)}</span> <strong>{_esc(sku.get("sku", ""))}</strong>{spend_badge}</summary>
  <p class="drill-note">{_esc(sku.get("note", ""))}</p>
  {fourp_rows}
  {module_rows}
</details>"""
        tiers_html += f"""<details class="drill drill-tier">
  <summary><strong>{_esc(t.get("label", ""))}</strong>
    <span class="drill-meta">{len(t.get("skus", []))} {_esc(sku_word)} · {_esc(spend_word)}: {t.get("spend", 0):,.0f}</span>
  </summary>
  <p class="drill-note">{_esc(" · ".join(x for x in (t.get("trend"), t.get("audience"), t.get("force"), t.get("channel_fit")) if x))}</p>
  {sku_rows}
</details>"""
    hint = f'<p class="drill-hint">{_esc(_s(data, "dash_tiers_drill_hint", ""))}</p>'
    return _section("tiers", _s(data, "dash_tiers_title", "Tier Map"),
                    _s(data, "dash_tiers_sub", ""), [hint + tiers_html])


def _portfolio_diagnosis(data: Dict[str, Any]) -> str:
    cards = []
    for d in data.get("portfolio", {}).get("diagnosis", []):
        badges = f'<span class="status">{_esc(d.get("severity", ""))}</span>'
        stance = d.get("invest_stance")
        if stance:
            word = _s(data, f"stance_{stance}", stance)
            badges = f'<span class="stance stance-{_esc(stance)}">{_esc(word)}</span> ' + badges
        cards.append(_wide_card(
            f"{d.get('lens', '')} {d.get('title', '')}",
            d.get("implication", ""),
            d,
            extra=badges,
        ))
    return _section("diagnosis", _s(data, "dash_diag_title", "Diagnosis Lenses"),
                    _s(data, "dash_diag_sub", "L1-L6 category and 4P diagnosis."), cards)


# reading order inside the SKU matrix: where to invest first, what to exit last
_VERDICT_ORDER = {"grow": 0, "hold": 1, "harvest": 2, "exit": 3}


def _portfolio_skus(data: Dict[str, Any]) -> str:
    skus = sorted(data.get("portfolio", {}).get("skus", []),
                  key=lambda r: _VERDICT_ORDER.get(str(r.get("verdict", "")), 9))
    cards = [
        _wide_card(s.get("sku", ""), s.get("note", ""), s,
                   extra=f'<span class="status">{_esc(_s(data, "verdict_" + str(s.get("verdict", "")), s.get("verdict", "")))}</span>')
        for s in skus
    ]
    return _section("skus", _s(data, "dash_skus_title", "SKU Matrix"),
                    _s(data, "dash_skus_sub", "SKU verdicts and 4P moves."), cards)


def _portfolio_handoff(data: Dict[str, Any]) -> str:
    grow = [s for s in data.get("portfolio", {}).get("skus", []) if s.get("verdict") == "grow"]
    if not grow:
        return ""
    cards = [
        _wide_card(s.get("sku", ""), s.get("fourP", {}).get("promotion", "") or s.get("note", ""), s)
        for s in grow
    ]
    return _section("handoff", _s(data, "dash_handoff_title", "Deep-Dive Handoff"),
                    _s(data, "dash_handoff_sub",
                       "Grow-verdict SKUs — confirm, then run each through the single-SKU pipeline."), cards)


def _evidence(data: Dict[str, Any]) -> str:
    evidence = data.get("evidence", {})
    rows = []
    for group in ["missing", "sourced", "assumed", "derived"]:
        for row in evidence.get(group, []):
            rows.append(_wide_card(
                row.get("label", row.get("id", "")),
                _number_text(row),
                row,
                extra=f'<span class="status">{group}</span>',
            ))
    for fact in evidence.get("facts", []):
        rows.append(_wide_card("Fact", fact.get("fact", ""), fact))
    return _section(
        "evidence",
        _s(data, "dash_evidence_title", "Evidence Ledger"),
        _s(data, "dash_evidence_sub", "Sourced facts, assumptions, derivations, and missing values."),
        rows or [_empty("No evidence rows available.")],
    )


def _section(section_id: str, title: str, subtitle: str, children: Iterable[str]) -> str:
    return f"""<section class="panel section" id="{_esc(section_id)}">
  <div class="section-head"><div><div class="eyebrow">{_esc(section_id)}</div><h2>{_esc(title)}</h2><p>{_esc(subtitle)}</p></div></div>
  <div class="panel-grid">{''.join(children)}</div>
</section>"""


def _wide_card(title: str, text: str, payload: Dict[str, Any], extra: str = "") -> str:
    body = text or payload.get("value_text") or "Needs data"
    return f"""<button class="wide-card" data-detail='{_detail_json(title, text, payload)}'>
  <span class="card-extra">{extra}</span>
  <strong>{_esc(title)}</strong>
  <span>{_esc(body)}</span>
</button>"""


def _number_text(row: Dict[str, Any]) -> str:
    value = row.get("value_text", "")
    note = row.get("needed_from") or row.get("basis") or row.get("note", "")
    return " · ".join(str(part) for part in [value, note] if part)


def _empty(text: str) -> str:
    return f'<div class="empty">{_esc(text)}</div>'


def _nav(data: Dict[str, Any]) -> str:
    # both report kinds share the five-question spine — the rail is the
    # reading line: 1 the call, 2 the why, 3 the play, 4 execution, 5 receipts
    s = data.get("strings", {})
    return "".join(
        f'<a href="#{ch}" title="{_esc(s.get(f"{ch}_question", ""))}">{n}</a>'
        for n, ch in enumerate(("ch1", "ch2", "ch3", "ch4", "ch5"), 1)
    )


def _detail_json(title: str, text: str, payload: Dict[str, Any]) -> str:
    return _esc(json.dumps({"title": title, "text": text, "payload": payload}, ensure_ascii=False))


def _script_json(payload: Dict[str, Any]) -> str:
    return (json.dumps(payload, ensure_ascii=False)
            .replace("&", "\\u0026")
            .replace("<", "\\u003c")
            .replace(">", "\\u003e"))


def _esc(value: Any) -> str:
    return escape(str(value), quote=True)


def _css() -> str:
    return r"""
:root{--bg:#f3f3f1;--panel:rgba(255,255,255,.88);--line:#e4e5de;--ink:#111510;--muted:#6d7068;--green:#dff3e8;--amber:#fff1bf;--orange:#ffe1c2;--red:#f8d2cf;--blue:#e2f0f5;--select:#245d7c}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--ink);font:13px/1.55 "Microsoft YaHei UI","Microsoft YaHei",Arial,sans-serif;letter-spacing:0}.decision-dashboard{display:grid;grid-template-columns:64px minmax(0,1fr) 320px;gap:16px;padding:16px}.rail{position:sticky;top:16px;height:calc(100vh - 32px);background:var(--panel);border:1px solid var(--line);border-radius:10px;display:flex;flex-direction:column;align-items:center;gap:10px;padding:12px 8px}.rail-mark{font-size:10px;color:var(--muted);border-bottom:1px solid var(--line);width:100%;text-align:center;padding-bottom:8px}.rail a{color:var(--muted);text-decoration:none;border:1px solid var(--line);border-radius:7px;padding:6px 8px;background:#fff}.rail a:hover{background:var(--blue);color:var(--select)}.workspace{display:flex;flex-direction:column;gap:14px;min-width:0}.section{scroll-margin-top:16px}.hero,.panel,.detail-panel{background:var(--panel);border:1px solid var(--line);border-radius:12px;box-shadow:0 16px 38px rgba(20,24,18,.06)}.hero{display:flex;justify-content:space-between;gap:16px;padding:16px}.hero h1{font-size:24px;line-height:1.15;margin:2px 0 6px}.hero h1 span{color:var(--muted);font-weight:500}.hero p{margin:0;color:var(--muted);max-width:820px}.hero-actions{display:flex;gap:8px;align-items:flex-start;flex-wrap:wrap;justify-content:flex-end}.pill,.kpi-card,.wide-card,.heat-cell,.graph-node{font:inherit;cursor:pointer}.pill{border:1px solid var(--line);border-radius:999px;background:#fff;padding:6px 10px}.pill.verdict{background:var(--amber)}.pill.muted{color:var(--muted)}.kpi-strip{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px}.kpi-card{border:1px solid var(--line);border-radius:9px;background:#fff;text-align:left;padding:12px;min-height:86px}.kpi-card span,.kpi-card em{display:block;color:var(--muted);font-style:normal}.kpi-card strong{display:block;font-size:22px;margin:4px 0}.panel{padding:16px}.section-head{display:flex;justify-content:space-between;gap:12px}.section-head h2{font-size:18px;margin:0}.section-head p{margin:2px 0 12px;color:var(--muted)}.eyebrow{font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}.panel-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:10px}.wide-card{position:relative;border:1px solid var(--line);border-radius:8px;background:#fff;text-align:left;padding:12px;min-height:104px;overflow:hidden}.wide-card strong{display:block;font-size:14px;margin-bottom:6px}.wide-card span{color:var(--muted)}.card-extra{position:absolute;top:10px;right:10px}.status{border:1px solid var(--line);border-radius:999px;padding:3px 7px;background:#f8f9f6;color:var(--muted);font-size:11px}.graph{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;width:100%}.graph-node{border:1px solid var(--line);border-radius:8px;background:#fff;padding:14px;font-weight:700}.heatmap{display:grid;grid-template-columns:180px repeat(var(--cols),minmax(86px,1fr));gap:1px;background:var(--line);overflow:auto;border:1px solid var(--line);border-radius:8px}.heat-head,.heat-channel,.heat-cell{background:#fff;padding:10px;min-width:0}.heat-head{font-weight:700}.heat-head span{font-size:11px;color:var(--muted);font-weight:400}.heat-channel{font-weight:700}.heat-cell{border:0;font-weight:800;text-align:center}.grade-H{background:var(--green)}.grade-T{background:var(--amber)}.grade-S{background:var(--orange)}.grade-A{background:var(--red)}.grade-N{background:#f2f4f7}.empty{border:1px dashed var(--line);border-radius:8px;padding:18px;color:var(--muted);background:#fff}.chapter-band{background:linear-gradient(135deg,#245d7c,#173d52);color:#fff;border:0;border-radius:12px;padding:14px 18px}.chapter-band .eyebrow{color:rgba(255,255,255,.7)}.chapter-band h2{margin:2px 0 0;font-size:19px}.chapter-band .ch-ans{margin:8px 0 0;background:rgba(255,255,255,.14);border-radius:7px;padding:7px 10px;font-size:12.5px}.chapter-band .ch-ans b{margin-right:6px;opacity:.8}.synthetic-note{margin:8px 0 0;color:var(--muted);font-size:11.5px;font-style:italic}.detail-panel{position:sticky;top:16px;height:calc(100vh - 32px);padding:16px;overflow:auto}.detail-panel h2{font-size:20px;margin:4px 0 12px}.detail-panel p{color:var(--muted)}.detail-kv{display:grid;grid-template-columns:1fr;gap:7px}.detail-kv div{border:1px solid var(--line);border-radius:7px;padding:8px;background:#fff;overflow-wrap:anywhere}.detail-kv b{display:block;color:var(--muted);font-size:11px;text-transform:uppercase}@media(max-width:980px){.decision-dashboard{grid-template-columns:48px minmax(0,1fr)}.detail-panel{position:static;grid-column:2;height:auto}.hero{flex-direction:column}.heatmap{grid-template-columns:150px repeat(var(--cols),minmax(74px,1fr))}}@media(max-width:640px){.decision-dashboard{display:block;padding:10px}.rail{position:static;height:auto;flex-direction:row;margin-bottom:10px;overflow:auto}.workspace{gap:10px}.detail-panel{margin-top:10px}.panel-grid{grid-template-columns:1fr}}@media print{.rail,.detail-panel{display:none}.decision-dashboard{display:block}.hero,.panel{box-shadow:none;break-inside:avoid}}
.kpi-card.tone-good strong{color:#16a34a}.kpi-card.tone-warn strong{color:#d97706}.kpi-card.tone-bad strong{color:#dc2626}
.ch-bridge{margin:8px 0 0;font-size:12px;color:rgba(255,255,255,.75);line-height:1.55}
details.fold{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:0}
details.fold>summary{cursor:pointer;list-style:none;padding:14px 18px;font-weight:700;font-size:14px;color:var(--muted)}
details.fold>summary::before{content:'▸ ';color:var(--select)}
details.fold[open]>summary::before{content:'▾ '}
details.fold>section{border:0;box-shadow:none;border-radius:0;border-top:1px solid var(--line)}
details.drill{border:1px solid var(--line);border-radius:8px;background:#fff;margin:8px 0}
details.drill>summary{cursor:pointer;list-style:none;padding:11px 14px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}
details.drill>summary::before{content:'▸';color:var(--muted)}
details.drill[open]>summary::before{content:'▾'}
details.drill-tier>summary strong{font-size:14px}
.drill-meta{color:var(--muted);font-size:12px;margin-left:auto}
details.drill-sku{margin:6px 12px;background:#fafaf8}
.drill-spend{margin-left:auto;font-weight:700;color:var(--select)}
.drill-note{margin:2px 14px 8px;color:var(--muted);font-size:12px;line-height:1.5}
.drill-fourp-row{margin:3px 14px;font-size:12px;line-height:1.5}
.drill-fourp-row b{display:inline-block;min-width:44px;color:var(--muted);font-weight:600}
.drill-module-row{display:flex;justify-content:space-between;margin:3px 14px;padding:5px 9px;background:var(--blue);border-radius:6px;font-size:12px}
.drill-hint{color:var(--muted);font-size:12px;margin:0 0 8px}
.stance{border-radius:999px;padding:3px 9px;font-size:11px;font-weight:700}
.stance-invest{background:var(--green);color:#14532d}
.stance-test{background:var(--blue);color:#245d7c}
.stance-hold{background:#f2f4f7;color:#6d7068}
.stance-fix{background:var(--amber);color:#854d0e}
.limits-intro{font-size:13px;line-height:1.6;margin:0 0 8px}
.limits-blocked{margin:6px 0 2px;font-size:12.5px}
.limits-blocked-list{margin:0 0 10px;padding-left:18px;font-size:12.5px;color:var(--muted)}
.limits-blocked-list li{margin:3px 0}
.csv-box{border:1px dashed var(--line);border-radius:8px;padding:12px;background:#fff}
.csv-head{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap}
.csv-head .pill{font-size:12px;cursor:pointer}
.csv-hint{color:var(--muted);font-size:12px;line-height:1.55;margin:8px 0}
.csv-box pre{max-height:180px;overflow:auto;background:#f8f9f6;border-radius:6px;padding:10px;font-size:11px;line-height:1.6;white-space:pre}
.inv-subhead{margin:16px 0 2px;font-size:14px}
.inv-subhint{color:var(--muted);font-size:12px;margin:0 0 8px}
.inv-group-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px;width:100%}
.inv-panel-meta{color:var(--muted);font-size:11.5px;margin:0 0 4px}
.inv-frontier-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;width:100%}
@media(max-width:760px){.inv-frontier-grid{grid-template-columns:1fr}}
.inv-panel{border:1px solid var(--line);border-radius:8px;background:#fff;padding:10px 12px}
.inv-panel-title{font-size:11.5px;font-weight:700;color:var(--muted);margin-bottom:6px}
.inv-svg{width:100%;height:auto;display:block}
.inv-svg-empty{color:var(--muted);font-size:12px;padding:20px 0;text-align:center}
.inv-conf-dot{display:inline-block;width:7px;height:7px;border-radius:50%;margin-left:4px;vertical-align:middle}
.aud-card{border:1px solid var(--line);border-radius:10px;background:#fff;padding:14px 16px;width:100%}
.aud-head{display:flex;justify-content:space-between;align-items:center;gap:10px}
.aud-head strong{font-size:15px}
.aud-role{border-radius:11px;padding:2px 10px;font-size:12px;font-weight:600;color:#fff;white-space:nowrap}
.aud-role-persuadable{background:#1a7f47}.aud-role-sure_thing,.aud-role-sleeping_dog{background:#c0392b}
.aud-role-lost_cause{background:#8a8f98}.aud-role-unknown{background:#b8860b}
.aud-who{margin:8px 0;font-size:12px;color:var(--muted)}
.aud-chip{display:inline-block;padding:1px 8px;margin:2px 4px 2px 0;border:1px solid var(--line);border-radius:11px;font-size:12px;color:var(--ink)}
.aud-chain{margin:8px 0;line-height:2}
.aud-factor{white-space:nowrap}.aud-factor .lab{font-size:11px;color:var(--muted)}
.aud-grade{display:inline-block;min-width:15px;text-align:center;padding:0 5px;margin-left:5px;border-radius:9px;color:#fff;font-size:11px;font-weight:700}
.aud-grade-A{background:#1a7f47}.aud-grade-B{background:#2f8f83}.aud-grade-C{background:#b8860b}.aud-grade-D{background:#c0392b}
.aud-result{font-size:16px;font-weight:700}
.aud-persuadable{margin:4px 0;font-size:13px}.aud-persuadable .lab{color:var(--muted)}
.aud-unknown{margin:4px 0;font-size:13px;color:var(--muted)}
.aud-reach{width:100%;border-collapse:collapse;margin-top:8px;font-size:12px}
.aud-reach th{text-align:left;color:var(--muted);font-weight:600;border-bottom:1px solid var(--line);padding:4px 6px}
.aud-reach td{border-bottom:1px solid var(--line);padding:4px 6px;vertical-align:top}
.aud-foot{margin-top:8px;font-size:12px}.aud-foot div{margin:3px 0}.aud-foot .lab{color:var(--muted)}
.aud-legend{color:var(--muted);font-size:11.5px;margin:6px 0 0}
"""


def _js() -> str:
    return r"""
function safeText(value){return value === null || value === undefined || value === "" ? "-" : String(value);}
function escapeHtml(value){
  return safeText(value).replace(/[&<>"']/g, (ch) => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"
  })[ch]);
}
function renderDetail(raw){
  const detail = JSON.parse(raw);
  document.getElementById("detail-title").textContent = detail.title || "Detail";
  const payload = detail.payload || {};
  const rows = Object.entries(payload).slice(0, 14).map(([key,value]) => {
    const rendered = Array.isArray(value) || (value && typeof value === "object") ? JSON.stringify(value) : safeText(value);
    return `<div><b>${escapeHtml(key)}</b>${escapeHtml(rendered)}</div>`;
  }).join("");
  document.getElementById("detail-body").innerHTML = `<p>${escapeHtml(detail.text)}</p><div class="detail-kv">${rows}</div>`;
}
document.querySelectorAll("[data-detail]").forEach((el) => {
  el.addEventListener("click", () => renderDetail(el.getAttribute("data-detail")));
});
function smcpCsvText(){
  const el = document.getElementById("smcp-csv-template");
  return el ? el.textContent : "";
}
function smcpCopyCsv(){
  const text = smcpCsvText();
  if (navigator.clipboard && navigator.clipboard.writeText) { navigator.clipboard.writeText(text); return; }
  const ta = document.createElement("textarea");
  ta.value = text; document.body.appendChild(ta); ta.select();
  document.execCommand("copy"); document.body.removeChild(ta);
}
function smcpDownloadCsv(){
  const blob = new Blob(["﻿" + smcpCsvText()], {type: "text/csv;charset=utf-8"});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "investment-cells-template.csv";
  document.body.appendChild(a); a.click();
  document.body.removeChild(a); URL.revokeObjectURL(a.href);
}
"""
