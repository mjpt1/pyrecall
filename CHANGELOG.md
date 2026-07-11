# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-07-11

### Added

- `pyrecall setup-host` — write `HOST_RULES.md`, bridge JSON with project cwd, and an `AGENTS.md` section
- `pyrecall harvest` — turn README / CONTRIBUTING / AGENTS bullets into durable conventions
- Bridge tool `harvest_docs`; stronger REQUIRED wording on `get_context` / `learn_correction`
- 30s demo scripts (`examples/demo.sh` / `demo.ps1`) and [docs/DEMO.md](docs/DEMO.md) recording guide

### Changed

- `init` runs host setup (rules + workflow + AGENTS section)
- Workflow text points hosts at `HOST_RULES.md` and `harvest`

## [0.3.0] - 2026-07-11

### Added

- `pyrecall watch` — poll docs/config/Python files and re-index on change
- `pyrecall packs list|install` — optional packs: fastapi, django, sqlalchemy, ruff
- `pyrecall workflow` — sticky before/after-edit checklist; written on `init`
- Recall `--tag` filter and `why` explanations on each hit
- Bridge tool `install_pack`; `get_context` / `search_memory` accept optional `tags`

### Changed

- `get_context` output includes why each result matched
- Bridge `learn_correction` description nudges hosts to persist user corrections

## [0.2.0] - 2026-07-11

### Added

- `pyrecall doctor` — diagnose PATH, Python, and `.pyrecall/` store health (Windows-friendly hints)
- `pyrecall forget` — deactivate a skill so it stops appearing in recall
- Config summarizer for `pyproject.toml` / ini-style files (keeps high-signal sections only)
- Smarter correction parsing (`don't use X, use Y`, `use Y instead of X`)
- Auto topic tags on learned skills (pytest, pathlib, typing, packaging, …)

### Changed

- Recall ranking demotes bulky auto-indexed dumps so skills/corrections surface first
- Recall output truncates long indexed bodies for readable context blocks
- Docs/index bodies are capped more tightly

### Notes

- PyPI distribution name remains `pyrecall-cli`; import and CLI remain `pyrecall`

## [0.1.0] - 2026-07-10

### Added

- Local SQLite store for memories, corrections, and skills under `.pyrecall/`
- CLI: `init`, `index`, `remember`, `learn`, `recall`, `skills`, `playbook`, `stats`, `export`, `import-data`, `serve`
- Correction learning that distills rejected/preferred pairs into reusable skills
- Local BM25 + overlap ranking (no network, no model downloads)
- Stdio JSON-RPC tool bridge with `get_context`, `search_memory`, `learn_correction`, and related tools
- Python default skills (pytest, typing, pathlib, I/O, exceptions, pyproject)
- Project indexer for docs and Python module signals
- Docs: README demo, bridge guide, PyPI publish guide
- GitHub Actions CI (Python 3.10–3.13 on Ubuntu/Windows) and Trusted Publishing workflow
- Example host configs for the stdio bridge

### Notes

- PyPI distribution name is `pyrecall-cli` (because `pyrecall` / `py-recall` collide with an existing project); import and CLI remain `pyrecall`

[0.4.0]: https://github.com/mjpt1/pyrecall/releases/tag/v0.4.0
[0.3.0]: https://github.com/mjpt1/pyrecall/releases/tag/v0.3.0
[0.2.0]: https://github.com/mjpt1/pyrecall/releases/tag/v0.2.0
[0.1.0]: https://github.com/mjpt1/pyrecall/releases/tag/v0.1.0
