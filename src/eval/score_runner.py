"""CLI entrypoint for ./score.sh.

Usage:
    python -m src.eval.score_runner --quick
    python -m src.eval.score_runner --full

At this stage (pre-M2), there is no NL2SQL pipeline yet.
The runner loads eval cases, produces a "stub" outcome for each
(execution_success=False, result_score=0.0, actual_behavior="none"),
and computes the baseline score.

As modules are added in M2+, the runner will call the real pipeline
and compare against gold results.
"""
from __future__ import annotations

import sys
from pathlib import Path

from src.eval.case_loader import load_cases
from src.eval.scorer import CaseOutcome, compute_scores

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_CASES_PATH = _PROJECT_ROOT / "eval" / "cases" / "combined_hard_cases.jsonl"


def _run_stub_pipeline(tier: str) -> list[CaseOutcome]:
    """Stub: no NL2SQL pipeline yet. Every case gets score 0."""
    cases = load_cases(_CASES_PATH, tier=tier)
    outcomes = []
    for c in cases:
        outcomes.append(
            CaseOutcome(
                case_id=c.case_id,
                category=c.category,
                expected_behavior=c.expected_behavior,
                actual_behavior="none",
                result_score=0.0,
                execution_success=False,
            )
        )
    return outcomes


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "--quick"
    if mode not in ("--quick", "--full"):
        print("Usage: python -m src.eval.score_runner [--quick | --full]", file=sys.stderr)
        sys.exit(2)

    tier = "core" if mode == "--quick" else None
    outcomes = _run_stub_pipeline(tier)
    report = compute_scores(outcomes)
    print(report.format_text())


if __name__ == "__main__":
    main()
