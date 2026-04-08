from __future__ import annotations


def build_system_prompt(schema: dict[str, dict[str, str]]) -> str:
    """Build the system prompt with schema context for SQL generation."""
    schema_lines = []
    for table, columns in schema.items():
        col_defs = ", ".join(f"{col} {dtype}" for col, dtype in columns.items())
        schema_lines.append(f"  {table}({col_defs})")
    schema_text = "\n".join(schema_lines)

    return f"""You are a SQL expert for a DuckDB database containing USAspending federal contract data.

Database schema:
{schema_text}

Agency name aliases (always use the full name in SQL, never abbreviations):
- DoD, DOD → Department of Defense
- HHS → Department of Health and Human Services
- DHS → Department of Homeland Security
- GSA → General Services Administration
- NASA → NASA

Rules:
- Write valid DuckDB SQL only.
- Return ONLY the SQL query, nothing else. No explanations.
- CRITICAL: Always use the FULL agency name in WHERE clauses, never abbreviations. Example: WHERE awarding_agency_name = 'Department of Homeland Security', NOT 'DHS'.
- Use fiscal_year column for fiscal year filters (integer, e.g. 2024).
- Use awarding_agency_name for agency filters.
- Use total_obligation for obligation amounts, total_outlay for outlay amounts.
- Use recipient_name for contractor/recipient filters.
- For "contracts" scope, filter on the contracts table directly.
- COUNT awards means COUNT(DISTINCT award_id), not COUNT(*) of rows.
- If the question is ambiguous about which metric to use, respond with exactly: CLARIFY: <reason>
- If the question cannot be answered from the schema, respond with exactly: ABSTAIN: <reason>"""


def build_user_prompt(question: str) -> str:
    """Build the user prompt from a natural language question."""
    return f"Write a SQL query to answer this question:\n{question}"
