from __future__ import annotations

import re

from src.ir import QuestionIR


def interpret_time(ir: QuestionIR) -> QuestionIR:
    """Extract time range from the question and update the IR."""
    question = ir.raw_question

    fy_match = re.search(r"(?:fiscal\s+year|FY)\s*(\d{4})", question, re.IGNORECASE)
    if fy_match:
        fy = int(fy_match.group(1))
        ir.time_range = {"fiscal_year": fy}

        q_match = re.search(r"Q(\d)", question)
        if q_match:
            ir.time_range["quarter"] = int(q_match.group(1))

        return ir

    year_match = re.search(r"(?:in|for)\s+(\d{4})\b", question)
    if year_match:
        ir.time_range = {"fiscal_year": int(year_match.group(1))}
        return ir

    return ir
