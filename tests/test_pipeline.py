from unittest.mock import patch, MagicMock
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


def test_run_question_handles_clarify(sample_db):
    with patch("src.pipeline.generate_sql") as mock_llm:
        mock_llm.return_value = "CLARIFY: amount is ambiguous between obligation and outlay"

        result = run_question(sample_db, "What is the amount for DoD?")
        assert result.behavior == "clarify"
        assert result.sql is None
        assert result.rows == []


def test_run_question_handles_abstain(sample_db):
    with patch("src.pipeline.generate_sql") as mock_llm:
        mock_llm.return_value = "ABSTAIN: no employee data in this schema"

        result = run_question(sample_db, "How many employees does NASA have?")
        assert result.behavior == "abstain"
        assert result.sql is None


def test_run_question_handles_sql_error(sample_db):
    with patch("src.pipeline.generate_sql") as mock_llm:
        mock_llm.return_value = "SELECT nonexistent_col FROM contracts"

        result = run_question(sample_db, "bad query")
        assert result.success is False
        assert result.error is not None
        assert result.behavior == "answer"
