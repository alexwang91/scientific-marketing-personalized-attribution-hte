# 12 · HTML Report Output Adapter

## Purpose

Specifies the canonical deliverable report format. The governing idea:

> **A good report is a document that lets someone who does not trust you
> check your reasoning.**

A report is a display of reasoning, not a display of conclusions. Credibility
comes from checkability, not from labels claiming credibility. Estimation
rules live in ref 16; this file covers structure and rendering.

This reference is the authoritative source on report shape, tag semantics,
provenance rendering, heatmap scoring, script bridges, and the acceptance
checklist. When to trigger: the user asks for a deliverable report, campaign
brief, trial plan, or formatted output after working through the pipeline.

---

## Report Structure: Part A + Part B

Every full report has two parts. The pipeline may emit only Part A when it
terminates early (short-report mode, see below).

### Part A — Decision Memo (first screen)

The reader sees this before scrolling. It contains exactly six elements:

1. **Verdict badge** — GO / NO-GO / CONDITIONAL (one of three; no hedged fourth option)
2. **Key math** — the central derivation that produced the verdict (unit margin → CAC ceiling)
3. **Viable channels** — which channels passed the screen and at what verdict level
4. **Top 2 actions** — the two highest-priority Treatment Cards, each ≤ 25 words
5. **Top challenge** — the single most consequential open or open-blocking challenge
6. **Next date** — the decision checkpoint when the go/no-go re-evaluation happens

The Decision Memo must stand alone. A reader who stops after the first screen
must leave with a correct (if coarse) picture — never a misleading one.

### Part B — Full Analysis (15 sections)

The 15 sections that follow the Decision Memo. See the section map below.

### Short-report mode

If the pipeline terminated at the viability screen (ref 13, Stage 3), the config
carries a `termination` block and the generator renders only:
- Part A (Decision Memo)
- Section 2 (The Math) — showing the ceiling and why nothing clears it
- Section 6 (Evidence & Gaps) — Missing ledger sorted by sensitivity
- A termination notice: what would change the verdict

**A short report is a success state, not a failure.** "The math says don't spend;
here are the levers that would change the math" is often the most valuable
deliverable. Do not pad a short report into a full one.

---

## Section Map (canonical sequence, as rendered by generate_report.py)

This map is the authoritative numbering and **matches the generator's output
exactly.** Section numbers are monotonic; the generator threads every heading
through `L(cfg, key, default)` so numbers and text localize together. If you
change the order here, change `generate_html()`'s `parts` list to match.

| # | Section | Renderer | Required | Script input |
|---|---------|----------|----------|--------------|
| 1 | Decision Memo (verdict band + body) | `s_memo` | Yes | — |
| 2 | The Math (CAC ceiling, sensitivity, channel screen) | `s_math` | Yes | — |
| 3 | Product & market facts | `s_product_facts` | Yes | — |
| 4 | Local channel map | `s_channel_map` | Yes | — |
| 5 | D dimension table + Causal Activation Reviewer | `s_dimensions` | Yes | — |
| 6 | Semantic heatmap (channel × dimension) | `s_heatmap` | Yes | — |
| 7 | H-main breakdown | `s_h_main` | Yes | — |
| 8 | Execution gates + Treatment Cards | `s_execution_gates` | Yes | `power_analysis.py` → sample-size gate |
| 9 | Causal Activation Reviewer (campaign-level challenges) | `s_challenges` | Yes | — |
| 10 | Budget allocation | `s_budget` | Yes | — |
| 11 | Priority plays + ROI scenarios | `s_priority_plays` | Yes | `qini_auuc.py` → AUUC gate (if model data) |
| 12 | KOL / Creator sourcing | `s_kol` | Conditional | — |
| 13 | Measurement plan | `s_measurement` | Yes | `power_analysis.py` → duration |
| 14 | Test plan (prediction / kill line / decision date) | `s_test_plan` | Yes | — |
| 15 | Suppression & risk rules | `s_suppression` | Yes | `ope_estimators.py` → support check |
| 16 | Evidence & gaps (sourced facts, assumption register, Missing ledger) | `s_evidence` | Yes | — |
| 17 | Sources + Verification checklist | `s_checklist` | Yes | — |

