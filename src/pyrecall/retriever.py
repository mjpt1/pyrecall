"""Retrieve relevant memories and skills for a query."""

from __future__ import annotations

from pathlib import Path

from pyrecall.models import SearchHit
from pyrecall.paths import find_project_root
from pyrecall.store import Store
from pyrecall.summarize import display_body
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


def _kind_boost(kind: str, title: str, tags: list[str], query: str = "") -> float:
    q = (query or "").lower()
    guidance_query = any(w in q for w in ("how", "should", "prefer", "write", "use"))

    if kind == "skill" and "correction" in tags:
        boost = 2.0
    elif kind == "skill":
        boost = 1.6
    elif kind == "correction":
        boost = 1.8
    elif kind == "decision":
        boost = 1.15
    elif kind == "convention" and "indexed" not in tags:
        boost = 1.1
    elif "indexed" in tags and title.startswith("Config:"):
        boost = 0.35
    elif "indexed" in tags and title.startswith("Module:") and "testing" in tags:
        boost = 0.3
    elif "indexed" in tags and title.startswith(("Module:", "File:")):
        boost = 0.5
    elif "indexed" in tags and title.startswith("Doc:"):
        boost = 0.7
    else:
        boost = 1.0

    if guidance_query and kind in {"skill", "correction"}:
        boost *= 1.25
    if guidance_query and "indexed" in tags:
        boost *= 0.75
    return boost


def _explain_why(
    *,
    kind: str,
    title: str,
    tags: list[str],
    query: str,
    query_tokens: list[str],
    tokens: list[str],
    score: float,
) -> list[str]:
    reasons: list[str] = []
    token_set = set(tokens)
    matched = [t for t in query_tokens if t in token_set]
    if matched:
        reasons.append(f"matched terms: {', '.join(matched[:5])}")

    q_words = set(query_tokens)
    q_lower = query.lower()
    tag_hits = sorted(
        {t for t in tags if t.lower() in q_words or t.lower() in q_lower}
    )
    if tag_hits:
        reasons.append(f"tag overlap: {', '.join(tag_hits[:5])}")

    if kind == "skill" and "correction" in tags:
        reasons.append("learned correction skill")
    elif kind == "skill":
        reasons.append("active skill")
    elif kind == "correction":
        reasons.append("stored correction")
    elif kind in {"decision", "convention"} and "indexed" not in tags:
        reasons.append(f"project {kind}")
    elif "indexed" in tags:
        reasons.append("indexed project file")

    if score >= 3:
        reasons.append("strong rank score")
    return reasons[:4]


def _normalize_tags(tags: list[str] | None) -> set[str]:
    if not tags:
        return set()
    return {t.strip().lower() for t in tags if t and t.strip()}


def search(
    query: str,
    *,
    limit: int = 8,
    include_skills: bool = True,
    include_memories: bool = True,
    tags: list[str] | None = None,
    under: str | None = None,
    root: Path | None = None,
) -> list[SearchHit]:
    project = find_project_root(root)
    store = Store(project)
    query_tokens = tokenize(query)
    required_tags = _normalize_tags(tags)
    scope = (under or "").replace("\\", "/").strip().lstrip("./")
    candidates: list[tuple[str, str, str, str, list[str], str | None, list[str]]] = []

    if include_memories:
        for memory in store.list_memories():
            if required_tags and not required_tags.intersection(
                {t.lower() for t in memory.tags}
            ):
                continue
            if scope:
                src = (memory.source_path or "").replace("\\", "/")
                scope_l = scope.lower()
                in_path = bool(src) and (
                    src == scope
                    or src.startswith(scope.rstrip("/") + "/")
                    or src.startswith(scope)
                )
                mentions = scope_l in memory.title.lower() or scope_l in memory.body.lower()
                if "indexed" in memory.tags or "harvested" in memory.tags:
                    if not (in_path or mentions):
                        continue
                elif src and not (in_path or mentions):
                    continue
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
            if required_tags and not required_tags.intersection(
                {t.lower() for t in skill.tags}
            ):
                continue
            if scope:
                # Keep skills always when scoped: they are project-wide guidance.
                # Boost later via path tokens in query if needed.
                pass
            text = f"{skill.name}\n{skill.rule}\n{' '.join(skill.examples)}\n{' '.join(skill.tags)}"
            if scope:
                text = f"{text}\n{scope}"
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
    for item_id, kind, title, body, tokens, source_path, item_tags in candidates:
        score = bm25_score(query_tokens, tokens, avgdl, df, n_docs)
        score += overlap_boost(query, title, body)
        score *= _kind_boost(kind, title, item_tags, query)
        if score <= 0:
            continue
        why = _explain_why(
            kind=kind,
            title=title,
            tags=item_tags,
            query=query,
            query_tokens=query_tokens,
            tokens=tokens,
            score=score,
        )
        scored.append(
            SearchHit(
                id=item_id,
                kind=kind,
                title=title,
                body=body,
                score=round(score, 4),
                tags=item_tags,
                source_path=source_path,
                why=why,
            )
        )

    scored.sort(key=lambda h: h.score, reverse=True)
    top = scored[: max(1, limit)]

    for hit in top:
        if hit.kind == "skill":
            store.bump_skill(hit.id)

    return top


def format_context(
    hits: list[SearchHit],
    *,
    max_chars: int = 3500,
    show_why: bool = True,
) -> str:
    if not hits:
        return "No matching project memory."
    parts: list[str] = []
    used = 0
    for i, hit in enumerate(hits, 1):
        body = display_body(hit.kind, hit.title, hit.body, hit.tags)
        block = (
            f"[{i}] ({hit.kind}) {hit.title}\n"
            f"{body}\n"
            f"tags: {', '.join(hit.tags) if hit.tags else '-'}"
        )
        if show_why and hit.why:
            block += f"\nwhy: {'; '.join(hit.why)}"
        if used + len(block) > max_chars:
            break
        parts.append(block)
        used += len(block)
    return "\n\n".join(parts)
