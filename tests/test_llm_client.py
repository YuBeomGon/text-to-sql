import os
from unittest.mock import patch, MagicMock
from src.llm_client import generate_sql


def test_generate_sql_returns_string():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "SELECT COUNT(*) FROM contracts"

    with patch("src.llm_client._get_client") as mock_get:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get.return_value = mock_client

        result = generate_sql(
            system_prompt="You are a SQL expert.",
            user_prompt="How many contracts?",
        )
        assert result == "SELECT COUNT(*) FROM contracts"
        mock_client.chat.completions.create.assert_called_once()


def test_generate_sql_strips_markdown_fences():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "```sql\nSELECT 1\n```"

    with patch("src.llm_client._get_client") as mock_get:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get.return_value = mock_client

        result = generate_sql(
            system_prompt="You are a SQL expert.",
            user_prompt="Test query",
        )
        assert result == "SELECT 1"


def test_generate_sql_uses_configured_model():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "SELECT 1"

    with patch("src.llm_client._get_client") as mock_get:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get.return_value = mock_client

        generate_sql("sys", "user", model="gpt-4o")
        call_kwargs = mock_client.chat.completions.create.call_args
        assert call_kwargs.kwargs["model"] == "gpt-4o"
