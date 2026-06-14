# 02 · Treatment Design & Action Library

## When to Use

When designing marketing actions, creatives, or coupons; when AI-generated
variants outpace your ability to test them; when a model "isn't learning
anything" and you suspect the action definition is the problem.

## Core Principle

**Poorly defined treatments produce unlearnable models.**
"Send a marketing message" is too coarse.
"30%-off coupon + urgency framing + WeChat service account + 48-hour window"
is a learnable action.

## Which Force Does the Treatment Move? (mechanism before card)

A treatment produces *incremental* lift only when it shifts the balance of
forces acting on one person's decision. Four forces (JTBD framing, recast
causally):

| Force | Pulls them | What a treatment does to it | Effect on τ(x) |
|-------|-----------|-----------------------------|----------------|
| **Push** — pain with the status quo | toward buying | name / sharpen the pain | raises τ where the pain is real but unspoken |
| **Pull** — attraction of the product | toward buying | demonstrate the specific benefit | raises τ where the benefit is *not yet known* — not where it's already obvious |
| **Habit** — inertia of current behavior | against buying | lower switching effort (trial, migration help) | reducing it raises τ; ignoring it wastes spend on the immovable |
| **Anxiety** — fear of the new choice | against buying | reduce it (proof, guarantee, easy returns) — or, badly, inflate it | reducing it raises τ; *manufacturing* it (fake scarcity) can make τ **negative** |

**The discipline**: every treatment card names the force it moves *and the
segment for whom that force is currently unsettled*. A coupon shown to someone
whose Pull is already maxed (brand-searcher, repeat buyer) moves no force — it
is a discount handed to a sure-thing: τ ≈ 0 and negative incremental margin.
The same coupon shown to someone with high Push but high Anxiety (wants it,
fears the commitment) moves the Anxiety force and can produce real lift.

This is the mechanism vocabulary behind the Causal Activation Reviewer's
core question (ref 14: "response to this action" vs "purchase propensity").
Push / Pull / Habit / Anxiety is how you *state which lever* the treatment
pulls; the reviewer then tests whether that lever is real.

**Where the force comes from**: source it from real customer voice (ref 00b),
not from desk intuition. Buyers name their own Push, Pull, Habit, and Anxiety in
reviews and threads — mine and weight them by prevalence. A `force_targeted`
value that was guessed is a guess with a yaml schema around it. Voice is
`Hypothesis`-grade: it tells you which force to aim at; only a holdout tells you
whether aiming there produces lift.

## Treatment Card Template (one card per action in the library)

```yaml
treatment_id: T-2026-031          # versioned; any dimension change = new ID
force_targeted: Anxiety           # Push / Pull / Habit / Anxiety — which force this moves (capitalized; distinct from push channel)
force_unsettled_for: high-Push users who haven't bought (fear of commitment)  # the segment where that force is still in play
channel: WeChat service account   # push / SMS / email / WeChat / outbound call / ad
incentive: 30%-off, cap ¥30, valid 48h
content: urgency-framing copy     # messaging frame, tone, length
timing: 2h after add-to-cart without checkout
frequency_cap: ≤2 same-type actions within 7 days
cost: channel_cost(¥0.05) + coupon_value × expected_redemption_rate
audience_constraint: exclude users with complaint in last 30 days
status: live / in-experiment / retired
```

## Decision Tree

```
How granular should actions be?
├─ Few combinations (<20 arms) → test each arm independently (standard multi-arm)
├─ Exploding combinations (channel × coupon × copy × timing)
│   ├─ Interactions likely between dimensions → factorial design
│   └─ Variants mainly differ in creative / copy → treatment featurization (see below)
└─ LLM continuously generating new variants → treatment featurization + arm count cap
```

## The LLM-Era Treatment Space Explosion

When creative production cost approaches zero, **the bottleneck shifts from
"making creatives" to "measurement bandwidth."** Testing each variant
independently requires linearly growing sample. Solutions:

1. **Treatment featurization**: model effect as a function of action attributes,
   τ(x, z) where z = (discount_depth, channel, copy_type, urgency_level, …).
   New variants don't need to be tested from scratch — interpolate in attribute
   space and validate with small traffic.

2. **Hierarchical models / partial pooling**: similar actions share statistical
   strength, giving usable estimates even with small per-variant samples.

3. **Cap concurrent live arms**: the action library can be large; the number of
   arms simultaneously in experiment should be bounded (heuristic: each arm
   should reach the power-required sample within 2–4 weeks — run
   `scripts/power_analysis.py`).

4. **LLM-as-judge for pre-screening only**: LLM can filter obviously inferior
   or policy-violating variants. LLM scores are not evidence of causal effect.
   All variants must pass through experiment before launch. (Red line → ref 09.)

5. **LLM embeddings as treatment features (cheapest LLM integration)**: rather
   than routing the LLM into the decision loop, encode each variant's text
   as an embedding vector and include it in z. Standard meta-learners then
   learn which embedding dimensions drive uplift. New LLM-generated copy slots
   into the same model at prediction time. Cost: one embedding call per variant
   at card creation, not at serving time.

