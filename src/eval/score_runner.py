"""CLI entrypoint for ./score.sh.

Usage:
    python -m src.eval.score_runner --quick
    python -m src.eval.score_runner --full
    python -m src.eval.score_runner --quick --stub   (no LLM, baseline zeros)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from src.config import load_config
from src.db import create_connection
from src.eval.case_loader import load_cases
from src.eval.result_compare import compare_results
from src.eval.scorer import CaseOutcome, compute_scores
from src.executor import execute_query
from src.loader import load_contracts_csv
from src.pipeline import run_question

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_CASES_PATH = _PROJECT_ROOT / "eval" / "cases" / "combined_hard_cases.jsonl"
_GOLD_PATH = _PROJECT_ROOT / "eval" / "cases" / "gold_easy_baseline.jsonl"


def _load_gold_sql() -> dict[str, str]:
    """Load gold SQL keyed by case_id."""
    gold = {}
    if _GOLD_PATH.exists():
        with open(_GOLD_PATH) as f:
            for line in f:
                entry = json.loads(line.strip())
                gold[entry["case_id"]] = entry["gold_sql"]
    return gold


def _find_csv_files() -> list[Path]:
    """Find downloaded CSV files in datasets/."""
    cfg = load_config()
    datasets_dir = _PROJECT_ROOT / cfg.datasets_dir
    csv_files = sorted(datasets_dir.glob("**/*.csv"))
    return csv_files


def _setup_db():
    """Create DuckDB connection and load any available CSV data."""
    conn = create_connection()
    csv_files = _find_csv_files()
    for csv_path in csv_files:
        load_contracts_csv(conn, csv_path)
    return conn


def _run_real_pipeline(tier: str | None) -> list[CaseOutcome]:
    """Run the real NL2SQL pipeline against eval cases."""
    cases = load_cases(_CASES_PATH, tier=tier)
    gold_sql = _load_gold_sql()
    conn = _setup_db()

    outcomes = []
    for c in cases:
        pipeline_result = run_question(conn, c.query)
        actual_behavior = pipeline_result.behavior

        result_score = 0.0
        if c.expected_behavior == "answer" and actual_behavior == "answer":
            if c.case_id in gold_sql and pipeline_result.success:
                gold_result = execute_query(conn, gold_sql[c.case_id])
                if gold_result.success:
                    verdict = compare_results(
                        gold_rows=gold_result.rows,
                        actual_rows=pipeline_result.rows,
                        order_sensitive=False,
                        numeric_tolerance=0.01,
                    )
                    result_score = verdict.score
        elif c.expected_behavior in ("clarify", "abstain"):
            verdict = compare_results(
                expected_behavior=c.expected_behavior,
                actual_behavior=actual_behavior,
            )
            result_score = verdict.score

        outcomes.append(
            CaseOutcome(
                case_id=c.case_id,
                category=c.category,
                expected_behavior=c.expected_behavior,
                actual_behavior=actual_behavior,
                result_score=result_score,
                execution_success=pipeline_result.success if actual_behavior == "answer" else True,
            )
        )
        status = "OK" if result_score > 0 else "MISS"
        print(f"  [{status}] {c.case_id}: {actual_behavior} (score={result_score:.2f})", file=sys.stderr)

    conn.close()
    return outcomes


def _run_stub_pipeline(tier: str | None) -> list[CaseOutcome]:
    """Stub: no LLM pipeline. Every case gets score 0."""
    cases = load_cases(_CASES_PATH, tier=tier)
    return [
        CaseOutcome(
            case_id=c.case_id,
            category=c.category,
            expected_behavior=c.expected_behavior,
            actual_behavior="none",
            result_score=0.0,
            execution_success=False,
        )
        for c in cases
    ]


def main() -> None:
    args = sys.argv[1:]
    use_stub = "--stub" in args
    args = [a for a in args if a != "--stub"]

    mode = args[0] if args else "--quick"
    if mode not in ("--quick", "--full"):
        print("Usage: python -m src.eval.score_runner [--quick | --full] [--stub]", file=sys.stderr)
        sys.exit(2)

    tier = "core" if mode == "--quick" else None

    if use_stub:
        outcomes = _run_stub_pipeline(tier)
    else:
        outcomes = _run_real_pipeline(tier)

    report = compute_scores(outcomes)
    print(report.format_text())


if __name__ == "__main__":
    main()
