from __future__ import annotations

import duckdb


def get_tables(conn: duckdb.DuckDBPyConnection) -> list[str]:
    """Return list of table names in the current database."""
    rows = conn.execute("SHOW TABLES").fetchall()
    return [row[0] for row in rows]


def get_columns(conn: duckdb.DuckDBPyConnection, table: str) -> dict[str, str]:
    """Return {column_name: column_type} for the given table."""
    rows = conn.execute(f'DESCRIBE "{table}"').fetchall()
    return {row[0]: row[1] for row in rows}
