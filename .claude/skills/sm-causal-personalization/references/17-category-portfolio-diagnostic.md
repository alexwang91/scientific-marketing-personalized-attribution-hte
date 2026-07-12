# 17 · Category Portfolio Diagnostic

## When to Use

When the operator arrives with a **whole category in one market** (a brand's
line-up of SKUs in one country) and asks "how is this category being run, where
am I bleeding, and what should each SKU do next" — *not* a single product launch.

This reference sits **upstream** of the single-SKU pipeline. It diagnoses the
portfolio, hands each SKU a verdict, and routes the "Grow" SKUs into ref 13 →
HTE for deep analysis. It does not replace that pipeline.

```
What did the operator bring?
├─ One SKU + country ("how should I invest behind product X in market Y")
│     → ref 13 product × country pipeline → ref 04 HTE  (skip this reference)
└─ A category + country + a list of in-market SKUs
      → THIS reference: diagnose the category → verdict each SKU
        → confirmed "Grow" SKUs descend into ref 13 → ref 04
```

## Core Principle: Diagnose Before You Recommend

A category playbook that opens with recommendations is a wish list. The report
opens with a **diagnosis** and every recommendation points back to the finding
that justifies it. Two rules close the loop:

- **Every 4P recommendation must trace to a finding.** A move with no diagnosed
  cause is desk intuition wearing a yaml schema.
- **Every finding must trace to evidence.** A sharp claim with no proof is slop
  with attitude.

The deliverable is allowed — encouraged — to be uncomfortable. A category that
is being run badly should read like it. But sharpness is earned by evidence, not
by tone (see the severity rule below).

## The Six Audit Lenses (2 market + 4 audited-P)

Diagnosis is primarily **category-level**; each SKU gets only a few lines in the
matrix. The four execution lenses mirror the 4P, so the audit and the
recommendation are structurally the same axis: audit each P, recommend each P.

| Lens | Audits | The uncomfortable question |
|------|--------|----------------------------|
| **L1 Band coverage & white space** | where the money is vs where you play | Which growing price band do you have *no* SKU in? |
| **L2 Category momentum** | is the pie growing / shrinking, in which bands | Is your volume anchored to a shrinking tier? |
| **L3 Portfolio architecture (Product)** | dead flagships, zombie SKUs, gaps, self-cannibalization | Which two SKUs are fighting each other? |
| **L4 Price positioning (Price)** | defensible vs no-man's-land vs permanent-promo spiral | Whose anchor price have you already destroyed with discounts? |
| **L5 Channel presence (Place)** | present where the segment buys; concentration risk | Which decisive shelf are you absent from? |
| **L6 Demand gen & digital shelf (Promotion)** | right message to right segment; site, PDP, reviews, localized content | Which SKU is invisible exactly where buyers decide? |

After-sales / service is deliberately **out of scope**: there is little a sales
operator can pull on it inside this report.

Each price tier also carries a **segment × force** read (the tier version of the
four forces, ref 02): different bands are moved by different levers — entry
buyers fight Habit, mid buyers carry Push + Anxiety, premium buyers respond to
Pull. These are Hypothesis-grade and meant for the operator to confirm or redraw.

## The One Rule That Keeps the Critique Honest

**Severity ≤ evidence grade.** A finding's severity cannot exceed what its proof
can carry:

| Severity | Means | Required evidence |
|----------|-------|-------------------|
| 🔴 Critical | losing money / share *now* | Sourced (directly verifiable, e.g. the PDP does not exist) |
| 🟠 Major | material risk | Assumed (basis stated) or strong Hypothesis |
| 🟡 Watch | flagged, evidence thin | Hypothesis — **auto-routed to the test queue** |

A scathing claim backed only by review counts or banner-frequency (Hypothesis)
**cannot be stamped Critical** — it is automatically downgraded to Watch and
enters the test queue with a visible note. This is the executable version of the
skill's contract (ref 16) and the line between a sharp consultant and a hater:
**a sharp claim must pay its evidence tax.** `generate_report.py` enforces the
cap at render time (`_cap_severity`).

## SKU Verdicts (the matrix output)

