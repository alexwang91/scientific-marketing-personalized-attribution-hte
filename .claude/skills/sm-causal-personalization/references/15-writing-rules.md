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

## Rule 10 — Narrative Structure: Making Theory Feel Necessary

The audience trusts us because the analysis is checkable (ref 16). But the audience
*uses* the analysis only if the theory feels necessary to them — not merely
explained. There is a precise difference:

- **Explained**: "Causal inference methods estimate the effect of an action
  holding confounders constant. CATE = E[Y(1)−Y(0)|X=x]."
- **Necessary**: "The attribution platform said the coupon drove +30% revenue.
  The holdout showed +2%. The 28-point gap was customers who would have bought
  anyway. That gap is real money charged to the marketing budget."

The second version shows the reader what went wrong without the theory.
The reader then *wants* the theory. These rules operationalize that.

---

### Rule 10a — Naive Method Failure First (the "ML alone is hardly prescriptive" device)

**Never open with what the framework is. Open with what breaks without it.**

The structure:
1. Name the standard approach the reader already uses.
2. State precisely where it fails — with a number if possible.
3. Introduce the remedy only after the reader feels the gap.

> **Wrong**: "Causal personalization uses HTE models to estimate individual
> treatment effects τ(x) = E[Y(1)−Y(0)|X=x], enabling more targeted action selection."
>
> **Right**: "A model trained to predict purchase probability will rank your
> best existing customers first — the people who would buy regardless of any
> action. A budget optimized on that model is a discount program for sure-things.
> HTE models rank by lift instead. Same budget, different people."

In report sections: every methodology section names the naive ceiling before
introducing the refinement. The ceiling is not a strawman — it is an honest
description of what the team was probably doing before.

---

### Rule 10b — Gap Stat Opener (落差数字开场)

**Lead a section with a number that quantifies the cost of the status quo.**

The number creates urgency without manufactured anxiety (ref 09). It must be
sourced or carry an Assumption label (Rule 2). Do not invent gap stats.

Structures that work:
- "Only X% of teams can measure incrementality across all channels." → [source]
- "A team with [naive method] captured [Y%] of achievable lift in [experiment]." → Evidence
- "The platform claimed ¥X. The holdout measured ¥Y. The ¥Z gap is unrecovered." → Assumption or Evidence

The gap stat belongs in:
- The report section intro (s2 narrative intro, s4 HTE intro, s7 budget intro)
- The executive memo `situation` field
- Any callout that gates a budget decision

**Hard rule**: if the gap stat is an Assumption or Hypothesis, label it as one.
A fabricated urgency number is a dark pattern (ref 09) and destroys the analysis's
credibility when audited.

---

### Rule 10c — Named Protagonist Threading (具名主角串联)

**One named, specific buyer persona threads through the whole analytical chain.**

The persona is not a demographic summary. It is a named fictional individual
whose situation the reader can track across sections. The same person appears:
at the moment of the purchase decision (s4 mechanism), in the targeting rule
(s5 dimension), in the treatment card (s7 action), and in the suppression check
(s15 anti-persona).

> "Wei Jian, 34, adds a smart scale to the cart at 11 pm on Sunday.
> She has viewed the product page four times. She has not bought.
> Her Push force (dissatisfaction with her old scale) is high. Her Anxiety
> force (commitment fear, return uncertainty) is also high. A 30%-off coupon
> with a 30-day return guarantee targets the Anxiety force — and for Wei Jian,
> that force is still unsettled."

Usage constraints:
- One persona per report. Two personas create confusion.
- The persona is fictional and explicitly labeled as illustrative.
- The persona must pass the governance check (ref 09): no protected-attribute
  proxy is assumed in the illustration.
- The persona appears in 2–4 sections, not everywhere. Overuse feels like a
  gimmick.

---

### Rule 10d — One-Line Compression (一句话压缩)

**Every framework gets a one-liner that a non-technical reader can repeat.**

The one-liner is not a simplification — it is the mechanism in its most
compressed form. Derive it from the core equation, not from the branding.

