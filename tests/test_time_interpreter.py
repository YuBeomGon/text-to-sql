from src.semantics.time_interpreter import interpret_time
from src.ir import QuestionIR


def test_interpret_fiscal_year():
    ir = QuestionIR(raw_question="contracts in fiscal year 2025")
    result = interpret_time(ir)
    assert result.time_range is not None
    assert result.time_range["fiscal_year"] == 2025


def test_interpret_fy_abbreviation():
    ir = QuestionIR(raw_question="NASA contracts in FY2024")
    result = interpret_time(ir)
    assert result.time_range["fiscal_year"] == 2024


def test_interpret_no_time():
    ir = QuestionIR(raw_question="total contracts for NASA")
    result = interpret_time(ir)
    assert result.time_range is None


def test_interpret_fiscal_quarter():
    ir = QuestionIR(raw_question="HHS contracts in fiscal year 2024 Q2")
    result = interpret_time(ir)
    assert result.time_range["fiscal_year"] == 2024
    assert result.time_range["quarter"] == 2
