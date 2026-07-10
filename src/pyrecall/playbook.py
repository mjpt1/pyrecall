"""Export skills as a human-readable playbook."""

from __future__ import annotations

from pathlib import Path

from pyrecall.paths import find_project_root
from pyrecall.store import Store


def skills_markdown(root: Path | None = None) -> str:
    project = find_project_root(root)
    skills = Store(project).list_skills(active_only=True)
    lines = ["# Project skills", ""]
    if not skills:
        lines.append("_No active skills yet. Use `pyrecall learn` to add some._")
        lines.append("")
        return "\n".join(lines)
    for skill in skills:
        lines.append(f"## {skill.name}")
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