The report's first screen is a verdict + one-line-per-P matrix. Four verdicts,
plain language, no philosophy:

| Verdict | Meaning | Next step |
|---------|---------|-----------|
| **Grow / Invest** | profit / growth room worth resourcing | → ref 13 deep dive (after operator confirms) |
| **Hold** | defend the band, no added investment | maintain |
| **Harvest** | stop investing, protect margin, plan a successor | wind down |
| **Exit** | clear inventory, successor already needed | delist |

A **Grow verdict is a Hypothesis**, not a conclusion: it says there is likely
room, not that the room is proven. Only the SKU pipeline's holdout / geo test
(ref 03) turns "looks like room" into Sourced incremental upside.

## Step-by-Step

1. **Bucket the SKUs by purchase decision, not by category label.** A mobile
   hotspot and a home router are not the same competitive field; mixing them
   confuses the competitor set. Cluster price tiers from observed price points
   (Hypothesis-grade) and let the operator confirm or redraw them.
2. **Scan the public shelf** (ref 00b discipline): list prices and promo
   frequency, review counts and rating trends, competitor SKUs and prices, PDP /
   site / localization presence, voice-of-customer force signals. Tag everything
   `Hypothesis` unless directly verifiable.
3. **Run the six lenses.** Write each finding as: statement → evidence (graded)
   → implication → the 4P move it justifies. Apply the severity cap.
4. **Verdict each SKU** and write its four one-liners. Keep per-SKU diagnosis to
   a few lines; depth is earned by a Grow verdict, not spent here.
5. **Hand the operator the report; collect corrections.** AI-scanned fields are
   Hypothesis; operator-supplied internals (sell-through, margin, contracts,
   inventory) promote to Sourced.
6. **Route confirmed Grow SKUs** into ref 13 → ref 04 for deep analysis, or —
   if the question is "how much do I spend, where, this cycle" rather than
   "does this SKU have real incremental upside" — into the optional
   investment plan below (Hold SKUs are also eligible; Harvest/Exit never are).

## Config Schema (generate_report.py)

`report_type: "category_portfolio"` switches the renderer. Key blocks:
`price_tiers[]` (id, label, trend, audience, force, channel_fit, your_skus,
competitors[]), `diagnosis[]` (lens, title, severity, finding, evidence,
evidence_grade, implication, recommendation), `portfolio[]` (sku, tier,
lifecycle, verdict, note, fourP{product,price,place,promotion}). All figures go
in the `numbers` registry under the provenance contract. Worked example:
`examples/aurora-airpurifier-category-config.json` (fictional, illustrative).

## Optional: Investment Plan (SKU × Marketing-Module Budget)

Randomized HTE cells must name `validation_ref`, and the matching
`investment_plan.hte_validation` entry must pass Qini/AUUC and decile
calibration gates before the dashboard calls that cell `validated`. A
measurement-gate string alone is not enough.

Adding `investment_plan` to the same config turns the diagnostic into a budget
decision: how much to spend, on which SKU, through which marketing lever, this
cycle — the SKU-level tier of the three-tier λ* rule in ref 06. It renders
into all five chapters (verdict + KPIs in ch1, the frontier chart in ch2, the
SKU × module matrix in ch3, activation cards in ch4, confidence + optional MMM
in ch5), in both the document report and `--format dashboard`.

Hard gates, enforced by `investment_schema.py` at build time (not a style
suggestion — a malformed plan fails the build):

- **Verdict gate**: a SKU verdicted `harvest` or `exit` above can never appear
  in `investment_plan.cells`, no matter how it would score. `grow` and `hold`
  are the only eligible verdicts.
- **No discount-style levers**: `modules[].id` must be a marketing lever
  (`search`, `retail_media`, `paid_social_video`, `creator_review`,
  `pdp_content`, `retail_activation`, `pr_reviews`, `crm_retention`,
  `measurement`) — `discount` / `coupon` / `rebate` / `price_subsidy` are
  rejected outright; this report recommends where to spend attention, never a
  margin giveaway.