**H-main** (section 7) = the set of channel×dimension cells the heatmap scored
`H` (primary investment). Section 7 breaks each one down into its HTE hypothesis
and its Treatment Card pointer; the cards themselves render in section 8.

**Evidence tag legend** is not a standalone section — the marker legend renders
inside the Decision Memo (section 1), and the claim-tag semantics are documented
below in this reference, not in the report body.

### Why the order matters

The report is a pyramid: a reader gets the conclusion in 30 seconds (section 1),
the reasoning in 3 minutes (sections 2–6), and full auditability in 30 minutes
(sections 7–17). The single most important insight must be the first sentence
of the Decision Memo — not buried in a reviewer table on page 4.

### Short-report mode (early termination)

When `config["termination"]` is set (pipeline stopped at the viability screen,
ref 13 Stage 3), the generator renders only: section 1 (Memo) + the termination
notice + section 2 (The Math) + section 16 (Evidence & gaps, Missing ledger
sorted by sensitivity). No full analysis sections. A short report is a success
state — do not pad it.

---

## Evidence Tag Semantics (claim-level labels in report text)

Every claim in the report must carry exactly one tag. No untagged ROI, CAC, or
KOL price is allowed. These tags label the **epistemological status of a claim**:
is it a verified fact, a scenario input, an unvalidated inference, or a
judgment pending measurement?

| Tag | CSS class | Meaning |
|-----|-----------|---------|
| `Evidence` | `.evidence` | Sourced fact, stable method, or validated result |
| `Assumption` | `.assumption` | Scenario input or estimate provided by user |
| `Hypothesis` | `.hypothesis` | Semantic prior or unvalidated HTE inference |
| `Needs test` | `.needs-test` | A judgment that will change budget, CAC, or KOL decisions |

**Hard rule**: any number with a currency symbol or "%" that affects budget, CAC,
or ROI must be tagged. No exceptions.

**Hard rule**: KOL fees are never `Evidence` unless a direct quote has been received.
Default: `Assumption` or `Needs quote`.

**Hard rule**: ROI and incrementality are never `Evidence` without a holdout or
credible identification strategy. Default: `Hypothesis` or `Needs test`.

Evidence tags operate at the level of claims in rendered HTML. Number-level
provenance (see next section) operates at the level of individual values in the
config registry. These are **two levels of the same obligation**, not alternatives.

---

## Number-Level Provenance (registry states enforced by generate_report.py)

Every number lives in the config's central `numbers` registry with one of four
provenance states:

| State | Marker | Meaning |
|-------|--------|---------|
| `sourced` | ◆ | Obtained from a cited external source with URL + date |
| `assumed` | ◇ | User-supplied input or declared estimate with basis |
| `derived` | ⊕ | Computed from other registered values by a stated formula |
| `missing` | ○ | Not yet obtained; registry entry has `needed_from` + `cost_to_get` |

The generator **fails the build** on any violation: unsourced "sourced" numbers,
value-carrying "missing" numbers, formulas referencing unregistered inputs,
circular derivations.

Rendering rules:
- Derived numbers render as three-line chains: symbolic formula → substituted
  values with provenance markers → result.
- Range inputs propagate as intervals (corner evaluation). Never midpoint.
- Missing numbers render as a gray dashed placeholder. Never a guessed value.
- Markers are superscripts (`◆/◇/⊕/○`), not pills — they do not count against
  the pill budget.
- A prose linter warns when body text contains a currency amount matching no
  registry value.

---

## Visual Elements (readability is a requirement, not a nicety)

A report that is a wall of tables fails its job. The generator renders three
data visuals from the config; use them — do not bury the decision in prose.