| Concept | One-liner |
|---------|-----------|
| HTE vs attribution | "谁因为你才买，而不是谁本来就会买" (who bought *because* of you, not who was going to buy anyway) |
| Force targeting | "优惠券给犹豫的人，不给已经决定的人" (coupons for the wavering, not the decided) |
| Suppression | "不打扰，也是一种策略" (not contacting is itself a choice) |
| OPE gate | "先在数据上开枪，再在用户上开枪" (fire on data first, then on users) |
| Holdout vs GCG | "留一部分人什么都不做，才能知道其他人的做法是否有效" |

The one-liner appears:
- In the executive memo `situation` or `decision` field — in plain language
- At the start of a methodology paragraph, before the technical definition
- In any section where the framework is introduced for the first time

**Hard rule**: the one-liner must be derivable from the actual math. It is a
compression, not a slogan. If the one-liner implies something the model cannot
deliver, rewrite the one-liner.

---

### Rule 10e — Honest Complexity Acknowledgment

**When something is genuinely hard, say so — and explain why it is hard.**

Pretending the analysis is simpler than it is destroys trust when the reader
tries to apply it and fails. Acknowledging complexity, with a specific reason,
builds trust.

> **Wrong**: "The model is straightforward to implement."
>
> **Right**: "Doubly-robust estimation is harder to debug than a propensity
> model — if both the outcome model and the propensity model are wrong, the
> estimator inherits both errors. The upside: it is wrong in a known direction.
> A single-model approach fails silently."

The acknowledgment includes:
1. The specific difficulty (not "this is complex").
2. Why it is hard (mechanism, not vibe).
3. What the difficulty protects the reader from (the alternative's failure mode).

---

### Rule 10f — Named Case + Number (点名案例 + 数字)

**Every abstract claim requires a named case and a number.**

"Causal personalization improves budget efficiency" is unactionable.
"In Booking's 2024 E3IR experiment, end-to-end reward optimization reduced
wasted spend by X% vs the two-stage baseline [Booking 2024, arXiv ref]" is
replicable and auditable.

The case can be:
- An internal experiment result (Evidence — cite the experiment ID and date)
- A published benchmark (Evidence — cite author, year, venue)
- A worked example from this analysis (Assumption — label the baseline)
- A named illustrative scenario (Hypothesis — label it explicitly)

The number can be:
- An absolute improvement (¥X saved, Y% lift)
- A relative comparison (2× better than the naive method)
- A cost of inaction (gap stat from Rule 10b)

**Hard rule**: "significant improvement," "meaningful lift," and "substantial
gains" are banned (anti-slop, Rule 4). Replace with the number or label it
`Needs test`.

---

### Rule 10g — Epistemological Positioning (问题 → 方案 → 方案有效的证据)

**Structure every major claim as: problem + remedy + evidence the remedy works.**

Top consulting reports do not just name the problem. They show the problem,
state the remedy, and provide evidence the remedy works — in that order.
We go one step further: because we have causal methods, we can state *why*
the remedy works (mechanism) and *when* it does not (overturn condition,
Rule 2b).

The three-part structure:

```
1. Problem       — what fails with the current approach, and what it costs
                   (gap stat from Rule 10b; naive method ceiling from Rule 10a)
2. Remedy        — the specific action, model, or policy change
                   (treatment card, dimension, or policy rule)
3. Evidence      — why the remedy works: prior experiment, mechanism argument,
                   or overturn condition stating when it would not work
```

This is not a formula to be followed mechanically. It is a test: if a section
cannot be summarized in these three parts, either the recommendation is missing,
the evidence is missing, or the problem has not been stated in a way the reader
can feel. Any of these is a writing failure.

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
- [ ] Every methodology section opens with the naive method's failure, not a definition
- [ ] Any gap stat carries Evidence / Assumption / Hypothesis label (no fabricated urgency)
- [ ] If a named persona is used, it appears in 2–4 sections, is labeled illustrative, and passes the governance proxy check
- [ ] Every framework is introduced with a one-liner compression before the technical definition
- [ ] Every abstract recommendation has a named case (experiment ID, published source, or labeled illustrative scenario) and a number
- [ ] Every major claim can be stated as: problem → remedy → evidence the remedy works
