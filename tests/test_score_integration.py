"""Integration test: load cases → stub outcomes → compute score → format report."""
from src.eval.case_loader import load_cases
from src.eval.scorer import CaseOutcome, compute_scores


def test_full_quick_pipeline(eval_cases_dir):
    cases_path = eval_cases_dir / "combined_hard_cases.jsonl"
    cases = load_cases(cases_path, tier="core")
    assert len(cases) == 190

    outcomes = []
    for c in cases:
        outcomes.append(
            CaseOutcome(
                case_id=c.case_id,
                category=c.category,
                expected_behavior=c.expected_behavior,
                actual_behavior="none",
                result_score=0.0,
                execution_success=False,
            )
        )

    report = compute_scores(outcomes)
    assert report.case_count == 190
    assert report.execution_success == 0.0
    assert report.positive_result_accuracy == 0.0
    text = report.format_text()
    assert "execution_success" in text
    assert "FAIL" in text


def test_perfect_score_pipeline(eval_cases_dir):
    """Simulate all-correct outcomes to verify scoring math."""
    cases_path = eval_cases_dir / "combined_hard_cases.jsonl"
    cases = load_cases(cases_path, tier="core")
    outcomes = []
    for c in cases:
        outcomes.append(
            CaseOutcome(
                case_id=c.case_id,
                category=c.category,
                expected_behavior=c.expected_behavior,
                actual_behavior=c.expected_behavior,
                result_score=1.0,
                execution_success=True,
            )
        )

    report = compute_scores(outcomes)
    assert report.execution_success == 1.0
    assert report.positive_result_accuracy == 1.0
    assert report.negative_abstain_f1 == 1.0
    assert report.risky_answer_rate == 0.0
    assert report.total == 1.0
