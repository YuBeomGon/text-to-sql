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
