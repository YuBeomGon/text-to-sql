import pytest
import duckdb
from pathlib import Path

from src.db import create_connection

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def project_root() -> Path:
    return _PROJECT_ROOT


@pytest.fixture
def eval_cases_dir(project_root) -> Path:
    return project_root / "eval" / "cases"


@pytest.fixture
def db_conn():
    """Provide a fresh in-memory DuckDB connection per test."""
    conn = create_connection()
    yield conn
    conn.close()


@pytest.fixture
def sample_db(db_conn):
    """DuckDB with a small sample contracts table for testing."""
    db_conn.execute("""
        CREATE TABLE contracts (
            award_id VARCHAR,
            awarding_agency_name VARCHAR,
            awarding_sub_agency_name VARCHAR,
            recipient_name VARCHAR,
            award_type VARCHAR,
            fiscal_year INTEGER,
            total_obligation DOUBLE,
            total_outlay DOUBLE,
            total_award_amount DOUBLE,
            action_date DATE,
            award_start_date DATE,
            naics_code VARCHAR,
            award_status VARCHAR
        )
    """)
    db_conn.execute("""
        INSERT INTO contracts VALUES
        ('AWD-001', 'Department of Defense', 'Army', 'Lockheed Martin Corp', 'contract', 2024, 5000000.0, 3000000.0, 6000000.0, '2024-01-15', '2024-01-01', '336411', 'active'),
        ('AWD-002', 'Department of Defense', 'Navy', 'Boeing Co', 'contract', 2024, 3000000.0, 2000000.0, 4000000.0, '2024-03-20', '2024-03-01', '336411', 'active'),
        ('AWD-003', 'NASA', 'Goddard', 'Northrop Grumman Corp', 'contract', 2024, 2000000.0, 1500000.0, 2500000.0, '2024-06-10', '2024-06-01', '541715', 'active'),
        ('AWD-004', 'NASA', 'JPL', 'Lockheed Martin Corp', 'contract', 2025, 4000000.0, 2500000.0, 5000000.0, '2024-11-05', '2024-10-01', '541715', 'active'),
        ('AWD-005', 'Department of Health and Human Services', 'CDC', 'Deloitte LLP', 'contract', 2025, 1000000.0, 800000.0, 1200000.0, '2025-01-10', '2025-01-01', '541611', 'active'),
        ('AWD-006', 'Department of Homeland Security', 'FEMA', 'Booz Allen Hamilton', 'contract', 2024, 1500000.0, 1000000.0, 2000000.0, '2024-04-15', '2024-04-01', '541611', 'closed'),
        ('AWD-007', 'General Services Administration', 'FAS', 'SAIC Inc', 'contract', 2025, 800000.0, 600000.0, 1000000.0, '2025-02-20', '2025-02-01', '541512', 'active')
    """)
    return db_conn
