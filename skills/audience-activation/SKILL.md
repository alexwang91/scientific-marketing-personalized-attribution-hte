# Audience Activation Planner v1

## Purpose

Generate a full-channel audience activation plan from a minimal input:

```yaml
country: Hungary
audience: people interested in cycling
```

Optional input may include:

```yaml
product_or_offer: optional
goal: purchase | lead | awareness | app_install | store_visit | unknown
budget_level: low | medium | high | unknown
first_party_data: none | website_visitors | crm | purchasers | app_users | unknown
target_region: optional
language: optional
```

If optional input is missing, make reasonable assumptions and state them in the report.

## User-facing rule

Keep the public interface simple:

```text
country + audience → full activation report
```

Do not expose synthetic population, silicon sampling, HTE, choice simulation, or segment-lift machinery to ordinary users unless they ask for methodology. Use those signals only as internal hypothesis sources.

## Safety and evidence rules

- Do not describe synthetic respondents as real consumers.
- Do not describe LLM / synthetic / expert assumptions as real sales, click, survey, or experiment data.
- Do not claim deterministic targeting unless the user supplies consented first-party audience data and the chosen platform supports that activation.
- ROI / ROAS is only a planning estimate unless AOV, margin, CVR, CAC, and observed campaign data exist.
- Every channel must have an executable mechanism. Do not write generic advice such as "use social media".

## Required output

The Markdown report must contain:

1. `# Audience Activation Plan`
2. `## 1. Activation Brief`
3. `## 2. Channel Priority Map`
4. `## 3. Channel Execution Specs`
5. `## 4. Budget Allocation`
6. `## 5. ROI / ROAS Planning Estimate`
7. `## 6. 30-Day Launch Plan`
8. `## 7. Quality Checks`

## Required channels

The Channel Priority Map must cover:

- Google Search
- YouTube / video
- Meta Facebook / Instagram
- TikTok
- Display / programmatic / contextual
- Marketplaces / retail media
- Local publishers / vertical communities
- Influencers / creators
- SEO / content
- CRM / retargeting
- Partnerships / offline

## Implementation

Use the deterministic baseline generator first:

```bash
python skills/audience-activation/scripts/generate_activation_plan.py \
  skills/audience-activation/examples/hungary-cycling-input.json \
  --output skills/audience-activation/examples/hungary-cycling-output.md
```

Validate output:

```bash
python skills/audience-activation/scripts/validate_activation_plan.py \
  skills/audience-activation/examples/hungary-cycling-output.md
```

Run tests:

```bash
python tests/test_generate_activation_plan.py
python tests/test_validate_activation_plan.py
python scripts/run_all_checks.py --include-slow
```

## v1 scope

- deterministic functions
- JSON input
- Markdown output
- fixed channel catalog
- Hungary + cycling localization
- no live ad APIs
- no live web research
- no complex agent orchestration
- no synthetic respondents exposed as real people
