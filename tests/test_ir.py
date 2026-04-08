from src.ir import QuestionIR


def test_question_ir_defaults():
    ir = QuestionIR(raw_question="How many contracts?")
    assert ir.raw_question == "How many contracts?"
    assert ir.normalized_question == ""
    assert ir.metric is None
    assert ir.entities == {}
    assert ir.time_range is None
    assert ir.scope == {}
    assert ir.ambiguities == []
    assert ir.should_clarify is False
    assert ir.should_abstain is False


def test_question_ir_with_values():
    ir = QuestionIR(
        raw_question="How many NASA contracts in FY2025?",
        normalized_question="How many NASA contracts in fiscal year 2025?",
        metric={"type": "count", "expression": "COUNT(DISTINCT award_id)"},
        entities={"agency": "NASA"},
        time_range={"fiscal_year": 2025},
        scope={"award_type": "contract_only"},
    )
    assert ir.entities["agency"] == "NASA"
    assert ir.time_range["fiscal_year"] == 2025
