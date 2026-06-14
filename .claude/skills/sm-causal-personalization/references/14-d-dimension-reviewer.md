# 14 · D Dimension Generation + Causal Activation Reviewer

## Purpose

Specify how D dimensions are generated, what qualifies them for the heatmap, and
how the Causal Activation Reviewer challenges each one before budget is allocated.

Two linked protocols: how candidate targeting dimensions (D dimensions) are
generated, and how an **independent adversarial pass** challenges them — with
verdicts that have mechanical consequences in the report.

The design failure to avoid: the same author generates dimensions, raises
challenges, answers them, and declares satisfaction. Self-review that always
ends in a handshake is theater. The fix is structural, not rhetorical.

---

## What Is a D Dimension?

A D dimension is an **operationalizable segmentation variable** that:
1. Is observable or inferable before the action is taken
2. Can be reached via a platform proxy (keyword, interest, behavior, lookalike)
3. Is mechanistically linked to a product feature or purchase barrier —
   "runners respond to GPS" is a correlation; "runners tracking route accuracy
   respond to GPS-precision claims because wrist pace-drift is their stated pain"
   is a mechanism
4. Modifies a creative, bid, frequency, or suppression decision
5. Can have its incremental effect estimated via A/B, holdout, UTM, or split report

D dimensions are **not** demographics. Age group, gender, and income are starting
hints — they only enter the heatmap when linked to a behavioral proxy that satisfies
the 5 conditions above.

**Gate**: ≥ 3 of 5, AND survives Part B review. Score honestly; most candidates
should fail.

**Scope rule (from ref 13)**: dimensions are generated only for channels that
survived the viability screen. 32 dimensions on an unscreened channel list is
surface without depth.

---

## Generation Protocol

**Step 1: Product mechanism scan**

For each product feature, ask:
> "Which type of person would respond *more* to this action because of this feature?"

Write the mechanism explicitly. "Runners respond to GPS" is not a mechanism.
"Runners who track route accuracy respond to GPS precision claims because their
current pain is pace drift on wrist-worn devices" is a mechanism.

**Name the force (mechanism vocabulary).** A mechanism is sharper when it names
*which force the action moves* for this person (ref 02): Push (an unspoken
pain), Pull (a benefit they don't yet know), Habit (switching inertia to
lower), or Anxiety (a fear to reduce). The GPS example is a **Pull** mechanism —
it works only for runners who don't *already* believe the watch is accurate.
State the force and the segment for whom it is still unsettled. A dimension
whose force is already settled (Pull maxed) is a sure-thing, not an incremental
opportunity — and is caught at Step 6 and by challenge 8 below.

**Step 2: Market path mapping**

For each mechanism, identify the local purchase path: how does this person search,
where do they compare, what channels exist to reach them?

**Step 3: Proxy validation**

For each mechanism + path, identify the reachable proxy:
- Keyword (e.g., "futoora" for running in Hungarian)
- Platform interest segment
- Content consumption signal (YouTube review viewer)
- Behavioral retargeting (cart abandon, product page visit)
- Retail category position (smartwatch category visitor on Alza)

**Step 4: Measurability check**

Is the incremental effect of targeting this proxy testable?
- A/B on creative or message
- Holdout group (no-contact arm)
- UTM + conversion tracking
- Platform lift study
- Geographic or time split

**Step 5: Sensitivity filter**

Check for:
- Body image / health language (especially weight, fitness goals)
- Age stereotyping
- Financial vulnerability signals
- Religious / ethnic targeting

Send any dimension that touches these to the Reviewer with a compliance flag before
including in the heatmap.

**Step 6: Anti-persona pass (the suppression output)**

The same scan, inverted. For each mechanism ask: "for whom is this force
*already settled*, or moving the *wrong way*?" These people are anti-personas,
and they are a first-class output of generation — not a remainder left after
targeting:

- **Pull already maxed** → sure-thing (brand-searcher, repeat buyer): suppress
  or holdout-only; never primary budget.
- **Habit immovable** → the treatment yields τ ≈ 0: suppress to save spend.
- **Anxiety-dominant where the only available lever inflates it** → compliance
  *and* negative-τ risk (ref 09): exclude.

Anti-personas feed the suppression rules (report section 15) and the policy's
do-not-target set (ref 06). Hand the list to ref 09 for the discriminatory-
exclusion check before it ships — suppressing a protected group from beneficial
offers is itself a fairness failure.

---

## Entry Gate

Dimension enters the heatmap iff ≥ 3 of 5 conditions are satisfied **and** it
passes the Reviewer with a verdict of "Retain" or "Retain (test)".

