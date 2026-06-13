# nwut

Shared Python utilities for external API clients. Used across VPS services and Lambda functions. Thin wrappers only — retry logic, error normalization, and env var validation. No business logic.

## Clients

| Client | Class | Env var required |
|---|---|---|
| Google Gemini | `GeminiClient` | `GEMINI_API_KEY` |

---

## Installation

### In an external repo (VPS service or Lambda)

Add to `requirements.in`, pinned to a tag:

```
nwut @ git+https://github.com/nwilson5/nwut.git@v0.1.0
```

Generate a locked `requirements.txt`:

```bash
uv pip compile requirements.in -o requirements.txt
```

Use the locked file in your Dockerfile:

```dockerfile
COPY requirements.txt .
RUN pip install -r requirements.txt
```

Transitive dependencies (`google-genai`, `tenacity`, etc.) are declared in `nwut/pyproject.toml` and resolved automatically — you do not need to list them in `requirements.in`.

To upgrade nwut, update the tag in `requirements.in` and re-run `uv pip compile`.

### Local development on nwut itself

```bash
git clone https://github.com/nwilson5/nwut
cd nwut
pip install -e ".[dev]"
```

The editable install (`-e`) means changes to source files take effect immediately — no reinstall needed.

### Jupyter notebooks (local scratch only)

Notebooks live in `notebooks/` — gitignored, never committed. Uses a dedicated conda env registered as a Jupyter kernel.

**One-time setup:**

```bash
conda create -n nwut python=3.14 -y
conda activate nwut
pip install -e ".[dev,notebook]"
python -m ipykernel install --user --name nwut --display-name "nwut"
```

**Launch:**

```bash
jupyter lab
# select "nwut" kernel in the notebook UI
```

You can launch from any conda env — the `nwut` kernel will appear in the list. A starter notebook is at `notebooks/gemini.ipynb`. It loads `.env` from the repo root explicitly so it works without direnv active.

---

## Environment variables

Each client validates its required env var at instantiation and raises `EnvironmentError` immediately if it is missing. Failures surface at startup, not at call time.

Set vars locally via `.env` + direnv:

```bash
# .env  (gitignored)
GEMINI_API_KEY=your-key-here
```

```bash
# .envrc
dotenv
```

```bash
direnv allow
```

In deployed services, vars are injected by Vault at deploy time via the CI/CD pipeline.

---

## Usage

### GeminiClient

```python
from nwut.clients.gemini import GeminiClient

client = GeminiClient()  # reads GEMINI_API_KEY from env

# Generate text
response = client.generate("Summarize the key principles of SRE in three sentences.")
print(response)

# Generate structured output
from dataclasses import dataclass

@dataclass
class Summary:
    title: str
    points: list[str]

result = client.generate_structured(
    "List the key principles of SRE as a title and bullet points.",
    schema=Summary,
)
print(result)
```

The default model is `gemini-2.5-flash`. Pass `model=` to override:

```python
client = GeminiClient(model="gemini-2.5-pro")
```

### Error handling

All clients raise from `nwut.errors` — never from the underlying SDK directly:

```python
from nwut import errors

try:
    response = client.generate("hello")
except errors.AuthError:
    # bad or missing API key
except errors.RateLimitError:
    # quota exceeded — client retries automatically before raising
except errors.TransientError:
    # upstream 5xx — client retries automatically before raising
except errors.ApiError:
    # catch-all for other API failures
```

Transient errors and rate limit errors are retried automatically with exponential backoff (up to 4 attempts) before the exception is raised to the caller.

---

## Testing

```bash
# Unit tests — mocked, no API key needed, runs in CI
pytest

# Integration tests — real API calls, requires GEMINI_API_KEY
# .env is loaded automatically, direnv not required
pytest -m integration

# Lint + format
ruff check . && ruff format --check .
```

Integration tests live in files named `test_*_integration.py` and are marked `@pytest.mark.integration`. They never run in CI.

For quick local experiments, create a `scratch.py` at the repo root (gitignored) and run it directly:

```bash
python scratch.py
```

---

## Adding a new client

1. Add `nwut/clients/<name>.py` subclassing `BaseClient`
2. Read credentials from `os.environ`, raise `EnvironmentError` if missing
3. Wrap SDK exceptions using `self._normalize_error()` or raise `nwut.errors` types directly
4. Add `tests/clients/test_<name>.py` (mocked) and optionally `test_<name>_integration.py`
5. Add the SDK as a dependency in `pyproject.toml`
6. Export the client from `nwut/__init__.py`
7. Add entry to `CHANGELOG.md`, run `make release v=<version>`

---

## Versioning

Follows semantic versioning. Releases are git tags — not published to PyPI.

| Change | Version bump |
|---|---|
| Bug fix, no API change | PATCH (`v0.1.0` → `v0.1.1`) |
| New client or method, backwards compatible | MINOR (`v0.1.0` → `v0.2.0`) |
| Breaking change to existing interface | MAJOR (`v0.1.0` → `v1.0.0`) |

Release process:

```bash
# 1. Add entry to CHANGELOG.md
# 2. Run:
make release v=0.2.0
```

Consuming repos update their pinned tag in `requirements.in` and re-run `uv pip compile` to pick up the new version.
