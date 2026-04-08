from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class QuestionIR:
    """Intermediate Representation of a parsed question."""
    raw_question: str
    normalized_question: str = ""
    metric: dict | None = None
    entities: dict = field(default_factory=dict)
    time_range: dict | None = None
    scope: dict = field(default_factory=dict)
    ambiguities: list[str] = field(default_factory=list)
    should_clarify: bool = False
    should_abstain: bool = False
    clarify_reason: str = ""
    abstain_reason: str = ""
