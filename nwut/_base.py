import logging
from collections.abc import Callable
from typing import Any

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from nwut.errors import TransientError, RateLimitError

logger = logging.getLogger(__name__)


def _is_retryable(exc: BaseException) -> bool:
    return isinstance(exc, (TransientError, RateLimitError))


def with_retry(func: Callable) -> Callable:
    """Decorator: exponential backoff on TransientError or RateLimitError."""
    return retry(
        retry=retry_if_exception_type((TransientError, RateLimitError)),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(4),
        reraise=True,
        before_sleep=lambda rs: logger.warning(
            "retrying %s (attempt %d): %s",
            func.__name__,
            rs.attempt_number,
            rs.outcome.exception(),
        ),
    )(func)


class BaseClient:
    """Shared base for all API clients. Subclasses handle their own SDK init."""

    def _normalize_error(self, exc: Exception, status_code: int | None = None) -> None:
        """Re-raise exc as the appropriate nwut error type."""
        from nwut.errors import ApiError, AuthError, RateLimitError, TransientError

        code = status_code or getattr(exc, "code", None) or getattr(exc, "status_code", None)

        if code in (401, 403):
            raise AuthError(str(exc), status_code=code) from exc
        if code == 429:
            raise RateLimitError(str(exc), status_code=code) from exc
        if code is not None and code >= 500:
            raise TransientError(str(exc), status_code=code) from exc

        raise ApiError(str(exc), status_code=code) from exc
