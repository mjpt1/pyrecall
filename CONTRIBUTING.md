# Contributing

## Setup

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Unix
source .venv/bin/activate

pip install -e ".[dev]"
```

## Checks

```bash
pytest
ruff check src tests
python -m build
twine check dist/*
```

Publishing steps: [docs/PUBLISH.md](docs/PUBLISH.md).

## Guidelines

- Keep recall fully local — no network calls in the ranking path.
- Prefer small, testable modules under `src/pyrecall/`.
- Add tests for new CLI commands and bridge tools.
- Do not add telemetry.
