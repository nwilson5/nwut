from unittest.mock import MagicMock, patch

import pytest

from nwut.clients.gemini import GeminiClient
from nwut.errors import AuthError, RateLimitError


def test_raises_if_api_key_missing(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(EnvironmentError, match="GEMINI_API_KEY"):
        GeminiClient()


def test_instantiates_with_key(gemini_env):
    with patch("nwut.clients.gemini.genai"):
        client = GeminiClient()
        assert client is not None


def test_generate_returns_text(gemini_env):
    mock_response = MagicMock()
    mock_response.text = "hello from gemini"

    with patch("nwut.clients.gemini.genai") as mock_genai:
        mock_genai.Client.return_value.models.generate_content.return_value = mock_response
        client = GeminiClient()
        result = client.generate("say hello")

    assert result == "hello from gemini"


def test_generate_raises_auth_error_on_client_error_403(gemini_env):
    from google.genai.errors import ClientError

    exc = ClientError(403, "permission denied")

    with patch("nwut.clients.gemini.genai") as mock_genai:
        mock_genai.Client.return_value.models.generate_content.side_effect = exc
        client = GeminiClient()
        with pytest.raises(AuthError):
            client.generate("test")


def test_generate_raises_rate_limit_error_on_client_error_429(gemini_env):
    from google.genai.errors import ClientError

    exc = ClientError(429, "quota exceeded")

    with patch("nwut.clients.gemini.genai") as mock_genai:
        mock_genai.Client.return_value.models.generate_content.side_effect = exc
        client = GeminiClient()
        with pytest.raises(RateLimitError):
            client.generate("test")


def test_generate_raises_transient_error_on_server_error(gemini_env):
    from google.genai.errors import ServerError

    from nwut.errors import TransientError

    exc = ServerError(500, "internal error")

    with patch("nwut.clients.gemini.genai") as mock_genai:
        mock_genai.Client.return_value.models.generate_content.side_effect = exc
        client = GeminiClient()
        with pytest.raises(TransientError):
            client.generate("test")


def test_generate_structured_returns_json_string(gemini_env):
    from dataclasses import dataclass

    @dataclass
    class Result:
        value: str

    mock_response = MagicMock()
    mock_response.text = '{"value": "hello"}'

    with patch("nwut.clients.gemini.genai") as mock_genai:
        mock_genai.Client.return_value.models.generate_content.return_value = mock_response
        client = GeminiClient()
        result = client.generate_structured("give me a result", schema=Result)

    assert result == '{"value": "hello"}'


def test_generate_structured_raises_transient_error_on_server_error(gemini_env):
    from google.genai.errors import ServerError

    from nwut.errors import TransientError

    exc = ServerError(503, "service unavailable")

    with patch("nwut.clients.gemini.genai") as mock_genai:
        mock_genai.Client.return_value.models.generate_content.side_effect = exc
        client = GeminiClient()
        with pytest.raises(TransientError):
            client.generate_structured("test", schema=object)
