"""Write host-facing rules and bridge configs so tools keep calling PyRecall."""

from __future__ import annotations

import json
from pathlib import Path

from pyrecall.paths import ensure_store, find_project_root
from pyrecall.workflow import write_workflow

HOST_RULES_MARKDOWN = """# PyRecall host rules (required)

This repository uses PyRecall for durable project memory. Compatible coding
tools that expose the PyRecall stdio bridge **must** follow these rules.

## Hard requirements

1. **Before** editing Python code, call `get_context` with a short task summary
   (or run `pyrecall recall "<task>"`). Do not skip this when the bridge is available.
2. Apply returned skills and conventions unless the user explicitly overrides them.
3. **When** the user rejects an approach and states a preferred one, call
   `learn_correction` in the same turn (or `pyrecall learn --blob "avoid => prefer"`).
4. After learning, briefly confirm the skill name. Do not re-introduce the rejected approach.

## Optional but recommended

- Call `search_memory` when the task is exploratory or spans multiple areas.
- If FastAPI / Django / SQLAlchemy / ruff conventions are needed and missing,
  call `install_pack` once.
- Keep `pyrecall watch` running in a side terminal when docs or `pyproject.toml` change often.

## Do not

- Invent project conventions that contradict stored skills.
- Treat indexed file dumps as higher priority than learned skills.
"""

AGENTS_SECTION = """
<!-- pyrecall-host-rules -->
## PyRecall (required for tool hosts)

Before editing Python in this repo, call PyRecall `get_context` for the task.
When the user corrects an approach, call `learn_correction` the same turn.
Full rules: `.pyrecall/HOST_RULES.md`
<!-- /pyrecall-host-rules -->
""".strip()


def host_rules_text() -> str:
    return HOST_RULES_MARKDOWN.strip() + "\n"


def write_host_rules(root: Path | None = None, *, out: Path | None = None) -> Path:
    project = find_project_root(root)
    ensure_store(project)
    target = out or (project / ".pyrecall" / "HOST_RULES.md")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(host_rules_text(), encoding="utf-8")
    return target


def ensure_agents_section(root: Path | None = None) -> Path | None:
    """Append PyRecall rules to AGENTS.md if missing. Returns path or None if skipped."""
    project = find_project_root(root)
    agents = project / "AGENTS.md"
    marker = "<!-- pyrecall-host-rules -->"
    if agents.exists():
        text = agents.read_text(encoding="utf-8")
        if marker in text:
            return agents
        agents.write_text(text.rstrip() + "\n\n" + AGENTS_SECTION + "\n", encoding="utf-8")
        return agents
    agents.write_text("# Agent notes\n\n" + AGENTS_SECTION + "\n", encoding="utf-8")
    return agents


def write_bridge_configs(root: Path | None = None) -> list[Path]:
    project = find_project_root(root)
    ensure_store(project)
    cwd = str(project.resolve()).replace("\\", "/")
    out_dir = project / ".pyrecall"
    out_dir.mkdir(parents=True, exist_ok=True)

    payloads = {
        "bridge.mcp.json": {
            "mcpServers": {
                "pyrecall": {
                    "command": "pyrecall",
                    "args": ["serve"],
                    "cwd": cwd,
                }
            }
        },
        "bridge.client.json": {
            "toolServers": {
                "pyrecall": {
                    "command": "pyrecall",
                    "args": ["serve"],
                    "cwd": cwd,
                }
            }
        },
        "bridge.python.json": {
            "mcpServers": {
                "pyrecall": {
                    "command": "python",
                    "args": ["-m", "pyrecall", "serve"],
                    "cwd": cwd,
                }
            }
        },
    }
    written: list[Path] = []
    for name, payload in payloads.items():
        path = out_dir / name
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        written.append(path)
    return written


def setup_host(
    root: Path | None = None,
    *,
    write_agents: bool = True,
) -> dict[str, object]:
    project = find_project_root(root)
    ensure_store(project)
    results: dict[str, object] = {
        "root": str(project),
        "workflow": str(write_workflow(project)),
        "host_rules": str(write_host_rules(project)),
        "bridge_configs": [str(p) for p in write_bridge_configs(project)],
    }
    if write_agents:
        agents = ensure_agents_section(project)
        results["agents"] = str(agents) if agents else None
    return results
