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


def _skill_name_from_texts(rejected: str, preferred: str) -> str:
    tokens = tokenize(f"{rejected} {preferred}")[:6]
    if not tokens:
        return "custom-correction"
    return "-".join(tokens[:4])


def distill_skill(
    rejected: str,
    preferred: str,
    *,
    context: str = "",
    reason: str = "",
    tags: list[str] | None = None,
) -> Skill:
    tags = tags or ["python", "correction"]
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
    tags = tags or ["python", "correction"]

    skill = distill_skill(
        rejected,
        preferred,
        context=context,
        reason=reason,
        tags=tags,
    )
    existing = store.find_skill_by_name(skill.name)
    if existing:
        existing.rule = skill.rule
        existing.examples = list(dict.fromkeys([*existing.examples, *skill.examples]))
        existing.tags = list(dict.fromkeys([*existing.tags, *tags]))
        existing.active = True
        skill = store.upsert_skill(existing)
    else:
        skill = store.upsert_skill(skill)

    correction = Correction(
        rejected=rejected,
        preferred=preferred,
        context=context,
        reason=reason,
        tags=tags,
        skill_id=skill.id,
    )
    store.add_correction(correction)

    memory = Memory(
        kind=MemoryKind.CORRECTION,
        title=f"Correction: {skill.name}",
        body=skill.rule,
        tags=tags,
        metadata={"skill_id": skill.id, "correction_id": correction.id},
    )
    store.upsert_memory(memory)

    return {
        "correction_id": correction.id,
        "skill_id": skill.id,
        "skill_name": skill.name,
        "rule": skill.rule,
    }


def looks_like_correction(text: str) -> bool:
    return bool(CORRECTION_CUES.search(text or ""))


def parse_correction_blob(text: str) -> tuple[str, str, str]:
    """
    Parse free-form correction text.

    Supported shapes:
      rejected => preferred
      avoid: ... | prefer: ...
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
    if looks_like_correction(raw):
        return "", raw, "Parsed from free-form correction cue"
    return "", raw, ""
