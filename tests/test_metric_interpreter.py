from src.semantics.metric_interpreter import interpret_metric
from src.ir import QuestionIR


def test_interpret_obligation():
    ir = QuestionIR(raw_question="total obligation for NASA")
    result = interpret_metric(ir)
    assert result.metric is not None
    assert result.metric["column"] == "total_obligation"


def test_interpret_outlay():
    ir = QuestionIR(raw_question="total outlay for DHS")
    result = interpret_metric(ir)
    assert result.metric["column"] == "total_outlay"


def test_interpret_count_awards():
    ir = QuestionIR(raw_question="how many contracts did NASA award")
    result = interpret_metric(ir)
    assert result.metric is not None
    assert "COUNT(DISTINCT award_id)" in result.metric["expression"]


def test_interpret_count_transactions():
    ir = QuestionIR(raw_question="total number of contract transactions for DHS")
    result = interpret_metric(ir)
    assert result.metric is not None
    assert "COUNT(*)" in result.metric["expression"]


def test_interpret_ambiguous_amount():
    ir = QuestionIR(raw_question="what is the amount for NASA contracts")
    result = interpret_metric(ir)
    assert result.should_clarify is True
    assert len(result.ambiguities) > 0


def test_interpret_explicit_metric_not_ambiguous():
    ir = QuestionIR(raw_question="total obligation for NASA")
    result = interpret_metric(ir)
    assert result.should_clarify is False
