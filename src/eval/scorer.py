from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CaseOutcome:
    case_id: str
    category: str
    expected_behavior: str
    actual_behavior: str
    result_score: float
    execution_success: bool


@dataclass
class ScoreReport:
    execution_success: float
    positive_result_accuracy: float
    negative_abstain_precision: float
    negative_abstain_recall: float
    negative_abstain_f1: float
    risky_answer_rate: float
    total: float
    case_count: int
    category_scores: dict[str, float]

    def format_text(self) -> str:
        lines = [
            "Score breakdown:",
            f"  case_count:                {self.case_count}",
            f"  execution_success:         {self.execution_success:.3f}",
            f"  positive_result_accuracy:  {self.positive_result_accuracy:.3f}",
            f"  negative_abstain_f1:       {self.negative_abstain_f1:.3f}",
            f"  risky_answer_rate:         {self.risky_answer_rate:.3f}",
            "",
            f"Total: {self.total:.3f}",
            "",
            "Gates:",
            f"  execution_success: {'PASS' if self.execution_success >= 0.995 else 'FAIL'}",
            f"  risky_answer_rate: {'PASS' if self.risky_answer_rate <= 0.02 else 'FAIL'}",
        ]
        if self.category_scores:
            lines.append("")
            lines.append("Per-category accuracy:")
            for cat, score in sorted(self.category_scores.items()):
                lines.append(f"  {cat:30s} {score:.3f}")
        return "\n".join(lines)


# M1 baseline weights — simplified because per-axis metrics (metric_definition,
# time_axis, etc.) are not computable until M2+.
# Target weights are in docs/evaluation_framework.md section 5.2.
_WEIGHTS = {
    "positive_result_accuracy": 0.50,
    "negative_abstain_f1": 0.30,
    "execution_success": 0.10,
    "risky_answer_penalty": 0.10,
}


def compute_scores(outcomes: list[CaseOutcome]) -> ScoreReport:
    """Compute aggregate scores from a list of case outcomes."""
    if not outcomes:
        return ScoreReport(
            execution_success=0.0, positive_result_accuracy=0.0,
            negative_abstain_precision=0.0, negative_abstain_recall=0.0,
            negative_abstain_f1=0.0, risky_answer_rate=0.0,
            total=0.0, case_count=0, category_scores={},
        )

    exec_ok = sum(1 for o in outcomes if o.execution_success)
    exec_rate = exec_ok / len(outcomes)

    answer_cases = [o for o in outcomes if o.expected_behavior == "answer"]
    if answer_cases:
        pos_acc = sum(o.result_score for o in answer_cases) / len(answer_cases)
    else:
        pos_acc = 0.0

    neg_expected = [o for o in outcomes if o.expected_behavior in ("clarify", "abstain")]
    neg_predicted = [o for o in outcomes if o.actual_behavior in ("clarify", "abstain")]
    neg_correct = [
        o for o in outcomes
        if o.expected_behavior in ("clarify", "abstain")
        and o.actual_behavior in ("clarify", "abstain")
    ]

    neg_precision = len(neg_correct) / len(neg_predicted) if neg_predicted else 0.0
    neg_recall = len(neg_correct) / len(neg_expected) if neg_expected else 0.0
    neg_f1 = (
        2 * neg_precision * neg_recall / (neg_precision + neg_recall)
        if (neg_precision + neg_recall) > 0
        else 0.0
    )

    risky = sum(
        1 for o in outcomes
        if o.expected_behavior in ("clarify", "abstain")
        and o.actual_behavior == "answer"
    )
    risky_rate = risky / len(outcomes)

    cat_scores: dict[str, float] = {}
    cat_counts: dict[str, list[float]] = {}
    for o in answer_cases:
        cat_counts.setdefault(o.category, []).append(o.result_score)
    for cat, scores in cat_counts.items():
        cat_scores[cat] = sum(scores) / len(scores)

    total = (
        _WEIGHTS["positive_result_accuracy"] * pos_acc
        + _WEIGHTS["negative_abstain_f1"] * neg_f1
        + _WEIGHTS["execution_success"] * exec_rate
        + _WEIGHTS["risky_answer_penalty"] * (1.0 - risky_rate)
    )

    return ScoreReport(
        execution_success=exec_rate,
        positive_result_accuracy=pos_acc,
        negative_abstain_precision=neg_precision,
        negative_abstain_recall=neg_recall,
        negative_abstain_f1=neg_f1,
        risky_answer_rate=risky_rate,
        total=total,
        case_count=len(outcomes),
        category_scores=cat_scores,
    )
