from src.schema_inspector import get_tables, get_columns


def test_get_tables_returns_contracts(sample_db):
    tables = get_tables(sample_db)
    assert "contracts" in tables


def test_get_columns_returns_expected_columns(sample_db):
    columns = get_columns(sample_db, "contracts")
    expected = {
        "award_id", "awarding_agency_name", "awarding_sub_agency_name",
        "recipient_name", "award_type", "fiscal_year",
        "total_obligation", "total_outlay", "total_award_amount",
        "action_date", "award_start_date", "naics_code", "award_status",
    }
    assert expected.issubset(set(columns.keys()))


def test_get_columns_includes_types(sample_db):
    columns = get_columns(sample_db, "contracts")
    assert columns["fiscal_year"] == "INTEGER"
    assert columns["total_obligation"] == "DOUBLE"
