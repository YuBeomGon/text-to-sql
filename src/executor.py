from __future__ import annotations

from dataclasses import dataclass, field

import duckdb


@dataclass
class QueryResult:
    success: bool
    columns: list[str] = field(default_factory=list)
    rows: list[tuple] = field(default_factory=list)
    error: str | None = None


def execute_query(conn: duckdb.DuckDBPyConnection, sql: str) -> QueryResult:
    """Execute SQL against DuckDB and return a structured result."""
    try:
        rel = conn.execute(sql)
        columns = [desc[0] for desc in rel.description]
        rows = rel.fetchall()
        return QueryResult(success=True, columns=columns, rows=rows)
    except duckdb.Error as e:
        return QueryResult(success=False, error=str(e))
