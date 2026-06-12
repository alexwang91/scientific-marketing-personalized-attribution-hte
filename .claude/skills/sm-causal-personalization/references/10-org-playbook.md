# 10 · Organizational Rollout Playbook (Marketing + Sales)

## When to Use

When methodology needs to land in a real organization; when asked "how do the
marketing / sales teams work with this?"; when KPIs are in conflict; when
planning the rollout roadmap.

---

## A. Marketing Playbook (toC: coupons / CRM / lifecycle)

### Three Foundational Infrastructure Pieces

1. **GCG institution** (ref 03): 1–5% permanent global control group +
   global frequency-control system enforcing it. Without frequency control, GCG
   is a document policy, not a real one.

2. **CDP / journey orchestration platform** (Braze / Iterable / custom):
   this is the deployment layer for NBT policy. π(x) output → orchestration
   platform executes the touch → events flow back to the data warehouse.
   Propensity logs must be instrumented at the orchestration layer, not
   retrofitted.

3. **Triggered > batch**: triggered campaigns (add-to-cart abandonment, pre-
   churn signals) have naturally well-defined treatments (ref 02). Start uplift
   in triggered scenarios before touching large-batch sends.

### Collaboration with Creative Teams

The treatment library (ref 02) is co-owned by data and creative: creative
supplies variant structure and messaging frameworks; data supplies measurement
bandwidth and conclusions. AI-generated variants enter the same
"pre-screen → experiment" pipeline. Creative's role shifts from "production
capacity" to "strategy and brand gatekeeping."

### KPI Restructuring (the root of organizational resistance)

- Channel teams KPI'd on "conversion volume" will always resist excluding
  sure-things. Change to: **GCG-calibrated incremental conversions / incremental profit**.
- Quarterly "CRM total incrementality report" (all treated vs GCG) becomes the
  only credible department-level metric.
- Counter-intuitive messaging guide (pair with the Ascarza one-pager, ref 05):
  *"We didn't skip 20% of high-intent users — we redirected the coupons we
  were giving away to them (they would have bought anyway) to users who are
  actually persuadable. Total conversions unchanged; gross margin up by X."*

---

## B. Sales Playbook (toB: leads / discounts / ABM)

### Uplift Lead Scoring ≠ Traditional Lead Scoring

Traditional lead scoring is propensity (who is likely to close). The causal
version asks: **which leads actually close because of sales rep follow-up?**
High-score leads contain many sure-things (self-service customers who would
sign without rep involvement) and lost causes (no amount of effort closes them).

- **Experiment design**: randomize medium-low-score leads to "SDR follow-up vs
  automated nurture only"; estimate τ(x) = incremental win rate from follow-up.
- **The constraint is SDR / AE time, not budget**: the ref 06 λ* solution
  applies directly — replace c_t with rep time cost; λ* = minimum incremental
  output per hour of sales time.

### Discount Approval (the biggest margin leak)

Classic scenario: reps request discounts as insurance on every deal.
The causal question: **does this discount change the win probability, or would
this deal close anyway?**

- **Experiment**: randomize discount approval thresholds on marginal deals
  (approve / deny for deals near the boundary); estimate discount's τ(deal).
- **Live system**: embed τ̂ into the approval workflow — deals where "high
  probability of closing without discount" get an extra friction question;
  deals where "discount is a genuine swing factor" get fast-tracked.
- This is the sure-things problem in a B2B jacket. Typically the highest ROI
  single-point application in B2B causal personalization.

### ABM Experiment Discipline

- Account-level treatments (executive dinners, custom content, dedicated POC)
  → **account-level cluster randomization** (ref 03). Contacts within an
  account communicate with each other; individual randomization guarantees
  contamination.
- Account samples are small by nature → paired randomization (match on
  industry × size) + continuous outcome variable (pipeline value, not binary
  won/lost) to maximize power.
- Sleeping dogs, B2B version: prospects who disengage or blacklist the brand
  after high-frequency SDR outreach. Outbound call / email frequency must be a
  guardrail.

### CRM Data Hygiene (the data-engineering prerequisite on the sales side)

Activity records (who was contacted, when, by which channel) are almost never
complete without systematic instrumentation. Missing activity records → missing
treatment logs → everything downstream fails. **Automate CRM activity capture
(call / email logging) before any modeling work.**

---

## C. Rollout Roadmap (anti-skip; maps to L1→L2→L3)

```
Phase 0 (months 1–2): Log instrumentation + propensity logging + GCG launch
                       + governance pre-check (ref 09)

Phase 1 (L1, months 3–6): First uplift analysis on one triggered-campaign
  scenario. Deliver "share of current spend landing on sure-things" report.
  Use this number to secure resources for Phase 2.

Phase 2 (L2, months 6–18): Offline policy + OPE + dual-holdout launch process.
  Scale to 3–5 scenarios.

Phase 3 (L3, enter only if all four ref-07 criteria are met)
```

**Organizational prerequisites**: from Phase 1, one causally literate analyst
permanently embedded in the business team (not borrowed). From Phase 2, data
engineering productizes propensity logging and the experiment platform.
Leadership aligned via quarterly incrementality reports; otherwise KPI conflict
kills the project in Phase 2.

## Common Failure Modes

- **Model first, logs second**: modeling is done; 40% of treatment records are
  found missing; rebuild from scratch.
- **Pushing uplift without changing KPIs**: channel team overrides policy
  output by hand; votes with their feet.
- **Borrowed analyst support**: analyst doesn't know the business context;
  business team doesn't trust the black-box scores; mutual attrition.
- **Skipping Phase 1**: no "waste percentage" report → no resource for Phase 2
  → project dies in planning.

## Acceptance Checklist

- [ ] GCG + frequency control + propensity log live before any modeling
- [ ] KPI includes incremental metric; quarterly incrementality report
      institutionalized
- [ ] Sales side: CRM activity auto-logging complete; discount approval
      integrates τ̂ friction question
- [ ] ABM experiments use account-level cluster randomization
- [ ] Current rollout phase documented; next-phase entry criteria team-aligned

## Literature

- Ascarza (2018, JMR) — the one-pager for executives on "risk ≠ rescuable"
  (ref 05)
- Hitsch & Misra (2018) "Heterogeneous Treatment Effects and Optimal Targeting
  Policy Evaluation" — profit-lens targeting
- Braze Global Control Group documentation and similar CDP vendor holdout
  guides — operational reference
