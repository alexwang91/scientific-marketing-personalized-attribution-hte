#!/usr/bin/env python3
"""Sample weighted persona skeletons from weighted statistical cells.

This script converts IPF/raked cells into person-level synthetic respondent
skeletons. It uses deterministic largest-remainder allocation by default, so
sample size is exact and reproducible.

Input rows should contain:
- cell_id
- hard: object
- population_weight or ipf_weight

Output rows contain:
- persona_id
- population_weight
- hard
- source_cell_id
- calibration_trace

The script does not generate soft traits, narratives, or product choices.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


WEIGHT_KEYS = ("population_weight", "ipf_weight", "seed_weight", "weight")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_number, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                value = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"line {line_number}: invalid JSON: {exc}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"line {line_number}: expected JSON object")
            value["_line_number"] = line_number
            records.append(value)
    if not records:
        raise ValueError("weighted cells file is empty")
    return records


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def cell_weight(cell: dict[str, Any]) -> float:
    for key in WEIGHT_KEYS:
        value = cell.get(key)
        if isinstance(value, (int, float)) and value > 0:
            return float(value)
    raise ValueError(f"line {cell.get('_line_number')}: cell has no positive weight in {WEIGHT_KEYS}")


def cell_identifier(cell: dict[str, Any], index: int) -> str:
    value = cell.get("cell_id")
    if isinstance(value, str) and value:
        return value
    iso2 = str(cell.get("iso2", "XX")).upper()
    return f"{iso2}-CELL-{index:06d}"


def infer_iso2(cells: list[dict[str, Any]]) -> str:
    for cell in cells:
        iso2 = cell.get("iso2")
        if isinstance(iso2, str) and len(iso2) == 2:
            return iso2.upper()
    return "XX"


def allocate_largest_remainder(
    weights: list[float],
    sample_size: int,
    *,
    min_one_per_positive_cell: bool,
) -> list[int]:
    if sample_size <= 0:
        raise ValueError("sample_size must be positive")
    if any(weight < 0 for weight in weights):
        raise ValueError("weights must be non-negative")
    positive_indices = [idx for idx, weight in enumerate(weights) if weight > 0]
    if not positive_indices:
        raise ValueError("no positive-weight cells")

    allocations = [0 for _ in weights]

    if min_one_per_positive_cell:
        if len(positive_indices) > sample_size:
            raise ValueError(
                "--min-one-per-positive-cell requires sample_size >= positive cell count"
            )
        for idx in positive_indices:
            allocations[idx] = 1
        remaining = sample_size - len(positive_indices)
        if remaining == 0:
            return allocations
        total = sum(weights[idx] for idx in positive_indices)
        quotas = [(idx, weights[idx] / total * remaining) for idx in positive_indices]
    else:
        total = sum(weights)
        quotas = [(idx, weight / total * sample_size) for idx, weight in enumerate(weights) if weight > 0]
        remaining = sample_size

    remainders: list[tuple[float, int]] = []
    for idx, quota in quotas:
        floor_value = math.floor(quota)
        allocations[idx] += floor_value
        remaining -= floor_value
        remainders.append((quota - floor_value, idx))

    remainders.sort(key=lambda item: (-item[0], item[1]))
    for _, idx in remainders[:remaining]:
        allocations[idx] += 1

    if sum(allocations) != sample_size:
        raise AssertionError("allocation did not match requested sample size")
    return allocations


def persona_id(prefix: str, index: int, width: int) -> str:
    return f"{prefix}-{index:0{width}d}"


def build_personas(
    cells: list[dict[str, Any]],
    allocations: list[int],
    *,
    id_prefix: str,
    id_width: int,
    start_index: int,
    allocation_method: str,
) -> list[dict[str, Any]]:
    personas: list[dict[str, Any]] = []
    next_index = start_index
    for cell_index, (cell, allocation) in enumerate(zip(cells, allocations, strict=True), 1):
        if allocation <= 0:
            continue
        weight = cell_weight(cell)
        per_person_weight = weight / allocation
        hard = cell.get("hard")
        if not isinstance(hard, dict):
            raise ValueError(f"line {cell.get('_line_number')}: cell hard field must be an object")
        trace = cell.get("calibration_trace") if isinstance(cell.get("calibration_trace"), dict) else {}
        source_cell_id = cell_identifier(cell, cell_index)
        for within_cell_index in range(1, allocation + 1):
            personas.append(
                {
                    "persona_id": persona_id(id_prefix, next_index, id_width),
                    "population_weight": per_person_weight,
                    "hard": dict(hard),
                    "soft": {},
                    "source_cell_id": source_cell_id,
                    "persona_stage": "hard_statistical_skeleton",
                    "calibration_trace": {
                        **trace,
                        "persona_sampling": {
                            "method": allocation_method,
                            "source_cell_id": source_cell_id,
                            "source_cell_weight": weight,
                            "personas_allocated_to_cell": allocation,
                            "within_cell_index": within_cell_index,
                        },
                    },
                }
            )
            next_index += 1
    return personas


def audit_summary(
    cells: list[dict[str, Any]],
    allocations: list[int],
    personas: list[dict[str, Any]],
    *,
    requested_sample_size: int,
    allocation_method: str,
) -> dict[str, Any]:
    weights = [cell_weight(cell) for cell in cells]
    total_cell_weight = sum(weights)
    total_persona_weight = sum(float(persona["population_weight"]) for persona in personas)
    sampled_indices = [idx for idx, allocation in enumerate(allocations) if allocation > 0]
    unsampled_indices = [idx for idx, allocation in enumerate(allocations) if allocation == 0 and weights[idx] > 0]
    unsampled_weight = sum(weights[idx] for idx in unsampled_indices)

    positive_weights = [float(persona["population_weight"]) for persona in personas]
    allocation_rows = []
    for idx, (cell, allocation) in enumerate(zip(cells, allocations, strict=True), 1):
        if allocation <= 0:
            continue
        allocation_rows.append(
            {
                "cell_id": cell_identifier(cell, idx),
                "cell_weight": weights[idx - 1],
                "allocated_personas": allocation,
                "persona_weight": weights[idx - 1] / allocation,
                "hard": cell.get("hard", {}),
            }
        )

    return {
        "requested_sample_size": requested_sample_size,
        "realized_sample_size": len(personas),
        "allocation_method": allocation_method,
        "cell_count": len(cells),
        "positive_cell_count": sum(1 for weight in weights if weight > 0),
        "sampled_cell_count": len(sampled_indices),
        "unsampled_positive_cell_count": len(unsampled_indices),
        "total_cell_weight": total_cell_weight,
        "total_persona_weight": total_persona_weight,
        "absolute_total_weight_error": total_persona_weight - total_cell_weight,
        "unsampled_positive_cell_weight": unsampled_weight,
        "unsampled_positive_cell_weight_share": unsampled_weight / total_cell_weight if total_cell_weight else None,
        "min_persona_weight": min(positive_weights) if positive_weights else None,
        "max_persona_weight": max(positive_weights) if positive_weights else None,
        "allocation_preview": allocation_rows[:50],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("weighted_cells", type=Path)
    parser.add_argument("--sample-size", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--audit", type=Path)
    parser.add_argument("--id-prefix", default="", help="Persona ID prefix. Defaults to ISO2 from cells.")
    parser.add_argument("--id-width", type=int, default=6)
    parser.add_argument("--start-index", type=int, default=1)
    parser.add_argument(
        "--min-one-per-positive-cell",
        action="store_true",
        help="Guarantee one persona for every positive-weight cell. Requires sample size >= positive cell count.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.id_width <= 0:
        raise ValueError("--id-width must be positive")
    if args.start_index <= 0:
        raise ValueError("--start-index must be positive")
    cells = load_jsonl(args.weighted_cells)
    weights = [cell_weight(cell) for cell in cells]
    allocation_method = "largest_remainder_min_one" if args.min_one_per_positive_cell else "largest_remainder"
    allocations = allocate_largest_remainder(
        weights,
        args.sample_size,
        min_one_per_positive_cell=args.min_one_per_positive_cell,
    )
    id_prefix = args.id_prefix or infer_iso2(cells)
    personas = build_personas(
        cells,
        allocations,
        id_prefix=id_prefix,
        id_width=args.id_width,
        start_index=args.start_index,
        allocation_method=allocation_method,
    )
    write_jsonl(args.output, personas)
    audit = audit_summary(
        cells,
        allocations,
        personas,
        requested_sample_size=args.sample_size,
        allocation_method=allocation_method,
    )
    if args.audit:
        args.audit.parent.mkdir(parents=True, exist_ok=True)
        args.audit.write_text(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    else:
        print(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
