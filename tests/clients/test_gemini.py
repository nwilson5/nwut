import pytest
from unittest.mock import MagicMock, patch

from nwut.clients.gemini import GeminiClient
from nwut.errors import ApiError, AuthError, RateLimitError


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
        mock_genai.GenerativeModel.return_value.generate_content.return_value = mock_response
        client = GeminiClient()
        result = client.generate("say hello")

    assert result == "hello from gemini"


def test_generate_raises_auth_error_on_permission_denied(gemini_env):
    from google.api_core.exceptions import PermissionDenied

    with patch("nwut.clients.gemini.genai") as mock_genai:
        mock_genai.GenerativeModel.return_value.generate_content.side_effect = PermissionDenied(
            "invalid key"
        )
        client = GeminiClient()
        with pytest.raises(AuthError):
            client.generate("test")


def test_generate_raises_rate_limit_error(gemini_env):
    from google.api_core.exceptions import ResourceExhausted

    with patch("nwut.clients.gemini.genai") as mock_genai:
        mock_genai.GenerativeModel.return_value.generate_content.side_effect = ResourceExhausted(
            "quota exceeded"
        )
        client = GeminiClient()
        with pytest.raises(RateLimitError):
            client.generate("test")
