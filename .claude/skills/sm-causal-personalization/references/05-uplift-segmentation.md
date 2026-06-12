# 05 · Uplift Segmentation

## When to Use

When explaining to stakeholders "why we're not targeting high-conversion users";
when building a user targeting strategy; when a team is treating churn-risk
segments as uplift segments.

## The Four Quadrants (communication tool, not a decision mechanism)

Classified by "would buy without marketing × would buy with marketing":

| | Buys with marketing | Does not buy with marketing |
|---|---|---|
| **Would buy anyway** | **Sure things**: marketing is pure waste — coupon is margin gifted away | **Sleeping dogs**: marketing makes them worse — negative incremental effect |
| **Would not buy without** | **Persuadables**: the only people worth targeting | **Lost causes**: unreachable no matter what |

**Scope of use**: the four quadrants are for stakeholder communication and
storytelling, not for live targeting decisions. Live decisions use continuous
τ̂(x) − cost + budget constraint (ref 06). The reasons:

- The four types are latent (unobservable at the individual level); they can
  only be approximated by τ̂(x)'s continuous distribution.
- Hard classification at a threshold discards magnitude information (τ̂ = 1%
  and τ̂ = 8% are both "persuadable" but have completely different budget
  priority).

## The Ascarza Lesson: Risk ≠ Rescuable

Ascarza (2018) ran experiments in two real retention programs and found that
**the highest-churn-risk users and the users who responded best to intervention
overlapped by less than half**. Targeting by "churn probability" (the industry
default) was significantly worse than targeting by uplift — high-risk users
contain many lost causes (nothing retains them) and even sleeping dogs
(reminding them is what prompts them to cancel).

This is the most persuasive slide for executives:
**"The people most likely to churn" and "the people where retention action is
most effective" are two different groups.**

The same logic applies directly to: high purchase probability ≠ coupon has
incremental effect; high win probability ≠ discount is necessary (B2B version
→ ref 10).

## Sleeping Dogs: The Most Overlooked Segment

- **Signal scenarios**: repurchase reminders that prompt "oh, I'm still
  subscribed to this?" reactions; clearance pushes that erode brand perception;
  high-frequency outreach triggering unsubscribes; exposing price-sensitive
  users to anchor prices
- **Detection difficulty**: τ(x) < 0 requires **larger samples** to detect
  (negative effects tend to be smaller in magnitude and sparser) and often
  surfaces only in the **long run** (unsubscribes, brand fatigue → ref 08)
- **Strategy**: users with significantly negative τ̂ → add to a "do-not-disturb"
  list; review periodically using GCG data

## Step-by-Step

1. Take τ̂(x) and confidence intervals from ref 04.
2. **For leadership**: draw the four-quadrant diagram + τ̂ distribution
   histogram, highlighting what share of the current policy's spend lands on
   sure-things. (This number is usually the most striking figure in the deck.)
3. **For live system**: do not assign labels; feed continuous τ̂ scores directly
   into policy optimization (ref 06).
4. Pull users with significantly negative τ̂ → do-not-disturb list + review
   mechanism.

## Common Failure Modes

- **Using propensity segments as uplift segments**: "high-intent audience" is
  the highest concentration of sure-things — increasing spend on them is the
  canonical anti-pattern
- **Running four-quadrant labels in production**: discards magnitude, mislabels
  users near thresholds
- **Ignoring sleeping dogs**: insufficient sample to detect negative effects →
  assumed they don't exist; long-term list destruction
- **Segments fixed forever**: τ(x) changes with lifecycle; last quarter's
  persuadable is this quarter's sure-thing

## Acceptance Checklist

- [ ] Stakeholders understand "risk / intent ≠ incrementality"
      (Ascarza one-pager delivered)
- [ ] Live targeting uses continuous τ̂; four-quadrant appears only in reporting
- [ ] Do-not-disturb list built with review cadence
- [ ] Segments refreshed on model retraining schedule

## Literature

- Ascarza (2018, JMR) "Retention Futility: Targeting High-Risk Customers Might
  Be Ineffective" — the core reference for this section
- Radcliffe & Surry (2011) "Real-World Uplift Modelling with Significance-Based
  Uplift Trees" — one origin of the four-quadrant taxonomy
- Hitsch, Misra & Sanders (2024, QME) "Heterogeneous Treatment Effects and
  Optimal Targeting Policy Evaluation" — causal framework for targeting policy
  evaluation