6. **AgentA/B simulation as pre-screening** (pilot evidence, not launch
   authorization): simulate two-agent conversations (agent=treated user vs
   agent=control user) to rank variants before committing experiment traffic.
   Screening gate only — does not replace holdout. LLM simulation results
   are pre-screening evidence; they are not valid for launch authorization
   (→ ref 09 AI hard lines).

## Defining the Control Group (the most error-prone detail)

- **"No action" vs "placeholder content" are two different controls**: the
  former measures the full effect of the action (including the act of reaching
  out); the latter measures only content differences. Choose deliberately.
- Control group users must be **reachable but randomly withheld** — using
  "users with no phone number" as control is classic confounding.
- Controls must be immune to **all similar actions**, not just this campaign
  (cross-campaign contamination is a persistent problem without global
  frequency control → ref 03 GCG).

## Creator / KOL Selection as Treatment Design

A creator *is* a treatment: the post is the content, the creator's audience is
the channel, and the creator's credibility is the mechanism. So a creator gets a
treatment card and names the force it moves — usually **Anxiety** (a trusted face
reduces fear of a new or expensive product) or **Pull** (a demonstration makes a
non-obvious benefit concrete). A creator who moves no force for the target
segment is reach bought at a CPM, not a treatment.

**Score the archetype before the person.** Decide the *kind* of creator the
segment's trust and proof needs demand (domain expert / peer / aspirational /
utility reviewer), then score candidates against that archetype — not the other
way around. Picking a creator first and reverse-justifying the fit is how budget
ends up following follower count instead of mechanism.

**Score on evidence, not vanity:**
- Audience–segment overlap (a *proxy* — label it as one)
- Proof / trust match to the specific force being moved
- Platform relevance to where the segment actually decides
- Brand-safety screen — a pass/fail gate, not a score
- Budget as a **range**, never a guaranteed CPA

**Hard line — follower count ≠ influence ≠ incrementality.** Reach, engagement
rate, and even a creator's past "conversions" are correlational; they do not
prove this creator caused incremental buyers for *your* product. Creator fit is
`Hypothesis`-grade (ref 00b): it tells you whom to pilot, not whom to scale. The
only thing that promotes a creator to Sourced is a **creator pilot with a holdout
or geo-control** (ref 03) — matched markets / audiences with and without the
campaign, read on incremental conversion, not on the creator's own dashboard.
Follower-weighted shortlists enter the experiment queue; they never go straight
to a contract.

## Step-by-Step

1. Write all existing actions as treatment cards; version and register them.
2. AI generates variants → auto-populate card fields (structured attributes) →
   LLM pre-screen → enter testing queue.
3. Select experiment structure per decision tree
   (independent arms / factorial / featurized).
4. Tag each action with cost; feeds into policy optimization (ref 06).

## Common Failure Modes

- **Treatment definition drift**: copy or coupon value changed mid-experiment —
  pre/post data is incomparable; the entire experiment is void
- **No versioning**: at analysis time you can't reconstruct what users actually
  received
- **Control group contamination**: control users touched by another team's
  campaign (requires global frequency control — see ref 03 GCG)
- **AI declares effective**: "LLM rates this copy better" used as launch
  justification — LLM judges text quality, not causal effect
- **Confounded dimensions**: changed channel and copy simultaneously —
  effect attribution is impossible
- **Treatment moves no force**: the action amplifies a Pull that is already
  maxed (coupon to a brand-searcher, reminder to a repeat buyer) — high
  attribution, zero increment. If the card cannot name a force *and* a segment
  for whom it is unsettled, expect τ ≈ 0.
- **Anxiety-inflation as the only mechanism**: the treatment works solely by
  manufacturing urgency / scarcity. This raises the Anxiety force, which can
  flip τ negative (lower conversion, higher post-purchase churn) and trips the
  red-team (ref 09 dark patterns).
- **Creator chosen on reach, not mechanism**: a high-follower creator whose
  audience already buys (Pull maxed) — high views, zero increment. Follower
  count is not a force; a creator dashboard is observational, not a holdout.

## Acceptance Checklist

- [ ] Every action has a treatment card with cost and version number
- [ ] Control group definition explicit (no-action vs placeholder); immune to
      similar actions
- [ ] Concurrent live arms ≤ measurement bandwidth
      (validated via `power_analysis.py`)
- [ ] LLM-generated variants go through "pre-screen → experiment" queue,
      not directly to launch
- [ ] Dimensions orthogonal: one dimension changed at a time, or explicit
      factorial design
- [ ] Every card names the force it moves (Push / Pull / Habit / Anxiety) and
      the segment for whom that force is currently unsettled; no card whose
      sole mechanism is manufactured Anxiety
- [ ] Any creator / KOL action scored against a trust-proof archetype first,
      budgeted as a range, and entered as a holdout / geo pilot — follower count
      never used as proof of incrementality

## Literature

- Box, Hunter & Hunter, *Statistics for Experimenters* — factorial design
- Gelman & Hill, *Data Analysis Using Regression and Multilevel/Hierarchical
  Models* — partial pooling
- Amazon Science: causal contextual bandits series — treatment featurization
  in industry
- Pattern credit: the archetype-first creator scoring adapts the "score-kol-fit"
  (S06) move from the GTM-Master skill suite (alexwang91/gtm-master), re-grounded
  here so creator fit stays Hypothesis-grade until a holdout / geo pilot proves
  incrementality — follower count is never proof.
