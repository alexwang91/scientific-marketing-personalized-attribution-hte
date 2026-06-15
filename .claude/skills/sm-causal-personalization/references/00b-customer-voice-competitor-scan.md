# 00b · Customer-Voice & Competitor Scan (where the forces and dimensions come from)

## When to Use

Right after the Move-1 cell characterization in ref 00, and before treatment
design (ref 02) or dimension generation (ref 14). Use it whenever you are about
to write down a Push/Pull/Habit/Anxiety force, a D dimension, or a competitor
claim and you notice the source is your own intuition rather than a real buyer.

This reference answers a question the rest of the skill assumes but never sources:
**where do the four forces and the candidate dimensions actually come from?** The
honest answer is *real customer voice*, mined and weighted — not invented at the
desk.

## Why This Exists (the gap it fills)

ref 02 names the four forces (Push, Pull, Habit, Anxiety). ref 14 generates and
challenges D dimensions. Both are only as good as their inputs. A treatment card
whose `force_targeted` was guessed is a guess with a yaml schema around it.

Real buyers state the forces in their own words, for free, at scale:

| In a review / thread they say… | Force | What it seeds |
|--------------------------------|-------|---------------|
| "dies after a day, I'm done charging it nightly" | **Push** (pain with status quo) | a treatment that names the pain; a battery-anxiety dimension |
| "finally I can track swims without taking it off" | **Pull** (specific benefit) | a benefit-demonstration creative for the segment that doesn't know this yet |
| "too lazy to migrate off Apple Health" | **Habit** (inertia) | a migration-help treatment; or a suppression flag (immovable) |
| "scared it won't be accurate / returns are a hassle" | **Anxiety** (fear of switching) | a proof / guarantee / easy-return treatment |

Competitor reviews are doubly useful: a rival's *one-star* reviews are your Pull
and your displacement wedge; a rival's *five-star* reviews are the Habit you must
overcome.

## The Hard Line (this is what makes it ours, not a sentiment dashboard)

**Customer voice is `Hypothesis`-grade evidence. It generates forces and
dimensions to TEST; it never proves incrementality.**

A complaint with 5,000 upvotes proves the pain is *widespread* — it is strong
evidence about prevalence. It says **nothing** about whether a treatment aimed at
that pain produces incremental lift. That still requires a holdout (ref 03). The
failure mode this line prevents: "users clearly hate the battery, so a
battery-focused campaign will work" — skipping straight from voice to launch,
which is exactly the attribution-without-causation error the whole skill exists to
stop.

Every artifact produced here carries the `Hypothesis` label (ref 15 Rule 2) and
enters the pre-screen → experiment queue (ref 02), never the launch path.

## Move A — Resolve the listening posts

Before searching, resolve *where this category's buyers actually talk* — it
differs by cell (ref 00 Axis 6, cultural specificity). Do not default to your
home market's platforms.

- **Keyless public sources** (usable directly): Reddit (`/r/<sub>` + comments),
  Hacker News, GitHub issues (for technical/dev products), app-store and
  marketplace reviews, the local price-comparison site's review section (ref 00
  thread C/D).
- **Web-search-reachable**: forums, YouTube review transcripts, local-language
  communities, news comment sections.
- **Resolve the entities first**: which subreddits, which hashtags, which local
  forums, which competitor SKUs to pull reviews for. A wrong handle returns
  confident noise.

> Borrowed from last30days-skill: rank by **engagement, not recency or SEO**. A
> 2-year-old complaint with 5,000 upvotes outweighs ten fresh low-engagement
> posts. Engagement is a prevalence proxy — and prevalence is the only thing voice
> legitimately measures.

## Move B — Extract into the skill's own schema

Do not produce a "brief." Produce structured inputs the downstream references
already consume. For each salient theme:

```yaml
voice_item:
  quote: "dies after a day, I'm done charging it nightly"   # verbatim, translated if needed
  source: reddit r/<sub>, 5.2k upvotes                       # platform + engagement
  prevalence: high / medium / low                            # from engagement weight
  force: Push                                                 # Push / Pull / Habit / Anxiety (ref 02)
  seeds_dimension: "battery-anxiety segment"                 # candidate D dimension (ref 14) or ""
  competitor: own / <rival SKU>                              # whose product this is about
  provenance: Hypothesis                                     # ALWAYS — never Evidence
  test_to_confirm: "holdout on battery-pain creative vs control"  # how voice becomes proof
```

