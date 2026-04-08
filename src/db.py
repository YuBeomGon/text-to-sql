from __future__ import annotations

import duckdb


def create_connection() -> duckdb.DuckDBPyConnection:
    """Create an in-memory DuckDB connection."""
    return duckdb.connect(database=":memory:")
