# Interactive Dashboard Migration Design

## Status

Approved direction: migrate the interactive dashboard experience from
`alexwang91/Scientific-Marketing`, but render this repository's own causal
personalization content, data model, and reasoning sequence.

Date: 2026-07-04

## Goal

Add a new interactive dashboard output for the current
`sm-causal-personalization` skill.

The dashboard should preserve this repository's core logic:

1. Decision Memo
2. Unit economics and CAC ceiling
3. Channel viability screen
4. D dimensions and causal reviewer challenges
5. Channel x dimension heatmap
6. H-main breakdown
7. Execution gates and Treatment Cards
8. Budget allocation and priority plays
9. Measurement, suppression, evidence, and verification

The reference repository provides the visual and interaction pattern:

- calm operating-dashboard layout
- left rail navigation
- first-screen KPI strip
- clickable relationship graph / heatmap / budget / treatment cards
- right detail panel
- readable labels instead of naked IDs
- evidence and missing-data states shown in the UI

The reference repository does not provide the case content, examples, product
logic, or claims.

## Non-Goals

- Do not replace the current HTML report generator.
- Do not remove or renumber the existing report sections.
- Do not copy the fictional Norway dashboard data from the reference repo.
- Do not introduce live ad APIs, live web research, or dynamic platform scraping.
- Do not require external JavaScript or remote fonts for the generated artifact.
- Do not make the first screen a marketing landing page.

## Output Shape

Keep the existing report output as the default.

Add a new format switch:

```bash
python generate_report.py --config ../examples/sample-sku-en-config.json --format dashboard --output dashboard.html
python generate_report.py --config ../examples/aurora-airpurifier-category-config.json --format dashboard --output portfolio-dashboard.html
```

Accepted values:

- `--format report`: current behavior, default
- `--format dashboard`: new interactive dashboard

`--depth` remains report-specific. The dashboard always renders the core
decision cockpit. If a config lacks optional sections, it shows honest empty
states such as `Needs data`, `No budget unlocked`, or `No viable channel yet`.

## Information Architecture

### SKU / Product-Country Dashboard

Use this when `report_type` is absent or not `category_portfolio`.

Required screen sections:

1. **Overview**
   - product, market, date
   - verdict badge
   - thesis in plain language
   - top next action and top blocker

2. **Economics**
   - KPI strip from `numbers`
   - unit margin derivation
   - CAC ceiling derivation
   - sensitivity cards
   - CAC interval vs ceiling visual

3. **Channel Screen**
   - channel verdict cards
   - `viable`, `undetermined`, `role-only`, and `not-viable` states
   - click opens the channel in the right detail panel

4. **Causal Map**
   - relationship graph:
     `Product -> Economics -> Channel -> Dimension -> Treatment -> Measurement`
   - graph nodes generated from existing config arrays

5. **Heatmap**
   - channel x D dimension grid
   - score legend: `H`, `T`, `S`, `N`, `A`
   - readable labels for each dimension
   - click opens: reason, proxy, treatment, challenge, validation action

6. **Treatments and Gates**
   - cards from `actions` / treatment-like rows
   - mechanism, guardrail, test, gate, blocked-by challenge if present
   - sample-size gate when `power_analysis` is present

7. **Budget and Plays**
   - budget phases or budget rows
   - priority plays and ROI scenario ranges when present
   - no fake spend if budget is locked or missing

8. **Evidence and Verification**
   - sourced facts
   - assumption registry
   - missing ledger
   - verification checklist

### Category Portfolio Dashboard

Use this when `report_type == "category_portfolio"`.

Required screen sections:

1. **Portfolio Verdict**
   - brand, category, market
   - count of Grow / Hold / Harvest / Exit verdicts
   - strongest diagnosis and most urgent data pull

2. **Tier Map**
   - price tiers and trends
   - audience and force per tier
   - channel fit

