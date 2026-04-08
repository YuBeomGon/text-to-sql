# AC Gate + IR-Based Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the architecture compliance gate and rebuild the pipeline around IR (Intermediate Representation) so that questions are parsed into structured meaning before reaching the LLM. This replaces the current shortcut pipeline that sends raw questions directly to LLM.

**Architecture:** Questions pass through entity resolver → metric interpreter → time interpreter → scope interpreter → ambiguity detector, producing an IR dataclass. The IR is then used to build a focused prompt for the LLM. The AC gate verifies this structure exists before accepting changes.

**Tech Stack:** Python 3.12, DuckDB, OpenAI, YAML configs, pytest

---

## File Structure

```
text-to-sql-v2/
├── config/
│   ├── slice.yaml                          # (existing)
│   ├── agency_aliases.yaml                 # agency abbreviation → full name
│   ├── metric_dictionary.yaml              # metric terms → column mappings
│   └── glossary.yaml                       # domain terms and count rules
├── src/
│   ├── ir.py                               # QuestionIR dataclass
│   ├── semantics/
│   │   ├── __init__.py
│   │   ├── entity_resolver.py              # normalize agency/recipient names
│   │   ├── metric_interpreter.py           # resolve metric terms to columns
│   │   ├── time_interpreter.py             # fiscal year/quarter conversion
│   │   ├── scope_interpreter.py            # contracts/prime/active scope
│   │   └── ambiguity_detector.py           # flag unresolvable ambiguity
│   ├── pipeline.py                         # (rewrite) IR-based orchestration
│   ├── prompt_builder.py                   # (rewrite) build from IR, not raw question
│   └── eval/
│       └── architecture_check.py           # AC-1 through AC-5
├── tests/
│   ├── test_ir.py
│   ├── test_entity_resolver.py
│   ├── test_metric_interpreter.py
│   ├── test_time_interpreter.py
│   ├── test_scope_interpreter.py
│   ├── test_ambiguity_detector.py
│   ├── test_pipeline.py                    # (rewrite)
│   └── test_architecture_check.py
└── score.sh                                # (modify) add AC gate
```

---

## Task 1: Architecture Compliance Checker

**Files:**
- Create: `src/eval/architecture_check.py`
- Create: `tests/test_architecture_check.py`
- Modify: `score.sh`

- [ ] **Step 1: Write the failing test**

`tests/test_architecture_check.py`:
```python
from src.eval.architecture_check import run_compliance_checks, ComplianceResult


def test_run_compliance_checks_returns_results():
    results = run_compliance_checks()
    assert isinstance(results, list)
    assert all(isinstance(r, ComplianceResult) for r in results)
    assert len(results) == 5  # AC-1 through AC-5


def test_compliance_result_has_fields():
    results = run_compliance_checks()
    r = results[0]
    assert hasattr(r, "check_id")
    assert hasattr(r, "description")
    assert hasattr(r, "status")  # "PASS", "FAIL", "WARN"
    assert hasattr(r, "detail")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /data/MyProject/side/text-to-sql-v2 && python -m pytest tests/test_architecture_check.py -v`

- [ ] **Step 3: Write implementation**

