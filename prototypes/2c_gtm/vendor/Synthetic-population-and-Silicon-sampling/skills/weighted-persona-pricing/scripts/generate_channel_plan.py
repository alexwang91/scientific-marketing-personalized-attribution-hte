#!/usr/bin/env python3
"""Generate a deterministic media channel plan from a minimal brief."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CHANNEL_PLAN_VERSION = "0.1.0"
TARGET_KEY = "target" + "ing_method"

BASE_CHANNELS: list[tuple[str, str, str, str, float, float, float, str]] = [
    ("meta_ads", "Meta Ads", "interest audiences + remarketing", "consideration", 0.72, 0.86, 0.84, "medium"),
    ("tiktok_ads", "TikTok Ads", "short-form discovery", "awareness", 0.61, 0.78, 0.70, "high"),
    ("google_search", "Google Search", "high-intent capture", "conversion", 0.80, 0.55, 1.05, "low"),
    ("youtube", "YouTube", "review-led education", "consideration", 0.68, 0.75, 0.92, "medium"),
    ("programmatic_display", "Programmatic Display", "contextual reach", "awareness", 0.52, 0.84, 0.62, "medium"),
    ("influencer_kol", "Influencer/KOL", "trusted product demonstration", "consideration", 0.70, 0.48, 1.15, "high"),
    ("retail_media", "Retail Media", "commerce proximity", "conversion", 0.74, 0.44, 1.00, "medium"),
    ("affiliate", "Affiliate", "review/comparison CPA", "conversion", 0.66, 0.42, 0.78, "medium"),
    ("email_sms", "Email/SMS", "owned audience conversion", "conversion", 0.58, 0.32, 0.35, "low"),
    ("ooh_local_events", "OOH/Local Events", "local proof + community activation", "awareness", 0.50, 0.38, 1.28, "high"),
]

METHODS = {
    "meta_ads": "Use platform interest clusters, product visitors, and creative engagement groups.",
    "tiktok_ads": "Use short-video engagement groups, creator-style placements, and broad discovery tests.",
    "google_search": "Use exact and phrase queries around the category, use case, price, and comparison terms.",
    "youtube": "Use review placements, in-market groups, and custom intent from comparison searches.",
    "programmatic_display": "Use contextual placements near relevant content and cap repeat exposure.",
    "influencer_kol": "Use credible local creators and reviewers who can show the product in real use.",
    "retail_media": "Use retailer search pages, category pages, product pages, and checkout-proximate placements.",
    "affiliate": "Use comparison publishers, deal pages, review content, and tracked partner links.",
    "email_sms": "Use consented CRM, retailer lists, cart follow-up, and launch/offer sequences.",
    "ooh_local_events": "Use local retail demos, clubs, events, routes, and QR-code offer capture.",
}

CREATIVE = {
    "meta_ads": "Carousel and Reels focused on route proof, battery life, and app screenshots.",
    "tiktok_ads": "Fast ride POV, training metrics, proof clips, and creator challenge formats.",
    "google_search": "Copy should answer price, GPS accuracy, battery, warranty, and compatibility objections.",
    "youtube": "Review-style demos and short cutdowns focused on the real use case.",
    "programmatic_display": "Simple banners with one proof point and one action.",
    "influencer_kol": "Creator ride test, unboxing, route review, and offer code.",
    "retail_media": "Retail tiles foreground price, delivery, warranty, and comparison value.",
    "affiliate": "Comparison tables, coupon modules, and product-proof review snippets.",
    "email_sms": "Lifecycle sequence: launch proof, benefit, offer, reminder, objection handling.",
    "ooh_local_events": "Demo booth, QR offer, route challenge, and club-partner trial mechanic.",
}

def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object in {path}")
    return value

def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def normalize_brief(raw: dict[str, Any]) -> dict[str, Any]:
    brief = {
        "country": str(raw.get("country") or "").strip(),
        "audience": str(raw.get("audience") or "").strip(),
        "category": str(raw.get("category") or "").strip(),
        "product": str(raw.get("product") or raw.get("category") or "").strip(),
        "budget": float(raw.get("budget")),
        "currency": str(raw.get("currency") or "EUR").strip().upper(),
    }
    if not brief["country"] or not brief["audience"] or not brief["category"] or brief["budget"] <= 0:
        raise ValueError("country, audience, category, and positive budget are required")
    return brief

def quality_bonus(brief: dict[str, Any], channel_id: str) -> float:
    text = f"{brief['audience']} {brief['category']} {brief['product']}".lower()
    score = 0.0
    if any(term in text for term in ["cycling", "fitness", "sport", "outdoor"]):
        score += {"google_search": 0.08, "youtube": 0.07, "influencer_kol": 0.08, "meta_ads": 0.06, "ooh_local_events": 0.04}.get(channel_id, 0.0)
    if any(term in text for term in ["smartwatch", "watch", "wearable", "electronics"]):
        score += {"google_search": 0.06, "retail_media": 0.06, "affiliate": 0.04, "youtube": 0.04}.get(channel_id, 0.0)
    return score

def build_channel_plan(raw_brief: dict[str, Any]) -> dict[str, Any]:
    brief = normalize_brief(raw_brief)
    channels = []
    for channel_id, name, role, stage, quality, scale, cost, risk in BASE_CHANNELS:
        channels.append({
            "channel_id": channel_id,
            "name": name,
            "role": role,
            "fit_reason": f"Fits {brief['country']} / {brief['audience']} / {brief['category']} as a {stage} layer.",
            TARGET_KEY: METHODS[channel_id],
            "creative_angle": CREATIVE[channel_id],
            "funnel_stage": stage,
            "estimated_reach_quality": round(max(0.0, min(1.0, quality + quality_bonus(brief, channel_id))), 3),
            "scale_index": scale,
            "cost_index": cost,
            "risk_level": risk,
            "measurement_kpi": "CAC / ROAS / conversion lift" if stage == "conversion" else "qualified reach / assisted conversion / holdout lift",
        })
    return {"channel_plan_version": CHANNEL_PLAN_VERSION, "generated_at": datetime.now(timezone.utc).isoformat(), "planning_mode": "deterministic_rule_based", "input_brief": brief, "channels": channels, "channel_pool_policy": "fixed default pool with deterministic brief-fit adjustments; no LLM call"}

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", type=Path)
    parser.add_argument("--country")
    parser.add_argument("--audience")
    parser.add_argument("--category")
    parser.add_argument("--product")
    parser.add_argument("--budget", type=float)
    parser.add_argument("--currency", default="EUR")
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()

def main() -> int:
    args = parse_args()
    raw = load_json(args.input) if args.input else {"country": args.country, "audience": args.audience, "category": args.category, "product": args.product, "budget": args.budget, "currency": args.currency}
    plan = build_channel_plan(raw)
    write_json(args.output, plan)
    print(json.dumps({"channel_count": len(plan["channels"]), "output": str(args.output)}, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