### KPI strip (`s_kpi_strip`)

Big-number stat cards at the top of section 2. Config: `kpi_strip` = list of
registry IDs. Each renders as a large value + its label, drawn straight from the
number registry (so provenance still holds). Feature the 3–4 numbers that drive
the verdict — typically price, unit margin, CAC ceiling, and the best channel's
CAC. This is the "30-second read" in numeric form.

### CAC bar chart (`s_cac_chart`) — the hero decision visual

A horizontal bar chart in section 2: each channel's CAC interval as a bar, a
vertical line at the CAC ceiling. Config: `cac_chart.ceiling_id` (defaults to
`cac_ceiling`); bars are pulled automatically from `channel_screen` entries that
carry a `cac_estimate`. Bar color = the channel's screen verdict
(green/amber/red). **Mechanically honest:** a bar fully under the ceiling still
renders amber if the verdict is `undetermined`, because a benchmark can disprove
viability but never prove it. The caption states this so the reader is not
confused by an amber bar that sits left of the line.

This chart replaces the channel-screen *table* as the primary read; the table
remains below as the auditable detail.

### Semantic heatmap (`s_heatmap`)

See below. Channel × dimension, color-coded cells.

**Typography contract:** headings scale (h1 28px, h2 20px), section headings
carry the accent color, KPI numbers are 30px. Size contrast — not bold alone —
carries the hierarchy (frontend-design). Tables are the *detail* layer; lead
each section with the finding or the visual, not the grid.

---

## Heatmap Score Semantics

| Score | CSS class | Meaning |
|-------|-----------|---------|
| H | `.hm-high` | Primary investment: strong mechanism, deployable proxy, testable |
| T | `.hm-test` | Test slot: weaker signal or proxy; small budget to learn |
| S | `.hm-small` | Small exploratory test only |
| N | `.hm-none` | Not a focus this round |
| A | `.hm-avoid` | Actively suppress: ad fatigue, sure-thing, compliance risk |

A dimension enters the heatmap only if it satisfies ≥ 3 of:
1. Observable before deployment
2. Reachable via a platform proxy
3. Mechanistically linked to a product feature or barrier
4. Measurable via A/B, holdout, UTM, or platform report
5. Changes a creative, bid, frequency, or suppression decision

The semantic heatmap is earned: dimension detail only appears for channels that
survived the viability screen. It must not appear before Stage 3 passes. For
viable channels it attaches as an appendix; it is never a default section for
unscreened channels.

---

## BLOCKED Stamp Rule

Any action (Treatment Card) whose challenge status is `open-blocking` renders
with a **⊘ BLOCKED** stamp. The stamp is config-mechanical: challenge `C{n}` is
`open-blocking` and action `T{id}` declares `"blocked_by": ["C{n}"]` in the
config → the generator stamps `T{id}`. No budget may be allocated to a BLOCKED
action until the challenge is resolved.

Blocked actions still appear in the report — they show the reasoning for the
block, the challenge text verbatim, and the condition that would unblock them.

---

## Script Bridge: How to Embed Script Outputs

### Section 9 — Sample Size Gate (power_analysis.py)

```python
from power_analysis import n_per_arm_ate, n_per_cell_hte, experiment_duration_days

n_ab  = n_per_arm_ate(baseline_rate=cfg["baseline_cvr"], mde_abs=cfg["mde_abs"])
n_hte = n_per_cell_hte(
    baseline_rate_a=cfg["baseline_cvr"], baseline_rate_b=cfg["baseline_cvr"],
    uplift_a=cfg["mde_abs"] * 2, uplift_b=cfg["mde_abs"]
)
days = experiment_duration_days(4 * n_hte, cfg["eligible_per_day"])
```

Embed in execution gate row "Sample size":

```html
<span class="tag evidence">Script</span>
ATE: {n_ab:,}/arm · HTE: {n_hte:,}/cell · ~{days}d at {eligible_per_day:,}/day
```