Aggregate the items into three outputs:

1. **Force map** — the four forces populated with real quotes + prevalence,
   feeding `force_targeted` / `force_unsettled_for` on treatment cards (ref 02).
2. **Candidate D dimensions** — themes that recur across many high-engagement
   posts, handed to ref 14's generation gate (which then challenges them; voice
   prevalence is *not* a free pass through the reviewer).
3. **Competitor positioning map** — who wins on which job, from their own
   reviews; one-star themes = your wedge, five-star themes = the Habit to beat.

## Move C — Anti-persona signals (feed governance, don't act unilaterally)

Voice also surfaces who to *leave alone*. Two kinds, routed to two owners:

- **Won't-move signal** (effectiveness): a segment whose reviews show their Pull
  is already maxed (devoted brand loyalists, repeat buyers) → candidate
  suppression for τ ≈ 0 → route to Policy + Reviewer (ref 14 Step 6).
- **Must-not-move signal** (compliance): voice revealing a vulnerable or
  protected-attribute-correlated group → route to ref 09; never encode silently.

Voice can *propose* an anti-persona; it cannot *approve* one. Approval runs the
discriminatory-exclusion check (ref 09).

## Common Failure Modes

- **Voice → launch (the cardinal sin)**: treating a popular complaint as proof a
  campaign will work. Voice sizes the pain; the holdout sizes the lift.
- **Home-market platform transfer**: scanning Reddit/X for a market that actually
  talks on a local forum or messaging app → confident, unrepresentative findings.
  This is the ref 00 Move-2 transfer error in a new disguise; log it in the same
  ledger.
- **Vocal-minority = majority**: the loudest reviewers are not the median buyer.
  Engagement measures prevalence *among the engaged*, which skews to extremes.
  State this when prevalence drives a decision.
- **Sentiment laundering**: an LLM "rates the sentiment 82% positive" presented as
  a number. Sentiment scores are not measurements; they get no provenance state
  above `Hypothesis`, and percentages implying precision are banned (ref 16).
- **Astroturf / review fraud**: incentivized or planted reviews. Cross-source
  corroboration (a theme appearing organically across independent platforms)
  raises confidence; a single-platform spike does not.
- **Competitor set drift**: pulling reviews for globally-famous rivals not sold
  locally. *Competitors not sold locally are not competitors* (ref 00 thread C).

## Acceptance Checklist

- [ ] Listening posts resolved for THIS cell, not defaulted from home market
- [ ] Findings ranked by engagement (prevalence proxy), not recency
- [ ] Every voice item carries a force tag, a competitor tag, and `Hypothesis`
      provenance — no item labeled Evidence
- [ ] Each force in the map has at least one verbatim quote + prevalence, or is
      explicitly marked `undetermined`
- [ ] Every voice-seeded dimension carries a `test_to_confirm` and is handed to
      ref 14 for challenge (not auto-retained)
- [ ] Anti-persona signals routed to Policy/Reviewer (won't-move) or ref 09
      (must-not-move) — none acted on unilaterally
- [ ] Cross-source corroboration noted where a theme drives a budget decision
- [ ] Transfer-assumption ledger (ref 00 Move 2) updated with any platform or
      competitor-set assumptions made here

## Integration with the rest of the skill

- **ref 00** — runs as a sub-move inside Stage 0; shares the transfer-assumption
  ledger. Cell characterization (Move 1) tells you *where* buyers talk (Axis 6).
- **ref 02** — the force map populates `force_targeted` / `force_unsettled_for`.
- **ref 14** — candidate dimensions enter the generation gate as inputs, then face
  the standard challenges (Challenge 8 force check); prevalence is not a bypass.
- **ref 09** — anti-persona signals route here for the discriminatory-exclusion
  check before any suppression ships.
- **ref 15 / 16** — the `Hypothesis` hard line and the ban on false-precision
  sentiment percentages are enforced as written there.

## Literature / Prior Art

- last30days-skill (mvanhorn) — the engagement-ranked, multi-source listening
  pattern this reference adapts. Borrowed: entity resolution, engagement-over-SEO
  ranking, cross-source cluster merging. **Not** borrowed: the brief-style output
  and any path from sentiment to a launch decision.
- Christensen et al., *Competing Against Luck* — Jobs-to-be-Done; the four forces
  of progress (Push / Pull / Habit / Anxiety) recast causally in ref 02.
- Voice-of-customer / review-mining literature — treat as hypothesis generation,
  not effect measurement.
