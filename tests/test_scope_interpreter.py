from src.semantics.scope_interpreter import interpret_scope
from src.ir import QuestionIR


def test_default_scope_is_contracts():
    ir = QuestionIR(raw_question="NASA obligations")
    result = interpret_scope(ir)
    assert result.scope.get("award_type") == "contract_only"


def test_prime_only_scope():
    ir = QuestionIR(raw_question="prime contracts for DHS")
    result = interpret_scope(ir)
    assert result.scope.get("prime_only") is True
