from src.prompt_builder import build_system_prompt, build_user_prompt


def test_build_system_prompt_contains_schema():
    schema = {"contracts": {"award_id": "VARCHAR", "fiscal_year": "INTEGER", "total_obligation": "DOUBLE"}}
    prompt = build_system_prompt(schema)
    assert "contracts" in prompt
    assert "award_id" in prompt
    assert "VARCHAR" in prompt
    assert "SELECT" in prompt.upper() or "SQL" in prompt.upper()


def test_build_system_prompt_contains_rules():
    schema = {"contracts": {"award_id": "VARCHAR"}}
    prompt = build_system_prompt(schema)
    assert "DuckDB" in prompt
    assert "contracts" in prompt.lower()


def test_build_user_prompt_contains_question():
    prompt = build_user_prompt("How many contracts did NASA award in fiscal year 2024?")
    assert "NASA" in prompt
    assert "2024" in prompt


def test_build_user_prompt_instructs_sql_only():
    prompt = build_user_prompt("Show total obligation for DoD")
    assert "SQL" in prompt.upper()
