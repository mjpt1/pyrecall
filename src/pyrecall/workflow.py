"""Sticky workflow helpers so coding tools keep calling PyRecall."""

from __future__ import annotations

from pathlib import Path

from pyrecall.paths import ensure_store, find_project_root

WORKFLOW_MARKDOWN = """# PyRecall workflow

Keep project memory in sync while editing this repository.

## Before you change Python code (required)

1. Call `get_context` (or run `pyrecall recall "<task>"`) with a short description of the task.
2. Follow returned skills and conventions unless the user overrides them.
3. See `.pyrecall/HOST_RULES.md` for the mandatory host checklist.

## When the user corrects you (required)

1. Call `learn_correction` (or run `pyrecall learn --blob "avoid => prefer"`).
2. Confirm the distilled skill name back to the user.

## When docs or project config change

1. Run `pyrecall harvest` after editing CONTRIBUTING / AGENTS / README conventions.
2. Run `pyrecall index`, or keep `pyrecall watch` running in a side terminal.

## One-time host setup

```bash
pyrecall setup-host
```

This writes host rules, bridge JSON under `.pyrecall/`, and an `AGENTS.md` section.

## Useful commands

```bash
pyrecall recall "how should tests be written"
pyrecall learn --blob "unittest.TestCase => pytest assert + fixtures"
pyrecall harvest
pyrecall packs install fastapi
pyrecall playbook
pyrecall serve
```

Bridge tools: `get_context`, `search_memory`, `learn_correction`, `add_memory`,
`list_skills`, `install_pack`.
"""


def workflow_text() -> str:
    return WORKFLOW_MARKDOWN.strip() + "\n"


def write_workflow(root: Path | None = None, *, out: Path | None = None) -> Path:
    project = find_project_root(root)
    ensure_store(project)
    target = out or (project / ".pyrecall" / "WORKFLOW.md")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(workflow_text(), encoding="utf-8")
    return target
