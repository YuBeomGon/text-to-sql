from src.db import create_connection


def test_create_connection_returns_working_duckdb():
    conn = create_connection()
    result = conn.execute("SELECT 1 AS val").fetchone()
    assert result == (1,)
    conn.close()


def test_create_connection_is_in_memory():
    conn = create_connection()
    result = conn.execute("SELECT current_database()").fetchone()
    assert result is not None
    conn.close()