`src/eval/architecture_check.py`:
```python
from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

_SRC_ROOT = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _SRC_ROOT.parent


@dataclass
class ComplianceResult:
    check_id: str
    description: str
    status: str  # "PASS", "FAIL", "WARN"
    detail: str = ""


def _check_ac1_ir_in_pipeline() -> ComplianceResult:
    """AC-1: pipeline.py must import and use IR conversion."""
    pipeline_path = _SRC_ROOT / "pipeline.py"
    if not pipeline_path.exists():
        return ComplianceResult("AC-1", "IR conversion in pipeline", "FAIL", "pipeline.py not found")
    source = pipeline_path.read_text()
    uses_ir = "from src.ir import" in source or "from src.ir " in source
    if not uses_ir:
        return ComplianceResult("AC-1", "IR conversion in pipeline", "FAIL", "pipeline.py does not import from src.ir")
    return ComplianceResult("AC-1", "IR conversion in pipeline", "PASS")


def _check_ac2_entity_resolver() -> ComplianceResult:
    """AC-2: entity_resolver must exist and be used in pipeline."""
    resolver_path = _SRC_ROOT / "semantics" / "entity_resolver.py"
    pipeline_path = _SRC_ROOT / "pipeline.py"
    if not resolver_path.exists():
        return ComplianceResult("AC-2", "Entity resolver used", "FAIL", "semantics/entity_resolver.py not found")
    if pipeline_path.exists():
        source = pipeline_path.read_text()
        if "entity_resolver" not in source:
            return ComplianceResult("AC-2", "Entity resolver used", "FAIL", "pipeline.py does not reference entity_resolver")
    return ComplianceResult("AC-2", "Entity resolver used", "PASS")


def _check_ac3_no_hardcoded_rules() -> ComplianceResult:
    """AC-3: prompt_builder must not contain hardcoded business rules."""
    prompt_path = _SRC_ROOT / "prompt_builder.py"
    if not prompt_path.exists():
        return ComplianceResult("AC-3", "No hardcoded rules in prompt", "WARN", "prompt_builder.py not found")
    source = prompt_path.read_text().lower()
    # Check for hardcoded agency aliases
    hardcoded_patterns = [
        "department of defense",
        "department of health",
        "department of homeland",
        "general services administration",
    ]
    found = [p for p in hardcoded_patterns if p in source]
    if found:
        return ComplianceResult("AC-3", "No hardcoded rules in prompt", "FAIL",
                                f"prompt_builder.py contains hardcoded agency names: {found}")
    return ComplianceResult("AC-3", "No hardcoded rules in prompt", "PASS")


def _check_ac4_metric_dictionary() -> ComplianceResult:
    """AC-4: metric_interpreter must exist and use config-based dictionary."""
    interp_path = _SRC_ROOT / "semantics" / "metric_interpreter.py"
    dict_path = _PROJECT_ROOT / "config" / "metric_dictionary.yaml"
    if not interp_path.exists():
        return ComplianceResult("AC-4", "Metric dictionary used", "FAIL", "semantics/metric_interpreter.py not found")
    if not dict_path.exists():
        return ComplianceResult("AC-4", "Metric dictionary used", "FAIL", "config/metric_dictionary.yaml not found")
    return ComplianceResult("AC-4", "Metric dictionary used", "PASS")


def _check_ac5_time_interpreter() -> ComplianceResult:
    """AC-5: time_interpreter must exist."""
    time_path = _SRC_ROOT / "semantics" / "time_interpreter.py"
    if not time_path.exists():
        return ComplianceResult("AC-5", "Time interpreter used", "WARN", "semantics/time_interpreter.py not found")
    return ComplianceResult("AC-5", "Time interpreter used", "PASS")


def run_compliance_checks() -> list[ComplianceResult]:
    """Run all architecture compliance checks."""
    return [
        _check_ac1_ir_in_pipeline(),
        _check_ac2_entity_resolver(),
        _check_ac3_no_hardcoded_rules(),
        _check_ac4_metric_dictionary(),
        _check_ac5_time_interpreter(),
    ]


def format_report(results: list[ComplianceResult]) -> str:
    lines = ["Architecture Compliance:"]
    for r in results:
        detail = f" — {r.detail}" if r.detail else ""
        lines.append(f"  {r.check_id} {r.description:40s} {r.status}{detail}")
    fails = [r for r in results if r.status == "FAIL"]
    if fails:
        lines.append(f"\nGate: FAIL ({len(fails)} violation(s))")
    else:
        lines.append("\nGate: PASS")
    return "\n".join(lines)


def main() -> None:
    results = run_compliance_checks()
    print(format_report(results))
    fails = [r for r in results if r.status == "FAIL"]
    if fails:
        exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_architecture_check.py -v`
Expected: 2 passed

- [ ] **Step 5: Wire into score.sh**

Replace `score.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

MODE="${1:---quick}"
EXTRA="${2:-}"

# Architecture compliance gate (always runs)
echo "=== Architecture Compliance ==="
python -m src.eval.architecture_check
AC_EXIT=$?
echo ""

# Score
echo "=== Score ==="
case "$MODE" in
  --quick|--full)
    python -m src.eval.score_runner "$MODE" $EXTRA
    ;;
  *)
    echo "Usage: ./score.sh --quick | --full [--stub]" >&2
    exit 2
    ;;
esac

# If AC failed, exit with error even if score passed
if [ $AC_EXIT -ne 0 ]; then
  echo ""
  echo "BLOCKED: Architecture compliance gate failed. Fix violations before merging."
  exit 1
fi
```

Note: change `set -euo pipefail` handling — AC check should not abort the script. Update:
```bash
#!/usr/bin/env bash
set -uo pipefail

cd "$(dirname "$0")"

MODE="${1:---quick}"
EXTRA="${2:-}"

# Architecture compliance gate (always runs)
echo "=== Architecture Compliance ==="
python -m src.eval.architecture_check || AC_FAIL=1
AC_FAIL=${AC_FAIL:-0}
echo ""

# Score
echo "=== Score ==="
case "$MODE" in
  --quick|--full)
    python -m src.eval.score_runner "$MODE" $EXTRA
    ;;
  *)
    echo "Usage: ./score.sh --quick | --full [--stub]" >&2
    exit 2
    ;;
esac

if [ "$AC_FAIL" -eq 1 ]; then
  echo ""
  echo "BLOCKED: Architecture compliance gate failed. Fix violations before merging."
  exit 1
fi
```

- [ ] **Step 6: Verify AC gate correctly fails on current code**

