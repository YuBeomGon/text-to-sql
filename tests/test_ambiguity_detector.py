from src.semantics.ambiguity_detector import detect_ambiguity
from src.ir import QuestionIR


def test_no_ambiguity():
    ir = QuestionIR(raw_question="total obligation for NASA in FY2025")
    ir.metric = {"column": "total_obligation"}
    ir.entities = {"agency": "NASA"}
    ir.time_range = {"fiscal_year": 2025}
    result = detect_ambiguity(ir)
    assert result.should_clarify is False


def test_ambiguity_already_flagged():
    ir = QuestionIR(raw_question="what is the amount")
    ir.should_clarify = True
    ir.ambiguities = ["amount is ambiguous"]
    result = detect_ambiguity(ir)
    assert result.should_clarify is True
