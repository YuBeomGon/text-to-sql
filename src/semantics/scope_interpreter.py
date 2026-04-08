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

    # Detect subagency references (pattern: "subagency X" or "for subagency X")
    sub_match = re.search(r"subagency\s+([A-Z][^,\.]+)", ir.raw_question)
    if sub_match:
        ir.scope["subagency"] = sub_match.group(1).strip()
    # Also detect "for <Proper Name>" after "within <Agency>"
    within_match = re.search(r"contracts?\s+for\s+(?:subagency\s+)?([A-Z][^,\.]+?)(?:\s+and\b|\s*$|\s*\.)", ir.raw_question)
    if within_match and "subagency" not in ir.scope:
        candidate = within_match.group(1).strip()
        # Don't treat agency names as subagencies
        if candidate not in (ir.entities.get("agency", ""), ""):
            ir.scope["subagency"] = candidate

    return ir
