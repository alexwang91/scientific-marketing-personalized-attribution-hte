#!/usr/bin/env python3
"""Run lightweight Audience Activation Planner v1 checks."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

COMMANDS = [
    [sys.executable, "tests/test_generate_activation_plan.py"],
    [sys.executable, "tests/test_validate_activation_plan.py"],
    [sys.executable, "tests/test_generate_report.py"],
    [sys.executable, "tests/test_causal_scripts.py"],  # skips itself if numpy/scipy absent
    [sys.executable, "skills/audience-activation/scripts/generate_activation_plan.py", "skills/audience-activation/examples/hungary-cycling-input.json", "--output", "skills/audience-activation/examples/hungary-cycling-output.md"],
    [sys.executable, "skills/audience-activation/scripts/validate_activation_plan.py", "skills/audience-activation/examples/hungary-cycling-output.md"],
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--include-slow", action="store_true", help="accepted for compatibility; v1 has no slow checks")
    parser.parse_args()
    for command in COMMANDS:
        print("$ " + " ".join(command))
        completed = subprocess.run(command, cwd=ROOT)
        if completed.returncode != 0:
            return completed.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
