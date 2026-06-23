#!/usr/bin/env python3
"""Generate a deterministic Audience Activation Planner v1 markdown report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

HERE = Path(__file__).resolve().parent
SKILL_DIR = HERE.parent
CATALOG_PATH = SKILL_DIR / "references" / "channel-catalog.json"

REQUIRED_CHANNELS = [
    "Google Search",
    "YouTube / video",
    "Meta Facebook / Instagram",
    "TikTok",
    "Display / programmatic / contextual",
    "Marketplaces / retail media",
    "Local publishers / vertical communities",
    "Influencers / creators",
    "SEO / content",
    "CRM / retargeting",
    "Partnerships / offline",
]

GOALS = {"purchase", "lead", "awareness", "app_install", "store_visit", "unknown"}
BUDGET_LEVELS = {"low", "medium", "high", "unknown"}
FIRST_PARTY = {"none", "website_visitors", "crm", "purchasers", "app_users", "unknown"}

PURCHASE_BUDGET = {
    "Google Search": 24,
    "CRM / retargeting": 16,
    "Meta Facebook / Instagram": 14,
    "Marketplaces / retail media": 12,
    "SEO / content": 8,
    "YouTube / video": 7,
    "TikTok": 6,
    "Display / programmatic / contextual": 5,
    "Influencers / creators": 4,
    "Local publishers / vertical communities": 2,
    "Partnerships / offline": 2,
}

AWARENESS_BUDGET = {
    "YouTube / video": 18,
    "TikTok": 16,
    "Meta Facebook / Instagram": 16,
    "Influencers / creators": 12,
    "Display / programmatic / contextual": 10,
    "Local publishers / vertical communities": 8,
    "SEO / content": 7,
    "Google Search": 6,
    "Partnerships / offline": 4,
    "Marketplaces / retail media": 2,
    "CRM / retargeting": 1,
}

BALANCED_BUDGET = {
    "Google Search": 16,
    "Meta Facebook / Instagram": 14,
    "YouTube / video": 12,
    "SEO / content": 10,
    "CRM / retargeting": 10,
    "TikTok": 9,
    "Marketplaces / retail media": 8,
    "Display / programmatic / contextual": 7,
    "Influencers / creators": 6,
    "Local publishers / vertical communities": 4,
    "Partnerships / offline": 4,
}


def load_catalog(path: Path = CATALOG_PATH) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    by_name = {row["channel"]: row for row in data.get("channels", [])}
    missing = [channel for channel in REQUIRED_CHANNELS if channel not in by_name]
    if missing:
        raise ValueError(f"channel catalog missing required channels: {missing}")
    return [by_name[channel] for channel in REQUIRED_CHANNELS]


def normalize_input(raw: Dict[str, Any]) -> Dict[str, str]:
    country = str(raw.get("country", "")).strip()
    audience = str(raw.get("audience", "")).strip()
    if not country:
        raise ValueError("country is required")
    if not audience:
        raise ValueError("audience is required")
    goal = str(raw.get("goal", "unknown")).strip() or "unknown"
    budget = str(raw.get("budget_level", raw.get("budget", "unknown"))).strip() or "unknown"
    first_party = str(raw.get("first_party_data", "unknown")).strip() or "unknown"
    return {
        "country": country,
        "audience": audience,
        "product_or_offer": str(raw.get("product_or_offer", "unspecified offer")).strip() or "unspecified offer",
        "goal": goal if goal in GOALS else "unknown",
        "budget_level": budget if budget in BUDGET_LEVELS else "unknown",
        "first_party_data": first_party if first_party in FIRST_PARTY else "unknown",
        "target_region": str(raw.get("target_region", "")).strip(),
        "language": str(raw.get("language", "")).strip(),
    }


def is_hungary_cycling(inp: Dict[str, str]) -> bool:
    country = inp["country"].lower()
    audience = inp["audience"].lower()
    return country == "hungary" and any(term in audience for term in ["cycling", "bicycle", "bike", "kerékpár", "bicikli"])


def localized_context(inp: Dict[str, str]) -> Dict[str, Any]:
    assumptions: List[str] = []
    if inp["language"]:
        language = inp["language"]
    elif inp["country"].lower() == "hungary":
        language = "Hungarian primary, English optional test"
        assumptions.append("language assumed: Hungarian primary, English optional test")
    else:
        language = "local language primary, English optional test"
        assumptions.append("language assumed from country because no language was provided")

    if inp["target_region"]:
        region = inp["target_region"]
    elif inp["country"].lower() == "hungary":
        region = "Hungary nationally, with Budapest as priority reporting split"
        assumptions.append("target_region assumed: national coverage with Budapest priority split")
    else:
        region = f"{inp['country']} nationally, with major cities separated when data allows"
        assumptions.append("target_region assumed: national coverage with major-city reporting split")

    if inp["goal"] == "unknown":
        assumptions.append("goal assumed: balanced acquisition and validation because no goal was provided")
    if inp["budget_level"] == "unknown":
        assumptions.append("budget_level unknown: use percentage allocation, not fake currency")
    if inp["product_or_offer"] == "unspecified offer":
        assumptions.append("product_or_offer missing: landing pages and creative remain category-level")
    if inp["first_party_data"] == "unknown":
        assumptions.append("first_party_data unknown: CRM and retargeting plan is conditional on consented audiences")

    if is_hungary_cycling(inp):
        keywords = ["kerékpár", "bicikli", "bringa", "e-bike", "kerékpár sisak", "bicikli lámpa", "kerékpár zár"]
        local_publishers = "Hungarian cycling publishers, Budapest cycling communities, bike shops, cycling clubs"
        creators = "Hungarian cycling, commuter, e-bike, MTB, road, and gravel creators"
    else:
        keywords = [inp["audience"], f"{inp['audience']} {inp['country']}", f"best {inp['audience']}", f"{inp['audience']} near me"]
        local_publishers = f"local vertical publishers and communities in {inp['country']} related to {inp['audience']}"
        creators = f"local creators whose audience geography matches {inp['country']} and niche matches {inp['audience']}"

    return {"language": language, "region": region, "assumptions": assumptions, "keywords": keywords, "local_publishers": local_publishers, "creators": creators}


def priority_for(channel: str, goal: str, first_party_data: str) -> str:
    if goal == "purchase":
        if channel in {"Google Search", "CRM / retargeting", "Meta Facebook / Instagram"}:
            return "High"
        if channel in {"Marketplaces / retail media", "SEO / content", "YouTube / video", "TikTok", "Influencers / creators", "Display / programmatic / contextual"}:
            return "Medium"
        return "Low"
    if goal == "awareness":
        if channel in {"YouTube / video", "TikTok", "Meta Facebook / Instagram", "Influencers / creators"}:
            return "High"
        if channel in {"Display / programmatic / contextual", "Local publishers / vertical communities", "SEO / content"}:
            return "Medium"
        return "Low"
    if channel in {"Google Search", "Meta Facebook / Instagram", "SEO / content", "CRM / retargeting"}:
        return "High" if goal in {"lead", "store_visit", "unknown"} else "Medium"
    return "Medium"


def confidence_for(inp: Dict[str, str], channel: str) -> str:
    if inp["product_or_offer"] == "unspecified offer" or inp["budget_level"] == "unknown":
        return "low"
    if channel == "CRM / retargeting" and inp["first_party_data"] in {"website_visitors", "crm", "purchasers", "app_users"}:
        return "medium"
    if channel == "Google Search":
        return "medium"
    return "low"


def roi_score_for(catalog_row: Dict[str, Any], inp: Dict[str, str]) -> int:
    goal = inp["goal"] if inp["goal"] in GOALS else "unknown"
    score = int(catalog_row["default_roi"].get(goal, catalog_row["default_roi"]["unknown"]))
    if catalog_row["channel"] == "CRM / retargeting" and inp["first_party_data"] in {"website_visitors", "crm", "purchasers", "app_users"}:
        score = min(5, score + 1)
    return max(1, min(5, score))


def channel_proxy(channel: str, inp: Dict[str, str], ctx: Dict[str, Any]) -> str:
    audience = inp["audience"]
    kw = ", ".join(ctx["keywords"])
    if channel == "Google Search":
        return f"Local-language intent keywords: {kw}"
    if channel == "YouTube / video":
        return f"Video custom segments and placements around {audience}; seed with keywords: {kw}"
    if channel == "Meta Facebook / Instagram":
        return f"Broad {inp['country']} audience, available interest proxies, engagement retargeting, and lookalikes if consented data exists"
    if channel == "TikTok":
        return f"Interest / behavior proxies plus short-form engagement audiences for {audience}"
    if channel == "Display / programmatic / contextual":
        return f"Contextual topics, managed placements, and publisher lists related to {audience}"
    if channel == "Marketplaces / retail media":
        return f"Category search terms, sponsored listings, and product feed attributes for {audience} products"
    if channel == "Local publishers / vertical communities":
        return ctx["local_publishers"]
    if channel == "Influencers / creators":
        return ctx["creators"]
    if channel == "SEO / content":
        return f"Local-language keyword clusters and buying guides for {kw}"
    if channel == "CRM / retargeting":
        return "Consented website visitors, cart abandoners, CRM contacts, purchasers, or app users where available"
    return f"Local partners, affiliates, events, clubs, retailers, and referral codes related to {audience}"


def creative_angle(channel: str, inp: Dict[str, str]) -> str:
    if is_hungary_cycling(inp):
        return {
            "Google Search": "safe city cycling, commuter convenience, e-bike accessories, fast delivery",
            "YouTube / video": "Budapest commute setup, night visibility, e-bike comfort, weekend ride checklist",
            "Meta Facebook / Instagram": "UGC-style commuter safety kit, lock / light bundle, product carousel",
            "TikTok": "three essentials for Budapest cyclists, bike lock test, night riding setup",
            "Display / programmatic / contextual": "contextual safety and commuter gear banners beside cycling content",
            "Marketplaces / retail media": "high-review safety bundles, delivery speed, price clarity",
            "Local publishers / vertical communities": "Hungarian cycling gear guide, Budapest commuter checklist",
            "Influencers / creators": "real commute demo, e-bike trip essentials, helmet and light setup",
            "SEO / content": "Hungarian buying guides for helmets, locks, lights, e-bike accessories",
            "CRM / retargeting": "complete your cycling setup, abandoned-cart reminder, seasonal checklist",
            "Partnerships / offline": "cycling club offers, repair-shop bundles, event referral codes",
        }[channel]
    return f"localized {inp['audience']} problem-solution messaging tied to {inp['product_or_offer']}"


def landing_destination(channel: str, inp: Dict[str, str]) -> str:
    offer = inp["product_or_offer"] if inp["product_or_offer"] != "unspecified offer" else inp["audience"]
    if channel == "Google Search":
        return f"local-language high-intent landing pages for {offer}"
    if channel == "Marketplaces / retail media":
        return "marketplace product detail pages with reviews, delivery, price, and feed quality fixed"
    if channel == "CRM / retargeting":
        return "saved cart, viewed product, personalized collection, or lifecycle email destination"
    if channel in {"Influencers / creators", "Partnerships / offline"}:
        return "creator / partner landing page with UTM, coupon code, and clear conversion path"
    if channel == "SEO / content":
        return "local-language guide pages with product modules and comparison blocks"
    return f"mobile-first local-language landing page for {offer}"


def exclusions(channel: str) -> str:
    if channel == "Google Search":
        return "free, jobs, used-only, research-only, and non-service-region queries where irrelevant"
    if channel == "CRM / retargeting":
        return "unsubscribed users, recent purchasers where not cross-selling, unsupported regions"
    if channel in {"YouTube / video", "Display / programmatic / contextual"}:
        return "low-quality placements, irrelevant content categories, recent purchasers where appropriate"
    return "recent purchasers where not cross-selling, unsupported regions, low-quality inventory or partners"


def kpi_for(channel: str, goal: str) -> str:
    if channel in {"Google Search", "Marketplaces / retail media", "CRM / retargeting"}:
        return "purchase CPA, ROAS planning estimate, conversion rate" if goal in {"purchase", "unknown"} else "qualified lead CPA or store visit proxy"
    if channel in {"YouTube / video", "TikTok", "Display / programmatic / contextual"}:
        return "qualified visit rate, engaged sessions, assisted conversions, remarketing pool growth"
    if channel == "SEO / content":
        return "organic qualified visits, ranking progress, assisted conversions"
    if channel == "Influencers / creators":
        return "creator-attributed sales or leads, coupon usage, whitelisted ad CPA"
    if channel == "Local publishers / vertical communities":
        return "qualified referral sessions, newsletter clicks, assisted conversions"
    return "partner-attributed leads or sales, referral code usage, event-sourced pipeline"


def budget_profile(goal: str) -> Dict[str, int]:
    if goal == "purchase":
        return PURCHASE_BUDGET
    if goal == "awareness":
        return AWARENESS_BUDGET
    return BALANCED_BUDGET


def scale_budget(profile: Dict[str, int], emphasis: str) -> Dict[str, int]:
    if emphasis in {"low", "medium"}:
        return profile.copy()
    adjusted = profile.copy()
    for channel in ["Meta Facebook / Instagram", "YouTube / video", "Google Search"]:
        adjusted[channel] += 1
    for channel in ["Partnerships / offline", "Local publishers / vertical communities", "Display / programmatic / contextual"]:
        adjusted[channel] = max(0, adjusted[channel] - 1)
    return adjusted


def build_budget_allocation(goal: str) -> Dict[str, Dict[str, int]]:
    profile = budget_profile(goal)
    return {level: scale_budget(profile, level) for level in ["low", "medium", "high"]}


def generate_plan(raw_input: Dict[str, Any]) -> Dict[str, Any]:
    inp = normalize_input(raw_input)
    ctx = localized_context(inp)
    allocation = build_budget_allocation(inp["goal"])
    channel_rows = []
    specs = []
    for row in load_catalog():
        channel = row["channel"]
        priority = priority_for(channel, inp["goal"], inp["first_party_data"])
        proxy = channel_proxy(channel, inp, ctx)
        channel_rows.append({
            "channel": channel,
            "funnel_role": row["funnel_role"],
            "audience_proxy": proxy,
            "execution_priority": priority,
            "budget_share": allocation["medium"][channel],
            "relative_roi_score": roi_score_for(row, inp),
            "confidence": confidence_for(inp, channel),
            "why": f"Uses an executable proxy mechanism for {inp['audience']} in {inp['country']}; score is a planning estimate, not calibrated ROAS.",
        })
        if priority in {"High", "Medium"}:
            specs.append({
                "channel": channel,
                "priority": priority,
                "objective": "drive purchases and validated demand" if inp["goal"] in {"purchase", "unknown"} else f"support {inp['goal']} goal",
                "geography": ctx["region"],
                "language": ctx["language"],
                "audience_setup": proxy,
                "keywords_interests_placements_creators": proxy,
                "exclusions": exclusions(channel),
                "creative_angle": creative_angle(channel, inp),
                "landing_or_destination": landing_destination(channel, inp),
                "kpi": kpi_for(channel, inp["goal"]),
                "operating_cadence": "daily spend / delivery check; weekly proxy, creative, and placement review",
                "risks": "proxy may not represent the true audience; short-term ROI may be noisy without calibrated conversion data",
                "validation_test": "run a capped test against a clear control or benchmark; scale only if KPI beats threshold with acceptable confidence",
            })
    return {"input": inp, "context": ctx, "activation_brief": {"country": inp["country"], "audience": inp["audience"], "goal": inp["goal"], "assumptions": ctx["assumptions"], "activation_thesis": f"Turn {inp['audience']} in {inp['country']} into executable channel proxies, validate the highest-intent paths first, then scale social, video, creator, content, and partnership channels based on observed campaign data."}, "channel_priority_map": channel_rows, "channel_execution_specs": specs, "budget_allocation": allocation}


def md_table(headers: List[str], rows: List[List[Any]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        out.append("| " + " | ".join(str(x).replace("\n", " ") for x in row) + " |")
    return "\n".join(out)


def render_markdown(plan: Dict[str, Any]) -> str:
    brief = plan["activation_brief"]
    lines: List[str] = ["# Audience Activation Plan", "", "## 1. Activation Brief", ""]
    assumptions = brief["assumptions"] or ["no optional inputs were missing"]
    lines += [md_table(["field", "value"], [["country", brief["country"]], ["audience", brief["audience"]], ["goal", brief["goal"]], ["assumptions", "; ".join(assumptions)], ["activation thesis", brief["activation_thesis"]]]), ""]

    lines += ["## 2. Channel Priority Map", ""]
    rows = [[r["channel"], r["funnel_role"], r["audience_proxy"], r["execution_priority"], f"{r['budget_share']}%", r["relative_roi_score"], r["confidence"], r["why"]] for r in plan["channel_priority_map"]]
    lines += [md_table(["channel", "funnel role", "audience proxy", "execution priority", "budget share", "relative ROI score", "confidence", "why"], rows), ""]

    lines += ["## 3. Channel Execution Specs", ""]
    for spec in plan["channel_execution_specs"]:
        lines += [f"### {spec['channel']}", ""]
        keys = ["objective", "geography", "language", "audience_setup", "keywords_interests_placements_creators", "exclusions", "creative_angle", "landing_or_destination", "kpi", "operating_cadence", "risks", "validation_test"]
        spec_rows = [["priority", spec["priority"]]] + [[k.replace("_", " "), spec[k]] for k in keys]
        lines += [md_table(["field", "plan"], spec_rows), ""]

    lines += ["## 4. Budget Allocation", ""]
    headers = ["budget level"] + REQUIRED_CHANNELS
    budget_rows = [[level] + [f"{plan['budget_allocation'][level][channel]}%" for channel in REQUIRED_CHANNELS] for level in ["low", "medium", "high"]]
    lines += [md_table(headers, budget_rows), "", "If no concrete budget amount is supplied, all budget guidance stays in percentages and does not invent currency values.", ""]

    lines += ["## 5. ROI / ROAS Planning Estimate", ""]
    lines += ["ROI is a planning estimate unless calibrated with real AOV, margin, CVR, CAC, and campaign data. Because these inputs are missing or optional in v1, use relative ROI score from 1-5 rather than fake ROAS.", ""]
    roi_rows = [[r["channel"], r["relative_roi_score"], r["confidence"], "assumption note: heuristic based on intent strength, first-party availability, and expected funnel role; not real attribution"] for r in plan["channel_priority_map"]]
    lines += [md_table(["channel", "relative ROI score", "confidence", "assumption note"], roi_rows), ""]

    lines += ["## 6. 30-Day Launch Plan", ""]
    launch_rows = [["Days 0-3", "tracking, landing page, assumptions", "Set conversion events, UTMs, consent checks, localized landing pages, assumptions log, and first reporting dashboard."], ["Days 4-10", "highest intent channels", "Launch Google Search, marketplace / retail media if relevant, and consented CRM / retargeting if data exists."], ["Days 11-20", "social/video/contextual expansion", "Launch Meta, YouTube / video, TikTok, and contextual tests with capped budgets and clear creative hypotheses."], ["Days 21-30", "creators/community/retargeting optimization", "Add creators, publishers, partnerships, refresh creatives, review validation tests, and reallocate budget based on observed data."]]
    lines += [md_table(["period", "focus", "actions"], launch_rows), ""]

    lines += ["## 7. Quality Checks", ""]
    checks = ["platform audiences are proxies, not deterministic access to every person in the audience", "ROI is a planning estimate unless calibrated with AOV, margin, CVR, CAC, and campaign data", "synthetic / assumed signals are hypotheses, not real consumers or observed behavior", "real validation requires campaign data, holdouts, experiments, or reliable first-party behavior", "each channel includes an executable mechanism rather than generic advice"]
    lines += ["\n".join(f"- [x] {check}" for check in checks), ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate an Audience Activation Plan markdown report.")
    parser.add_argument("input", type=Path, help="Input JSON file")
    parser.add_argument("--output", type=Path, help="Output markdown path")
    args = parser.parse_args()
    markdown = render_markdown(generate_plan(json.loads(args.input.read_text(encoding="utf-8"))))
    if args.output:
        args.output.write_text(markdown, encoding="utf-8")
    else:
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
