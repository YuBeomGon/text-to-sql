from __future__ import annotations

from src.ir import QuestionIR


def build_system_prompt(schema: dict[str, dict[str, str]], ir: QuestionIR) -> str:
    """Build the system prompt using schema and IR context."""
    schema_lines = []
    for table, columns in schema.items():
        col_defs = ", ".join(f"{col} {dtype}" for col, dtype in columns.items())
        schema_lines.append(f"  {table}({col_defs})")
    schema_text = "\n".join(schema_lines)

    # Build context hints from IR
    hints = []
    if ir.entities.get("agency"):
        hints.append(f"Agency filter: awarding_agency_name = '{ir.entities['agency']}'")
    if ir.entities.get("recipient"):
        hints.append(f"Recipient filter: recipient_name ILIKE '%{ir.entities['recipient']}%'")
    if ir.time_range:
        fy = ir.time_range.get("fiscal_year")
        if fy:
            hints.append(f"Time filter: fiscal_year = {fy}")
        q = ir.time_range.get("quarter")
        if q:
            hints.append(f"Quarter: Q{q} of FY{fy}")
    if ir.metric:
        if ir.metric.get("expression"):
            hints.append(f"Metric: use {ir.metric['expression']}")
        elif ir.metric.get("column"):
            hints.append(f"Metric column: {ir.metric['column']}")

    hints_text = "\n".join(f"- {h}" for h in hints) if hints else "- No specific hints derived from question"

    return f"""You are a SQL expert for a DuckDB database containing USAspending federal contract data.

Database schema:
{schema_text}

Interpreted context from the question:
{hints_text}

Rules:
- Write valid DuckDB SQL only.
- Return ONLY the SQL query, nothing else. No explanations.
- Use the interpreted context above to guide your query.
- If the question is ambiguous about which metric to use, respond with exactly: CLARIFY: <reason>
- If the question cannot be answered from the schema, respond with exactly: ABSTAIN: <reason>"""


def build_user_prompt(ir: QuestionIR) -> str:
    """Build the user prompt from the IR."""
    q = ir.normalized_question if ir.normalized_question else ir.raw_question
    return f"Write a SQL query to answer this question:\n{q}"
