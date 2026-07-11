"""Poll project files and re-index when they change."""

from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path

from pyrecall.indexer import index_project
from pyrecall.paths import find_project_root, load_config

# High-signal paths worth watching even if globs are broad.
WATCH_HINTS = (
    "README.md",
    "README.rst",
    "CONTRIBUTING.md",
    "AGENTS.md",
    "CONVENTIONS.md",
    "pyproject.toml",
    "setup.cfg",
    "tox.ini",
    ".python-version",
)


def _iter_watch_files(root: Path) -> list[Path]:
    config = load_config(root)
    files: set[Path] = set()
    for hint in WATCH_HINTS:
        candidate = root / hint
        if candidate.is_file():
            files.add(candidate.resolve())
    for pattern in config.include_globs:
        # Limit to shallow docs/config + Python under src/tests to keep polling cheap.
        if pattern.endswith(".py"):
            for base in (root / "src", root / "tests", root):
                if not base.exists():
                    continue
                for path in base.rglob("*.py"):
                    if path.is_file() and ".pyrecall" not in path.parts:
                        files.add(path.resolve())
        elif any(token in pattern for token in (".md", ".rst", "pyproject", "setup.cfg", "tox")):
            for path in root.glob(pattern):
                if path.is_file():
                    files.add(path.resolve())
    # Cap to avoid scanning huge trees every tick
    return sorted(files)[:400]


def snapshot_mtimes(root: Path) -> dict[str, float]:
    snap: dict[str, float] = {}
    for path in _iter_watch_files(root):
        try:
            snap[str(path)] = path.stat().st_mtime
        except OSError:
            continue
    return snap


def watch_once(root: Path | None = None) -> dict[str, object]:
    """Re-index immediately (useful for tests and scripts)."""
    project = find_project_root(root)
    result = index_project(project, replace_indexed=True)
    return {"root": str(project), **result}


def watch_loop(
    root: Path | None = None,
    *,
    interval: float = 2.0,
    once: bool = False,
    on_change: Callable[[dict[str, object]], None] | None = None,
    max_iterations: int | None = None,
) -> None:
    """Poll for file changes and re-index. Blocks until interrupted unless limited."""
    project = find_project_root(root)
    previous = snapshot_mtimes(project)
    # Always index once on start so watchers begin from a fresh store.
    result = index_project(project, replace_indexed=True)
    if on_change:
        on_change({"event": "start", **result})
    if once:
        return

    iterations = 0
    while True:
        if max_iterations is not None and iterations >= max_iterations:
            return
        time.sleep(max(0.2, interval))
        iterations += 1
        current = snapshot_mtimes(project)
        if current != previous:
            previous = current
            result = index_project(project, replace_indexed=True)
            if on_change:
                on_change({"event": "change", **result})
