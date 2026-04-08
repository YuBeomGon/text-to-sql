#!/usr/bin/env python3
"""Run 20 easy baseline cases through the real pipeline and print results.

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
EASY_CASES = PROJECT_ROOT / "eval" / "cases" / "easy_baseline.jsonl"
GOLD_FILE = PROJECT_ROOT / "eval" / "cases" / "gold_easy_baseline.jsonl"


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

    # Load cases and gold
    cases = [json.loads(l) for l in open(EASY_CASES)]
    gold = {e["case_id"]: e["gold_sql"] for e in (json.loads(l) for l in open(GOLD_FILE))}

    correct = 0
    total = len(cases)

    for c in cases:
        case_id = c["case_id"]
        query = c["query"]

        result = run_question(conn, query)

        if result.behavior != "answer":
            print(f"  [{case_id}] BEHAVIOR: {result.behavior} — expected answer")
            continue

        if not result.success:
            print(f"  [{case_id}] SQL ERROR: {result.error}")
            print(f"    SQL: {result.sql}")
            continue

        # Compare with gold
        if case_id in gold:
            gold_result = execute_query(conn, gold[case_id])
            if gold_result.success and gold_result.rows == result.rows:
                correct += 1
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
    conn.close()


if __name__ == "__main__":
    main()