Run: `./score.sh --quick --stub`
Expected: AC gate shows FAIL for AC-1, AC-2, AC-4, AC-5 (IR modules don't exist yet), score still prints, then BLOCKED message.

- [ ] **Step 7: Commit**

```bash
git add src/eval/architecture_check.py tests/test_architecture_check.py score.sh
git commit -m "feat(ac): implement architecture compliance gate AC-1 through AC-5

Checks that pipeline uses IR conversion (AC-1), entity resolver (AC-2),
no hardcoded prompt rules (AC-3), metric dictionary (AC-4), and time
interpreter (AC-5). Wired into score.sh — runs before scoring.

Currently FAIL on AC-1, AC-2, AC-4, AC-5 — this is correct and expected.
These will PASS as M2 IR modules are implemented."
```

---

## Task 2: Config Files (Agency Aliases, Metric Dictionary, Glossary)

**Files:**
- Create: `config/agency_aliases.yaml`
- Create: `config/metric_dictionary.yaml`
- Create: `config/glossary.yaml`

- [ ] **Step 1: Create agency_aliases.yaml**

`config/agency_aliases.yaml`:
```yaml
# Maps common abbreviations and variants to canonical agency names
# Used by entity_resolver to normalize questions before LLM
aliases:
  "DoD": "Department of Defense"
  "DOD": "Department of Defense"
  "Defense": "Department of Defense"
  "HHS": "Department of Health and Human Services"
  "Health and Human Services": "Department of Health and Human Services"
  "DHS": "Department of Homeland Security"
  "Homeland Security": "Department of Homeland Security"
  "GSA": "General Services Administration"
  "NASA": "NASA"
```

- [ ] **Step 2: Create metric_dictionary.yaml**

`config/metric_dictionary.yaml`:
```yaml
# Maps metric terms in natural language to SQL column expressions
# Used by metric_interpreter to resolve what "amount", "spending", etc. mean
metrics:
  obligation:
    column: "total_obligation"
    aggregation: "SUM"
    description: "Total dollars obligated for the award"
  outlay:
    column: "total_outlay"
    aggregation: "SUM"
    description: "Total dollars outlayed (actually spent)"
  award_amount:
    column: "total_award_amount"
    aggregation: "SUM"
    description: "Current total value of the award"
  transaction_obligation:
    column: "federal_action_obligation"
    aggregation: "SUM"
    description: "Obligation amount for a single transaction"

# Terms that map to specific metrics
term_mappings:
  "obligation": "obligation"
  "obligations": "obligation"
  "obligated": "obligation"
  "outlay": "outlay"
  "outlays": "outlay"
  "outlayed": "outlay"
  "spent": "outlay"
  "spending": "obligation"  # default to obligation when ambiguous
  "award amount": "award_amount"
  "contract value": "award_amount"

# Ambiguous terms that should trigger CLARIFY
ambiguous_terms:
  - "amount"
  - "money"
  - "dollars"
  - "funding"
  - "cost"

# Count types
counts:
  awards:
    expression: "COUNT(DISTINCT award_id)"
    description: "Number of unique awards"
  transactions:
    expression: "COUNT(*)"
    description: "Number of transaction rows"
  recipients:
    expression: "COUNT(DISTINCT recipient_name)"
    description: "Number of unique recipients"
```

- [ ] **Step 3: Create glossary.yaml**

`config/glossary.yaml`:
```yaml
# Domain term definitions for the USAspending contracts domain
# Used to help the system understand what terms mean in context

terms:
  fiscal_year:
    definition: "Federal fiscal year runs Oct 1 to Sep 30. FY2025 = Oct 1 2024 to Sep 30 2025."
    column: "fiscal_year"
    type: "INTEGER"

  contract:
    definition: "A federal procurement contract. Each row in the contracts table is one transaction."

  award:
    definition: "A contract award identified by award_id. One award can have multiple transactions."

  transaction:
    definition: "A single action on a contract. Each row in the contracts table is one transaction."

  recipient:
    definition: "The entity receiving the contract. Identified by recipient_name."

  awarding_agency:
    definition: "The federal agency that awarded the contract. Use awarding_agency_name column."

  prime_award:
    definition: "A direct federal contract (not a subaward). The contracts table contains only prime awards."
```

- [ ] **Step 4: Verify YAML syntax**

Run: `python -c "import yaml; [yaml.safe_load(open(f'config/{f}')) for f in ['agency_aliases.yaml','metric_dictionary.yaml','glossary.yaml']]; print('all valid')"`

- [ ] **Step 5: Commit**

```bash
git add config/agency_aliases.yaml config/metric_dictionary.yaml config/glossary.yaml
git commit -m "feat(m2): add metadata configs for entity, metric, and glossary

Agency aliases, metric dictionary with ambiguous term detection, and
glossary definitions. These are the SSOT for business rules — modules
read from these configs instead of hardcoding rules in prompts."
```

---

## Task 3: IR Dataclass

**Files:**
- Create: `src/ir.py`
- Create: `tests/test_ir.py`

- [ ] **Step 1: Write the failing test**

`tests/test_ir.py`:
```python
from src.ir import QuestionIR


def test_question_ir_defaults():
    ir = QuestionIR(raw_question="How many contracts?")
    assert ir.raw_question == "How many contracts?"
    assert ir.normalized_question == ""
    assert ir.metric is None
    assert ir.entities == {}
    assert ir.time_range is None
    assert ir.scope == {}
    assert ir.ambiguities == []
    assert ir.should_clarify is False
    assert ir.should_abstain is False


def test_question_ir_with_values():
    ir = QuestionIR(
        raw_question="How many NASA contracts in FY2025?",
        normalized_question="How many NASA contracts in fiscal year 2025?",
        metric={"type": "count", "expression": "COUNT(DISTINCT award_id)"},
        entities={"agency": "NASA"},
        time_range={"fiscal_year": 2025},
        scope={"award_type": "contract_only"},
    )
    assert ir.entities["agency"] == "NASA"
    assert ir.time_range["fiscal_year"] == 2025
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Write implementation**

`src/ir.py`:
```python
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class QuestionIR:
    """Intermediate Representation of a parsed question.

    This is the structured meaning derived from a natural language question
    BEFORE it reaches the LLM for SQL generation.
    """
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_ir.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add src/ir.py tests/test_ir.py
git commit -m "feat(m2): add QuestionIR dataclass for intermediate representation

Structured meaning derived from a question before LLM: metric, entities,
time_range, scope, ambiguities. This is the core data structure that all
semantic interpretation modules produce and the prompt builder consumes."
```

---

## Task 4: Entity Resolver

**Files:**
- Create: `src/semantics/__init__.py`
- Create: `src/semantics/entity_resolver.py`
- Create: `tests/test_entity_resolver.py`

- [ ] **Step 1: Write the failing test**

`tests/test_entity_resolver.py`:
```python
from src.semantics.entity_resolver import resolve_entities


def test_resolve_dhs_to_full_name():
    result = resolve_entities("DHS contracts in fiscal year 2025")
    assert result.entities["agency"] == "Department of Homeland Security"
    assert "DHS" not in result.normalized_question
    assert "Department of Homeland Security" in result.normalized_question


def test_resolve_hhs_to_full_name():
    result = resolve_entities("HHS total obligation")
    assert result.entities["agency"] == "Department of Health and Human Services"


def test_resolve_nasa_stays_nasa():
    result = resolve_entities("NASA contracts")
    assert result.entities["agency"] == "NASA"


def test_resolve_full_name_unchanged():
    result = resolve_entities("Department of Defense contracts")
    assert result.entities["agency"] == "Department of Defense"


def test_resolve_no_agency():
    result = resolve_entities("total contracts in fiscal year 2025")
    assert "agency" not in result.entities


def test_resolve_recipient():
    result = resolve_entities("Lockheed Martin contracts for NASA")
    assert result.entities.get("agency") == "NASA"
    assert "Lockheed Martin" in result.entities.get("recipient", "")
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Write implementation**

`src/semantics/__init__.py` — empty file

`src/semantics/entity_resolver.py`:
```python
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

    # Resolve agency aliases (longest match first to avoid partial matches)
    agency_found = None
    for alias, canonical in sorted(aliases.items(), key=lambda x: len(x[0]), reverse=True):
        pattern = re.compile(re.escape(alias), re.IGNORECASE)
        if pattern.search(normalized):
            normalized = pattern.sub(canonical, normalized)
            agency_found = canonical
            break

    # If no alias matched, check for full canonical names in the question
    if not agency_found:
        canonical_names = set(aliases.values())
        for name in sorted(canonical_names, key=len, reverse=True):
            if name.lower() in normalized.lower():
                agency_found = name
                break

    if agency_found:
        ir.entities["agency"] = agency_found

    # Simple recipient detection: capitalized multi-word names that aren't agencies
    # This is a basic heuristic — will be improved in later iterations
    agency_names = set(aliases.values()) | set(aliases.keys())
    words = question.split()
    for i, word in enumerate(words):
        if word[0].isupper() and word.lower() not in {"the", "for", "in", "and", "of", "by", "how", "what", "show", "list", "count", "total", "which", "where", "with"}:
            # Check if this is part of a known agency
            is_agency = any(word.lower() in name.lower() for name in agency_names)
            if not is_agency and i + 1 < len(words) and words[i + 1][0].isupper():
                recipient = f"{word} {words[i + 1]}"
                ir.entities["recipient"] = recipient
                break

    ir.normalized_question = normalized
    return ir
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_entity_resolver.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add src/semantics/__init__.py src/semantics/entity_resolver.py tests/test_entity_resolver.py
git commit -m "feat(m2): add entity resolver — normalize agency/recipient from config

Reads agency aliases from config/agency_aliases.yaml, replaces abbreviations
in questions with canonical names. No hardcoded rules in the module itself.
Resolves AC-2 compliance check."
```

---

## Task 5: Metric Interpreter

**Files:**
- Create: `src/semantics/metric_interpreter.py`
- Create: `tests/test_metric_interpreter.py`

- [ ] **Step 1: Write the failing test**

`tests/test_metric_interpreter.py`:
```python
from src.semantics.metric_interpreter import interpret_metric
from src.ir import QuestionIR


def test_interpret_obligation():
    ir = QuestionIR(raw_question="total obligation for NASA")
    result = interpret_metric(ir)
    assert result.metric is not None
    assert result.metric["column"] == "total_obligation"


def test_interpret_outlay():
    ir = QuestionIR(raw_question="total outlay for DHS")
    result = interpret_metric(ir)
    assert result.metric["column"] == "total_outlay"


def test_interpret_count_awards():
    ir = QuestionIR(raw_question="how many contracts did NASA award")
    result = interpret_metric(ir)
    assert result.metric is not None
    assert "COUNT(DISTINCT award_id)" in result.metric["expression"]


def test_interpret_count_transactions():
    ir = QuestionIR(raw_question="total number of contract transactions for DHS")
    result = interpret_metric(ir)
    assert result.metric is not None
    assert "COUNT(*)" in result.metric["expression"]


def test_interpret_ambiguous_amount():
    ir = QuestionIR(raw_question="what is the amount for NASA contracts")
    result = interpret_metric(ir)
    assert result.should_clarify is True
    assert len(result.ambiguities) > 0


def test_interpret_explicit_metric_not_ambiguous():
    ir = QuestionIR(raw_question="total obligation for NASA")
    result = interpret_metric(ir)
    assert result.should_clarify is False
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Write implementation**

`src/semantics/metric_interpreter.py`:
```python
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
        # Determine what to count
        if re.search(r"\btransaction", question_lower):
            count_info = counts.get("transactions", {})
            ir.metric = {"type": "count", "expression": count_info.get("expression", "COUNT(*)"), "column": None}
            return ir
        elif re.search(r"\brecipient|\bvendor|\bcontractor", question_lower):
            count_info = counts.get("recipients", {})
            ir.metric = {"type": "count", "expression": count_info.get("expression", "COUNT(DISTINCT recipient_name)"), "column": None}
            return ir
        else:
            # Default: count awards
            count_info = counts.get("awards", {})
            ir.metric = {"type": "count", "expression": count_info.get("expression", "COUNT(DISTINCT award_id)"), "column": None}
            return ir

    # Check for ambiguous terms first
    ambiguous_terms = config.get("ambiguous_terms", [])
    for term in ambiguous_terms:
        if re.search(rf"\b{re.escape(term)}\b", question_lower):
            # Check if a specific metric is also mentioned (overrides ambiguity)
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

    # Check for aggregation keywords without explicit metric (default to obligation)
    if re.search(r"\btotal\b|\bsum\b|\bmax\b|\bmin\b|\baverage\b|\bavg\b", question_lower):
        default_metric = metrics.get("obligation", {})
        ir.metric = {
            "type": "aggregate",
            "column": default_metric.get("column", "total_obligation"),
            "aggregation": "SUM",
            "expression": f"SUM({default_metric.get('column', 'total_obligation')})",
        }

    return ir
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_metric_interpreter.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add src/semantics/metric_interpreter.py tests/test_metric_interpreter.py
git commit -m "feat(m2): add metric interpreter — config-based metric resolution

Reads metric_dictionary.yaml to resolve terms like 'obligation', 'outlay',
'transactions' to SQL expressions. Detects ambiguous terms ('amount',
'money') and flags for clarification. No hardcoded rules.
Resolves AC-4 compliance check."
```

---

## Task 6: Time Interpreter

**Files:**
- Create: `src/semantics/time_interpreter.py`
- Create: `tests/test_time_interpreter.py`

- [ ] **Step 1: Write the failing test**

`tests/test_time_interpreter.py`:
```python
from src.semantics.time_interpreter import interpret_time
from src.ir import QuestionIR


def test_interpret_fiscal_year():
    ir = QuestionIR(raw_question="contracts in fiscal year 2025")
    result = interpret_time(ir)
    assert result.time_range is not None
    assert result.time_range["fiscal_year"] == 2025


def test_interpret_fy_abbreviation():
    ir = QuestionIR(raw_question="NASA contracts in FY2024")
    result = interpret_time(ir)
    assert result.time_range["fiscal_year"] == 2024


def test_interpret_no_time():
    ir = QuestionIR(raw_question="total contracts for NASA")
    result = interpret_time(ir)
    assert result.time_range is None


def test_interpret_fiscal_quarter():
    ir = QuestionIR(raw_question="HHS contracts in fiscal year 2024 Q2")
    result = interpret_time(ir)
    assert result.time_range["fiscal_year"] == 2024
    assert result.time_range["quarter"] == 2
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Write implementation**

`src/semantics/time_interpreter.py`:
```python
from __future__ import annotations

import re

from src.ir import QuestionIR


def interpret_time(ir: QuestionIR) -> QuestionIR:
    """Extract time range from the question and update the IR."""
    question = ir.raw_question

    # Match "fiscal year YYYY" or "FY YYYY" or "FYYYYY"
    fy_match = re.search(r"(?:fiscal\s+year|FY)\s*(\d{4})", question, re.IGNORECASE)
    if fy_match:
        fy = int(fy_match.group(1))
        ir.time_range = {"fiscal_year": fy}

        # Check for quarter
        q_match = re.search(r"Q(\d)", question)
        if q_match:
            ir.time_range["quarter"] = int(q_match.group(1))

        return ir

    # Match standalone 4-digit year in context of "in YYYY" or "for YYYY"
    year_match = re.search(r"(?:in|for)\s+(\d{4})\b", question)
    if year_match:
        ir.time_range = {"fiscal_year": int(year_match.group(1))}
        return ir

    return ir
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_time_interpreter.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/semantics/time_interpreter.py tests/test_time_interpreter.py
git commit -m "feat(m2): add time interpreter — rule-based fiscal year/quarter parsing

Extracts fiscal year and quarter from questions using regex patterns.
No LLM involvement — purely rule-based. Resolves AC-5 compliance check."
```

---

## Task 7: Scope Interpreter + Ambiguity Detector

**Files:**
- Create: `src/semantics/scope_interpreter.py`
- Create: `src/semantics/ambiguity_detector.py`
- Create: `tests/test_scope_interpreter.py`
- Create: `tests/test_ambiguity_detector.py`

- [ ] **Step 1: Write scope tests**

`tests/test_scope_interpreter.py`:
```python
from src.semantics.scope_interpreter import interpret_scope
from src.ir import QuestionIR


def test_default_scope_is_contracts():
    ir = QuestionIR(raw_question="NASA obligations")
    result = interpret_scope(ir)
    assert result.scope.get("award_type") == "contract_only"


def test_prime_only_scope():
    ir = QuestionIR(raw_question="prime contracts for DHS")
    result = interpret_scope(ir)
    assert result.scope.get("prime_only") is True
```

- [ ] **Step 2: Write ambiguity tests**

`tests/test_ambiguity_detector.py`:
```python
from src.semantics.ambiguity_detector import detect_ambiguity
from src.ir import QuestionIR


def test_no_ambiguity():
    ir = QuestionIR(raw_question="total obligation for NASA in FY2025")
    ir.metric = {"column": "total_obligation"}
    ir.entities = {"agency": "NASA"}
    ir.time_range = {"fiscal_year": 2025}
    result = detect_ambiguity(ir)
    assert result.should_clarify is False


def test_ambiguity_already_flagged():
    ir = QuestionIR(raw_question="what is the amount")
    ir.should_clarify = True
    ir.ambiguities = ["amount is ambiguous"]
    result = detect_ambiguity(ir)
    assert result.should_clarify is True
```

- [ ] **Step 3: Write implementations**

`src/semantics/scope_interpreter.py`:
```python
from __future__ import annotations

import re

from src.ir import QuestionIR


def interpret_scope(ir: QuestionIR) -> QuestionIR:
    """Determine the query scope from the question."""
    question_lower = ir.raw_question.lower()

    # Default: contracts only (this dataset only has contracts)
    ir.scope["award_type"] = "contract_only"

    # Check for prime-only
    if re.search(r"\bprime\b", question_lower):
        ir.scope["prime_only"] = True

    # Check for active-only
    if re.search(r"\bactive\b|\bopen\b", question_lower):
        ir.scope["active_only"] = True

    return ir
```

`src/semantics/ambiguity_detector.py`:
```python
from __future__ import annotations

from src.ir import QuestionIR


def detect_ambiguity(ir: QuestionIR) -> QuestionIR:
    """Final ambiguity check after all interpreters have run."""
    # If already flagged by metric_interpreter, keep it
    if ir.should_clarify or ir.should_abstain:
        return ir

    # If no metric was resolved for a question that seems to ask for a value
    # (not a count), that might be ambiguous
    # This is conservative — only flag if truly unresolvable

    return ir
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_scope_interpreter.py tests/test_ambiguity_detector.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/semantics/scope_interpreter.py src/semantics/ambiguity_detector.py tests/test_scope_interpreter.py tests/test_ambiguity_detector.py
git commit -m "feat(m2): add scope interpreter and ambiguity detector

Scope interpreter sets default contract_only scope and detects prime/active.
Ambiguity detector is a final pass that preserves flags from earlier stages."
```

---

## Task 8: Rebuild Pipeline with IR

**Files:**
- Modify: `src/pipeline.py`
- Modify: `src/prompt_builder.py`
- Modify: `tests/test_pipeline.py`

- [ ] **Step 1: Rewrite pipeline.py**

`src/pipeline.py`:
```python
from __future__ import annotations

from dataclasses import dataclass, field

import duckdb

from src.executor import execute_query
from src.ir import QuestionIR
from src.llm_client import generate_sql
from src.prompt_builder import build_system_prompt, build_user_prompt
from src.schema_inspector import get_columns, get_tables
from src.semantics.entity_resolver import resolve_entities
from src.semantics.metric_interpreter import interpret_metric
from src.semantics.time_interpreter import interpret_time
from src.semantics.scope_interpreter import interpret_scope
from src.semantics.ambiguity_detector import detect_ambiguity


@dataclass
class PipelineResult:
    behavior: str  # "answer", "clarify", "abstain"
    sql: str | None = None
    columns: list[str] = field(default_factory=list)
    rows: list[tuple] = field(default_factory=list)
    success: bool = False
    error: str | None = None
    raw_llm_output: str = ""
    ir: QuestionIR | None = None


def _get_schema(conn: duckdb.DuckDBPyConnection) -> dict[str, dict[str, str]]:
    schema = {}
    for table in get_tables(conn):
        schema[table] = get_columns(conn, table)
    return schema


def _build_ir(question: str) -> QuestionIR:
    """Run the question through all semantic interpretation stages."""
    ir = resolve_entities(question)
    ir = interpret_metric(ir)
    ir = interpret_time(ir)
    ir = interpret_scope(ir)
    ir = detect_ambiguity(ir)
    return ir


def run_question(
    conn: duckdb.DuckDBPyConnection,
    question: str,
    model: str | None = None,
) -> PipelineResult:
    """Run a natural language question through the IR-based NL2SQL pipeline."""
    # Stage 1: Semantic interpretation → IR
    ir = _build_ir(question)

    # Stage 2: Check if we should clarify or abstain before calling LLM
    if ir.should_clarify:
        return PipelineResult(
            behavior="clarify",
            ir=ir,
            raw_llm_output=ir.clarify_reason,
        )
    if ir.should_abstain:
        return PipelineResult(
            behavior="abstain",
            ir=ir,
            raw_llm_output=ir.abstain_reason,
        )

    # Stage 3: Build prompts from IR + schema
    schema = _get_schema(conn)
    system_prompt = build_system_prompt(schema, ir)
    user_prompt = build_user_prompt(ir)

    # Stage 4: LLM generates SQL
    raw_output = generate_sql(system_prompt, user_prompt, model=model)

    # Check for LLM-level CLARIFY/ABSTAIN
    if raw_output.startswith("CLARIFY:"):
        return PipelineResult(behavior="clarify", ir=ir, raw_llm_output=raw_output)
    if raw_output.startswith("ABSTAIN:"):
        return PipelineResult(behavior="abstain", ir=ir, raw_llm_output=raw_output)

    # Stage 5: Execute SQL
    query_result = execute_query(conn, raw_output)

    return PipelineResult(
        behavior="answer",
        sql=raw_output,
        columns=query_result.columns,
        rows=query_result.rows,
        success=query_result.success,
        error=query_result.error,
        raw_llm_output=raw_output,
        ir=ir,
    )
```

- [ ] **Step 2: Rewrite prompt_builder.py to use IR**

`src/prompt_builder.py`:
```python
from __future__ import annotations

from src.ir import QuestionIR


def build_system_prompt(schema: dict[str, dict[str, str]], ir: QuestionIR) -> str:
    """Build the system prompt using schema and IR context."""
    schema_lines = []
    for table, columns in schema.items():
        col_defs = ", ".join(f"{col} {dtype}" for col, dtype in columns.items())
        schema_lines.append(f"  {table}({col_defs})")
    schema_text = "\n".join(schema_lines)

    # Build context hints from IR
    hints = []
    if ir.entities.get("agency"):
        hints.append(f"Agency filter: awarding_agency_name = '{ir.entities['agency']}'")
    if ir.entities.get("recipient"):
        hints.append(f"Recipient filter: recipient_name ILIKE '%{ir.entities['recipient']}%'")
    if ir.time_range:
        fy = ir.time_range.get("fiscal_year")
        if fy:
            hints.append(f"Time filter: fiscal_year = {fy}")
        q = ir.time_range.get("quarter")
        if q:
            hints.append(f"Quarter: Q{q} of FY{fy}")
    if ir.metric:
        if ir.metric.get("expression"):
            hints.append(f"Metric: use {ir.metric['expression']}")
        elif ir.metric.get("column"):
            hints.append(f"Metric column: {ir.metric['column']}")

    hints_text = "\n".join(f"- {h}" for h in hints) if hints else "- No specific hints derived from question"

    return f"""You are a SQL expert for a DuckDB database containing USAspending federal contract data.

Database schema:
{schema_text}

Interpreted context from the question:
{hints_text}

Rules:
- Write valid DuckDB SQL only.
- Return ONLY the SQL query, nothing else. No explanations.
- Use the interpreted context above to guide your query.
- If the question is ambiguous about which metric to use, respond with exactly: CLARIFY: <reason>
- If the question cannot be answered from the schema, respond with exactly: ABSTAIN: <reason>"""


def build_user_prompt(ir: QuestionIR) -> str:
    """Build the user prompt from the IR."""
    q = ir.normalized_question if ir.normalized_question else ir.raw_question
    return f"Write a SQL query to answer this question:\n{q}"
```

- [ ] **Step 3: Update tests/test_pipeline.py**

`tests/test_pipeline.py`:
```python
from unittest.mock import patch
from src.pipeline import run_question, PipelineResult


def test_run_question_returns_answer(sample_db):
    with patch("src.pipeline.generate_sql") as mock_llm:
        mock_llm.return_value = "SELECT COUNT(DISTINCT award_id) FROM contracts WHERE awarding_agency_name = 'NASA'"

        result = run_question(sample_db, "How many contracts did NASA award?")
        assert isinstance(result, PipelineResult)
        assert result.behavior == "answer"
        assert result.sql is not None
        assert result.success is True
        assert len(result.rows) == 1
        assert result.rows[0][0] == 2
        # Verify IR was created
        assert result.ir is not None
        assert result.ir.entities.get("agency") == "NASA"


def test_run_question_ambiguous_metric_detected_by_ir(sample_db):
    """When metric interpreter detects ambiguity, pipeline should clarify WITHOUT calling LLM."""
    with patch("src.pipeline.generate_sql") as mock_llm:
        result = run_question(sample_db, "What is the amount for NASA?")
        assert result.behavior == "clarify"
        # LLM should NOT have been called — IR caught the ambiguity
        mock_llm.assert_not_called()


def test_run_question_handles_llm_clarify(sample_db):
    with patch("src.pipeline.generate_sql") as mock_llm:
        mock_llm.return_value = "CLARIFY: unclear scope"
        result = run_question(sample_db, "Show NASA spending details")
        assert result.behavior == "clarify"


def test_run_question_handles_sql_error(sample_db):
    with patch("src.pipeline.generate_sql") as mock_llm:
        mock_llm.return_value = "SELECT nonexistent_col FROM contracts"
        result = run_question(sample_db, "bad query")
        assert result.success is False
        assert result.error is not None


def test_run_question_entity_resolution(sample_db):
    """Verify that DHS gets resolved to full name in IR."""
    with patch("src.pipeline.generate_sql") as mock_llm:
        mock_llm.return_value = "SELECT COUNT(*) FROM contracts WHERE awarding_agency_name = 'Department of Homeland Security'"
        result = run_question(sample_db, "DHS contracts")
        assert result.ir.entities.get("agency") == "Department of Homeland Security"
```

- [ ] **Step 4: Update tests/test_prompt_builder.py**

`tests/test_prompt_builder.py`:
```python
from src.prompt_builder import build_system_prompt, build_user_prompt
from src.ir import QuestionIR


def test_build_system_prompt_contains_schema():
    schema = {"contracts": {"award_id": "VARCHAR", "fiscal_year": "INTEGER"}}
    ir = QuestionIR(raw_question="test")
    prompt = build_system_prompt(schema, ir)
    assert "contracts" in prompt
    assert "award_id" in prompt


def test_build_system_prompt_contains_ir_hints():
    schema = {"contracts": {"award_id": "VARCHAR"}}
    ir = QuestionIR(
        raw_question="NASA obligations in FY2025",
        entities={"agency": "NASA"},
        time_range={"fiscal_year": 2025},
        metric={"column": "total_obligation", "expression": "SUM(total_obligation)"},
    )
    prompt = build_system_prompt(schema, ir)
    assert "NASA" in prompt
    assert "2025" in prompt
    assert "total_obligation" in prompt


def test_build_user_prompt_uses_normalized():
    ir = QuestionIR(
        raw_question="DHS contracts",
        normalized_question="Department of Homeland Security contracts",
    )
    prompt = build_user_prompt(ir)
    assert "Department of Homeland Security" in prompt
    assert "DHS" not in prompt


def test_build_user_prompt_falls_back_to_raw():
    ir = QuestionIR(raw_question="NASA contracts")
    prompt = build_user_prompt(ir)
    assert "NASA" in prompt
```

- [ ] **Step 5: Run all tests**

Run: `python -m pytest tests/ -v`
Expected: all pass

- [ ] **Step 6: Verify AC gate improves**

Run: `python -m src.eval.architecture_check`
Expected: AC-1 PASS, AC-2 PASS, AC-3 PASS, AC-4 PASS, AC-5 PASS (or WARN)

- [ ] **Step 7: Commit**

```bash
git add src/pipeline.py src/prompt_builder.py tests/test_pipeline.py tests/test_prompt_builder.py
git commit -m "feat(m2): rebuild pipeline with IR — question passes through semantic layers

Pipeline now: question → entity_resolver → metric_interpreter →
time_interpreter → scope_interpreter → ambiguity_detector → IR →
prompt_builder (from IR) → LLM → SQL → execute.

Ambiguous metrics detected at IR stage BEFORE calling LLM (saves cost).
Prompt builder receives structured hints from IR instead of raw question.
All AC checks should now PASS."
```

---

## Task 9: Smoke Test + Score Verification

- [ ] **Step 1: Run smoke test**

Run: `python scripts/smoke_test.py`
Report results.

- [ ] **Step 2: Run score.sh with stub**

Run: `./score.sh --quick --stub`
Expected: AC gate PASS, score baseline.

- [ ] **Step 3: Record in improvement log**

Update `docs/improvement_log.md` with IR pipeline results.

- [ ] **Step 4: Commit and push**

```bash
git push origin main
```

---

## Self-Review

**1. Spec coverage:**
- AC gate: Task 1
- Config files: Task 2
- IR dataclass: Task 3
- Entity resolver: Task 4
- Metric interpreter: Task 5
- Time interpreter: Task 6
- Scope + ambiguity: Task 7
- Pipeline rebuild: Task 8
- Verification: Task 9

**2. Placeholder scan:** No TBD/TODO. All code complete.

**3. Type consistency:**
- `QuestionIR` (Task 3) used in Tasks 4-8 — fields match
- `build_system_prompt(schema, ir)` new signature (Task 8) — callers updated
- `build_user_prompt(ir)` new signature (Task 8) — callers updated
- `PipelineResult.ir` field added (Task 8) — used in tests
