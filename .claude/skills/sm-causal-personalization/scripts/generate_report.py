#!/usr/bin/env python3
"""
generate_report.py — Scientific Marketing HTML Report Generator

Generates structured HTML campaign reports from a config dict or JSON file.
Bridges power_analysis.py + qini_auuc.py + ope_estimators.py into the report.

Usage:
  python generate_report.py --demo > report.html
  python generate_report.py --config config.json --output report.html

Config schema: see DEMO_CONFIG below. Full spec: references/12-html-report-output.md.
Product pipeline (how to build config from product inputs): references/13-product-country-pipeline.md.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

# ── optional script imports ───────────────────────────────────────────────────
_HERE = Path(__file__).parent


def _import_power():
    try:
        sys.path.insert(0, str(_HERE))
        from power_analysis import n_per_arm_ate, n_per_cell_hte, experiment_duration_days
        return n_per_arm_ate, n_per_cell_hte, experiment_duration_days
    except Exception:
        return None, None, None


def _import_qini():
    try:
        sys.path.insert(0, str(_HERE))
        from qini_auuc import auuc_bootstrap_ci
        return auuc_bootstrap_ci
    except Exception:
        return None


def _import_ope():
    try:
        sys.path.insert(0, str(_HERE))
        from ope_estimators import support_check
        return support_check
    except Exception:
        return None


# ── HTML helpers ──────────────────────────────────────────────────────────────

_TAG_CLASS = {
    "evidence": "evidence",
    "assumption": "assumption",
    "hypothesis": "hypothesis",
    "needs-test": "needs-test",
    "needs-quote": "needs-test",
}
_TAG_LABEL = {
    "evidence": "Evidence",
    "assumption": "Assumption",
    "hypothesis": "Hypothesis",
    "needs-test": "Needs test",
    "needs-quote": "Needs quote",
}

_HM_CLASS = {"H": "hm-high", "T": "hm-test", "S": "hm-small", "N": "hm-none", "A": "hm-avoid"}


def tag(status: str) -> str:
    cls = _TAG_CLASS.get(status, "needs-test")
    label = _TAG_LABEL.get(status, status.title())
    return f'<span class="tag {cls}">{label}</span>'


def hm(v: str) -> str:
    cls = _HM_CLASS.get(v, "hm-none")
    return f'<td class="hm {cls}">{v}</td>'


def esc(s: str) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ── CSS ───────────────────────────────────────────────────────────────────────

_CSS = """
  :root {
    --bg:#f6f7f8;--panel:#fff;--ink:#172026;--muted:#5f6b76;--line:#d9dee3;
    --high:#dff3e8;--high-ink:#145c3b;--test:#fff1bf;--test-ink:#6b4e00;
    --small:#ffe1c2;--small-ink:#7a3d00;--avoid:#f8d2cf;--avoid-ink:#84211b;
    --neutral:#f2f4f7;--neutral-ink:#4c5965;--blue:#245d7c;
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--ink);font-family:Arial,"Helvetica Neue",sans-serif;line-height:1.48}
  header{padding:28px 32px 20px;border-bottom:1px solid var(--line);background:#fff}
  main{max-width:1480px;margin:0 auto;padding:22px 24px 48px}
  h1{margin:0 0 8px;font-size:30px;line-height:1.15}
  h2{margin:28px 0 12px;font-size:20px;border-bottom:1px solid var(--line);padding-bottom:8px}
  h3{margin:18px 0 8px;font-size:16px}
  p{margin:6px 0 10px}
  a{color:#0f5f91}
  .meta{display:grid;grid-template-columns:repeat(4,minmax(180px,1fr));gap:10px;margin-top:14px}
  .meta div,.callout,section{background:var(--panel);border:1px solid var(--line);border-radius:8px}
  .meta div{padding:10px 12px;min-height:62px}
  .label{display:block;color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.04em;margin-bottom:4px}
  section{padding:16px;margin:14px 0}
  .grid-2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
  .grid-3{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
  .callout{border-left:5px solid var(--blue);padding:14px 16px;margin:14px 0;background:#f9fbfc}
  .tag{display:inline-block;padding:3px 7px;border-radius:999px;border:1px solid var(--line);background:#fff;font-size:12px;color:#33414d;margin:2px 3px 2px 0;white-space:nowrap}
  .evidence{border-color:#8bc5aa;color:#0f6842}
  .assumption{border-color:#e4c36a;color:#805d00}
  .hypothesis{border-color:#9fc3df;color:#164f78}
  .needs-test{border-color:#e5a19b;color:#8a2018}
  .table-wrap{overflow-x:auto;border:1px solid var(--line);border-radius:8px;background:#fff}
  table{width:100%;border-collapse:collapse;min-width:860px;font-size:13px}
  th,td{border-bottom:1px solid var(--line);border-right:1px solid var(--line);padding:8px 9px;text-align:left;vertical-align:top}
  th{background:#edf1f4;font-weight:700;position:sticky;top:0;z-index:1}
  tr:last-child td{border-bottom:0}
  td:last-child,th:last-child{border-right:0}
  .num{text-align:right;white-space:nowrap}
  .hm{text-align:center;color:var(--neutral-ink);font-weight:700;min-width:46px}
  .hm-high{background:var(--high);color:var(--high-ink)}
  .hm-test{background:var(--test);color:var(--test-ink)}
  .hm-small{background:var(--small);color:var(--small-ink)}
  .hm-avoid{background:var(--avoid);color:var(--avoid-ink)}
  .hm-none{background:var(--neutral);color:var(--neutral-ink)}
  .legend{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0 12px}
  .swatch{display:inline-flex;align-items:center;gap:6px;padding:5px 8px;border:1px solid var(--line);border-radius:999px;background:#fff;font-size:12px}
  .box{width:14px;height:14px;border-radius:3px;display:inline-block}
  .kpi{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:10px 0 4px}
  .kpi div{border:1px solid var(--line);border-radius:8px;padding:12px;background:#fff}
  .kpi strong{display:block;font-size:22px;margin-top:4px}
  .decision-list{display:grid;grid-template-columns:repeat(2,minmax(260px,1fr));gap:10px;margin-top:10px}
  .decision-list div{border:1px solid var(--line);border-radius:8px;padding:10px 12px;background:#fbfcfd}
  footer{max-width:1480px;margin:0 auto;padding:18px 24px 40px;color:var(--muted);font-size:12px}
  @media(max-width:900px){.meta,.grid-2,.grid-3,.kpi,.decision-list{grid-template-columns:1fr}header{padding:22px 18px 16px}main{padding:14px}h1{font-size:24px}}
  @media print{body{background:#fff}section,.meta div,.callout{break-inside:avoid}a{color:#000;text-decoration:underline}.table-wrap{overflow:visible}table{font-size:11px}}
"""


# ── Section renderers ─────────────────────────────────────────────────────────

def s_header(cfg: dict) -> str:
    meta_fields = [
        ("Product", esc(cfg.get("product", "—"))),
        ("Market", esc(cfg.get("market", "—"))),
        ("Pilot Budget", esc(cfg.get("budget", "—"))),
        ("Margin Assumption", esc(cfg.get("margin_assumption", "—"))),
    ]
    meta = "".join(
        f'<div><span class="label">{k}</span>{v}</div>' for k, v in meta_fields
    )
    subtitle = esc(cfg.get("subtitle", "Channel allocation, D-dimension heatmap, Treatment Cards, measurement plan."))
    return f"""<header>
  <h1>{esc(cfg.get("product",""))} {esc(cfg.get("market",""))} Campaign Report</h1>
  <p>{subtitle}</p>
  <div class="meta">{meta}</div>
</header>"""


def s_core_decision(cfg: dict) -> str:
    cd = cfg.get("core_decision", {})
    rec = esc(cd.get("recommendation", ""))
    tag_lines = "".join(
        f'<p>{tag(t["cls"])} {esc(t["text"])}</p>'
        for t in cd.get("tags", [])
    )
    kpis = cd.get("kpis", [])
    kpi_html = "".join(
        f'<div><span class="label">{esc(k["label"])}</span><strong>{esc(k["value"])}</strong></div>'
        for k in kpis
    )
    return f"""<section>
  <h2>1. Core Decision</h2>
  <div class="callout">
    <p><strong>Recommendation:</strong> {rec}</p>
    {tag_lines}
  </div>
  <div class="kpi">{kpi_html}</div>
</section>"""


def s_evidence_legend() -> str:
    return f"""<section>
  <h2>2. Evidence Tags</h2>
  <p>
    {tag("evidence")} Sourced fact, validated experiment, or script output.&nbsp;
    {tag("assumption")} Scenario input or user-supplied estimate.&nbsp;
    {tag("hypothesis")} Semantic prior or unvalidated HTE inference.&nbsp;
    {tag("needs-test")} Judgment that will change budget, channel, or KOL decisions.
  </p>
  <p>All currency figures, CAC, ROI, and KOL prices must carry a tag. No untagged numbers in this report.</p>
</section>"""


def s_product_facts(cfg: dict) -> str:
    rows = "".join(
        f"""<tr>
          <td>{esc(f["fact"])}</td>
          <td>{tag(f.get("status","hypothesis"))}</td>
          <td>{esc(f.get("use",""))}</td>
          <td><a href="{esc(f.get("source_url","#"))}">{esc(f.get("source_label","—"))}</a></td>
        </tr>"""
        for f in cfg.get("product_facts", [])
    )
    return f"""<section>
  <h2>3. Product &amp; Market Facts</h2>
  <div class="table-wrap"><table>
    <thead><tr><th>Fact</th><th>Status</th><th>Use in plan</th><th>Source</th></tr></thead>
    <tbody>{rows}</tbody>
  </table></div>
</section>"""


def s_assumptions(cfg: dict) -> str:
    rows = "".join(
        f"""<tr>
          <td>{esc(a["assumption"])}</td>
          <td class="num">{esc(a["value"])}</td>
          <td>{esc(a.get("impact",""))}</td>
          <td>{esc(a.get("validation",""))}</td>
        </tr>"""
        for a in cfg.get("assumptions", [])
    )
    return f"""<section>
  <h2>4. Assumption Register</h2>
  <div class="table-wrap"><table>
    <thead><tr><th>Assumption</th><th>Value</th><th>Impact</th><th>Validation action</th></tr></thead>
    <tbody>{rows}</tbody>
  </table></div>
</section>"""


def s_channel_map(cfg: dict) -> str:
    rows = "".join(
        f"""<tr>
          <td>{esc(c["name"])}</td>
          <td>{esc(c.get("proxy",""))}</td>
          <td>{esc(c.get("match_quality",""))}</td>
          <td>{esc(c.get("task",""))}</td>
          <td>{esc(c.get("risk",""))}</td>
        </tr>"""
        for c in cfg.get("channels", [])
    )
    return f"""<section>
  <h2>5. Local Channel Map</h2>
  <div class="table-wrap"><table>
    <thead><tr><th>Channel</th><th>Local audience proxy</th><th>Match quality</th><th>Primary task</th><th>Risk</th></tr></thead>
    <tbody>{rows}</tbody>
  </table></div>
</section>"""


def s_dimensions(cfg: dict) -> str:
    dims = cfg.get("dimensions", [])
    dim_rows = "".join(
        f"""<tr>
          <td>{esc(d["id"])}</td>
          <td>{esc(d["name"])}</td>
          <td>{esc(d.get("logic",""))}</td>
          <td>{esc(d.get("proxy",""))}</td>
          <td>{tag(d.get("status","hypothesis"))}</td>
        </tr>"""
        for d in dims
    )
    # Causal Activation Reviewer challenges
    challenges = cfg.get("reviewer_challenges", [])
    rev_rows = "".join(
        f"""<tr>
          <td>{esc(r["item"])}</td>
          <td>{esc(r["question"])}</td>
          <td>{esc(r["handling"])}</td>
          <td>{esc(r["next_evidence"])}</td>
        </tr>"""
        for r in challenges
    )
    rev_section = ""
    if challenges:
        rev_section = f"""
  <div class="callout">
    <h3>Causal Activation Reviewer</h3>
    <p><strong>Role:</strong> Challenges every D dimension and heatmap cell. Checks
    that each dimension is pre-deployment observable, has a platform proxy, is
    mechanistically linked to the product, can have its incremental effect tested,
    and does not carry compliance or sure-thing risk. Verdicts: Retain / Retain (test) /
    Demote S / Suppression only / Delete. See ref 14 for full protocol.</p>
    <div class="table-wrap"><table>
      <thead><tr><th>Challenged dimension</th><th>Challenge raised</th><th>Current handling</th><th>Next evidence</th></tr></thead>
      <tbody>{rev_rows}</tbody>
    </table></div>
    <p><strong>Reviewer conclusion:</strong> D dimensions are candidate operational
    variables, serving trial design and evidence collection. Before entering primary
    budget, each must pass: deployable proxy, testable incrementality, stated mechanism,
    no obvious compliance or margin risk.</p>
  </div>"""

    return f"""<section>
  <h2>6. D Dimensions &amp; Causal Activation Reviewer</h2>
  <div class="callout">
    <h3>How D dimensions are generated</h3>
    <p><strong>Generation logic:</strong> D columns come from
    "product mechanism × local purchase path × platform proxy × measurability."
    Features that could change incremental purchase response are identified,
    then mapped to locally reachable platform signals. Dimensions that lack a
    deployable proxy, cannot be measured, or create compliance risk are excluded.</p>
    <p><strong>Entry threshold:</strong> ≥ 3 of 5 conditions must be satisfied:
    pre-deployment observable, platform proxy exists, mechanism stated,
    incrementality testable, drives a creative/bid/suppression decision.</p>
  </div>
  <div class="table-wrap"><table>
    <thead><tr><th>D</th><th>Dimension</th><th>Mechanism</th><th>Local proxy</th><th>Status</th></tr></thead>
    <tbody>{dim_rows}</tbody>
  </table></div>
  {rev_section}
</section>"""


def s_heatmap(cfg: dict) -> str:
    dims = cfg.get("dimensions", [])
    heatmap = cfg.get("heatmap", {})
    channels = [c["name"] for c in cfg.get("channels", [])]
    if not dims or not heatmap:
        return ""
    dim_ids = [d["id"] for d in dims]
    dim_names = [d["name"] for d in dims]

    header_cells = "".join(f"<th>{esc(n)}</th>" for n in dim_names)
    body_rows = ""
    for ch in channels:
        row_data = heatmap.get(ch, {})
        cells = "".join(hm(row_data.get(did, "N")) for did in dim_ids)
        body_rows += f"<tr><td>{esc(ch)}</td>{cells}</tr>\n"

    legend = """
  <div class="legend">
    <span class="swatch"><span class="box" style="background:var(--high)"></span>H main</span>
    <span class="swatch"><span class="box" style="background:var(--test)"></span>T test</span>
    <span class="swatch"><span class="box" style="background:var(--small)"></span>S small</span>
    <span class="swatch"><span class="box" style="background:var(--neutral)"></span>N no focus</span>
    <span class="swatch"><span class="box" style="background:var(--avoid)"></span>A avoid/suppress</span>
  </div>"""

    return f"""<section>
  <h2>7. Semantic Dimension Heatmap</h2>
  <p>Rows: channels. Columns: D dimensions.
  H = primary investment · T = test slot · S = small test · N = not this round · A = actively suppress.</p>
  {legend}
  <div class="table-wrap"><table>
    <thead><tr><th>Channel</th>{header_cells}</tr></thead>
    <tbody>{body_rows}</tbody>
  </table></div>
</section>"""


def s_treatments(cfg: dict, power_note: str = "") -> str:
    # Execution gates
    gates = cfg.get("execution_gates", [])
    gate_rows = "".join(
        f"""<tr>
          <td>{esc(g["gate"])}</td>
          <td>{tag(g.get("status_cls","hypothesis"))} {esc(g.get("status",""))}</td>
          <td>{esc(g.get("can_do",""))}</td>
          <td>{esc(g.get("cannot_do",""))}</td>
          <td>{esc(g.get("next",""))}</td>
        </tr>"""
        for g in gates
    )
    power_block = ""
    if power_note:
        power_block = f'<div class="callout"><p>{power_note}</p></div>'

    # Treatment cards
    treatments = cfg.get("treatments", [])
    t_rows = "".join(
        f"""<tr>
          <td>{esc(t["id"])}</td>
          <td>{esc(t["action"])}</td>
          <td>{esc(t.get("audience",""))}</td>
          <td>{esc(t.get("baseline",""))}</td>
          <td>{esc(t.get("cost_formula",""))}</td>
          <td>{esc(t.get("mechanism",""))}</td>
          <td>{esc(t.get("guardrail",""))}</td>
          <td>{esc(t.get("measurement",""))}</td>
        </tr>"""
        for t in treatments
    )

    log_note = """<p>To upgrade from trial to OPE or policy learning, log:
    eligible_treatment_set, treatment_id, creative_id, assignment_probability,
    holdout_flag, cost, gross_margin, negative_feedback, policy_version, frequency_state.</p>"""

    return f"""<section>
  <h2>9. Execution Gates &amp; Treatment Cards</h2>
  <div class="callout">
    <p><strong>Maturity:</strong> Current analysis is at L0 hypothesis → early L1 experiment foundation.
    Use for trial design and channel prioritization.
    Do not treat semantic heatmap scores or platform proxies as CATE facts or scale-ready conclusions.</p>
    <p><strong>Scale gate:</strong> Each primary action requires a holdout or credible baseline,
    treatment-level cost, impression/click/conversion log, margin metric, and negative-feedback indicator
    before budget is increased.</p>
  </div>
  {power_block}
  <div class="table-wrap"><table>
    <thead><tr><th>Gate</th><th>Status</th><th>Can do now</th><th>Cannot do</th><th>Next step</th></tr></thead>
    <tbody>{gate_rows}</tbody>
  </table></div>
  <h3>Treatment Cards</h3>
  <div class="table-wrap"><table>
    <thead><tr><th>ID</th><th>Action</th><th>Audience / proxy</th><th>Baseline</th><th>Cost formula</th><th>Mechanism</th><th>Guardrail</th><th>Measurement</th></tr></thead>
    <tbody>{t_rows}</tbody>
  </table></div>
  {log_note}
</section>"""


def s_budget(cfg: dict) -> str:
    rows = "".join(
        f"""<tr>
          <td>{esc(b["module"])}</td>
          <td class="num">{esc(b["budget"])}</td>
          <td class="num">{esc(b["pct"])}</td>
          <td>{esc(b.get("rationale",""))}</td>
          <td>{tag(b.get("status_cls","hypothesis"))} {esc(b.get("status",""))}</td>
        </tr>"""
        for b in cfg.get("budget_allocation", [])
    )
    return f"""<section>
  <h2>10. Budget Allocation</h2>
  <div class="table-wrap"><table>
    <thead><tr><th>Module</th><th>Budget</th><th>Share</th><th>Rationale</th><th>Status</th></tr></thead>
    <tbody>{rows}</tbody>
  </table></div>
</section>"""


def s_plays(cfg: dict) -> str:
    rows = "".join(
        f"""<tr>
          <td>{esc(p["id"])}</td>
          <td>{esc(p.get("audience",""))}</td>
          <td>{esc(p.get("channel",""))}</td>
          <td class="num">{tag("assumption")} {esc(p.get("budget",""))}</td>
          <td class="num">{tag("hypothesis")} {esc(p.get("est_cac",""))}</td>
          <td class="num">{tag("hypothesis")} {esc(p.get("est_units",""))}</td>
          <td class="num">{tag(p.get("status_cls","hypothesis"))} {esc(p.get("roi_range",""))}</td>
          <td>{tag(p.get("status_cls","hypothesis"))}</td>
        </tr>"""
        for p in cfg.get("plays", [])
    )
    return f"""<section>
  <h2>11. Priority Plays &amp; ROI Scenarios</h2>
  <p>All CAC, unit, and ROI figures are planning hypotheses until validated by holdout or credible baseline.</p>
  <div class="table-wrap"><table>
    <thead><tr><th>Play</th><th>Audience</th><th>Channel</th><th>Budget</th><th>Est. CAC</th><th>Est. Units</th><th>Net ROI range</th><th>Status</th></tr></thead>
    <tbody>{rows}</tbody>
  </table></div>
</section>"""


def s_kols(cfg: dict) -> str:
    kols = cfg.get("kols", [])
    if not kols:
        return ""
    rows = "".join(
        f"""<tr>
          <td>{esc(k.get("type",""))}</td>
          <td>{esc(k.get("candidate",""))}</td>
          <td>{esc(k.get("signal",""))}</td>
          <td class="num">{tag("needs-test")} {esc(k.get("est_fee",""))}</td>
          <td>{esc(k.get("fee_rationale",""))}</td>
          <td>{esc(k.get("use",""))}</td>
          <td>{esc(k.get("validation",""))}</td>
        </tr>"""
        for k in kols
    )
    return f"""<section>
  <h2>12. KOL / Creator Sourcing</h2>
  <p>{tag("needs-test")} All fees are planning estimates. Obtain direct quote + usage rights before commitment.
  KOL incremental ROI is {tag("hypothesis")} until a matched holdout or UTM-based incrementality test is run.</p>
  <div class="table-wrap"><table>
    <thead><tr><th>Type</th><th>Candidate</th><th>Public signal</th><th>Est. fee</th><th>Fee basis</th><th>Use</th><th>Validation action</th></tr></thead>
    <tbody>{rows}</tbody>
  </table></div>
</section>"""


def s_measurement(cfg: dict, power_duration: str = "") -> str:
    mp = cfg.get("measurement_plan", {})
    dur_note = f"<p>{power_duration}</p>" if power_duration else ""
    return f"""<section>
  <h2>13. Measurement Plan</h2>
  <div class="grid-3">
    <div>
      <h3>Creative A/B</h3>
      <p>{tag("needs-test")} {esc(mp.get("creative_ab","TBD"))}</p>
    </div>
    <div>
      <h3>Incentive Test</h3>
      <p>{tag("needs-test")} {esc(mp.get("incentive_test","TBD"))}</p>
    </div>
    <div>
      <h3>KOL Incrementality</h3>
      <p>{tag("needs-test")} {esc(mp.get("kol_incrementality","TBD"))}</p>
    </div>
  </div>
  {dur_note}
  <p><strong>Scale rule:</strong> {esc(mp.get("scale_rule","Add budget when incremental CAC is below target and guardrails are stable."))}</p>
  <p><strong>Pause rule:</strong> {esc(mp.get("pause_rule","Pause scale when CAC exceeds ceiling and no long-term value evidence exists."))}</p>
</section>"""


def s_suppression(cfg: dict) -> str:
    rows = "".join(
        f"""<tr>
          <td>{esc(r.get("group",""))}</td>
          <td>{esc(r.get("reason",""))}</td>
          <td>{esc(r.get("action",""))}</td>
          <td>{tag(r.get("status_cls","hypothesis"))}</td>
        </tr>"""
        for r in cfg.get("suppression_rules", [])
    )
    return f"""<section>
  <h2>14. Suppression &amp; Risk Rules</h2>
  <div class="table-wrap"><table>
    <thead><tr><th>Risk group</th><th>Reason</th><th>Action</th><th>Status</th></tr></thead>
    <tbody>{rows}</tbody>
  </table></div>
</section>"""


def s_sources(cfg: dict) -> str:
    items = "".join(
        f'<li><a href="{esc(s.get("url","#"))}">{esc(s.get("label","—"))}</a></li>'
        for s in cfg.get("sources", [])
    )
    return f"""<section>
  <h2>15a. Sources</h2>
  <ol>{items}</ol>
</section>"""


def s_checklist(cfg: dict) -> str:
    rows = "".join(
        f"""<tr>
          <td>{esc(c["item"])}</td>
          <td>{tag(c.get("status_cls","needs-test"))} {esc(c.get("status",""))}</td>
          <td>{esc(c.get("next",""))}</td>
        </tr>"""
        for c in cfg.get("checklist", [])
    )
    return f"""<section>
  <h2>15b. Verification Checklist</h2>
  <div class="table-wrap"><table>
    <thead><tr><th>Check</th><th>Status</th><th>Next step</th></tr></thead>
    <tbody>{rows}</tbody>
  </table></div>
</section>"""


# ── Script bridge ─────────────────────────────────────────────────────────────

def run_power_bridge(cfg: dict) -> tuple[str, str]:
    """Returns (power_note for s_treatments, duration_note for s_measurement)."""
    pa = cfg.get("power_analysis", {})
    if not pa:
        return "", ""

    n_ate_fn, n_hte_fn, dur_fn = _import_power()
    if not n_ate_fn:
        return (
            '<span class="tag needs-test">Script unavailable</span> '
            "Install scipy to enable power_analysis.py bridge.",
            ""
        )

    try:
        baseline = pa.get("baseline_cvr", 0.02)
        mde = pa.get("mde_abs", 0.004)
        epd = pa.get("eligible_per_day", 10000)
        n_ab = n_ate_fn(baseline, mde)
        n_hte = n_hte_fn(baseline, baseline, mde * 2, mde)
        days = dur_fn(4 * n_hte, epd)
        power_note = (
            f'<span class="tag evidence">power_analysis.py</span> '
            f"Baseline CVR {baseline:.1%}, MDE {mde:.2%} → "
            f"ATE: <strong>{n_ab:,}/arm</strong> · "
            f"HTE: <strong>{n_hte:,}/cell ({4*n_hte:,} total)</strong> · "
            f"HTE/ATE multiplier ≈ {4*n_hte/(2*n_ab):.1f}×"
        )
        dur_note = (
            f'<span class="tag evidence">power_analysis.py</span> '
            f"At {epd:,} eligible users/day → HTE experiment needs ~<strong>{days} days</strong>. "
            f"Reduce dimensions or increase traffic if this exceeds the campaign window."
        )
        return power_note, dur_note
    except Exception as e:
        return f'<span class="tag needs-test">Script error</span> {esc(str(e))}', ""


# ── Main assembler ────────────────────────────────────────────────────────────

def generate_html(cfg: dict) -> str:
    power_note, dur_note = run_power_bridge(cfg)
    report_date = cfg.get("report_date", str(date.today()))

    sections = "\n".join([
        s_core_decision(cfg),
        s_evidence_legend(),
        s_product_facts(cfg),
        s_assumptions(cfg),
        s_channel_map(cfg),
        s_dimensions(cfg),
        s_heatmap(cfg),
        "<section><h2>8. H-Main Breakdown</h2>"
        "<p>Each H cell from the heatmap should have a corresponding Treatment Card row in section 9. "
        "See the Treatment Cards table for per-channel, per-dimension breakdown of direction, "
        "audience proxy, mechanism, and measurement approach.</p></section>",
        s_treatments(cfg, power_note),
        s_budget(cfg),
        s_plays(cfg),
        s_kols(cfg),
        s_measurement(cfg, dur_note),
        s_suppression(cfg),
        s_sources(cfg),
        s_checklist(cfg),
    ])

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(cfg.get("product",""))} {esc(cfg.get("market",""))} Campaign Report</title>
  <style>{_CSS}</style>
</head>
<body>
{s_header(cfg)}
<main>{sections}</main>
<footer>
  Scientific Marketing HTML report · Generated {report_date} ·
  All ROI and CAC figures are planning hypotheses until validated by holdout or credible baseline. ·
  <a href="https://github.com/alexwang91/scientific-marketing-personalized-attribution-hte">skill reference</a>
</footer>
</body>
</html>"""


# ── Demo config ───────────────────────────────────────────────────────────────

DEMO_CONFIG: dict[str, Any] = {
    "product": "ProductX Smart Wearable",
    "market": "Target Market",
    "subtitle": "Channel allocation, D-dimension heatmap, Treatment Cards, measurement plan.",
    "budget": "1,000,000 USD",
    "margin_assumption": "40% gross margin",
    "price": 299,
    "margin_rate": 0.40,
    "report_date": str(date.today()),

    "core_decision": {
        "recommendation": (
            "Run 4-week pilot. Search/Retail captures purchase intent; "
            "Creator/KOL builds third-party proof; Retargeting tops up at low frequency. "
            "Scale only when incremental CAC < $90 and holdout confirms positive incremental margin."
        ),
        "tags": [
            {"cls": "assumption", "text": "Price $299 and 40% margin are user inputs; not confirmed by finance."},
            {"cls": "needs-test", "text": "Incremental CAC and ROI range are planning hypotheses. Holdout required before scale decision."},
        ],
        "kpis": [
            {"label": "Target CAC", "value": "<$90"},
            {"label": "Unit Margin", "value": "$120"},
            {"label": "Primary Channels", "value": "4"},
            {"label": "Holdout Reserve", "value": "5%"},
        ],
    },

    "product_facts": [
        {"fact": "ProductX listed at $299 MSRP on official site.", "status": "evidence", "use": "Baseline price and margin.", "source_label": "Official site", "source_url": "#"},
        {"fact": "Key features: GPS, 10-day battery, 1.9\" AMOLED, health monitoring.", "status": "evidence", "use": "Creative direction and D dimension mapping.", "source_label": "Product page", "source_url": "#"},
        {"fact": "Available on top 3 local e-commerce platforms.", "status": "evidence", "use": "Retail media prioritization.", "source_label": "Market guide", "source_url": "#"},
    ],

    "assumptions": [
        {"assumption": "Pilot budget", "value": "1,000,000 USD", "impact": "Channel allocation and minimum sample.", "validation": "Replace with approved budget."},
        {"assumption": "Gross margin", "value": "40%", "impact": "CAC ceiling and ROI.", "validation": "Finance confirmation required."},
        {"assumption": "KOL fee range", "value": "$2,000–$15,000", "impact": "ROI scenario modeling.", "validation": "Obtain direct quotes."},
        {"assumption": "Incrementality fraction", "value": "40–65% of tracked sales", "impact": "Prevents platform attribution overcount.", "validation": "Holdout or platform lift test."},
    ],

    "channels": [
        {"name": "Search (Brand + Category)", "proxy": "brand keywords, category queries, competitor alternatives", "match_quality": "High — especially high-intent", "task": "Capture demand", "risk": "Sure-thing cannibalization on brand terms"},
        {"name": "Shopping / PMax", "proxy": "product feed, category shoppers, price-compare visitors", "match_quality": "High–Medium", "task": "Convert comparison shoppers", "risk": "Weak incrementality visibility"},
        {"name": "Retail Media", "proxy": "category visitors, brand searchers, cart abandoners", "match_quality": "High — close to purchase", "task": "Last-mile conversion", "risk": "Placement terms need direct negotiation"},
        {"name": "Social Prospecting", "proxy": "fitness, health, tech-gadget, lifestyle interests", "match_quality": "Medium", "task": "Expand audience, test framing", "risk": "Broad interests dilute audience quality"},
        {"name": "YouTube Review", "proxy": "product review viewers, comparison searchers", "match_quality": "Medium", "task": "Build third-party proof", "risk": "Creator fit and cost volatility"},
        {"name": "KOL / Creator", "proxy": "fitness, outdoor, lifestyle creator audiences", "match_quality": "Medium", "task": "Authentic use-case demonstration", "risk": "Audience location and incremental effect unverified"},
        {"name": "Retargeting", "proxy": "product page visitors, cart abandoners, video viewers", "match_quality": "High relevance", "task": "Low-frequency proof top-up", "risk": "Ad fatigue and sleeping-dog risk"},
    ],

    "dimensions": [
        {"id": "D1", "name": "Brand in-market", "logic": "Brand preference reduces purchase friction.", "proxy": "Brand keyword searches, category site visitors", "status": "hypothesis"},
        {"id": "D2", "name": "Smartwatch in-market", "logic": "Category purchase intent — already in decision mode.", "proxy": "Smartwatch searches, feed category visitors", "status": "hypothesis"},
        {"id": "D3", "name": "Running / Fitness", "logic": "GPS and lightweight design directly addresses running use case.", "proxy": "Running interest, fitness creator audiences", "status": "hypothesis"},
        {"id": "D4", "name": "Health / Sleep", "logic": "Health monitoring is a daily-wear motivation.", "proxy": "Health, sleep, wellness content interests", "status": "hypothesis"},
        {"id": "D5", "name": "Battery pain", "logic": "10-day battery is a provable differentiator.", "proxy": "Long battery queries, comparison content viewers", "status": "hypothesis"},
        {"id": "D6", "name": "Price compare", "logic": "$299 is comparable; value proof can reduce hesitation.", "proxy": "Price-compare searches, shopping filter users", "status": "needs-test"},
        {"id": "D7", "name": "Competitor alternative", "logic": "Users comparing alternatives; battery/price angles viable.", "proxy": "Competitor alternative searches, review viewers", "status": "needs-test"},
        {"id": "D8", "name": "Cart abandon", "logic": "Close to purchase; blocked by price, shipping, or trust.", "proxy": "Cart abandoners, product page return visitors", "status": "hypothesis"},
        {"id": "D9", "name": "Tech review reader", "logic": "Research behavior signals risk-reduction need.", "proxy": "Tech review viewers, product review searches", "status": "hypothesis"},
        {"id": "D10", "name": "Ad fatigue", "logic": "High frequency may generate negative incremental effect.", "proxy": "High frequency, hide/report signals", "status": "needs-test"},
    ],

    "heatmap": {
        "Search (Brand + Category)":   {"D1":"H","D2":"H","D3":"T","D4":"T","D5":"H","D6":"H","D7":"T","D8":"N","D9":"T","D10":"N"},
        "Shopping / PMax":             {"D1":"H","D2":"H","D3":"T","D4":"T","D5":"H","D6":"H","D7":"T","D8":"T","D9":"S","D10":"N"},
        "Retail Media":                {"D1":"H","D2":"H","D3":"T","D4":"T","D5":"T","D6":"H","D7":"T","D8":"H","D9":"S","D10":"S"},
        "Social Prospecting":          {"D1":"T","D2":"T","D3":"T","D4":"H","D5":"T","D6":"S","D7":"S","D8":"T","D9":"S","D10":"S"},
        "YouTube Review":              {"D1":"T","D2":"H","D3":"T","D4":"H","D5":"H","D6":"T","D7":"H","D8":"N","D9":"H","D10":"N"},
        "KOL / Creator":               {"D1":"T","D2":"T","D3":"H","D4":"H","D5":"T","D6":"S","D7":"T","D8":"N","D9":"S","D10":"N"},
        "Retargeting":                 {"D1":"H","D2":"H","D3":"T","D4":"T","D5":"H","D6":"T","D7":"T","D8":"H","D9":"T","D10":"A"},
    },

    "reviewer_challenges": [
        {"item": "D6 Price compare", "question": "Price-seekers may buy anyway; platform ROAS will overcount. Positive incremental margin?", "handling": "Keep in test with incremental margin guardrail; not primary budget.", "next_evidence": "Discount vs proof vs no-contact holdout comparison."},
        {"item": "D1 Brand search", "question": "Brand searchers are likely sure-things; paid capture may cannibalize organic.", "handling": "Primary investment but low-intensity holdout required.", "next_evidence": "Brand keyword holdout or region/time-split low-bid control."},
        {"item": "D10 Ad fatigue", "question": "Retargeting can harm high-intent users. Sleeping-dog risk documented.", "handling": "Suppression dimension only; frequency cap and cooldown enforced.", "next_evidence": "Frequency, hide/report, no-contact arm comparison."},
    ],

    "treatments": [
        {"id":"T01","action":"Search brand + category capture","audience":"Brand searchers, smartwatch in-market queries","baseline":"Low bid or holdout","cost_formula":"CPC + landing cost","mechanism":"Reduce search-to-purchase friction.","guardrail":"Brand-term sure-thing cannibalization.","measurement":"Brand keyword holdout; incremental CAC by query type."},
        {"id":"T02","action":"Shopping / PMax value proof","audience":"Category feed visitors, price-compare signals","baseline":"Generic feed or no campaign","cost_formula":"CPC/CPA + feed ops","mechanism":"Price, battery, rating, stock proof reduces decision cost.","guardrail":"PMax automation hides low-incrementality traffic.","measurement":"Split brand/category/competitor; track new customer rate and margin."},
        {"id":"T03","action":"Retail sponsored placement","audience":"Retail category visitors, brand searchers","baseline":"Organic retail ranking","cost_formula":"Retail media fee + placement cost","mechanism":"Stock, warranty, reviews trust at point of purchase.","guardrail":"Discount-driven low-margin cohort.","measurement":"Retailer report by category visitor, new vs returning, cart abandon."},
        {"id":"T04","action":"YouTube / tech review proof","audience":"Smartwatch review viewers, comparison searchers","baseline":"Brand video only or no review","cost_formula":"Creator fee + production + usage rights + amplification","mechanism":"Third-party explanation of battery, feature boundary, competitor gap.","guardrail":"Health/competitor claims; view-without-conversion waste.","measurement":"UTM, view quality, search lift, retargeting holdout."},
        {"id":"T05","action":"KOL fitness / lifestyle content","audience":"Running, health-habit, lifestyle creator followers","baseline":"No creator content","cost_formula":"Creator fee + usage rights + paid amplification","mechanism":"Real use-case proof: lightweight wear, GPS tracking, sleep/health.","guardrail":"Audience location mismatch; engagement-only without purchase.","measurement":"Audience country screenshot, UTM, paid amplification holdout."},
        {"id":"T06","action":"Retargeting low-frequency proof","audience":"Product page visitors, cart abandoners, video viewers","baseline":"No-contact holdout","cost_formula":"CPM/CPC + frequency cap overhead","mechanism":"Supplement price, stock, warranty, battery proof.","guardrail":"Ad fatigue, sleeping-dog, sure-thing.","measurement":"Proof creative vs light incentive vs no-contact; negative feedback + incremental margin."},
    ],

    "execution_gates": [
        {"gate":"Maturity","status":"L0 / early L1","status_cls":"hypothesis","can_do":"Design pilot and validation plan.","cannot_do":"Declare any segment has a true CATE.","next":"Build holdout for brand, retail, and retargeting."},
        {"gate":"Attribution & incrementality","status":"Needs test","status_cls":"needs-test","can_do":"Use platform reports for operational feedback.","cannot_do":"Use platform ROAS as causal incrementality proof.","next":"Establish no-contact control per channel."},
        {"gate":"Sample size","status":"Run script","status_cls":"needs-test","can_do":"Start with coarse dimensions: channel × primary message.","cannot_do":"Treat all D dimensions as separately estimable HTEs.","next":"Pull eligible users, daily traffic, baseline CVR → power_analysis.py."},
        {"gate":"Propensity log","status":"Missing","status_cls":"needs-test","can_do":"Record manual allocation rules and budget weights.","cannot_do":"Run OPE or policy learning.","next":"Log: eligible_treatment_set, assignment_probability, policy_version."},
    ],

    "power_analysis": {
        "baseline_cvr": 0.02,
        "mde_abs": 0.004,
        "eligible_per_day": 10000,
    },

    "budget_allocation": [
        {"module":"Retail Media","budget":"200,000","pct":"20.0%","rationale":"Closest to purchase; highest intent.","status":"Needs quote","status_cls":"needs-test"},
        {"module":"Search / Shopping / PMax","budget":"225,000","pct":"22.5%","rationale":"Capture brand, category, and battery-pain queries.","status":"Needs keyword data","status_cls":"needs-test"},
        {"module":"KOL / Creator","budget":"200,000","pct":"20.0%","rationale":"Build proof and reusable creative assets.","status":"Hypothesis","status_cls":"hypothesis"},
        {"module":"Social Prospecting","budget":"150,000","pct":"15.0%","rationale":"Test fitness, design, health, and daily-wear framing.","status":"Hypothesis","status_cls":"hypothesis"},
        {"module":"Retargeting","budget":"100,000","pct":"10.0%","rationale":"Low-frequency proof for product-page visitors and cart abandoners.","status":"Needs holdout","status_cls":"needs-test"},
        {"module":"YouTube / Review","budget":"75,000","pct":"7.5%","rationale":"Support comparison and proof mission.","status":"Hypothesis","status_cls":"hypothesis"},
        {"module":"Measurement / Holdout","budget":"50,000","pct":"5.0%","rationale":"Prevent platform ROAS from substituting for incrementality.","status":"Evidence","status_cls":"evidence"},
    ],

    "plays": [
        {"id":"P1","audience":"Brand + smartwatch in-market","channel":"Search + Retail","budget":"185,000","est_cac":"$65–$95","est_units":"1,950–2,840","roi_range":"0.37–1.23","status_cls":"hypothesis"},
        {"id":"P2","audience":"Fitness / running / outdoor","channel":"KOL + Social + YouTube","budget":"165,000","est_cac":"$90–$180","est_units":"920–1,830","roi_range":"-0.30–0.45","status_cls":"needs-test"},
        {"id":"P3","audience":"Battery pain + competitor comparison","channel":"Search + YouTube","budget":"100,000","est_cac":"$80–$150","est_units":"670–1,250","roi_range":"-0.10–0.60","status_cls":"needs-test"},
        {"id":"P4","audience":"Retail category visitors","channel":"Retail Media","budget":"130,000","est_cac":"$55–$85","est_units":"1,530–2,360","roi_range":"0.53–1.55","status_cls":"needs-test"},
        {"id":"P5","audience":"Cart abandoners / product page","channel":"Retargeting","budget":"100,000","est_cac":"$65–$110","est_units":"910–1,540","roi_range":"0.13–1.00","status_cls":"needs-test"},
    ],

    "measurement_plan": {
        "creative_ab": "Sport performance vs long battery/lightweight daily wear vs health/sleep proof.",
        "incentive_test": "No incentive vs light benefit vs price discount. Guardrail: incremental margin per eligible user.",
        "kol_incrementality": "Creator content + paid amplification; matched holdout where feasible.",
        "scale_rule": "Add budget when incremental CAC < $90 and guardrails stable.",
        "pause_rule": "Pause scale when CAC > $120 and no long-term value evidence.",
    },

    "suppression_rules": [
        {"group":"Competing ecosystem heavy users","reason":"Ecosystem habits create purchase barriers.","action":"Test only price/battery comparison; avoid ecosystem replacement claims.","status_cls":"hypothesis"},
        {"group":"Deal-only buyers","reason":"Negative incremental margin if discount > proof value.","action":"Exclude from primary budget; small isolated test only.","status_cls":"hypothesis"},
        {"group":"High-frequency retargeted","reason":"Ad fatigue and sleeping-dog risk.","action":"Frequency cap; cooldown window; proof-first creative.","status_cls":"needs-test"},
        {"group":"App-dependent users","reason":"Third-party app expectations may block purchase.","action":"Set explicit compatibility boundaries; do not over-promise.","status_cls":"evidence"},
    ],

    "sources": [
        {"label": "Official product page", "url": "#"},
        {"label": "Market e-commerce guide", "url": "#"},
        {"label": "Retail platform ranking", "url": "#"},
        {"label": "Scientific Marketing skill — GitHub", "url": "https://github.com/alexwang91/scientific-marketing-personalized-attribution-hte"},
    ],

    "checklist": [
        {"item":"Product price","status":"Evidence","status_cls":"evidence","next":"Re-check before media launch."},
        {"item":"Gross margin","status":"Assumption","status_cls":"assumption","next":"Finance confirmation required."},
        {"item":"KOL fees","status":"Needs quote","status_cls":"needs-test","next":"Obtain direct rate + usage rights."},
        {"item":"Retail media availability","status":"Needs quote","status_cls":"needs-test","next":"Contact platforms for placement terms."},
        {"item":"Keyword volume + CPC","status":"Needs data pull","status_cls":"needs-test","next":"Pull keyword planner or DSP forecast."},
        {"item":"Incrementality","status":"Needs experiment","status_cls":"needs-test","next":"Set holdout for search, retail, retargeting, KOL."},
        {"item":"Maturity gate","status":"L0 / early L1","status_cls":"hypothesis","next":"Complete data gaps in execution gate section before OPE."},
        {"item":"Treatment Cards","status":"Method","status_cls":"evidence","next":"Write T01–T06 into campaign brief and logging spec."},
        {"item":"Propensity log","status":"Missing","status_cls":"needs-test","next":"Log: eligible_treatment_set, assignment_probability, policy_version."},
        {"item":"Compliance claims","status":"Needs review","status_cls":"needs-test","next":"Review health, payment, performance claims for local standards."},
    ],
}


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate a Scientific Marketing HTML report.")
    parser.add_argument("--demo", action="store_true", help="Run with built-in demo config")
    parser.add_argument("--config", help="Path to JSON config file")
    parser.add_argument("--output", help="Output HTML file (default: stdout)")
    args = parser.parse_args()

    if args.demo:
        cfg = DEMO_CONFIG
    elif args.config:
        with open(args.config) as f:
            cfg = json.load(f)
    else:
        parser.print_help()
        sys.exit(1)

    html = generate_html(cfg)

    if args.output:
        Path(args.output).write_text(html, encoding="utf-8")
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(html)


if __name__ == "__main__":
    main()
