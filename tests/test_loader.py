import tempfile
import csv
from pathlib import Path

from src.db import create_connection
from src.loader import load_contracts_csv


def _write_sample_csv(directory: Path) -> Path:
    """Write a tiny CSV that mimics USAspending contract columns."""
    filepath = directory / "contracts_sample.csv"
    rows = [
        {
            "award_id_piid": "AWD-T01",
            "awarding_agency_name": "NASA",
            "awarding_sub_agency_name": "JPL",
            "recipient_name": "SpaceX",
            "award_type": "contract",
            "fiscal_year": "2024",
            "total_obligation": "1000000.00",
            "total_outlay": "500000.00",
            "total_award_amount": "1200000.00",
            "action_date": "2024-02-15",
            "period_of_performance_start_date": "2024-02-01",
            "naics_code": "336414",
            "award_status": "active",
        },
    ]
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    return filepath


def test_load_contracts_csv_creates_table(tmp_path):
    csv_path = _write_sample_csv(tmp_path)
    conn = create_connection()
    load_contracts_csv(conn, csv_path)
    tables = conn.execute("SHOW TABLES").fetchall()
    table_names = [t[0] for t in tables]
    assert "contracts" in table_names
    conn.close()


def test_load_contracts_csv_row_count(tmp_path):
    csv_path = _write_sample_csv(tmp_path)
    conn = create_connection()
    load_contracts_csv(conn, csv_path)
    count = conn.execute("SELECT COUNT(*) FROM contracts").fetchone()[0]
    assert count == 1
    conn.close()


def test_load_contracts_csv_column_mapping(tmp_path):
    csv_path = _write_sample_csv(tmp_path)
    conn = create_connection()
    load_contracts_csv(conn, csv_path)
    row = conn.execute("SELECT award_id, awarding_agency_name, fiscal_year, total_obligation FROM contracts").fetchone()
    assert row[0] == "AWD-T01"
    assert row[1] == "NASA"
    assert row[2] == 2024
    assert row[3] == 1000000.00
    conn.close()
