# 13 · Product-to-Country Pipeline (7 stages, may terminate early)

## Purpose

Turn "user gives a product + market" into a decision memo (ref 12). The
pipeline's defining property: **it is allowed to stop.** A pipeline that
always produces a full media plan regardless of what the data says is a
template, not an analysis — and readers can smell the difference.

```
Stage 1  Evidence pull        prices, platforms, competitors — all with URL+date
Stage 2  Unit economics       pure math: margin → CAC ceiling → sensitivity
Stage 3  Channel screen       benchmark ranges vs ceiling → viable / not-viable /
                              undetermined
         ── POSSIBLE TERMINUS: if nothing is viable or undetermined-with-a-path,
            emit the short report: "don't spend; here are the levers" ──
Stage 4  Dimension generation D dimensions ONLY for surviving channels (ref 14)
Stage 5  Adversarial review   independent pass; immutable challenges (ref 14)
Stage 6  Test design          prediction / kill line / decision date + power calc
Stage 7  Render               provenance-validated config → generate_report.py
```

The stage order is the argument order: nothing downstream may run before its
upstream gate. Dimension work for a channel that fails the screen is deleted
effort *and* credibility damage.

---

## Stage 1 — Evidence pull

Collect, each with URL + access date (→ `facts` + `numbers` as **sourced**):

1. Local retail price(s) — actual listings, noting the spread across SKUs/retailers
2. Dominant retail platforms and price-comparison sites for the market
3. Direct competitor products and price positions
4. Structural demand facts (e.g., "ISPs bundle free routers" — the kind of fact
   that caps the addressable market)
5. Local compliance constraints on claims (health, speed, finance)

Anything not obtainable goes into the registry as **missing** with
`needed_from` + `cost_to_get` — not as a guess. User-supplied inputs (margin,
budget envelope) register as **assumed** with basis.

## Stage 2 — Unit economics

Pure derivation, zero new assumptions beyond declared ones:

```
unit_margin = price × margin_rate
cac_ceiling = unit_margin × cac_share_of_margin   (share itself is a declared assumption)
```

Then the **sensitivity table**: for each assumption, what change flips the
conclusion, ranked. This ranking becomes (a) the thesis's overturn conditions,
(b) the sort order of the Missing ledger, (c) the verification order in
stage 6. Low-ticket products live or die here: a 60 RON unit margin is itself
the report's central finding.

## Stage 3 — Channel screen (the gate that may end the report)

For each candidate channel, attempt `CAC = cost-per-touch ÷ conversion-per-touch`
with whatever provenance is available, and apply the benchmark asymmetry
(ref 16): benchmarks may prove **not-viable**, never **viable**.

| Verdict | Meaning | Downstream |
|---------|---------|-----------|
| viable | local data shows CAC < ceiling | proceeds to stage 4 |
| undetermined | interval spans ceiling, or inputs missing | proceeds ONLY as a data-acquisition action |
| not-viable | best case still fails the ceiling | one line in rejected options |
| role-only | non-acquisition role (objection-answering content, proof asset) | small envelope, no CAC claim |

**Termination rule**: if no channel is viable and no undetermined channel has a
cheap data path, stop. Emit the short report (ref 12): verdict no-go, the math,
the levers, the Missing ledger. This is a complete, successful deliverable.

## Stage 4 — Dimension generation (survivors only)

Run ref 14's generation protocol per surviving channel. Expect few dimensions —
quality over coverage. The v1 failure mode was 32 dimensions for an unscreened
channel list: maximal surface, zero verified depth.

## Stage 5 — Adversarial review

Independent pass per ref 14. Input: the data and the screen — **not** the
recommendations (the reviewer must not anchor on what the analysis wants).
Output: immutable challenges with status; `open-blocking` challenges stamp
dependent actions in the report. Standard library: sure-thing, deal-seeker,
correlation≠mechanism, proxy-reality, fatigue/sleeping-dog, compliance,
market-ceiling.

## Stage 6 — Test design

Every surviving action gets the three-piece set:

```
Prediction:    falsifiable, with a number and a direction
Test:          duration / spend / cell structure; power_analysis.py for sample size
Kill line:     the result that declares the hypothesis dead (numeric, dated)
Decision date: when this line must become Sourced or be declared dead
```

Plus a decision calendar: the single date when the go/no-go re-evaluation
happens, named in the memo's checkpoint decisions.

## Stage 7 — Render

Assemble the config (schema: `examples/ax3-romania-config.json`), then:

```bash
python scripts/generate_report.py --config config.json --validate-only   # must pass
python scripts/generate_report.py --config config.json --output report.html
```

Build failure = a number broke the provenance contract. Fix the analysis,
not the validator.

---

## Failure modes

| Failure | Smell | Fix |
|---------|-------|-----|
| Template completeness | Full 6 sections for a product whose math died in stage 2 | Use the terminus; short report |
| Screen skipped | Dimensions/heatmaps for channels never tested against the ceiling | Re-run stage 3; delete unearned detail |
| Costume numbers | Play tables with CAC/ROI ranges and no formulas | Ref 16; registry or deletion |
| Reviewer anchoring | Challenges that read like endorsements | Stage 5 sees data, not recommendations |
| No terminus fear | Analyst pads the report to justify the effort spent | The short report IS the deliverable; say so |
