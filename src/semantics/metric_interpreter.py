from __future__ import annotations

import re
from pathlib import Path

import yaml

from src.ir import QuestionIR

_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "metric_dictionary.yaml"


def _load_dictionary() -> dict:
    with open(_CONFIG_PATH) as f:
        return yaml.safe_load(f)


def interpret_metric(ir: QuestionIR) -> QuestionIR:
    """Interpret the metric from the question and update the IR."""
    config = _load_dictionary()
    question_lower = ir.raw_question.lower()

    # Check for count-type questions first
    counts = config.get("counts", {})
    if re.search(r"\bhow many\b|\bcount\b|\bnumber of\b", question_lower):
        if re.search(r"\btransaction", question_lower):
            count_info = counts.get("transactions", {})
            ir.metric = {"type": "count", "expression": count_info.get("expression", "COUNT(*)"), "column": None}
            return ir
        elif re.search(r"\brecipient|\bvendor|\bcontractor", question_lower):
            count_info = counts.get("recipients", {})
            ir.metric = {"type": "count", "expression": count_info.get("expression", "COUNT(DISTINCT recipient_name)"), "column": None}
            return ir
        else:
            count_info = counts.get("awards", {})
            ir.metric = {"type": "count", "expression": count_info.get("expression", "COUNT(DISTINCT award_id)"), "column": None}
            return ir

    # Check for ambiguous terms
    ambiguous_terms = config.get("ambiguous_terms", [])
    for term in ambiguous_terms:
        if re.search(rf"\b{re.escape(term)}\b", question_lower):
            term_mappings = config.get("term_mappings", {})
            specific_found = False
            for map_term in term_mappings:
                if map_term != term and re.search(rf"\b{re.escape(map_term)}\b", question_lower):
                    specific_found = True
                    break
            if not specific_found:
                ir.should_clarify = True
                ir.ambiguities.append(f"'{term}' is ambiguous — could mean obligation, outlay, or award amount")
                ir.clarify_reason = f"Ambiguous metric term: {term}"
                return ir

    # Check for specific metric terms
    term_mappings = config.get("term_mappings", {})
    metrics = config.get("metrics", {})
    for term, metric_key in sorted(term_mappings.items(), key=lambda x: len(x[0]), reverse=True):
        if re.search(rf"\b{re.escape(term)}\b", question_lower):
            metric_info = metrics.get(metric_key, {})
            ir.metric = {
                "type": "aggregate",
                "column": metric_info.get("column", "total_obligation"),
                "aggregation": metric_info.get("aggregation", "SUM"),
                "expression": f"{metric_info.get('aggregation', 'SUM')}({metric_info.get('column', 'total_obligation')})",
            }
            return ir

    # Default for aggregation keywords
    if re.search(r"\btotal\b|\bsum\b|\bmax\b|\bmin\b|\baverage\b|\bavg\b", question_lower):
        default_metric = metrics.get("obligation", {})
        ir.metric = {
            "type": "aggregate",
            "column": default_metric.get("column", "total_obligation"),
            "aggregation": "SUM",
            "expression": f"SUM({default_metric.get('column', 'total_obligation')})",
        }

    return ir
