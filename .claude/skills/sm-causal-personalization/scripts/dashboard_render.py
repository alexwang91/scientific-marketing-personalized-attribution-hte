#!/usr/bin/env python3
"""Render normalized dashboard data as a single-file interactive HTML cockpit."""

from __future__ import annotations

import json
from html import escape
from typing import Any, Dict, Iterable


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
    <div class="eyebrow">Detail</div>
    <h2 id="detail-title">Select an item</h2>
    <div id="detail-body"><p>Click a KPI, channel, heatmap cell, treatment, diagnosis, or evidence row to inspect its reasoning.</p></div>
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
        _heatmap(data),
        _suppression(data),
        ch("ch4"),
        _treatments(data),
        _budgets(data),
        _checklist(data),
        ch("ch5"),
        _causal_map(data),
        _challenges_section(data),
        _evidence(data),
    ])


def _chapter_head(ch_id: str, title: str, question: str, answer_label: str, answer: str) -> str:
    answer_html = f'<p class="ch-ans"><b>{_esc(answer_label)}</b> {_esc(answer)}</p>' if answer else ""
    return f"""<section class="chapter-band section" id="{_esc(ch_id)}">
  <div class="eyebrow">{_esc(title)}</div>
  <h2>{_esc(question)}</h2>
  {answer_html}
</section>"""


def _render_category(data: Dict[str, Any]) -> str:
    return "\n".join([
        _hero(data, "Portfolio Verdict"),
        _kpis(data),
        _portfolio_tiers(data),
        _portfolio_diagnosis(data),
        _portfolio_skus(data),
        _evidence(data),
    ])


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
    <button class="pill" data-detail='{_detail_json("Top action", overview.get("top_action", ""), overview)}'>Top action</button>
    <button class="pill muted" data-detail='{_detail_json("Top blocker", overview.get("top_blocker", ""), overview)}'>Top blocker</button>
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
        "Economics",
        "Unit economics, CAC ceiling, and sensitivity levers.",
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
        "Channel Screen",
        "Which channels can be defended before spend is unlocked.",
        cards or [_empty("No channel screen available.")],
    )


def _causal_map(data: Dict[str, Any]) -> str:
    nodes = ["Product", "Economics", "Channel", "Dimension", "Treatment", "Measurement"]
    html = "".join(
        f'<button class="graph-node" data-detail=\'{_detail_json(n, "Layer in the causal decision chain.", {"layer": n})}\'>{_esc(n)}</button>'
        for n in nodes
    )
    return _section("map", "Causal Map", "The dashboard keeps the reasoning sequence visible.", [f'<div class="graph">{html}</div>'])


def _heatmap(data: Dict[str, Any]) -> str:
    heatmap = data.get("heatmap", {})
    columns = heatmap.get("columns", [])
    rows = heatmap.get("rows", [])
    s = data.get("strings", {})
    channels = {c["id"]: c for c in data.get("channels", [])}
    if not columns or not rows:
        return _section("heatmap", "Play matrix", "Channel x audience fit.", [_empty("No heatmap data available.")])

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
        "Play matrix",
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
    return _section("suppression", "Who NOT to touch",
                    "Targeting these people burns money — exclusions are part of the play.", cards)


def _budgets(data: Dict[str, Any]) -> str:
    rows = data.get("budgets", [])
    if not rows:
        return ""
    cards = [_wide_card(f'{r.get("phase", "")} · {r.get("item", "")}',
                        f'{r.get("budget_text", "—")} — {r.get("condition", "")}', r)
             for r in rows]
    return _section("budgets", "Budget release",
                    "Money unlocks stage by stage; each line names its release condition.", cards)


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
                    "Everything that must land before budget unlocks.", cards)


def _challenges_section(data: Dict[str, Any]) -> str:
    rows = data.get("challenges", [])
    if not rows:
        return ""
    cards = [_wide_card(f'{c.get("id", "")} · {c.get("target", "")}', c.get("question", ""), c,
                        extra=f'<span class="status">{_esc(c.get("status", ""))}</span>')
             for c in rows]
    return _section("challenges", "Self-critique",
                    "Independent challenges to this analysis — open items block dependent spend.", cards)


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
        "Treatment Gates",
        "Every action carries mechanism, guardrail, test, and gate.",
        cards or [_empty("No treatment/action cards available.")],
    )


def _portfolio_tiers(data: Dict[str, Any]) -> str:
    cards = [
        _wide_card(t.get("label", ""), f"{t.get('trend', '')} · {t.get('audience', '')} · {t.get('channel_fit', '')}", t)
        for t in data.get("portfolio", {}).get("tiers", [])
    ]
    return _section("tiers", "Tier Map", "Price tiers, audiences, forces, and channel fit.", cards)


def _portfolio_diagnosis(data: Dict[str, Any]) -> str:
    cards = [
        _wide_card(
            f"{d.get('lens', '')} {d.get('title', '')}",
            d.get("implication", ""),
            d,
            extra=f'<span class="status">{_esc(d.get("severity", ""))}</span>',
        )
        for d in data.get("portfolio", {}).get("diagnosis", [])
    ]
    return _section("diagnosis", "Diagnosis Lenses", "L1-L6 category and 4P diagnosis.", cards)


def _portfolio_skus(data: Dict[str, Any]) -> str:
    cards = [
        _wide_card(f"{s.get('sku', '')} · {s.get('verdict', '')}", s.get("note", ""), s)
        for s in data.get("portfolio", {}).get("skus", [])
    ]
    return _section("skus", "SKU Matrix", "SKU verdicts and 4P moves.", cards)


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
        "Evidence Ledger",
        "Sourced facts, assumptions, derivations, and missing values.",
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
    if data.get("kind") == "category_portfolio":
        items = [("overview", "01"), ("kpis", "02"), ("tiers", "03"), ("diagnosis", "04"), ("skus", "05"), ("evidence", "06")]
        return "".join(f'<a href="#{sid}">{label}</a>' for sid, label in items)
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
"""
