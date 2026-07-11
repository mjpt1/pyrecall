"""Summarize config files and keep indexed bodies readable."""

from __future__ import annotations

import re

from pyrecall.textutil import snippet

SECTION_RE = re.compile(r"^\[([^\]]+)\]\s*$", re.MULTILINE)
INTERESTING = (
    "project",
    "project.optional-dependencies",
    "project.scripts",
    "tool.pytest",
    "tool.pytest.ini_options",
    "tool.ruff",
    "tool.ruff.lint",
    "tool.coverage",
    "tool.mypy",
    "build-system",
)


def summarize_config_text(text: str, *, limit: int = 1400) -> str:
    """Keep high-signal sections from pyproject/setup.cfg-like files."""
    raw = text.strip()
    if not raw:
        return ""
    if len(raw) <= limit and raw.count("\n") < 80:
        return raw

    parts = SECTION_RE.split(raw)
    # parts: [preamble, section1, body1, section2, body2, ...]
    kept: list[str] = []
    if parts and parts[0].strip():
        # build-system often appears before first named section in TOML via table
        preamble = parts[0].strip()
        if "build-backend" in preamble or "requires" in preamble:
            kept.append(preamble[:400])

    for i in range(1, len(parts), 2):
        section = parts[i].strip().lower()
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        if not any(section == name or section.startswith(name + ".") for name in INTERESTING):
            # also keep short sections that mention pytest/test
            if "pytest" not in section and "test" not in section and "project" not in section:
                continue
        block_lines = []
        for line in body.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            # Skip repetitive filler often found in generated fixtures
            if stripped.count("=") == 1 and stripped.split("=", 1)[0].strip() in {"x", "y", "n"}:
                continue
            block_lines.append(line)
            if len(block_lines) >= 10:
                break
        block = f"[{parts[i].strip()}]\n" + "\n".join(block_lines)
        block = block.strip()
        kept.append(block[:400])
        if sum(len(k) for k in kept) >= limit:
            break

    if not kept:
        return snippet(raw, limit)
    out = "\n\n".join(kept)
    return snippet(out, limit)


def display_body(kind: str, title: str, body: str, tags: list[str], *, max_len: int = 360) -> str:
    """Truncate bulky indexed dumps for human/tool-facing recall output."""
    text = (body or "").strip()
    if not text:
        return ""
    if title.startswith("Config:"):
        return snippet(text, min(max_len, 260))
    bulky = (
        kind in {"convention", "doc", "note"}
        and ("indexed" in tags or title.startswith(("Config:", "Doc:", "Module:", "File:")))
    )
    if bulky or len(text) > max_len:
        return snippet(text, max_len)
    return text
