from src.eval.scorer import compute_scores, ScoreReport, CaseOutcome


def _make_outcomes() -> list[CaseOutcome]:
    return [
        CaseOutcome(case_id="EASY-001", category="easy_baseline", expected_behavior="answer", actual_behavior="answer", result_score=1.0, execution_success=True),
        CaseOutcome(case_id="EASY-002", category="easy_baseline", expected_behavior="answer", actual_behavior="answer", result_score=1.0, execution_success=True),
        CaseOutcome(case_id="MET-002", category="metric_ambiguity", expected_behavior="answer", actual_behavior="answer", result_score=0.0, execution_success=True),
        CaseOutcome(case_id="MET-001", category="metric_ambiguity", expected_behavior="clarify", actual_behavior="clarify", result_score=1.0, execution_success=True),
        CaseOutcome(case_id="SCOPE-001", category="scope_state", expected_behavior="clarify", actual_behavior="answer", result_score=0.0, execution_success=True),
    ]


def test_compute_scores_returns_report():
    outcomes = _make_outcomes()
    report = compute_scores(outcomes)
    assert isinstance(report, ScoreReport)


def test_positive_result_accuracy():
    outcomes = _make_outcomes()
    report = compute_scores(outcomes)
    assert abs(report.positive_result_accuracy - 2 / 3) < 0.01


def test_negative_abstain_f1():
    outcomes = _make_outcomes()
    report = compute_scores(outcomes)
    assert report.negative_abstain_precision == 1.0
    assert report.negative_abstain_recall == 0.5


def test_execution_success():
    outcomes = _make_outcomes()
    report = compute_scores(outcomes)
    assert report.execution_success == 1.0


def test_risky_answer_rate():
    outcomes = _make_outcomes()
    report = compute_scores(outcomes)
    assert abs(report.risky_answer_rate - 1 / 5) < 0.01


def test_total_weighted_score():
    outcomes = _make_outcomes()
    report = compute_scores(outcomes)
    assert 0.0 <= report.total <= 1.0
