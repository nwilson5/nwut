import os

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from nwut._base import BaseClient, with_retry
from nwut.errors import AuthError


class GeminiClient(BaseClient):
    """Thin wrapper around the Gemini generative AI SDK.

    Reads GEMINI_API_KEY from the environment. Raises EnvironmentError at
    instantiation if the key is missing, so failures surface immediately
    rather than at call time.
    """

    DEFAULT_MODEL = "gemini-2.0-flash"

    def __init__(self, model: str = DEFAULT_MODEL):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError("GEMINI_API_KEY is not set")
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model)

    @with_retry
    def generate(self, prompt: str) -> str:
        """Generate a text response for the given prompt."""
        try:
            response = self._model.generate_content(prompt)
            return response.text
        except google_exceptions.PermissionDenied as exc:
            raise AuthError(str(exc), status_code=403) from exc
        except google_exceptions.ResourceExhausted as exc:
            from nwut.errors import RateLimitError
            raise RateLimitError(str(exc), status_code=429) from exc
        except google_exceptions.ServiceUnavailable as exc:
            from nwut.errors import TransientError
            raise TransientError(str(exc), status_code=503) from exc
        except Exception as exc:
            self._normalize_error(exc)

    @with_retry
    def generate_structured(self, prompt: str, schema: type) -> dict:
        """Generate a response parsed into a structured dict matching schema.

        schema should be a dataclass or Pydantic model. The response is
        parsed via the Gemini structured output feature.
        """
        try:
            model = genai.GenerativeModel(
                self._model.model_name,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                ),
            )
            response = model.generate_content(prompt)
            return response.text
        except google_exceptions.PermissionDenied as exc:
            raise AuthError(str(exc), status_code=403) from exc
        except google_exceptions.ResourceExhausted as exc:
            from nwut.errors import RateLimitError
            raise RateLimitError(str(exc), status_code=429) from exc
        except google_exceptions.ServiceUnavailable as exc:
            from nwut.errors import TransientError
            raise TransientError(str(exc), status_code=503) from exc
        except Exception as exc:
            self._normalize_error(exc)
