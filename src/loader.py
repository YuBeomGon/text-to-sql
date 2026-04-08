from __future__ import annotations

from pathlib import Path

import duckdb

_COLUMN_MAP = {
    "award_id_piid": "award_id",
    "awarding_agency_name": "awarding_agency_name",
    "awarding_sub_agency_name": "awarding_sub_agency_name",
    "recipient_name": "recipient_name",
    "award_type": "award_type",
    "fiscal_year": "fiscal_year",
    "total_obligation": "total_obligation",
    "total_outlay": "total_outlay",
    "total_award_amount": "total_award_amount",
    "action_date": "action_date",
    "period_of_performance_start_date": "award_start_date",
    "naics_code": "naics_code",
    "award_status": "award_status",
}


def load_contracts_csv(
    conn: duckdb.DuckDBPyConnection,
    csv_path: Path,
) -> None:
    """Load a USAspending contracts CSV into the 'contracts' table."""
    source_cols = ", ".join(
        f'"{src}" AS {dst}' for src, dst in _COLUMN_MAP.items()
    )

    table_exists = conn.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'contracts'"
    ).fetchone()[0]

    if table_exists:
        conn.execute(f"""
            INSERT INTO contracts
            SELECT {source_cols}
            FROM read_csv_auto('{csv_path}', header=true, all_varchar=true)
        """)
    else:
        conn.execute(f"""
            CREATE TABLE contracts AS
            SELECT {source_cols}
            FROM read_csv_auto('{csv_path}', header=true, all_varchar=true)
        """)

    conn.execute("""
        CREATE OR REPLACE TABLE contracts AS
        SELECT
            award_id,
            awarding_agency_name,
            awarding_sub_agency_name,
            recipient_name,
            award_type,
            CAST(fiscal_year AS INTEGER) AS fiscal_year,
            CAST(total_obligation AS DOUBLE) AS total_obligation,
            CAST(total_outlay AS DOUBLE) AS total_outlay,
            CAST(total_award_amount AS DOUBLE) AS total_award_amount,
            TRY_CAST(action_date AS DATE) AS action_date,
            TRY_CAST(award_start_date AS DATE) AS award_start_date,
            naics_code,
            award_status
        FROM contracts
    """)
