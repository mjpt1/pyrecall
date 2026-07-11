"""Harvest conventions from project docs into durable memories."""

from __future__ import annotations

import re
from pathlib import Path

from pyrecall.models import Memory, MemoryKind
from pyrecall.paths import find_project_root
from pyrecall.store import Store

HARVEST_FILES = (
    "README.md",
    "CONTRIBUTING.md",
    "AGENTS.md",
    "CONVENTIONS.md",
    "docs/CONTRIBUTING.md",
    "docs/AGENTS.md",
)

SECTION_HINTS = (
    "test",
    "testing",
    "convention",
    "style",
    "guideline",
    "standard",
    "practice",
    "coding",
    "python",
    "lint",
    "type",
    "prefer",
    "rule",
    "development",
    "workflow",
    "contribution",
    "architecture",
    "api",
    "error",
    "packaging",
)

BULLET_RE = re.compile(r"^\s*[-*+]\s+(.+)$")
NUMBERED_RE = re.compile(r"^\s*\d+[.)]\s+(.+)$")
HEADING_RE = re.compile(r"^(#{1,3})\s+(.+)$")


def _interesting_section(title: str) -> bool:
    lower = title.lower()
    return any(hint in lower for hint in SECTION_HINTS)


def _parse_sections(text: str) -> list[tuple[str, list[str]]]:
    sections: list[tuple[str, list[str]]] = []
    current = "Document"
    bullets: list[str] = []
    for raw in text.splitlines():
        heading = HEADING_RE.match(raw)
        if heading:
            if bullets:
                sections.append((current, bullets))
            current = heading.group(2).strip()
            bullets = []
            continue
        for pattern in (BULLET_RE, NUMBERED_RE):
            match = pattern.match(raw)
            if match:
                item = match.group(1).strip()
                # Strip simple markdown emphasis
                item = re.sub(r"[*`_]+", "", item).strip()
                if 12 <= len(item) <= 400:
                    bullets.append(item)
                break
    if bullets:
        sections.append((current, bullets))
    return sections


def _candidate_paths(root: Path) -> list[Path]:
    found: list[Path] = []
    for rel in HARVEST_FILES:
        path = root / rel
        if path.is_file():
            found.append(path)
    # Also pick top-level *CONTRIBUTING* / *CONVENTION* variants
    for path in root.iterdir():
        if not path.is_file():
            continue
        name = path.name.lower()
        if name.endswith((".md", ".rst")) and any(
            key in name for key in ("contribut", "convention", "agent", "develop")
        ):
            if path not in found:
                found.append(path)
    return found


def _clear_harvested(store: Store, source_path: str | None = None) -> int:
    removed = 0
    for memory in store.list_memories():
        if "harvested" not in memory.tags:
            continue
        if source_path and memory.source_path != source_path:
            continue
        with store.connect() as conn:
            conn.execute("DELETE FROM memories WHERE id = ?", (memory.id,))
        removed += 1
    return removed


def harvest_docs(
    root: Path | None = None,
    *,
    replace: bool = True,
    max_items: int = 40,
) -> dict[str, int | str]:
    project = find_project_root(root)
    store = Store(project)
    if replace:
        _clear_harvested(store)

    added = 0
    files = 0
    for path in _candidate_paths(project):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = path.relative_to(project).as_posix()
        files += 1
        sections = _parse_sections(text)
        for section, bullets in sections:
            if not _interesting_section(section) and section != "Document":
                # Still take Document-level bullets from CONTRIBUTING/AGENTS
                if path.name.lower() not in {
                    "contributing.md",
                    "agents.md",
                    "conventions.md",
                }:
                    continue
            for bullet in bullets:
                if added >= max_items:
                    return {
                        "root": str(project),
                        "files": files,
                        "memories": added,
                    }
                title = f"Doc rule: {bullet[:60]}"
                # Prefer unique titles
                existing = {m.title for m in store.list_memories()}
                if title in existing:
                    continue
                memory = Memory(
                    kind=MemoryKind.CONVENTION,
                    title=title,
                    body=f"From {rel} § {section}\n{bullet}",
                    tags=["python", "harvested", "docs"],
                    source_path=rel,
                    metadata={"harvest_section": section},
                )
                store.upsert_memory(memory)
                added += 1

    return {"root": str(project), "files": files, "memories": added}
