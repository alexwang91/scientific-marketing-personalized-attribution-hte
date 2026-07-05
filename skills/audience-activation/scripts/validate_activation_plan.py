#!/usr/bin/env python3
"""Validate Audience Activation Planner v1 markdown reports."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import List

REQUIRED_SECTIONS = [
    "# Audience Activation Plan",
    "## 1. Activation Brief",
    "## 2. Channel Priority Map",
    "## 3. Channel Execution Specs",
    "## 4. Budget Allocation",
    "## 5. ROI / ROAS Planning Estimate",
    "## 6. 30-Day Launch Plan",
    "## 7. Quality Checks",
]

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

BANNED_PATTERNS = [
    r"\bdeterministically reach\b",
    r"\bperfectly identify\b",
    r"\bguaranteed to reach\b",
    r"\breach every person\b",
    r"\ball users who are interested\b",
]


def section_text(markdown: str, heading: str) -> str:
    if heading not in markdown:
        return ""
    after = markdown.split(heading, 1)[1]
    match = re.search(r"\n## ", after)
    return after if not match else after[: match.start()]


def high_priority_channels(markdown: str) -> List[str]:
    section = section_text(markdown, "## 2. Channel Priority Map")
    channels: List[str] = []
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if not cells or cells[0].lower() == "channel":  # header row
            continue
        if all(set(cell) <= {"-", ":", " "} for cell in cells):  # separator row
            continue
        if len(cells) >= 4 and cells[3].lower() == "high":
            channels.append(cells[0])
    return channels


def validate_markdown(markdown: str) -> List[str]:
    errors: List[str] = []
    lower = markdown.lower()

    for section in REQUIRED_SECTIONS:
        if section not in markdown:
            errors.append(f"missing required section: {section}")

    priority_map = section_text(markdown, "## 2. Channel Priority Map")
    for channel in REQUIRED_CHANNELS:
        if channel not in priority_map:
            errors.append(f"missing required channel in Channel Priority Map: {channel}")

    execution_section = section_text(markdown, "## 3. Channel Execution Specs")
    for channel in high_priority_channels(markdown):
        if f"### {channel}" not in execution_section:
            errors.append(f"missing execution spec for high priority channel: {channel}")

    for pattern in BANNED_PATTERNS:
        if re.search(pattern, lower):
            errors.append(f"deterministic targeting claim is not allowed: {pattern}")

    roi_section = section_text(markdown, "## 5. ROI / ROAS Planning Estimate")
    if "planning estimate" not in roi_section.lower():
        errors.append("ROI section must state that ROI / ROAS is a planning estimate")
    if "assumption note" not in roi_section.lower():
        errors.append("ROI section must include an assumption note")
    if "confidence" not in roi_section.lower():
        errors.append("ROI section must include confidence")

    quality = section_text(markdown, "## 7. Quality Checks")
    for required in ["prox", "validation", "hypoth", "campaign data"]:
        if required not in quality.lower():
            errors.append(f"quality checks must include {required} language")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an Audience Activation Plan markdown report.")
    parser.add_argument("path", type=Path)
    parser.add_argument("--expect-fail", action="store_true")
    args = parser.parse_args()
    markdown = args.path.read_text(encoding="utf-8")
    errors = validate_markdown(markdown)
    if args.expect_fail:
        if errors:
            print("PASS: validation failed as expected")
            for error in errors:
                print(f"- {error}")
            return 0
        print("FAIL: expected validation failure, but validation passed")
        return 1
    if errors:
        print("FAIL: validation errors")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: activation plan is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