### Section 11 — AUUC Gate (qini_auuc.py)

If uplift model scores are available:

```python
from qini_auuc import auuc_bootstrap_ci
import numpy as np

auuc, lo, hi = auuc_bootstrap_ci(y_true, w, tau_hat)
gate_passes = lo > 0
```

Embed in priority plays table:

```html
<span class="tag evidence">Script</span>
AUUC = {auuc:.1f}  95% CI [{lo:.1f}, {hi:.1f}]
→ {"Gate PASSED" if gate_passes else "Gate FAILED — do not scale"}
```

### Section 14 — OPE Support Check (ope_estimators.py)

Before any policy evaluation:

```python
from ope_estimators import support_check
result = support_check(t_logged, p_logged, pi_new)
# embed result["verdict"] in the gate row
```

---

## Pill Budget and Verdict Vocabulary

Pills (colored capsules) are rationed because 50 tags = 0 tags. Only four
families exist:

| Family | Values |
|--------|--------|
| Report verdict | GO / NO-GO / CONDITIONAL (exactly one) |
| Channel verdict | viable / not-viable / undetermined / role-only |
| Challenge status | resolved / open / open-blocking |
| Block stamp | ⊘ BLOCKED by C{n} |

Target: **fewer than 20 pills in a full report.** `undetermined` is a legal and
common channel verdict — honest blanks beat fabricated completeness. `role-only`
marks channels evaluated for a non-acquisition role (e.g., review content that
answers an objection) where CAC math does not apply.

---

## Readability Budget

- Tables: **maximum 4 columns.** More fields → cards (the generator renders
  actions and test plans as cards natively).
- One callout per section, maximum.
- Derivation chains in monospace blocks; prose in sentences.
- Language follows the user (ref 15); markers, verdicts, and IDs stay English.

---

## Writing Rules for Report Text

All report text follows ref 15. Key obligations in brief:

1. **Language**: match user's language; technical terms stay English
2. **No untagged numbers**: every ROI / CAC / KOL price / budget figure carries a claim tag AND exists in the registry
3. **Decision-first**: lead with the recommendation, evidence second
4. **No filler**: strip "it is worth noting that", "in conclusion", "as mentioned above"
5. **Callout usage**: use `.callout` only for the single most important decision or
   reviewer finding per section; do not put general summaries in callouts

---

## Generation Commands

```bash
# Validate config contract without rendering
python scripts/generate_report.py --config config.json --validate-only

# Render full report
python scripts/generate_report.py --config config.json --output report.html

# Built-in demo (minimal schema)
python scripts/generate_report.py --demo > demo.html
```

Worked example config: `examples/sample-sku-en-config.json`.

---

## Acceptance Checklist

- [ ] Part A (Decision Memo) alone tells the verdict, the central math, viable channels, top 2 actions, top challenge, and the next date
- [ ] Every section present and non-empty (or short-report mode declared)
- [ ] All monetary figures carry Evidence / Assumption / Hypothesis / Needs test claim tags
- [ ] Zero numbers without registry provenance — `--validate-only` passes, no lint warnings
- [ ] At least one honest `undetermined` or Missing entry on any real project (a registry with no unknowns is lying)
- [ ] Heatmap legend rendered with correct color swatches; heatmap only present for screen survivors
- [ ] Causal Activation Reviewer table present in section 6
- [ ] Unresolved blocking challenges are visible and stamp their dependent actions with ⊘ BLOCKED
- [ ] Sensitivity table present; Missing ledger sorted by sensitivity
- [ ] At least one script output embedded (power_analysis.py sample size minimum)
- [ ] Treatment Cards cover all H-main channel/dimension pairs
- [ ] Every budgeted action has a kill line and a decision date
- [ ] Measurement plan states explicit scale-up and pause rules
- [ ] Verification checklist covers propensity log, compliance claims, holdout gate
- [ ] Pill count < 20; no table wider than 4 columns
