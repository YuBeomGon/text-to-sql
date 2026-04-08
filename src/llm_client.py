from __future__ import annotations

import os
import re

from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

_DEFAULT_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


def _strip_sql_fences(text: str) -> str:
    """Remove ```sql ... ``` markdown fences if present."""
    text = text.strip()
    pattern = r"^```(?:sql)?\s*\n?(.*?)\n?```$"
    match = re.match(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text


def generate_sql(
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
) -> str:
    """Send prompts to OpenAI and return the generated SQL string."""
    client = _get_client()
    response = client.chat.completions.create(
        model=model or _DEFAULT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.0,
    )
    raw = response.choices[0].message.content or ""
    return _strip_sql_fences(raw)
