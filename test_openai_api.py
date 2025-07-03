#!/usr/bin/env python3
import os
import pytest

try:
    import openai
except ImportError:  # pragma: no cover - dependency missing
    openai = None


def test_openai_api():
    if openai is None:
        pytest.skip("openai package not installed")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not configured")

    openai.api_key = api_key
    resp = openai.models.list()
    assert hasattr(resp, "data")

    chat = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Say hello in one word."}],
        temperature=0,
    )
    assert chat.choices[0].message.content

if __name__ == "__main__":
    test_openai_api()
