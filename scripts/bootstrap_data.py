#!/usr/bin/env python3
"""Download USAspending data and load it into DuckDB for verification.

Usage:
    python scripts/bootstrap_data.py

This script:
1. Downloads contract data for the 5 core agencies, FY2024-2025
2. Extracts CSVs to datasets/
3. Loads them into DuckDB in-memory
4. Prints row counts and sample data for verification
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import load_config
from src.data_download import fetch_data
from src.db import create_connection
from src.loader import load_contracts_csv
from src.schema_inspector import get_tables, get_columns

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def main():
    cfg = load_config()
    dest_dir = PROJECT_ROOT / cfg.datasets_dir

    # FY2025: Oct 1 2024 — Sep 30 2025
    csv_paths = fetch_data(
        agencies=cfg.core_agencies,
        start_date="2024-10-01",
        end_date="2025-09-30",
        dest_dir=dest_dir,
    )

    if not csv_paths:
        print("ERROR: No CSV files extracted.")
        sys.exit(1)

    print(f"\nLoading {len(csv_paths)} CSV file(s) into DuckDB...")
    conn = create_connection()
    for csv_path in csv_paths:
        print(f"  Loading: {csv_path.name}")
        load_contracts_csv(conn, csv_path)

    # Verify
    tables = get_tables(conn)
    print(f"\nTables: {tables}")

    if "contracts" in tables:
        row_count = conn.execute("SELECT COUNT(*) FROM contracts").fetchone()[0]
        print(f"Total rows: {row_count}")

        agency_counts = conn.execute("""
            SELECT awarding_agency_name, COUNT(*) as cnt
            FROM contracts
            GROUP BY awarding_agency_name
            ORDER BY cnt DESC
        """).fetchall()
        print("\nRows by agency:")
        for agency, cnt in agency_counts:
            print(f"  {agency}: {cnt}")

        columns = get_columns(conn, "contracts")
        print(f"\nColumns ({len(columns)}): {list(columns.keys())}")

    conn.close()
    print("\nDone. Data files are in datasets/")


if __name__ == "__main__":
    main()