- **`confidence` is computed, never a raw field**: each cell states its
  `tau_hat` and `tau_source` (`randomized_hte` / `modeled_hte` /
  `mmm_calibrated_prior` / `expert_assumption` / `missing`); the badge
  (`validated` / `mmm_calibrated` / `assumption_grade` / `blocked`) is derived
  from that plus `measurement_gate` and `readiness` — setting a `confidence`
  field directly on a cell is a build error.
- **Evidence-tier ROI floors** (optional): `required_mroi_by_confidence`
  maps a confidence badge to its own minimum marginal return — e.g.
  `{"validated": 1.3, "assumption_grade": 1.7}` — so unvalidated cells must
  clear a higher bar before they out-compete validated ones for budget.
- **Interval-coverage gate** (optional): `hte_validation.min_interval_coverage`
  adds a third validation gate — a model's tau intervals must empirically
  cover reality on holdout (per-ref `interval_coverage`, or computed from
  `decile_calibration` rows carrying `tau_lo`/`tau_hi`) before its cells can
  wear the "validated" badge.
- **A `tau_source: "missing"` cell carries no `tau_hat`** (that would be a
  guess dressed as data) and must name `needed_from` — it renders in ch1's
  "never funded this round" list, not silently dropped.

Optional `mmm` block bridges an already-fit pymc-marketing macro-calibration
summary (`mode: "provided_summary"`) into ch5; omit it and ch5 states plainly
that no macro calibration was supplied this cycle, rather than guessing.

Worked example: `examples/aurora-airpurifier-category-config.json` also
carries an `investment_plan` (three Grow/Hold SKUs, mixed confidence tiers,
one deliberately blocked cell) — see `examples/rendered/aurora-category.html`
and `aurora-category-dashboard.html` for the rendered result.

## Common Failure Modes

- **Same chart, different purchase decisions**: lumping distinct buyer journeys
  (e.g. a portable device and a home device) into one map — the competitor set
  is wrong from the start. Bucket first (Step 1).
- **Sharp but unsupported**: severity not capped by evidence → the diagnosis is
  an opinion column, not a finding.
- **Verdict treated as conclusion**: "Grow" shipped to budget without the
  pipeline's holdout. It is a Hypothesis until tested.
- **Lifecycle signal read as sales**: review velocity stalling ≠ confirmed
  decline; it is a Hypothesis until internal data confirms.
- **Recommendation with no cause**: a 4P line that points to no finding — delete
  it, or find the finding.
- **Deep analysis smuggled into the category report**: per-SKU sections balloon
  into full HTE write-ups. Keep them light; deep work lives in ref 13 / 04.

## Acceptance Checklist

- [ ] SKUs bucketed by purchase decision before any price-band map
- [ ] Every finding carries evidence + an explicit grade; severity ≤ grade
- [ ] Every 4P recommendation points back to a specific finding
- [ ] Each SKU has exactly one verdict (Grow / Hold / Harvest / Exit) and four
      one-liners
- [ ] Grow verdicts flagged as Hypothesis, routed to ref 13 for holdout proof
- [ ] AI-scanned fields tagged Hypothesis; operator internals tagged Sourced
- [ ] Per-SKU sections stay light; no deep HTE write-ups in this report
- [ ] Any creator / KOL named in a Promotion recommendation has passed **Gate 0**
      (category exclusivity check in this market) before scoring or budgeting —
      unknown exclusivity status = gated, not recommended

## Literature

- Day (1977) "Diagnosing the Product Portfolio" — the original portfolio-verdict
  logic (grow / hold / harvest / divest), recast here on an evidence cap.
- Minto, *The Pyramid Principle* — finding → implication → recommendation
  ("so what / now what") as the report's spine.
- Pattern credit: the category-readiness audit and per-SKU 4P matrix adapt the
  consumer-launch diagnostic moves from the GTM-Master skill suite
  (alexwang91/gtm-master), re-grounded on this skill's provenance contract so a
  verdict stays Hypothesis until a holdout proves it.
- See also ref 00b (voice = Hypothesis), ref 02 (four forces, KOL), ref 13
  (the SKU pipeline this feeds), ref 16 (provenance states).
