# Changelog

## v0.1.0 — 2026-06-12

- Initial release
- `GeminiClient` — generate text and structured output via Gemini API
- `BaseClient` — shared retry logic (exponential backoff via tenacity) and error normalization
- `errors` — `ApiError`, `AuthError`, `RateLimitError`, `TransientError`
