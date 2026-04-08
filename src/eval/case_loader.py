from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class EvalCase:
    case_id: str
    category: str
    polarity: str
    expected_behavior: str
    difficulty: str
    query: str
    tags: list[str]
    expected_semantics: dict
    notes: str
    eval_tier: str


def load_cases(
    path: Path,
    tier: str | None = None,
    category: str | None = None,
) -> list[EvalCase]:
    """Load eval cases from a JSONL file, optionally filtering by tier or category."""
    cases: list[EvalCase] = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            raw = json.loads(line)
            case = EvalCase(
                case_id=raw["case_id"],
                category=raw["category"],
                polarity=raw["polarity"],
                expected_behavior=raw["expected_behavior"],
                difficulty=raw["difficulty"],
                query=raw["query"],
                tags=raw.get("tags", []),
                expected_semantics=raw.get("expected_semantics", {}),
                notes=raw.get("notes", ""),
                eval_tier=raw.get("eval_tier", "core"),
            )
            if tier and case.eval_tier != tier:
                continue
            if category and case.category != category:
                continue
            cases.append(case)
    return cases
