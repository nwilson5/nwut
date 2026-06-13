import pytest
from dotenv import load_dotenv

load_dotenv()


@pytest.fixture
def gemini_env(monkeypatch):
    """Set a fake GEMINI_API_KEY so GeminiClient can be instantiated in tests."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-fake")
