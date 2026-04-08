from src.eval.architecture_check import run_compliance_checks, ComplianceResult


def test_run_compliance_checks_returns_results():
    results = run_compliance_checks()
    assert isinstance(results, list)
    assert all(isinstance(r, ComplianceResult) for r in results)
    assert len(results) == 5


def test_compliance_result_has_fields():
    results = run_compliance_checks()
    r = results[0]
    assert hasattr(r, "check_id")
    assert hasattr(r, "description")
    assert hasattr(r, "status")
    assert hasattr(r, "detail")
