from __future__ import annotations

from dataclasses import dataclass, field

import duckdb

from src.executor import execute_query
from src.ir import QuestionIR
from src.llm_client import generate_sql
from src.prompt_builder import build_system_prompt, build_user_prompt
from src.schema_inspector import get_columns, get_tables
from src.semantics.entity_resolver import resolve_entities
from src.semantics.metric_interpreter import interpret_metric
from src.semantics.time_interpreter import interpret_time
from src.semantics.scope_interpreter import interpret_scope
from src.semantics.ambiguity_detector import detect_ambiguity


@dataclass
class PipelineResult:
    behavior: str  # "answer", "clarify", "abstain"
    sql: str | None = None
    columns: list[str] = field(default_factory=list)
    rows: list[tuple] = field(default_factory=list)
    success: bool = False
    error: str | None = None
    raw_llm_output: str = ""
    ir: QuestionIR | None = None


def _get_schema(conn: duckdb.DuckDBPyConnection) -> dict[str, dict[str, str]]:
    schema = {}
    for table in get_tables(conn):
        schema[table] = get_columns(conn, table)
    return schema


def _build_ir(question: str) -> QuestionIR:
    """Run the question through all semantic interpretation stages."""
    ir = resolve_entities(question)
    ir = interpret_metric(ir)
    ir = interpret_time(ir)
    ir = interpret_scope(ir)
    ir = detect_ambiguity(ir)
    return ir


def run_question(
    conn: duckdb.DuckDBPyConnection,
    question: str,
    model: str | None = None,
) -> PipelineResult:
    """Run a natural language question through the IR-based NL2SQL pipeline."""
    # Stage 1: Semantic interpretation -> IR
    ir = _build_ir(question)

    # Stage 2: Check if we should clarify or abstain before calling LLM
    if ir.should_clarify:
        return PipelineResult(
            behavior="clarify",
            ir=ir,
            raw_llm_output=ir.clarify_reason,
        )
    if ir.should_abstain:
        return PipelineResult(
            behavior="abstain",
            ir=ir,
            raw_llm_output=ir.abstain_reason,
        )

    # Stage 3: Build prompts from IR + schema
    schema = _get_schema(conn)
    system_prompt = build_system_prompt(schema, ir)
    user_prompt = build_user_prompt(ir)

    # Stage 4: LLM generates SQL
    raw_output = generate_sql(system_prompt, user_prompt, model=model)

    # Check for LLM-level CLARIFY/ABSTAIN
    if raw_output.startswith("CLARIFY:"):
        return PipelineResult(behavior="clarify", ir=ir, raw_llm_output=raw_output)
    if raw_output.startswith("ABSTAIN:"):
        return PipelineResult(behavior="abstain", ir=ir, raw_llm_output=raw_output)

    # Stage 5: Execute SQL
    query_result = execute_query(conn, raw_output)

    return PipelineResult(
        behavior="answer",
        sql=raw_output,
        columns=query_result.columns,
        rows=query_result.rows,
        success=query_result.success,
        error=query_result.error,
        raw_llm_output=raw_output,
        ir=ir,
    )
