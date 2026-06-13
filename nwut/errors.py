class ApiError(Exception):
    """Base error for all nwut API clients."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class AuthError(ApiError):
    """Invalid or missing API key."""


class RateLimitError(ApiError):
    """Rate limit or quota exceeded."""


class TransientError(ApiError):
    """Temporary failure — safe to retry."""
