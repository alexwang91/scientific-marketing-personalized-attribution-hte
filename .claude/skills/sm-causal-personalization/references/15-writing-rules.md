# 15 · Language, Tone, and Writing Rules

## Purpose

The skill generates content for business decision-makers, not academic reviewers.
Writing rules for every output — chat, reports, treatment cards. The audience
is a business decision-maker who does not yet trust the analysis. Trust is
earned by checkability (ref 16) and by prose that says exactly what is known,
assumed, and unknown — in that order of prominence.

This reference enforces concrete writing rules that apply to every output — chat
responses, HTML reports, Treatment Cards, and callouts.

---

## Rule 1 — Language Detection and Response Policy

**Always respond in the user's language.** Detection is based on the most recent
user message. Mixed input: use the dominant language.

Technical terms stay in English regardless of response language:

| Always English | Never translate |
|----------------|-----------------|
| HTE, CATE, GCG | — |
| OPE, IPS, SNIPS, DR | — |
| Qini, AUUC | — |
| T01, D1, P1, C1 (Treatment/Dimension/Play/Challenge IDs) | — |
| CAC, ROI, ROAS, CPM, CPC, CPA | — |
| A/B, holdout, propensity | — |
| GO / NO-GO / CONDITIONAL, viable / undetermined | — |

Currency, units, and numbers follow the local format for the market in scope.

---

## Rule 2 — Evidence Label Obligation

**Every number that affects a decision must carry one of four claim labels:**

| Label | When |
|-------|------|
| `Evidence` | The number comes from a cited source, a validated experiment, or a script output |
| `Assumption` | User-supplied input or market-standard estimate not yet verified |
| `Hypothesis` | Inferred from mechanism or prior; no direct measurement |
| `Needs test` | The number will change a budget, channel, or KOL decision — must be validated before scale |

**Hard rule**: any sentence containing a currency symbol (€, $, ¥, HUF, CNY, etc.),
a "%" describing conversion or ROI, or a CAC/ROAS figure — that sentence must contain
a tag before it is delivered to the user.

**Hard rule**: KOL fees are never Evidence unless a direct quote has been received.
Default tag for KOL price ranges: `Assumption` or `Needs quote`.

**Hard rule**: ROI and incrementality are never Evidence without a holdout or
credible identification strategy. Default tag: `Hypothesis` or `Needs test`.

**Two levels of the same obligation**: claim labels appear in rendered HTML on prose
claims. Number-level provenance states (sourced / assumed / derived / missing) live in
the config registry and are enforced by generate_report.py. A number must satisfy
both: the prose claim carries an Evidence/Assumption/Hypothesis/Needs-test label, and
the underlying registry entry carries a sourced/assumed/derived/missing provenance
state. See ref 12 for registry rendering rules.

---

## Rule 2b — Falsifiability Obligation

Every major claim carries its overturn condition. Every recommendation has a kill line.

> **Wrong**: "Social prospecting is not recommended."
>
> **Right**: "Social prospecting fails the screen (best-case benchmark CAC 47 RON
> vs 35.8 ceiling). This flips if margin is ≥ 40% or mesh attach exceeds 30%."

A report that cannot state what would change its mind is advocacy. The decision
memo's `overturn_conditions` field is mandatory, sourced from the top of the
sensitivity table. A section that makes a directional claim without stating what
data would reverse it is incomplete.

---

## Rule 3 — Decision-First (Pyramid) Structure

Lead with the recommendation. Put evidence, caveats, and methodology after.
Conclusion first, at every scale: the report leads with the memo; a section
leads with its finding; a paragraph leads with its point.

**Wrong:**
> "Based on an analysis of the channel landscape and semantic dimensions, considering
>  the competitive dynamics and the maturity of measurement infrastructure, we recommend
>  starting with a trial."

**Right:**
> "Recommendation: 4-week trial. Search/Retail captures intent; Creator builds proof;
>  Retargeting tops up at low frequency. Scale only when incremental CAC < [target] and
>  a holdout confirms positive incremental margin."

The reader who stops after one screen, one sentence, or one row should leave with
a correct (if coarse) picture — never a misleading one.

---

## Rule 4 — Anti-Slop Rules

Strip these phrases from all outputs. If removing a phrase leaves the meaning
unchanged, remove it.

| Banned phrase | Replace with |
|---------------|-------------|
| "It is worth noting that…" | State the point directly |
| "As mentioned above…" | Reference the section/label |
| "In conclusion…" | Just conclude |
| "It is important to emphasize…" | Emphasize by placement, not by stating it's important |
| "We recommend a comprehensive approach…" | Say what the approach is |
| "This is a complex topic…" | Skip; address the complexity |
| "There are many factors to consider…" | List the factors |
| "Leverage synergies…" | Specify the mechanism |
| "Best-in-class…" | State the metric |
| "Holistic view…" | Say what the view covers |
| "Delve into…" | Just start |
| "Comprehensive approach…" | Name the approach |

