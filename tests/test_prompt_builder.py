from src.prompt_builder import build_system_prompt, build_user_prompt
from src.ir import QuestionIR


def test_build_system_prompt_contains_schema():
    schema = {"contracts": {"award_id": "VARCHAR", "fiscal_year": "INTEGER"}}
    ir = QuestionIR(raw_question="test")
    prompt = build_system_prompt(schema, ir)
    assert "contracts" in prompt
    assert "award_id" in prompt


def test_build_system_prompt_contains_ir_hints():
    schema = {"contracts": {"award_id": "VARCHAR"}}
    ir = QuestionIR(
        raw_question="NASA obligations in FY2025",
        entities={"agency": "NASA"},
        time_range={"fiscal_year": 2025},
        metric={"column": "total_obligation", "expression": "SUM(total_obligation)"},
    )
    prompt = build_system_prompt(schema, ir)
    assert "NASA" in prompt
    assert "2025" in prompt
    assert "total_obligation" in prompt


def test_build_user_prompt_uses_normalized():
    ir = QuestionIR(
        raw_question="DHS contracts",
        normalized_question="Department of Homeland Security contracts",
    )
    prompt = build_user_prompt(ir)
    assert "Department of Homeland Security" in prompt
    assert "DHS" not in prompt


def test_build_user_prompt_falls_back_to_raw():
    ir = QuestionIR(raw_question="NASA contracts")
    prompt = build_user_prompt(ir)
    assert "NASA" in prompt
