# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.1.0]: https://github.com/mjpt1/pyrecall/releases/tag/v0.1.0
