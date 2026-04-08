from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_SRC_ROOT = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _SRC_ROOT.parent


@dataclass
class ComplianceResult:
    check_id: str
    description: str
    status: str
    detail: str = ""


def _check_ac1_ir_in_pipeline() -> ComplianceResult:
    pipeline_path = _SRC_ROOT / "pipeline.py"
    if not pipeline_path.exists():
        return ComplianceResult("AC-1", "IR conversion in pipeline", "FAIL", "pipeline.py not found")
    source = pipeline_path.read_text()
    uses_ir = "from src.ir import" in source or "from src.ir " in source
    if not uses_ir:
        return ComplianceResult("AC-1", "IR conversion in pipeline", "FAIL", "pipeline.py does not import from src.ir")
    return ComplianceResult("AC-1", "IR conversion in pipeline", "PASS")


def _check_ac2_entity_resolver() -> ComplianceResult:
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
    prompt_path = _SRC_ROOT / "prompt_builder.py"
    if not prompt_path.exists():
        return ComplianceResult("AC-3", "No hardcoded rules in prompt", "WARN", "prompt_builder.py not found")
    source = prompt_path.read_text().lower()
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
    interp_path = _SRC_ROOT / "semantics" / "metric_interpreter.py"
    dict_path = _PROJECT_ROOT / "config" / "metric_dictionary.yaml"
    if not interp_path.exists():
        return ComplianceResult("AC-4", "Metric dictionary used", "FAIL", "semantics/metric_interpreter.py not found")
    if not dict_path.exists():
        return ComplianceResult("AC-4", "Metric dictionary used", "FAIL", "config/metric_dictionary.yaml not found")
    return ComplianceResult("AC-4", "Metric dictionary used", "PASS")


def _check_ac5_time_interpreter() -> ComplianceResult:
    time_path = _SRC_ROOT / "semantics" / "time_interpreter.py"
    if not time_path.exists():
        return ComplianceResult("AC-5", "Time interpreter used", "WARN", "semantics/time_interpreter.py not found")
    return ComplianceResult("AC-5", "Time interpreter used", "PASS")


def run_compliance_checks() -> list[ComplianceResult]:
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
