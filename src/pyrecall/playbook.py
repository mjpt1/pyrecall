"""Export skills as a human-readable playbook."""

from __future__ import annotations

from pathlib import Path

from pyrecall.paths import find_project_root
from pyrecall.store import Store

SECTION_ORDER = (
    "testing",
    "pytest",
    "fastapi",
    "django",
    "sqlalchemy",
    "ruff",
    "lint",
    "typing",
    "mypy",
    "pathlib",
    "packaging",
    "uv",
    "poetry",
    "celery",
    "asyncio",
    "api",
    "errors",
    "correction",
    "python",
)


def _section_for(tags: list[str]) -> str:
    lower = [t.lower() for t in tags]
    for key in SECTION_ORDER:
        if key in lower and key not in {"python", "correction"}:
            return key
    if "correction" in lower:
        return "corrections"
    return "general"


def skills_markdown(root: Path | None = None) -> str:
    project = find_project_root(root)
    skills = Store(project).list_skills(active_only=True)
    lines = ["# Project skills", ""]
    if not skills:
        lines.append("_No active skills yet. Use `pyrecall learn` to add some._")
        lines.append("")
        return "\n".join(lines)

    grouped: dict[str, list] = {}
    for skill in skills:
        section = _section_for(skill.tags)
        grouped.setdefault(section, []).append(skill)

    # Stable order: known sections first, then alpha
    ordered_keys = [k for k in SECTION_ORDER if k in grouped]
    ordered_keys += ["corrections"] if "corrections" in grouped else []
    ordered_keys += ["general"] if "general" in grouped else []
    for key in sorted(grouped):
        if key not in ordered_keys:
            ordered_keys.append(key)

    for section in ordered_keys:
        lines.append(f"## {section}")
        lines.append("")
        for skill in grouped[section]:
            lines.append(f"### {skill.name}")
            lines.append("")
            lines.append(skill.rule.strip())
            lines.append("")
            if skill.examples:
                lines.append("Examples:")
                lines.append("")
                for example in skill.examples:
                    lines.append(f"- `{example}`")
                lines.append("")
            if skill.tags:
                lines.append(f"Tags: {', '.join(skill.tags)}")
                lines.append("")
            lines.append(f"Hits: {skill.hit_count}")
            lines.append("")
    return "\n".join(lines)


def write_skills_markdown(out: Path, root: Path | None = None) -> Path:
    out.write_text(skills_markdown(root), encoding="utf-8")
    return out
