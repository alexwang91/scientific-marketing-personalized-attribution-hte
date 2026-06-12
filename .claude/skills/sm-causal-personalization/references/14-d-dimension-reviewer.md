# 14 · D Dimensions + Adversarial Review Protocol

## Purpose

Two linked protocols: how candidate targeting dimensions (D dimensions) are
generated, and how an **independent adversarial pass** challenges them — with
verdicts that have mechanical consequences in the report.

The v1 design failed because the same author generated dimensions, raised
challenges, answered them, and declared satisfaction. Self-review that always
ends in a handshake is theater. The fix is structural, not rhetorical.

---

## Part A — D Dimension Generation

A D dimension is an operationalizable targeting variable satisfying:

1. Observable before the action is taken
2. Reachable via a platform proxy in this market (keyword, behavior, category visit)
3. Mechanistically linked to a product feature or purchase barrier —
   "runners respond to GPS" is a correlation; "runners tracking route accuracy
   respond to GPS-precision claims because wrist pace-drift is their stated pain"
   is a mechanism
4. Able to change a concrete decision (creative, bid, frequency, suppression)
5. Testable for incremental effect (holdout, A/B, UTM, geo/time split)

**Gate**: ≥ 3 of 5, AND survives Part B review. Score honestly; most candidates
should fail.

**Scope rule (from ref 13)**: dimensions are generated only for channels that
survived the viability screen. 32 dimensions on an unscreened channel list is
surface without depth.

**Demographics rule**: age/gender are never standalone dimensions — only
modifiers on a behavioral proxy ("25–34 AND smartwatch-search"), and the
mechanism must explain differential *response to this action*, not differential
purchase propensity.

**Sensitive attributes**: anything requiring inference of health condition,
financial distress, protected characteristics → human compliance review before
inclusion; body-image-adjacent language defaults to excluded.

---

## Part B — Adversarial Review Protocol

### Independence requirements (the part that makes it real)

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

### Verdict states and their mechanical consequences

| Status | Meaning | Effect in report (enforced by generate_report.py) |
|--------|---------|--------------------------------------------------|
| `resolved` | Answered with data or a designed test | None |
| `open` | Unanswered, doesn't gate spend | Visible in section 4 |
| `open-blocking` | Unanswered AND a budget decision depends on it | Every action listing it in `blocked_by` renders with a **⊘ BLOCKED** stamp; the action must not receive budget until resolution |

The blocking linkage is config-mechanical: challenge `C1` is `open-blocking`
and action `T03` declares `"blocked_by": ["C1"]` → the generator stamps T03.
No judgment call at render time.

### Standard challenge library

Raise every applicable one; product-specific challenges on top.

| Challenge | Canonical question | Typical resolution path |
|-----------|-------------------|------------------------|
| Sure-thing | Would these users convert anyway? Platform attribution will claim them regardless | Holdout / low-bid control designed in from day one |
| Deal-seeker | Does this channel select people whose increment is negative after discount? | Incremental-margin guardrail arm vs no-touch |
| Correlation ≠ mechanism | Is this dimension predictive of *response to this action* or merely of purchase? | State the mechanism or demote |
| Proxy reality | Can this signal actually be bought, in this market, at what minimum audience? | Platform UI check; demote if speculative |
| Fatigue / sleeping-dog | Will frequency harm high-intent users? | Frequency cap + cooldown + no-contact arm |
| Compliance | Does targeting or creative infer a protected/sensitive attribute? | Human review; default exclude |
| Market ceiling | Does a structural fact (e.g., ISPs give routers away free) cap the addressable market below plan? | Size the ceiling before scaling claims |

### Anti-theater checks

A review pass is fake if any of these hold:

- Every challenge ends `resolved` (real projects always have open questions)
- Challenges restate the analysis's own caveats in question form
- Resolutions cite the analysis's reasoning rather than data or designed tests
- No challenge, if upheld, would change a single number in the budget

If the review changes nothing, it wasn't a review — rerun it with stricter
independence.
