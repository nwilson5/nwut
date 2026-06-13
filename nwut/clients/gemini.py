import os

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from nwut._base import BaseClient, with_retry
from nwut.errors import AuthError, RateLimitError, TransientError


class GeminiClient(BaseClient):
    """Thin wrapper around the Gemini SDK (google-genai).

    Reads GEMINI_API_KEY from the environment. Raises EnvironmentError at
    instantiation if the key is missing, so failures surface immediately
    rather than at call time.
    """

    DEFAULT_MODEL = "gemini-2.0-flash"

    def __init__(self, model: str = DEFAULT_MODEL):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError("GEMINI_API_KEY is not set")
        self._client = genai.Client(api_key=api_key)
        self._model = model

    @with_retry
    def generate(self, prompt: str) -> str:
        """Generate a text response for the given prompt."""
        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
            )
            return response.text
        except genai_errors.ClientError as exc:
            self._normalize_error(exc, status_code=exc.code)
        except genai_errors.ServerError as exc:
            raise TransientError(str(exc), status_code=exc.code) from exc

    @with_retry
    def generate_structured(self, prompt: str, schema: type) -> str:
        """Generate a response conforming to schema.

        schema should be a dataclass or Pydantic model. Returns the raw JSON
        string — callers parse it into the schema type as needed.
        """
        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                ),
            )
            return response.text
        except genai_errors.ClientError as exc:
            self._normalize_error(exc, status_code=exc.code)
        except genai_errors.ServerError as exc:
            raise TransientError(str(exc), status_code=exc.code) from exc
