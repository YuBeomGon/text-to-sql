from src.executor import execute_query, QueryResult


def test_execute_query_returns_rows(sample_db):
    result = execute_query(sample_db, "SELECT award_id FROM contracts WHERE awarding_agency_name = 'NASA'")
    assert isinstance(result, QueryResult)
    assert result.success is True
    assert len(result.rows) == 2
    assert result.columns == ["award_id"]


def test_execute_query_returns_error_on_bad_sql(sample_db):
    result = execute_query(sample_db, "SELECT nonexistent FROM contracts")
    assert result.success is False
    assert result.error is not None
    assert result.rows == []


def test_execute_query_aggregate(sample_db):
    result = execute_query(
        sample_db,
        "SELECT SUM(total_obligation) AS total FROM contracts WHERE awarding_agency_name = 'Department of Defense'"
    )
    assert result.success is True
    assert len(result.rows) == 1
    assert result.rows[0][0] == 8000000.0
