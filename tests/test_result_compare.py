from src.eval.result_compare import compare_results, CompareVerdict


def test_exact_match():
    gold_rows = [(1, "NASA", 5000000.0)]
    actual_rows = [(1, "NASA", 5000000.0)]
    verdict = compare_results(gold_rows, actual_rows, order_sensitive=False)
    assert verdict.match is True
    assert verdict.score == 1.0


def test_order_insensitive_match():
    gold = [(1, "A"), (2, "B")]
    actual = [(2, "B"), (1, "A")]
    verdict = compare_results(gold, actual, order_sensitive=False)
    assert verdict.match is True


def test_order_sensitive_mismatch():
    gold = [(1, "A"), (2, "B")]
    actual = [(2, "B"), (1, "A")]
    verdict = compare_results(gold, actual, order_sensitive=True)
    assert verdict.match is False


def test_row_count_mismatch():
    gold = [(1,), (2,)]
    actual = [(1,), (2,), (3,)]
    verdict = compare_results(gold, actual, order_sensitive=False)
    assert verdict.match is False


def test_empty_both():
    verdict = compare_results([], [], order_sensitive=False)
    assert verdict.match is True
    assert verdict.score == 1.0


def test_numeric_tolerance():
    gold = [(1000000.001,)]
    actual = [(1000000.002,)]
    verdict = compare_results(gold, actual, order_sensitive=False, numeric_tolerance=0.01)
    assert verdict.match is True


def test_partial_overlap_score():
    gold = [(1,), (2,), (3,)]
    actual = [(1,), (2,), (4,)]
    verdict = compare_results(gold, actual, order_sensitive=False)
    assert verdict.match is False
    assert 0.0 < verdict.score < 1.0


def test_clarify_behavior_match():
    verdict = compare_results(
        gold_rows=None,
        actual_rows=None,
        expected_behavior="clarify",
        actual_behavior="clarify",
    )
    assert verdict.match is True


def test_clarify_expected_but_answered():
    verdict = compare_results(
        gold_rows=None,
        actual_rows=[(1,)],
        expected_behavior="clarify",
        actual_behavior="answer",
    )
    assert verdict.match is False
