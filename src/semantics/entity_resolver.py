from __future__ import annotations

import re
from pathlib import Path

import yaml

from src.ir import QuestionIR

_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "agency_aliases.yaml"


def _load_aliases() -> dict[str, str]:
    with open(_CONFIG_PATH) as f:
        data = yaml.safe_load(f)
    return data.get("aliases", {})


def resolve_entities(question: str) -> QuestionIR:
    """Resolve entity names in the question and return a partial IR."""
    aliases = _load_aliases()
    ir = QuestionIR(raw_question=question)
    normalized = question

    # Resolve agency aliases (longest match first)
    agency_found = None
    for alias, canonical in sorted(aliases.items(), key=lambda x: len(x[0]), reverse=True):
        pattern = re.compile(re.escape(alias), re.IGNORECASE)
        if pattern.search(normalized):
            normalized = pattern.sub(canonical, normalized)
            agency_found = canonical
            break

    # If no alias matched, check for full canonical names
    if not agency_found:
        canonical_names = set(aliases.values())
        for name in sorted(canonical_names, key=len, reverse=True):
            if name.lower() in normalized.lower():
                agency_found = name
                break

    if agency_found:
        ir.entities["agency"] = agency_found

    # Simple recipient detection: capitalized multi-word names not matching agencies
    agency_names = set(aliases.values()) | set(aliases.keys())
    words = question.split()
    skip_words = {"the", "for", "in", "and", "of", "by", "how", "what", "show", "list",
                  "count", "total", "which", "where", "with", "all", "top", "from"}
    for i, word in enumerate(words):
        if not word[0].isupper() or word.lower() in skip_words:
            continue
        is_agency = any(word.lower() in name.lower() for name in agency_names)
        if not is_agency and i + 1 < len(words) and words[i + 1][0].isupper():
            recipient = f"{word} {words[i + 1]}"
            ir.entities["recipient"] = recipient
            break

    ir.normalized_question = normalized
    return ir
