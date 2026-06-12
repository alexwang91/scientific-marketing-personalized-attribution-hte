# 15 · Language, Tone, and Writing Rules

## Purpose

The skill generates content for business decision-makers, not academic reviewers.
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
| T01, D1, P1 (Treatment/Dimension/Play IDs) | — |
| CAC, ROI, ROAS, CPM, CPC, CPA | — |
| A/B, holdout, propensity | — |

Currency, units, and numbers follow the local format for the market in scope.

---

## Rule 2 — Evidence Label Obligation

**Every number that affects a decision must carry one of four labels:**

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

---

## Rule 3 — Decision-First Structure

Lead with the recommendation. Put evidence, caveats, and methodology after.

**Wrong:**
> "Based on an analysis of the channel landscape and semantic dimensions, considering
>  the competitive dynamics and the maturity of measurement infrastructure, we recommend
>  starting with a trial."

**Right:**
> "Recommendation: 4-week trial. Search/Retail captures intent; Creator builds proof;
>  Retargeting tops up at low frequency. Scale only when incremental CAC < [target] and
>  a holdout confirms positive incremental margin."

---

## Rule 4 — Anti-Slop Rules

Strip these phrases from all outputs:

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

**General rule**: if removing a phrase leaves the meaning unchanged, remove it.

---

## Rule 5 — Terminology Consistency

Use these terms consistently; do not substitute with approximations:

| Correct term | Do not use |
|-------------|-----------|
| Incremental lift / incremental effect | "Causal impact" (unless in academic context) |
| Holdout group / no-contact arm | "Control group" (Control group implies RCT; holdout may be observational) |
| Treatment Card | "Campaign brief", "activation plan" |
| D dimension | "Audience segment", "targeting layer" (these differ from D dimensions) |
| Causal Activation Reviewer | "Review step", "sanity check" |
| Execution gate | "Launch checklist" |
| Platform ROAS | "True ROI" (they are not the same) |
| Incremental CAC | "CAC" (unmodified CAC conflates incremental and platform-attributed) |

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

---

## Rule 9 — Maturity Honest Labeling

Do not overstate what the current analysis can claim:

| Maturity | What it supports | What it does not support |
|----------|-----------------|--------------------------|
| L0 (hypothesis) | Trial design, channel prioritization, KOL inquiry | Any CATE claim, ROI fact |
| L1 (GCG + retrospective) | ATE by channel, coarse uplift segments | Individual CATE, policy optimization |
| L2 (offline policy + OPE) | Policy comparison, budget allocation | Online deployment claims |
| L3 (bandit + online) | Continuous optimization | Retrospective explanation |

Label the current analysis maturity at the top of Section 9 (Execution Gates) and
the verification checklist. Do not let the analysis appear more mature than the data
supports.

---

## Quick Pre-Delivery Checklist

Before any output is delivered:

- [ ] Language matches user's input language
- [ ] All currency / ROI / KOL figures carry Evidence / Assumption / Hypothesis / Needs test
- [ ] Recommendation appears before supporting evidence
- [ ] No banned phrases present
- [ ] Technical terms are English; non-technical prose is in user's language
- [ ] Maturity level is stated honestly
- [ ] Table used where ≥ 3 items × ≥ 2 dimensions
- [ ] Callouts used sparingly (≤ 1 per section)
