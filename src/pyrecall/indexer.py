"""Index project files into local memories."""

from __future__ import annotations

from pathlib import Path, PurePosixPath

from pyrecall.models import Memory, MemoryKind, ProjectConfig
from pyrecall.paths import find_project_root, load_config
from pyrecall.store import Store
from pyrecall.textutil import snippet

DOC_NAMES = {
    "readme.md",
    "contributing.md",
    "conventions.md",
    "agents.md",
    "changelog.md",
}


def _match(rel: str, pattern: str) -> bool:
    norm = rel.replace("\\", "/")
    path = PurePosixPath(norm)
    candidates = [pattern]
    if pattern.startswith("**/"):
        candidates.append(pattern[3:])
    for candidate in candidates:
        if path.match(candidate):
            return True
        if PurePosixPath(path.name).match(candidate):
            return True
    # Segment excludes: **/.venv/**, **/__pycache__/**
    compact = pattern.replace("**/", "").replace("/**", "").strip("/")
    if compact and "/" not in compact and "*" not in compact:
        return compact in path.parts
    return False


def _is_excluded(rel: str, patterns: list[str]) -> bool:
    return any(_match(rel, pat) for pat in patterns)


def _is_included(rel: str, patterns: list[str]) -> bool:
    return any(_match(rel, pat) for pat in patterns)


def iter_project_files(root: Path, config: ProjectConfig) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            rel = path.relative_to(root).as_posix()
        except ValueError:
            continue
        if _is_excluded(rel, config.exclude_globs):
            continue
        if not _is_included(rel, config.include_globs):
            continue
        try:
            if path.stat().st_size > config.max_file_bytes:
                continue
        except OSError:
            continue
        files.append(path)
    return sorted(files)


def _memory_from_file(root: Path, path: Path) -> Memory | None:
    rel = path.relative_to(root).as_posix()
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    if not text.strip():
        return None

    name = path.name.lower()
    suffix = path.suffix.lower()
    if name in DOC_NAMES or suffix in {".md", ".rst"}:
        kind = MemoryKind.DOC
        title = f"Doc: {rel}"
        body = text[:8000]
    elif name in {"pyproject.toml", "setup.cfg", "tox.ini"}:
        kind = MemoryKind.CONVENTION
        title = f"Config: {rel}"
        body = text[:8000]
    elif suffix == ".py":
        kind = MemoryKind.NOTE
        title = f"Module: {rel}"
        lines = text.splitlines()
        kept: list[str] = []
        for line in lines[:120]:
            stripped = line.strip()
            if (
                stripped.startswith('"""')
                or stripped.startswith("'''")
                or stripped.startswith("import ")
                or stripped.startswith("from ")
                or stripped.startswith("def ")
                or stripped.startswith("class ")
                or stripped.startswith("@")
                or stripped.startswith("#")
            ):
                kept.append(line)
        body = "\n".join(kept) if kept else snippet(text, 1200)
    else:
        kind = MemoryKind.NOTE
        title = f"File: {rel}"
        body = snippet(text, 2000)

    tags = ["indexed", "python"] if suffix == ".py" else ["indexed"]
    if "test" in rel:
        tags.append("testing")
    return Memory(
        kind=kind,
        title=title,
        body=body,
        tags=tags,
        source_path=rel,
        language="python" if suffix == ".py" else "text",
        metadata={"bytes": len(text.encode("utf-8", errors="ignore"))},
    )


def index_project(root: Path | None = None, replace_indexed: bool = True) -> dict[str, int]:
    project = find_project_root(root)
    config = load_config(project)
    store = Store(project)

    if replace_indexed:
        for memory in store.list_memories():
            if "indexed" in memory.tags:
                store.delete_memory(memory.id)

    files = iter_project_files(project, config)
    added = 0
    for path in files:
        memory = _memory_from_file(project, path)
        if memory is None:
            continue
        store.upsert_memory(memory)
        added += 1

    return {"files": len(files), "memories": added, "root": str(project)}
