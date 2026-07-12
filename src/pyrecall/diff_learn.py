"""Infer corrections from unified diffs / patches."""

from __future__ import annotations

import re
from pathlib import Path


def parse_diff_text(text: str) -> tuple[str, str, str]:
    """
    Extract rejected (removed) and preferred (added) snippets from a diff.

    Returns (rejected, preferred, context_hint).
    """
    raw = text or ""
    removed: list[str] = []
    added: list[str] = []
    files: list[str] = []

    for line in raw.splitlines():
        if line.startswith("--- ") or line.startswith("+++ "):
            name = line[4:].strip()
            if name not in {"/dev/null", "a", "b"} and not name.startswith("/dev/"):
                # strip a/ or b/ prefixes
                name = re.sub(r"^[ab]/", "", name)
                if name and name not in files:
                    files.append(name)
            continue
        if line.startswith("diff ") or line.startswith("index ") or line.startswith("@@"):
            continue
        if line.startswith("-"):
            body = line[1:]
            if body.strip():
                removed.append(body.rstrip())
            continue
        if line.startswith("+"):
            body = line[1:]
            if body.strip():
                added.append(body.rstrip())
            continue

    rejected = "\n".join(removed).strip()
    preferred = "\n".join(added).strip()
    context = f"From diff in {', '.join(files[:3])}" if files else "From diff"
    return rejected, preferred, context


def parse_diff_file(path: Path) -> tuple[str, str, str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return parse_diff_text(text)


def looks_like_diff(text: str) -> bool:
    if not text:
        return False
    lines = text.splitlines()
    has_minus = any(line.startswith("-") and not line.startswith("---") for line in lines)
    has_plus = any(line.startswith("+") and not line.startswith("+++") for line in lines)
    return has_minus and has_plus
