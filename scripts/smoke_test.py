#!/usr/bin/env python3
"""Run 50 smoke test cases through the real pipeline and print results.

Usage:
    python scripts/smoke_test.py

Requires:
- OPENAI_API_KEY in .env
- Data in datasets/ (run scripts/bootstrap_data.py first)
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.db import create_connection
from src.loader import load_contracts_csv
from src.executor import execute_query
from src.pipeline import run_question

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CASES_DIR = PROJECT_ROOT / "eval" / "cases"
SMOKE_CASES = CASES_DIR / "smoke_cases.jsonl"


def _load_all_cases() -> dict[str, dict]:
    """Load all cases from all JSONL files, keyed by case_id."""
    all_cases = {}
    for f in CASES_DIR.glob("*.jsonl"):
        if f.name in ("gold_easy_baseline.jsonl", "gold_smoke_hard.jsonl", "gold_result_snapshot_template.jsonl", "smoke_cases.jsonl"):
            continue
        for line in open(f):
            c = json.loads(line.strip())
            all_cases[c["case_id"]] = c
    return all_cases


def _load_gold() -> dict[str, str]:
    """Load gold SQL from both easy and hard gold files."""
    gold = {}
    for f in [CASES_DIR / "gold_easy_baseline.jsonl", CASES_DIR / "gold_smoke_hard.jsonl"]:
        if f.exists():
            for line in open(f):
                entry = json.loads(line.strip())
                gold[entry["case_id"]] = entry["gold_sql"]
    return gold


def main():
    # Load data
    csv_files = sorted((PROJECT_ROOT / "datasets").glob("**/*.csv"))
    if not csv_files:
        print("ERROR: No CSV files in datasets/. Run scripts/bootstrap_data.py first.")
        sys.exit(1)

    conn = create_connection()
    for f in csv_files:
        load_contracts_csv(conn, f)
    row_count = conn.execute("SELECT COUNT(*) FROM contracts").fetchone()[0]
    print(f"Loaded {row_count} rows into DuckDB\n")

    # Load smoke case IDs
    smoke_ids = [json.loads(l)["case_id"] for l in open(SMOKE_CASES)]
    all_cases = _load_all_cases()
    gold = _load_gold()

    correct = 0
    total = len(smoke_ids)
    by_category = {}

    for case_id in smoke_ids:
        c = all_cases.get(case_id)
        if not c:
            print(f"  [{case_id}] NOT FOUND in case files")
            continue

        query = c["query"]
        expected_behavior = c["expected_behavior"]
        result = run_question(conn, query)

        cat = c.get("category", "unknown")
        by_category.setdefault(cat, {"correct": 0, "total": 0})
        by_category[cat]["total"] += 1

        # Clarify/abstain cases: check behavior match
        if expected_behavior in ("clarify", "abstain"):
            if result.behavior == expected_behavior:
                correct += 1
                by_category[cat]["correct"] += 1
                print(f"  [{case_id}] CORRECT ({expected_behavior})")
            else:
                print(f"  [{case_id}] WRONG — expected {expected_behavior}, got {result.behavior}")
            continue

        # Answer cases
        if result.behavior != "answer":
            print(f"  [{case_id}] BEHAVIOR: {result.behavior} — expected answer")
            continue

        if not result.success:
            print(f"  [{case_id}] SQL ERROR: {result.error}")
            print(f"    SQL: {result.sql}")
            continue

        if case_id in gold:
            gold_result = execute_query(conn, gold[case_id])
            if gold_result.success and gold_result.rows == result.rows:
                correct += 1
                by_category[cat]["correct"] += 1
                print(f"  [{case_id}] CORRECT")
            else:
                print(f"  [{case_id}] MISMATCH")
                print(f"    Generated: {result.sql}")
                print(f"    Gold:      {gold[case_id]}")
                if result.rows:
                    print(f"    Got rows:  {result.rows[:3]}")
                if gold_result.success and gold_result.rows:
                    print(f"    Want rows: {gold_result.rows[:3]}")
        else:
            print(f"  [{case_id}] NO GOLD — executed ok, {len(result.rows)} rows")

    print(f"\nResult: {correct}/{total} correct ({correct/total*100:.0f}%)")
    print("\nPer-category:")
    for cat, counts in sorted(by_category.items()):
        c, t = counts["correct"], counts["total"]
        print(f"  {cat:30s} {c}/{t} ({c/t*100:.0f}%)" if t > 0 else f"  {cat:30s} 0/0")

    conn.close()


if __name__ == "__main__":
    main()
