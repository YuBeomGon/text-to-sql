from src.eval.case_loader import load_cases, EvalCase


def test_load_all_cases(eval_cases_dir):
    cases = load_cases(eval_cases_dir / "combined_hard_cases.jsonl")
    assert len(cases) == 228
    assert all(isinstance(c, EvalCase) for c in cases)


def test_load_cases_filter_core_tier(eval_cases_dir):
    cases = load_cases(eval_cases_dir / "combined_hard_cases.jsonl", tier="core")
    assert all(c.eval_tier == "core" for c in cases)
    assert len(cases) == 190


def test_load_cases_filter_by_category(eval_cases_dir):
    cases = load_cases(eval_cases_dir / "combined_hard_cases.jsonl", category="metric_ambiguity")
    assert all(c.category == "metric_ambiguity" for c in cases)
    assert len(cases) >= 26


def test_eval_case_has_expected_fields(eval_cases_dir):
    cases = load_cases(eval_cases_dir / "combined_hard_cases.jsonl")
    c = cases[0]
    assert c.case_id is not None
    assert c.query is not None
    assert c.expected_behavior in ("answer", "clarify", "abstain")
    assert c.polarity in ("positive", "ambiguous", "negative")