| Condition | Check |
|-----------|-------|
| Pre-deployment observable | Yes / Partially / No |
| Platform proxy exists | Yes / Estimate / No |
| Mechanism stated | Yes / Weak / No |
| Incrementality testable | Yes / Hard / No |
| Drives a decision change | Yes / Maybe / No |

Score 0/1 per condition. Threshold: ≥ 3.

---

## Full D Dimension Candidate Template

For each candidate, fill:

```
D{n}
name:          short label (≤ 5 words)
mechanism:     one sentence — why this dimension changes incremental response
proxy:         what platform signal represents this dimension locally
entry_score:   x/5 (cite which conditions pass)
reviewer_flag: none / compliance / sure-thing / ad-fatigue / low-proxy / weak-mechanism
verdict:       Retain / Retain (test only) / Demote S / Suppression only / Delete
resolution:    resolved / open / open-blocking
```

---

## Causal Activation Reviewer

### Role

The Causal Activation Reviewer is a **built-in adversarial function**. It runs as
part of D dimension processing and asks the hardest question about each proposed
H or T cell:

> "Why do you believe this dimension has *positive incremental effect* rather than
>  merely high correlation with purchase?"

### Independence Requirements (the part that makes it real)

1. **Separate pass.** The review runs as its own step — ideally a separate
   subagent; at minimum a separate prompt in a fresh context. Its input is the
   *evidence and the screen* (facts, registry, channel verdicts). It does
   **not** receive the recommendations, so it cannot anchor on what the
   analysis wants to conclude.
2. **Immutable output.** Challenges are quoted verbatim in the report. The
   analysis may *respond*; it may not edit, soften, or summarize the challenge.
3. **Resolution requires data.** A challenge moves to `resolved` only by
   pointing at a sourced fact, a derivation, or a designed test with a kill
   line. Rhetorical reassurance does not resolve anything.
4. **Open is a normal terminal state.** A challenge with no current answer
   stays open in the published report. An unresolved question displayed
   honestly builds more trust than ten resolved softballs.

### Five Verdict Types

| Verdict | Meaning | Heatmap treatment |
|---------|---------|-------------------|
| Retain | Evidence or mechanism is strong; proxy is deployable; risk is manageable | H or T as proposed |
| Retain (test only) | Plausible mechanism but weak proxy or unvalidated effect | Downgrade to T or S |
| Demote S | Proxy too broad or incrementality uncertain | Downgrade to S |
| Suppression only | Dimension identifies users to *exclude*, not target | Mark A in heatmap |
| Delete | Mechanism not stated; proxy is vanity metric; compliance risk | Remove from heatmap |

### Resolution Status States

Each challenge carries a resolution status in addition to the five verdict types
above. The verdict determines heatmap treatment; the resolution status determines
report rendering (enforced by generate_report.py).

| Status | Meaning | Effect in report |
|--------|---------|-----------------|
| `resolved` | Answered with data or a designed test | None |
| `open` | Unanswered, doesn't gate spend | Visible in section 4 |
| `open-blocking` | Unanswered AND a budget decision depends on it | Every action listing it in `blocked_by` renders with a **⊘ BLOCKED** stamp; the action must not receive budget until resolution |

The blocking linkage is config-mechanical: challenge `C1` is `open-blocking`
and action `T03` declares `"blocked_by": ["C1"]` → the generator stamps T03.
No judgment call at render time.

### Standard Challenge Library

The Reviewer always raises every applicable one; product-specific challenges on top.

**1. Sure-thing check**

> "Are these users buying already regardless of the action? Would a holdout show zero
>  incremental lift? Platform attribution will claim them regardless."

*Most common for*: brand keyword, retargeting, existing customer base.
*Resolution*: Retain with holdout design mandatory; flag sure-thing risk in guardrail.
*Canonical question*: Would these users convert anyway?
*Typical resolution path*: Holdout / low-bid control designed in from day one.

**2. Correlation ≠ mechanism**

> "Is this dimension predictive of purchase (demographic correlation) or predictive of
>  incremental response to this specific action?"

