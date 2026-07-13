# 16 · Estimation Discipline: Number Provenance, Fermi Chains, Sensitivity

## Purpose

This reference is the foundation for every number that appears in any output of
this skill. It exists because the single fastest way to destroy a report's
credibility is a number with no visible origin. A number without provenance is
not "approximately right" — it is fabrication wearing the costume of analysis.

**Core rule: honest blanks beat fabricated completeness.**

---

## The Four Provenance States

Every number in any deliverable is in exactly one state. There is no fifth state.

| State | Marker | Requirement | Render |
|-------|--------|-------------|--------|
| **Sourced** | `[S]` | URL + access date | Value + source link |
| **Assumed** | `[A]` | Explicit basis ("user input", "industry convention X") + entry in assumption register | Value + basis |
| **Derived** | `[D]` | Formula shown; every input is itself Sourced / Assumed / Derived | Full derivation chain |
| **Missing** | `[M]` | What data, where to get it, cost to get it, what decisions it blocks | Gray placeholder — **never a guessed value** |

Enforcement is mechanical, not aspirational: `generate_report.py` validates the
number registry and **refuses to render** any number that lacks provenance
fields. A derived number whose inputs don't resolve is a build error.

### What is banned

- Point estimates or ranges typed directly into tables ("est. CAC 28–50 RON")
  with no formula. If you cannot show the derivation, the cell is Missing.
- "Hypothesis" as a label for an invented number. Hypothesis describes a causal
  claim awaiting a test — it is not a license to publish made-up quantities.
- Benchmarks silently presented as local facts (see below).

---

## Derivation Chains (Fermi Discipline)

Every Derived number renders as a three-line chain: symbolic formula,
substituted values with provenance markers, result.

```
unit_margin = price × margin_rate
            = 199 RON [S: Altex, 2026-06-12] × 30% [A: user input, unconfirmed]
            = 59.7 RON

cac_ceiling = unit_margin × cac_share_of_margin
            = 59.7 RON [D] × 60% [A: convention — acquisition may consume
                                   at most 60% of first-order margin]
            = 35.8 RON
```

Rules:

1. **One unknown per line.** If a formula needs two missing inputs, the output
   is Missing, and both inputs go to the Missing ledger.
2. **The chain inherits the weakest provenance.** A Derived value built on an
   Assumed input is only as strong as the assumption — the marker trail makes
   this visible, and the sensitivity table (below) quantifies it.
3. **Ranges propagate as intervals.** If an input is a range, evaluate the
   formula at the endpoints and report the resulting interval. Never collapse
   a range to its midpoint to make a table look cleaner.
4. **"Undetermined" is a legal result.** When a screening computation spans the
   decision threshold (e.g., CAC interval 17–150 RON vs ceiling 35.8 RON), the
   verdict is *undetermined*, and the next action is to acquire the data that
   narrows the interval — not to pick the flattering endpoint.

---

## Benchmark Rules

Benchmarks (industry CPC/CVR/CPM ranges) are legitimate inputs **only** under
all three conditions:

1. Registered as **Assumed** with basis "industry benchmark range, not local
   data" — never as Sourced, even if the benchmark itself has a citation.
   (The citation proves the benchmark exists, not that it applies here.)
2. Entered as a **range**, never a point.
3. Any verdict resting on a benchmark is automatically capped at
   *not-viable* or *undetermined* — a benchmark can kill an option
   (best-case endpoint still fails the threshold) but can never green-light
   one (that requires local data).

This asymmetry is intentional: benchmarks are good enough to say "the math
cannot work even in the best case", and never good enough to say "this will work."

---

## Sensitivity Analysis (mandatory section)

Every report with a quantitative conclusion includes a sensitivity table
answering: **which single assumption, if wrong, flips the conclusion?**

| Assumption change | Effect on conclusion | Verification priority |
|------------------|---------------------|----------------------|
| margin 30% → 40% | CAC ceiling 35.8 → 47.8; channel X may flip to viable | 1 — highest |
| price at 160 (lowest SKU) | ceiling drops to 28.8; nearly all channels out | 2 |
| mesh attach rate > 30% | effective ticket +60%; entire screen re-runs | 3 |

Two obligations follow:

1. **Verification order = sensitivity order.** The data-acquisition list in the
   Missing ledger is sorted by how much each item moves the conclusion, not by
   how easy it is to get.
2. **The thesis must name its overturn conditions.** The decision memo states
   explicitly: "this conclusion flips if A or B or C" — taken directly from the
   top rows of this table. A report that cannot state what would change its
   mind is advocacy, not analysis.

---

## The Missing Ledger

Missing numbers are first-class citizens with their own table (in the evidence
appendix), sorted by sensitivity:

| What | Where to get it | Cost | Blocks |
|------|----------------|------|--------|
| Romanian-language keyword CPC | Google Keyword Planner | 0 budget, 1 hour | Search channel verdict |
| Retail media rate card | eMAG/Altex direct inquiry | 0 budget, 1 email | Retail channel verdict |
| Landing page CVR | 2-week pilot or historical data | pilot budget | All CAC math |

A report whose strongest section is its Missing ledger is often the most
useful report you can deliver: it converts ignorance from a hidden liability
into a priced work plan.

---

## The Identification Gate (before any incremental claim)

No ATE / uplift / incremental number enters a report without answering, in
one or two sentences: what is the confounding story, what identification
strategy handles it (randomization, adjustment set, geo split, holdout), and
is the effect identifiable at all from the data at hand? Non-identifiable →
the claim is *abstained from*, mechanically: the verdict stays undetermined,
tau_source stays `missing`, and the schema enforces the paper trail —
`randomized_hte` requires a `validation_ref`, `modeled_hte` requires an
`identification` note, `expert_assumption` requires a `tau_basis`
(`investment_schema.py` fails the build otherwise).

Why mechanical rather than judgment: CausalDS (arXiv 2607.08093) benchmarked
frontier LLM agents on exactly this workflow and found the two weakest axes
are (a) abstaining on non-identifiable estimands (56-75% even for frontier
models) and (b) interval calibration — nominal 95% ATE intervals covered only
20-71% empirically. Both are therefore build-time checks in this repo, not
things the analyst (human or model) is trusted to remember: the abstention
contract above, and the interval-coverage gate in `hte_core.py`
(`min_interval_coverage`) that refuses the "validated" badge to any model
whose own uncertainty intervals fail to cover reality on holdout.

## Failure Modes

| Failure | Smell | Fix |
|---------|-------|-----|
| Costume ranges | Table full of "X–Y" with no formulas | Delete; re-derive or mark Missing |
| Midpoint laundering | Range inputs, point outputs | Propagate intervals |
| Benchmark promotion | "Industry CPC is 0.8 so our CAC is…" presented as local | Re-tag Assumed; cap verdict at undetermined |
| Completeness theater | Every cell filled, zero Missing entries | If a real project has no unknowns, the registry is lying |
| Sensitivity omitted | Conclusion stated without overturn conditions | Add table; rewrite thesis to name flip conditions |
