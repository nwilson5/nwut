from dataclasses import dataclass

import pytest

from nwut.clients.gemini import GeminiClient


@pytest.mark.integration
def test_generate_returns_text():
    client = GeminiClient()
    result = client.generate("Say 'hello' and nothing else.")
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.integration
def test_generate_structured_returns_parsed_json():
    @dataclass
    class Answer:
        value: str

    client = GeminiClient()
    result = client.generate_structured(
        "Respond with a single word answer: what color is the sky?",
        schema=Answer,
    )
    assert isinstance(result, str)
    assert "value" in result