Also banned: passive evasions ("it was found that"), hedging chains ("may
potentially possibly"), and nominalization stacks ("operationalization of
the utilization").

**General rule**: if removing a phrase leaves the meaning unchanged, remove it.

---

## Rule 5 — Terminology Consistency and Honest-State Vocabulary

Use these terms consistently; do not substitute with approximations:

| Correct term | Do not use |
|-------------|-----------|
| Incremental lift / incremental effect | "Causal impact" (unless in academic context) |
| Holdout group / no-contact arm | "Control group" (implies RCT; holdout may be observational) |
| Treatment Card | "Campaign brief", "activation plan" |
| D dimension | "Audience segment", "targeting layer" (these differ from D dimensions) |
| Causal Activation Reviewer | "Review step", "sanity check" |
| Execution gate | "Launch checklist" |
| Platform ROAS | "True ROI" (they are not the same) |
| Incremental CAC | "CAC" (unmodified CAC conflates incremental and platform-attributed) |

**Four honest-state expressions** — use these when the state is genuinely uncertain:

| Say | Don't say |
|-----|-----------|
| "undetermined — interval spans the ceiling; pull CPC data first" | a confident midpoint |
| "missing; obtainable from X at zero cost" | a placeholder guess |
| "open challenge, blocks budget line T03" | silence about an unanswered objection |
| "this is the report's weakest point: …" | hoping the reader won't notice |

Uncertainty stated precisely reads as competence. Uncertainty papered over
reads as either ignorance or deception — and the reader can't tell which,
so they assume the worse.

---

## Rule 6 — Tone: Business-Facing, Not Academic

Avoid:
- Passive voice ("it was found that…")
- Nominalizations ("operationalization", "utilization")
- Hedging chains ("may potentially possibly suggest…")

Use:
- Active voice with a named subject ("The data shows…", "The model predicts…")
- Short sentences (≤ 25 words) for recommendations; longer allowed for mechanism explanations
- Concrete numbers over vague ranges ("CAC below 30,000 HUF" not "acceptable CAC")

---

## Rule 7 — Table vs Prose

Use a table when:
- Comparing ≥ 3 options on ≥ 2 dimensions
- Listing Treatment Cards, D dimensions, or budget rows
- Showing a checklist or gate status

Use prose when:
- Explaining a mechanism or causal chain
- Giving a single recommendation with one condition
- Writing a callout summary

Do not mix tables and prose by repeating the same content in both forms.

---

## Rule 8 — Callout Usage

A callout (the blue left-border block in the HTML template) is reserved for:
- The single most important recommendation per section
- A Reviewer conclusion
- A gate that blocks progress

Do not use callouts for:
- General methodology overviews
- Lists of conditions (use a table)
- Repeating a point already made in the section header

One callout per section, maximum.

---

## Rule 9 — Maturity Honest Labeling

Do not overstate what the current analysis can claim. State the maturity level
(L0–L3) where conclusions are drawn, and respect its ceiling.

| Maturity | What it supports | What it does not support |
|----------|-----------------|--------------------------|
| L0 (hypothesis) | Trial design, channel prioritization, KOL inquiry | Any CATE claim, ROI fact |
| L1 (GCG + retrospective) | ATE by channel, coarse uplift segments | Individual CATE, policy optimization |
| L2 (offline policy + OPE) | Policy comparison, budget allocation | Online deployment claims |
| L3 (bandit + online) | Continuous optimization | Retrospective explanation |

L0 supports trial design and channel screens, not CATE claims; L1 supports
channel-level ATE, not per-segment optimization; L2 supports policy comparison
via OPE; only L3 supports continuous-optimization claims. A report must never
read one level more mature than its data.

Label the current analysis maturity at the top of Section 9 (Execution Gates) and
the verification checklist. Do not let the analysis appear more mature than the data
supports.

---

## Form Budget

Pills (colored capsules) are rationed because 50 tags = 0 tags. Only four
families of pills exist: report verdict, channel verdicts, challenge statuses,
block stamps. Nothing else gets a capsule. See ref 12 for the pill vocabulary.

- Tables: **maximum 4 columns.** More fields → cards.
- One callout per section, maximum.
- Recommendation sentences ≤ 25 words; mechanism explanations may run longer.
- Target fewer than 20 pills in a full report.

---

## Pre-Delivery Checklist

Before any output is delivered:

- [ ] Language matches user's input language; technical terms English
- [ ] All currency / ROI / KOL figures carry Evidence / Assumption / Hypothesis / Needs test claim labels
- [ ] Every prose number exists in the registry (provenance lint clean)
- [ ] Every major claim has an overturn condition; every budgeted action a kill line
- [ ] Recommendation appears before supporting evidence (decision-first)
- [ ] No banned phrases present; anti-slop list applied
- [ ] Technical terms are English; non-technical prose is in user's language
- [ ] At least one honestly-stated unknown (real projects always have them)
- [ ] Maturity level is stated honestly and not exceeded
- [ ] Table used where ≥ 3 items × ≥ 2 dimensions
- [ ] Callouts used sparingly (≤ 1 per section)
- [ ] Form budget respected: tables ≤ 4 columns, pills < 20, recommendations ≤ 25 words