3. **Diagnosis Lenses**
   - L1-L6 cards
   - severity, evidence grade, implication, recommendation
   - click opens right-panel detail

4. **SKU Matrix**
   - SKU verdict table / cards
   - 4P recommendations
   - Grow SKUs highlighted as handoff candidates

5. **Evidence and Gaps**
   - missing numbers from `numbers`
   - facts from `facts`
   - data pulls needed before deep SKU analysis

## Dashboard Data Contract

Introduce an internal normalized object, not necessarily persisted:

```python
DashboardData = {
    "kind": "sku" | "category_portfolio",
    "meta": {...},
    "overview": {...},
    "kpis": [...],
    "economics": {...},
    "channels": [...],
    "dimensions": [...],
    "heatmap": {...},
    "treatments": [...],
    "budgets": [...],
    "plays": [...],
    "challenges": [...],
    "evidence": {...},
    "portfolio": {...},
}
```

Rules:

- Build `DashboardData` from the current config. Do not require users to write a
  second dashboard-specific config.
- Preserve number provenance markers from `numbers`.
- Preserve claim states: `Evidence`, `Assumption`, `Hypothesis`, `Needs test`.
- Use `id + short label` in UI tags, for example `A1 Pull CPC` or `C1 sure-thing risk`.
- Missing values remain missing. They never become guessed dashboard values.

## Mapping From Current Config

### Common

- `meta` -> dashboard title, subtitle, language, market labels
- `numbers` -> KPI strip, economics, missing ledger, provenance detail panel
- `facts` -> source registry / evidence cards
- `labels` -> localized UI override where already supported

### SKU

- `decision_memo` -> overview verdict, thesis, next actions, overturn conditions
- `derivations` -> economics derivation cards
- `sensitivity` -> sensitivity cards
- `channel_screen` -> channel cards and CAC visual
- `dimensions` / `d_dimensions` style config, if present -> dimension list
- `heatmap` / `h_main` style config, if present -> heatmap and H-main cards
- `actions` -> treatment/action cards
- `rejected_options` -> rejected action panel
- `challenges` -> reviewer challenges and blocked states
- `test_plan` -> test timeline and kill lines
- `budget` / `priority_plays`, if present -> budget and plays sections
- `measurement`, `suppression`, `checklist`, if present -> verification sections

### Category Portfolio

- `price_tiers` -> tier map
- `diagnosis` -> diagnosis lens cards
- `portfolio` -> SKU verdict matrix and 4P recommendations
- `numbers` -> evidence and missing ledger
- `facts` -> source registry

## Visual System

Use the reference dashboard's operating-cockpit pattern:

- near-white or calm gray background
- white left navigation rail
- main workspace in readable bands
- right detail panel for selected item
- restrained green / amber / red / gray status colors
- cards at 8px radius or less where possible
- no decorative hero section
- no purple AI gradient palette
- no nested card stacks
- no persistent animation

Typography:

- compact executive headings
- dense but readable tables
- long message / reasoning text in wide brief cards, not narrow columns
- no negative letter spacing
- IDs never appear without a human-readable label nearby

Responsive behavior:

- At narrow widths, the right detail panel moves below the main content.
- Long labels wrap with `overflow-wrap: anywhere`.
- Heatmap supports horizontal scroll if needed.

## Interaction Model

Click targets:

- KPI card
- channel card
- relationship graph node
- heatmap cell
- treatment/action card
- budget row
- challenge card
- evidence/missing-data row
- category diagnosis lens
- SKU verdict card

Right panel displays:

- selected object title
- status / provenance / verdict
- why this matters
- linked objects
- next validation action
- risk or challenge

Search:

- Single search box filters channels, dimensions, treatments, challenges, SKUs,
  and evidence rows.

Navigation:

- Left rail anchors sections.
- Active nav updates on click and scroll.

## Implementation Design

Add implementation in small units inside
`.claude/skills/sm-causal-personalization/scripts/`.

