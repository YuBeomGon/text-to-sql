from __future__ import annotations

from src.ir import QuestionIR


def detect_ambiguity(ir: QuestionIR) -> QuestionIR:
    """Final ambiguity check after all interpreters have run."""
    if ir.should_clarify or ir.should_abstain:
        return ir

    return ir
