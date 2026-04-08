from __future__ import annotations

import re

from src.ir import QuestionIR


def interpret_scope(ir: QuestionIR) -> QuestionIR:
    """Determine the query scope from the question."""
    question_lower = ir.raw_question.lower()

    ir.scope["award_type"] = "contract_only"

    if re.search(r"\bprime\b", question_lower):
        ir.scope["prime_only"] = True

    if re.search(r"\bactive\b|\bopen\b", question_lower):
        ir.scope["active_only"] = True

    return ir
