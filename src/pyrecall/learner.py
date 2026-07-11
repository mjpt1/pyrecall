"""Learn durable skills from user corrections."""

from __future__ import annotations

import re
from pathlib import Path

from pyrecall.models import Correction, Memory, MemoryKind, Skill
from pyrecall.paths import find_project_root
from pyrecall.store import Store
from pyrecall.textutil import snippet, tokenize

CORRECTION_CUES = re.compile(
    r"(?i)\b("
    r"no[, ]|"
    r"don't|"
    r"do not|"
    r"instead|"
    r"prefer|"
    r"use .+ not|"
    r"not .+ use|"
    r"wrong|"
    r"fix|"
    r"avoid|"
    r"نه|"
    r"نکن|"
    r"به جاش|"
    r"ترجیح"
    r")\b"
)

TOPIC_TAGS = (
    ("pytest", ("pytest", "unittest", "testcase", "fixture", "parametrize")),
    ("pathlib", ("pathlib", "os.path", "path(")),
    ("typing", ("type hint", "typing", "list[", "dict[", "optional[")),
    ("packaging", ("pyproject", "setup.cfg", "setup.py", "wheel")),
    ("errors", ("except", "exception", "raise ", "bare except")),
    ("testing", ("test_", "tests/", "assert ")),
)


def _skill_name_from_texts(rejected: str, preferred: str) -> str:
    tokens = tokenize(f"{rejected} {preferred}")[:8]
    if not tokens:
        return "custom-correction"
    # Prefer distinctive tokens over stop-ish leftovers
    name = "-".join(tokens[:5])
    return name[:64].strip("-") or "custom-correction"


def _infer_tags(rejected: str, preferred: str, reason: str, context: str) -> list[str]:
    blob = f"{rejected}\n{preferred}\n{reason}\n{context}".lower()
    tags = ["python", "correction"]
    for tag, needles in TOPIC_TAGS:
        if any(n in blob for n in needles):
            tags.append(tag)
    return list(dict.fromkeys(tags))


def distill_skill(
    rejected: str,
    preferred: str,
    *,
    context: str = "",
    reason: str = "",
    tags: list[str] | None = None,
) -> Skill:
    auto_tags = _infer_tags(rejected, preferred, reason, context)
    tags = list(dict.fromkeys([*(tags or []), *auto_tags]))
    name = _skill_name_from_texts(rejected, preferred)
    reason_bit = reason.strip() or "Follow the preferred approach below."
    rule = (
        f"{reason_bit}\n"
        f"Avoid: {snippet(rejected, 220)}\n"
        f"Prefer: {snippet(preferred, 220)}"
    )
    if context.strip():
        rule += f"\nContext: {snippet(context, 220)}"
    examples = [preferred.strip()] if preferred.strip() else []
    return Skill(name=name, rule=rule, examples=examples, tags=tags)


def learn_correction(
    rejected: str,
    preferred: str,
    *,
    context: str = "",
    reason: str = "",
    tags: list[str] | None = None,
    root: Path | None = None,
) -> dict:
    project = find_project_root(root)
    store = Store(project)

    skill = distill_skill(
        rejected,
        preferred,
        context=context,
        reason=reason,
        tags=tags,
    )
    existing = store.find_skill_by_name(skill.name)
    if existing is None:
        # Merge into a close existing correction skill when names drift slightly
        for candidate in store.list_skills(active_only=False):
            if "correction" not in candidate.tags:
                continue
            shared = set(tokenize(candidate.name)) & set(tokenize(skill.name))
            if len(shared) >= 2:
                existing = candidate
                break

    if existing:
        existing.rule = skill.rule
        existing.examples = list(dict.fromkeys([*existing.examples, *skill.examples]))
        existing.tags = list(dict.fromkeys([*existing.tags, *skill.tags]))
        existing.active = True
        skill = store.upsert_skill(existing)
    else:
        skill = store.upsert_skill(skill)

    correction = Correction(
        rejected=rejected,
        preferred=preferred,
        context=context,
        reason=reason,
        tags=skill.tags,
        skill_id=skill.id,
    )
    store.add_correction(correction)

    memory = Memory(
        kind=MemoryKind.CORRECTION,
        title=f"Correction: {skill.name}",
        body=skill.rule,
        tags=skill.tags,
        metadata={"skill_id": skill.id, "correction_id": correction.id},
    )
    store.upsert_memory(memory)

    return {
        "correction_id": correction.id,
        "skill_id": skill.id,
        "skill_name": skill.name,
        "rule": skill.rule,
        "tags": skill.tags,
    }


def looks_like_correction(text: str) -> bool:
    return bool(CORRECTION_CUES.search(text or ""))


def parse_correction_blob(text: str) -> tuple[str, str, str]:
    """
    Parse free-form correction text.

    Supported shapes:
      rejected => preferred
      avoid: ... | prefer: ...
      don't use X, use Y / use Y instead of X
      raw text (stored as preferred with empty rejected)
    """
    raw = (text or "").strip()
    if "=>" in raw:
        left, right = raw.split("=>", 1)
        return left.strip(), right.strip(), ""
    if "|" in raw and ("avoid" in raw.lower() or "prefer" in raw.lower()):
        parts = [p.strip() for p in raw.split("|")]
        rejected = ""
        preferred = ""
        for part in parts:
            low = part.lower()
            if low.startswith("avoid:"):
                rejected = part.split(":", 1)[1].strip()
            elif low.startswith("prefer:"):
                preferred = part.split(":", 1)[1].strip()
        return rejected, preferred, ""

    instead = re.search(
        r"(?i)(?:don't|do not|dont)\s+use\s+(.+?)[,;]?\s+(?:use|prefer)\s+(.+)$",
        raw,
    )
    if instead:
        return instead.group(1).strip(), instead.group(2).strip(), ""

    instead_of = re.search(r"(?i)use\s+(.+?)\s+instead\s+of\s+(.+)$", raw)
    if instead_of:
        return instead_of.group(2).strip(), instead_of.group(1).strip(), ""

    if looks_like_correction(raw):
        return "", raw, "Parsed from free-form correction cue"
    return "", raw, ""