Proposed modules:

- `dashboard_data.py`
  - converts existing config into `DashboardData`
  - no HTML rendering
  - unit-testable with dict assertions

- `dashboard_render.py`
  - renders single-file HTML from `DashboardData`
  - owns CSS and inline JavaScript
  - no config validation logic

- `dashboard_validate.py` or test helper
  - checks internal ID cross-references
  - checks heatmap shape
  - checks no leftover placeholders
  - checks budget sums only when a real budget exists

Modify:

- `generate_report.py`
  - parse `--format`
  - keep `report` path unchanged
  - call dashboard modules for `dashboard`

Packaging:

- include new modules in the `smcp` package mapping already defined in
  `pyproject.toml`
- optional console command can stay `sm-report`; no new CLI name required

## Tests

Add focused tests:

1. `tests/test_dashboard_data.py`
   - sample SKU config converts to `kind="sku"`
   - category config converts to `kind="category_portfolio"`
   - missing numbers remain missing
   - key IDs are human-readable

2. `tests/test_dashboard_render.py`
   - dashboard HTML contains `<!doctype html>`
   - contains no `__PLACEHOLDER__`
   - includes overview, economics, channel, treatment, and evidence sections
   - category dashboard includes tier map, diagnosis, SKU matrix
   - inline script parses as JavaScript or is simple enough to smoke-check via
     substring tests if Node is unavailable

3. Existing `tests/test_generate_report.py`
   - add CLI smoke test:
     `generate_report.py --demo --format dashboard`

4. `scripts/run_all_checks.py`
   - include new dashboard tests

CI should continue to run current report checks. Add dashboard render smoke tests
for:

- `sample-sku-en-config.json`
- `sample-sku-zh-config.json`
- `aurora-airpurifier-category-config.json`

## Error Handling

- If a section lacks source data, render a clear empty state rather than dropping
  the section silently.
- If a heatmap references an unknown dimension or channel, fail dashboard
  validation.
- If a treatment references a missing challenge, fail dashboard validation.
- If a number violates provenance rules, reuse the existing config validation
  failure before rendering.
- If optional scientific dependencies are missing, the dashboard still renders
  but marks the script-derived gate as unavailable.

## Migration Phases

### Phase 1: Structure and Data

- Add `DashboardData` conversion.
- Add minimal dashboard HTML shell.
- Render SKU and category example dashboards.
- Add tests.

### Phase 2: Full Readability Pass

- Add polished operating-dashboard CSS.
- Add right detail panel.
- Add search and click interactions.
- Add responsive behavior.

### Phase 3: Validation and CI

- Add dashboard validator.
- Add CI smoke rendering.
- Add drift checks if examples are committed.

## Risks

- `generate_report.py` is already large. New dashboard code should live in
  separate modules to avoid making it harder to maintain.
- Existing configs may not contain enough heatmap / treatment detail for every
  dashboard section. Empty states must be honest and readable.
- The reference dashboard's data contract is richer than this repository's
  current examples. Copying it directly would force fake data. The safer path is
  to normalize this repository's own config into a smaller cockpit contract.
- Visual polish can hide missing evidence. The UI must make `missing`,
  `assumed`, and `undetermined` visible.

## Acceptance Criteria

- Existing report output remains unchanged by default.
- `--format dashboard` renders a single-file interactive HTML dashboard.
- Dashboard content comes from current config fields and current causal logic.
- Sample SKU dashboard shows the chain:
  Decision Memo -> CAC ceiling -> channel screen -> treatment gates -> evidence.
- Category dashboard shows:
  tier map -> L1-L6 diagnosis -> SKU verdict matrix -> evidence gaps.
- Every clickable item updates the right detail panel.
- No generated dashboard contains reference-repo fictional product content.
- `python scripts/run_all_checks.py` passes.
- CI renders dashboard smoke outputs for all committed example configs.
