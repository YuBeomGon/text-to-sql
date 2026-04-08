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
        assert result.ir is not None
        assert result.ir.entities.get("agency") == "NASA"


def test_run_question_ambiguous_metric_detected_by_ir(sample_db):
    """When metric interpreter detects ambiguity, pipeline should clarify WITHOUT calling LLM."""
    with patch("src.pipeline.generate_sql") as mock_llm:
        result = run_question(sample_db, "What is the amount for NASA?")
        assert result.behavior == "clarify"
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
    with patch("src.pipeline.generate_sql") as mock_llm:
        mock_llm.return_value = "SELECT COUNT(*) FROM contracts WHERE awarding_agency_name = 'Department of Homeland Security'"
        result = run_question(sample_db, "DHS contracts")
        assert result.ir.entities.get("agency") == "Department of Homeland Security"
