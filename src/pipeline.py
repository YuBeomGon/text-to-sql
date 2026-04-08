from __future__ import annotations

from dataclasses import dataclass, field

import duckdb

from src.executor import execute_query
from src.llm_client import generate_sql
from src.prompt_builder import build_system_prompt, build_user_prompt
from src.schema_inspector import get_columns, get_tables


@dataclass
class PipelineResult:
    behavior: str  # "answer", "clarify", "abstain"
    sql: str | None = None
    columns: list[str] = field(default_factory=list)
    rows: list[tuple] = field(default_factory=list)
    success: bool = False
    error: str | None = None
    raw_llm_output: str = ""


def _get_schema(conn: duckdb.DuckDBPyConnection) -> dict[str, dict[str, str]]:
    schema = {}
    for table in get_tables(conn):
        schema[table] = get_columns(conn, table)
    return schema


def run_question(
    conn: duckdb.DuckDBPyConnection,
    question: str,
    model: str | None = None,
) -> PipelineResult:
    """Run a natural language question through the full NL2SQL pipeline."""
    schema = _get_schema(conn)
    system_prompt = build_system_prompt(schema)
    user_prompt = build_user_prompt(question)

    raw_output = generate_sql(system_prompt, user_prompt, model=model)

    if raw_output.startswith("CLARIFY:"):
        return PipelineResult(
            behavior="clarify",
            raw_llm_output=raw_output,
        )
    if raw_output.startswith("ABSTAIN:"):
        return PipelineResult(
            behavior="abstain",
            raw_llm_output=raw_output,
        )

    query_result = execute_query(conn, raw_output)

    return PipelineResult(
        behavior="answer",
        sql=raw_output,
        columns=query_result.columns,
        rows=query_result.rows,
        success=query_result.success,
        error=query_result.error,
        raw_llm_output=raw_output,
    )
