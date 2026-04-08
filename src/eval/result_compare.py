from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CompareVerdict:
    match: bool
    score: float
    reason: str = ""


def _rows_as_sets(rows: list[tuple]) -> set[tuple]:
    """Normalize rows into a frozenset for order-insensitive comparison."""
    normalized = []
    for row in rows:
        normalized.append(tuple(row))
    return set(normalized)


def _numeric_close(a, b, tol: float) -> bool:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) <= tol
    return a == b


def _stable_sort_key(row: tuple) -> tuple:
    """Sort key that handles mixed types deterministically."""
    return tuple((type(v).__name__, str(v)) for v in row)


def _rows_match_with_tolerance(
    gold: list[tuple], actual: list[tuple], tol: float, order_sensitive: bool
) -> tuple[bool, float]:
    if len(gold) != len(actual):
        # Partial overlap score: count matching rows.
        # Note: partial overlap ignores numeric_tolerance (known limitation).
        gold_set = _rows_as_sets(gold)
        actual_set = _rows_as_sets(actual)
        overlap = len(gold_set & actual_set)
        total = max(len(gold_set), len(actual_set))
        return False, overlap / total if total > 0 else 0.0

    if not order_sensitive:
        gold = sorted(gold, key=_stable_sort_key)
        actual = sorted(actual, key=_stable_sort_key)

    matched = 0
    for g, a in zip(gold, actual):
        if len(g) != len(a):
            continue
        if all(_numeric_close(gv, av, tol) for gv, av in zip(g, a)):
            matched += 1

    score = matched / len(gold) if gold else 1.0
    return score == 1.0, score


def compare_results(
    gold_rows: list[tuple] | None = None,
    actual_rows: list[tuple] | None = None,
    order_sensitive: bool = False,
    numeric_tolerance: float = 0.0,
    expected_behavior: str = "answer",
    actual_behavior: str = "answer",
) -> CompareVerdict:
    """Compare actual query results against gold, handling behavior routing."""

    # Behavior-level comparison (clarify/abstain cases)
    if expected_behavior in ("clarify", "abstain"):
        if actual_behavior == expected_behavior:
            return CompareVerdict(match=True, score=1.0, reason="behavior_match")
        return CompareVerdict(
            match=False, score=0.0,
            reason=f"expected {expected_behavior}, got {actual_behavior}",
        )

    # Result-set comparison (answer cases)
    if gold_rows is None or actual_rows is None:
        return CompareVerdict(match=False, score=0.0, reason="missing_data")

    if len(gold_rows) == 0 and len(actual_rows) == 0:
        return CompareVerdict(match=True, score=1.0, reason="both_empty")

    is_match, score = _rows_match_with_tolerance(
        gold_rows, actual_rows, numeric_tolerance, order_sensitive
    )
    reason = "exact_match" if is_match else "partial_or_mismatch"
    return CompareVerdict(match=is_match, score=score, reason=reason)
