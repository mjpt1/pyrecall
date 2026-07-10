"""Retrieve relevant memories and skills for a query."""

from __future__ import annotations

from pathlib import Path

from pyrecall.models import SearchHit
from pyrecall.paths import find_project_root
from pyrecall.store import Store
from pyrecall.textutil import bm25_score, overlap_boost, tokenize


def _doc_stats(docs: list[tuple[str, list[str]]]) -> tuple[float, dict[str, int]]:
    if not docs:
        return 1.0, {}
    avgdl = sum(len(tokens) for _, tokens in docs) / len(docs)
    df: dict[str, int] = {}
    for _, tokens in docs:
        for term in set(tokens):
            df[term] = df.get(term, 0) + 1
    return avgdl, df


def search(
    query: str,
    *,
    limit: int = 8,
    include_skills: bool = True,
    include_memories: bool = True,
    root: Path | None = None,
) -> list[SearchHit]:
    project = find_project_root(root)
    store = Store(project)
    query_tokens = tokenize(query)
    candidates: list[tuple[str, str, str, str, list[str], str | None, list[str]]] = []

    if include_memories:
        for memory in store.list_memories():
            text = f"{memory.title}\n{memory.body}\n{' '.join(memory.tags)}"
            candidates.append(
                (
                    memory.id,
                    memory.kind.value,
                    memory.title,
                    memory.body,
                    tokenize(text),
                    memory.source_path,
                    memory.tags,
                )
            )

    if include_skills:
        for skill in store.list_skills(active_only=True):
            text = f"{skill.name}\n{skill.rule}\n{' '.join(skill.examples)}\n{' '.join(skill.tags)}"
            candidates.append(
                (
                    skill.id,
                    "skill",
                    skill.name,
                    skill.rule,
                    tokenize(text),
                    None,
                    skill.tags,
                )
            )

    if not candidates:
        return []

    docs = [(c[0], c[4]) for c in candidates]
    avgdl, df = _doc_stats(docs)
    n_docs = len(docs)

    scored: list[SearchHit] = []
    for item_id, kind, title, body, tokens, source_path, tags in candidates:
        score = bm25_score(query_tokens, tokens, avgdl, df, n_docs)
        score += overlap_boost(query, title, body)
        if kind == "skill":
            score *= 1.15
        if kind == "correction":
            score *= 1.2
        if score <= 0:
            continue
        scored.append(
            SearchHit(
                id=item_id,
                kind=kind,
                title=title,
                body=body,
                score=round(score, 4),
                tags=tags,
                source_path=source_path,
            )
        )

    scored.sort(key=lambda h: h.score, reverse=True)
    top = scored[: max(1, limit)]

    # Track skill usefulness
    for hit in top:
        if hit.kind == "skill":
            store.bump_skill(hit.id)

    return top


def format_context(hits: list[SearchHit], *, max_chars: int = 4000) -> str:
    if not hits:
        return "No matching project memory."
    parts: list[str] = []
    used = 0
    for i, hit in enumerate(hits, 1):
        block = (
            f"[{i}] ({hit.kind}) {hit.title}\n"
            f"{hit.body.strip()}\n"
            f"tags: {', '.join(hit.tags) if hit.tags else '-'}"
        )
        if used + len(block) > max_chars:
            break
        parts.append(block)
        used += len(block)
    return "\n\n".join(parts)