*Most common for*: age groups, gender, income tiers.
*Resolution*: Retain only if a behavioral proxy is added (e.g., "25–34 AND
smartwatch-search" not "25–34").
*Canonical question*: Is this dimension predictive of *response to this action* or merely of purchase?
*Typical resolution path*: State the mechanism or demote.

**3. Platform proxy reality check**

> "Can you actually buy this signal on this platform in this market? What does it cost?
>  What is its minimum audience size?"

*Resolution*: If proxy is speculative, downgrade to T or S.
*Canonical question*: Can this signal actually be bought, in this market, at what minimum audience?
*Typical resolution path*: Platform UI check; demote if speculative.

**4. Ad fatigue / sleeping-dog**

> "For retargeting and high-frequency prospecting: is there evidence that heavy
>  exposure harms high-intent users?"

*Resolution*: Frequency cap + no-contact arm required; mark as A if no frequency
control is possible.
*Canonical question*: Will frequency harm high-intent users?
*Typical resolution path*: Frequency cap + cooldown + no-contact arm.

**5. Compliance / sensitivity**

> "Does this dimension require inferring a health condition, financial state, or
>  other protected attribute? Is the creative claim within regulatory bounds?"

*Resolution*: Retain only if the proxy is behavior-based (e.g., "health content
viewer") not inferred attribute (e.g., "overweight user").
*Canonical question*: Does targeting or creative infer a protected/sensitive attribute?
*Typical resolution path*: Human review; default exclude.

**6. Deal-seeker**

*Canonical question*: Does this channel select people whose increment is negative after discount?
*Typical resolution path*: Incremental-margin guardrail arm vs no-touch.

**7. Market ceiling**

*Canonical question*: Does a structural fact (e.g., ISPs give routers away free) cap the addressable market below plan?
*Typical resolution path*: Size the ceiling before scaling claims.

**8. Force check (mechanism synthesis for challenges 1 and 2)**

> "Which of the four forces (ref 02) does targeting this dimension assume the
>  treatment moves — and is that force still *unsettled* for this segment, or
>  already settled?"

Challenges 1 and 2 ask *whether* incremental response exists; the force check
asks *through which lever* — and a dimension that cannot name an unsettled force
fails both. Pull already maxed (brand search, repeat buyer) = sure-thing (#1);
a "force" that is really just purchase propensity = correlation (#2).

*Most common for*: brand search, warm-cart retargeting, lookalikes of converters.
*Canonical question*: Does the treatment move a still-unsettled force for this segment, or merely amplify one already maxed?
*Typical resolution path*: Name the force and the segment it's unsettled for; if none, demote to S or Suppression only.

### Anti-Theater Checks

A review pass is fake if any of these hold:

- Every challenge ends `resolved` (real projects always have open questions)
- Challenges restate the analysis's own caveats in question form
- Resolutions cite the analysis's reasoning rather than data or designed tests
- No challenge, if upheld, would change a single number in the budget

If the review changes nothing, it wasn't a review — rerun it with stricter
independence.

---

## Reviewer Output Format

The Reviewer's output is a table embedded in section 6 of the HTML report:

```
| Challenged dimension | Challenge raised | Current handling | Next evidence |
|---------------------|-----------------|-----------------|---------------|
| D7 Price compare    | Ad fatigue / deal-seeker inflation of ROAS | Primary budget with incremental margin guardrail | Discount vs proof vs no-contact comparison |
| D1 Brand search     | Sure-thing cannibalization | Low-intensity holdout mandatory | Brand keyword holdout or split bid control |
```

Followed by a **Reviewer conclusion** callout:
> "D dimensions are candidate operational variables, serving trial design and evidence
>  collection. Before entering primary budget, each must pass: deployable proxy,
>  testable incrementality, stated mechanism, no obvious compliance or margin risk."

---

## Handling Age and Gender Dimensions

Age and gender segments are **never standalone D dimensions**. They may appear in
the heatmap only as modifiers:

- "25–34 AND fitness-content viewer" (not "25–34")
- "Female AND lifestyle-watch interest" (not "Female")

Mechanism must reference why the age/gender group responds *differently to this
specific action*, not just why they might purchase.

**Demographics rule**: age/gender are never standalone dimensions — only
modifiers on a behavioral proxy ("25–34 AND smartwatch-search"), and the
mechanism must explain differential *response to this action*, not differential
purchase propensity.

---

## Compliance Dimension Rules

Any dimension that could require inferring:
- Medical condition or health risk
- Financial distress or vulnerability
- Religious belief or ethnic background
- Pregnancy or family status

→ Must be reviewed by human compliance team before heatmap inclusion. Tag as
  `Needs review` in the verification checklist.

Dimensions involving body image language ("weight loss", "slimming") must be
reviewed for local advertising standards. Default: Demote to S with strict creative
guardrails, or Delete.

**Sensitive attributes**: anything requiring inference of health condition,
financial distress, protected characteristics → human compliance review before
inclusion; body-image-adjacent language defaults to excluded.
