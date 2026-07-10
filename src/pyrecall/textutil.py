"""Lightweight local text ranking (no network, no external model downloads)."""

from __future__ import annotations

import math
import re
from collections import Counter

TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]+|[آ-یء]+|\d+")

STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "to",
        "of",
        "in",
        "on",
        "for",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "with",
        "as",
        "by",
        "at",
        "from",
        "this",
        "that",
        "it",
        "we",
        "you",
        "they",
        "i",
        "not",
        "but",
        "if",
        "then",
        "else",
        "when",
        "use",
        "using",
        "used",
        "please",
        "should",
        "would",
        "could",
        "can",
        "will",
        "just",
        "also",
        "into",
        "about",
    }
)


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text or "") if t.lower() not in STOPWORDS]


def term_freq(tokens: list[str]) -> Counter[str]:
    return Counter(tokens)


def bm25_score(
    query_tokens: list[str],
    doc_tokens: list[str],
    avgdl: float,
    df: dict[str, int],
    n_docs: int,
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    if not query_tokens or not doc_tokens or n_docs <= 0:
        return 0.0
    tf = term_freq(doc_tokens)
    dl = len(doc_tokens)
    score = 0.0
    for term in query_tokens:
        if term not in tf:
            continue
        freq = tf[term]
        doc_freq = df.get(term, 0)
        idf = math.log(1 + (n_docs - doc_freq + 0.5) / (doc_freq + 0.5))
        denom = freq + k1 * (1 - b + b * dl / max(avgdl, 1.0))
        score += idf * (freq * (k1 + 1)) / denom
    return score


def overlap_boost(query: str, title: str, body: str) -> float:
    q = set(tokenize(query))
    if not q:
        return 0.0
    title_hits = len(q & set(tokenize(title)))
    body_hits = len(q & set(tokenize(body)))
    return title_hits * 2.0 + body_hits * 0.15


def snippet(text: str, limit: int = 280) -> str:
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"
