# 07 · Online Learning & Contextual Bandits

## When to Use

When asked "should we use a bandit?"; when actions are numerous, creatives
update frequently, and offline retraining can't keep pace.

## First, Confirm You Actually Need L3 (most teams don't)

```
□ Actions / creatives are numerous and continuously refreshed (new arms weekly)?
□ Environment is non-stationary (seasonal, inventory-driven, fast competitive response)?
□ Feedback is fast (Y observable within hours to a few days)?
□ L2 is already running smoothly (OPE, propensity logs, guardrails, dual holdout)?
```

If all four are not checked, stay at L2: offline policy + periodic retraining
+ fixed exploration traffic. Cheaper, auditable, sufficient.
**Deploying a bandit when actions are few and the environment is stable adds
complexity for no benefit.**

## What a Contextual Bandit Is

At each decision: observe context x → choose action t → observe reward r.
Goal: maximize cumulative reward while continuously exploring.

Two mainstream algorithms in one line each:

- **Thompson Sampling**: maintain a posterior distribution over each action's
  effect; sample from the posterior to choose. Simple to implement; works well
  in practice. Default choice.
- **LinUCB**: model effects as linear functions of context; select the action
  with the highest "estimated value + uncertainty bonus." Suited when the
  context-effect relationship is approximately linear.

**The fundamental value of exploration = continuous measurement bandwidth.**
Exploration traffic is automated continuous experimentation — new arms get
evaluated, drift gets detected. Bandits natively log propensity (the selection
probability), making all logs directly reusable for OPE. This is the essential
difference from hard-coded rules.

## Reward Design (the real mechanism preventing short-termism)

"Causal framework prevents chasing short-term conversion" is not a vague
claim — it requires three concrete mechanisms:

1. **Reward = incremental profit proxy, not clicks / conversions**: use the
   profit equation from ref 01; at minimum subtract coupon cost, otherwise the
   bandit will learn to give maximum coupons to everyone.

2. **Surrogate calibration**: short-term reward must be aligned to long-term
   LTV via the surrogate index (ref 08). The short-term ↔ long-term correlation
   must be reviewed quarterly.

3. **GCG cannot be retired**: within-bandit arm comparisons ≠ incrementality
   evidence — all arms are "doing marketing"; the bandit only answers "which
   action is best." Incrementality evidence always comes from bandit traffic
   vs GCG.

## Drift & Feedback Loops

- **Drift monitoring**: context distribution drift (PSI etc.); per-arm effect
  drift (rolling window vs historical); exploration fraction not compressed
  below effective threshold.

- **Feedback loops**: the policy changes the population — users who receive
  coupons regularly learn to wait (price anchor shifted by the strategy itself).
  Detection: compare baseline behavior of GCG users vs treated users' drifting
  baseline. This is another reason to keep the permanent GCG (ref 03).

- **New arm cold start**: use treatment featurization (ref 02) to give new arms
  an informed prior inherited from similar arms, rather than starting from a
  uniform prior and burning traffic.

## Step-by-Step

1. Run the "need L3" four-check list; if not all pass, go back to ref 06.
2. Write the reward function using the profit equation; Finance confirms.
3. Default: Thompson Sampling + treatment features (linear or shallow-tree
   posterior).
4. Traffic structure: GCG (1–5%) + bandit (remaining); bandit handles
   its own exploration internally.
5. Propensity logs auto-written to data warehouse (bandit naturally produces
   these; confirm the pipeline is wired).
6. Drift monitoring + guardrail auto-rollback + quarterly surrogate review.

## Common Failure Modes

- **Using within-bandit comparisons as incrementality**: "arm A is 20% better
  than arm B" ≠ "arm A has positive lift" — both could be net negative; only
  GCG reveals this.
- **Reward defined as clicks**: bandit learns clickbait + maximum discount
  within one week.
- **Exploration shut off by operations**: "exploration traffic is wasting
  money" → three months later all estimates are stale; bandit degrades to a
  frozen rule.
- **Skipping to L3 without L2 foundations**: no propensity logs, no guardrails
  — when something goes wrong, you can neither audit nor roll back.
- **Non-stationarity ignored**: updating the posterior with all historical data;
  the model is stubborn about outdated conclusions after a seasonal shift.
  Use a sliding window or discount factor.

## Acceptance Checklist

- [ ] All four "need L3" criteria checked
- [ ] Reward = profit proxy and has passed surrogate calibration
- [ ] GCG permanently maintained outside the bandit
- [ ] Propensity logs going to data warehouse; OPE reusable
- [ ] Drift monitoring, minimum exploration floor, guardrail rollback all live

## Delayed Reward: Impatient Bandits (Spotify, 2024)

The standard bandit assumes the reward signal arrives quickly. In subscription
or B2B settings, the true outcome (retention, contract renewal) arrives weeks
to months later, but you need a reward signal now.

**Impatient Bandits solution** (Spotify/Cornell, WWW 2024):

```
1. Train a Bayesian surrogate model:
     P(long_term_Y | partial_signal_at_day_k, arm, context)
   using historical complete trajectories.

2. At bandit update time (day k), impute:
     r̂ = E[Y | observed so far, arm, x]
   as the reward signal for Thompson Sampling.

3. Update the posterior on r̂, not on the eventual Y.
   When Y finally arrives, do a retrospective posterior correction.
```

**Key check**: the partial-signal model must be calibrated. At quarterly
review, compare r̂ predictions at day-k vs actual long-term Y —
miscalibration here compounds into reward-signal bias that corrupts the bandit.

This pattern generalizes to any setting where you have fast partial signals
correlated with slow final outcomes (day-7 engagement → 90-day LTV, etc.).
It is the bandit equivalent of the surrogate index in ref 08.

## Literature

- Li et al. (2010) "A Contextual-Bandit Approach to Personalized News Article
  Recommendation" — LinUCB
- Russo et al. (2018) "A Tutorial on Thompson Sampling"
- Amazon Science: causal contextual bandits series — bandits under causal
  constraints
- Agarwal et al. (2016) "Making Contextual Decisions with Low Technical Debt"
  — industrial deployment (Decision Service)
- Bompaire et al. (2024, WWW / Spotify) "Impatient Bandits: Optimizing
  Recommendations that Drive Long-Term Engagement" — delayed reward in
  production bandit systems
