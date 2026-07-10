"""PyRecall command-line interface."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from pyrecall import __version__
from pyrecall.bridge import serve_stdio
from pyrecall.indexer import index_project
from pyrecall.learner import learn_correction, parse_correction_blob
from pyrecall.models import Memory, MemoryKind, ProjectConfig
from pyrecall.paths import ensure_store, find_project_root, load_config, save_config
from pyrecall.playbook import write_skills_markdown
from pyrecall.python_rules import seed_defaults
from pyrecall.retriever import format_context, search
from pyrecall.store import Store

app = typer.Typer(
    name="pyrecall",
    help="Local project memory and correction learning for Python workflows.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()


def _root(path: Path | None) -> Path:
    return find_project_root(path) if path else find_project_root()


@app.callback()
def main_callback() -> None:
    """PyRecall CLI."""


@app.command("version")
def version_cmd() -> None:
    """Print version."""
    console.print(__version__)


@app.command("init")
def init_cmd(
    path: Path | None = typer.Option(
        None, "--path", "-p", help="Project root (default: cwd)"
    ),
    name: str | None = typer.Option(None, "--name", "-n", help="Project name"),
    force: bool = typer.Option(False, "--force", help="Overwrite config if present"),
) -> None:
    """Initialize local memory store in the current project."""
    root = (path or Path.cwd()).resolve()
    store_path = ensure_store(root)
    config_file = store_path / "config.json"
    if config_file.exists() and not force:
        console.print(f"[yellow]Already initialized:[/yellow] {store_path}")
    else:
        config = ProjectConfig(name=name or root.name)
        save_config(config, root)
        console.print(f"[green]Initialized[/green] {store_path}")

    store = Store(root)
    seeded = seed_defaults(store)
    console.print(
        f"Seeded Python defaults — skills: {seeded['skills']}, "
        f"memories: {seeded['memories']}"
    )
    console.print("Next: [bold]pyrecall index[/bold] then [bold]pyrecall recall \"...\"[/bold]")


@app.command("index")
def index_cmd(
    path: Path | None = typer.Option(None, "--path", "-p"),
    keep: bool = typer.Option(
        False, "--keep", help="Keep previous indexed entries instead of replacing them"
    ),
) -> None:
    """Index project docs and Python signals into local memory."""
    root = _root(path)
    ensure_store(root)
    result = index_project(root, replace_indexed=not keep)
    console.print(
        f"[green]Indexed[/green] {result['memories']} memories "
        f"from {result['files']} files in {result['root']}"
    )


@app.command("remember")
def remember_cmd(
    title: str = typer.Argument(..., help="Short title"),
    body: str = typer.Argument(..., help="Durable note / decision / convention"),
    kind: str = typer.Option("note", "--kind", "-k", help="decision|convention|note|doc"),
    tag: list[str] = typer.Option(["python"], "--tag", "-t"),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Store a durable project memory."""
    root = _root(path)
    memory = Memory(kind=MemoryKind(kind), title=title, body=body, tags=list(tag))
    Store(root).upsert_memory(memory)
    console.print(f"[green]Saved[/green] {memory.id} — {memory.title}")


@app.command("learn")
def learn_cmd(
    rejected: str | None = typer.Option(None, "--rejected", "-r"),
    preferred: str | None = typer.Option(None, "--preferred", "-P"),
    blob: str | None = typer.Option(
        None,
        "--blob",
        "-b",
        help="Free-form: 'avoid => prefer' or 'avoid: x | prefer: y'",
    ),
    context: str = typer.Option("", "--context", "-c"),
    reason: str = typer.Option("", "--reason"),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Learn a reusable skill from a correction."""
    root = _root(path)
    rej = rejected or ""
    pref = preferred or ""
    why = reason
    if blob:
        parsed_r, parsed_p, parsed_reason = parse_correction_blob(blob)
        rej = rej or parsed_r
        pref = pref or parsed_p
        why = why or parsed_reason
    if not pref:
        raise typer.BadParameter("Provide --preferred or --blob")
    result = learn_correction(
        rej or "(unspecified)",
        pref,
        context=context,
        reason=why,
        root=root,
    )
    console.print(f"[green]Learned skill[/green] {result['skill_name']}")
    console.print(result["rule"])


@app.command("recall")
def recall_cmd(
    query: str = typer.Argument(..., help="What to look up"),
    limit: int = typer.Option(8, "--limit", "-n"),
    raw: bool = typer.Option(False, "--raw", help="Print JSON instead of context block"),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Recall relevant memories and skills."""
    root = _root(path)
    hits = search(query, limit=limit, root=root)
    if raw:
        console.print_json(json.dumps([h.model_dump() for h in hits], default=str))
        return
    if not hits:
        console.print("[yellow]No matches[/yellow]")
        return
    console.print(format_context(hits))


@app.command("skills")
def skills_cmd(
    path: Path | None = typer.Option(None, "--path", "-p"),
    all_skills: bool = typer.Option(False, "--all", help="Include inactive skills"),
) -> None:
    """List learned skills."""
    root = _root(path)
    skills = Store(root).list_skills(active_only=not all_skills)
    table = Table(title="Skills")
    table.add_column("Name")
    table.add_column("Hits", justify="right")
    table.add_column("Tags")
    table.add_column("Rule")
    for skill in skills:
        table.add_row(
            skill.name,
            str(skill.hit_count),
            ", ".join(skill.tags),
            skill.rule.replace("\n", " ")[:80],
        )
    console.print(table)


@app.command("stats")
def stats_cmd(path: Path | None = typer.Option(None, "--path", "-p")) -> None:
    """Show store statistics."""
    root = _root(path)
    stats = Store(root).stats()
    config = load_config(root)
    console.print_json(
        json.dumps({"project": config.name, **stats}, ensure_ascii=False, indent=2)
    )


@app.command("playbook")
def playbook_cmd(
    out: Path = typer.Option(Path("SKILLS.md"), "--out", "-o"),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Write active skills to a markdown playbook."""
    root = _root(path)
    target = write_skills_markdown(out, root)
    console.print(f"[green]Wrote[/green] {target}")


@app.command("export")
def export_cmd(
    out: Path = typer.Option(Path("pyrecall-export.json"), "--out", "-o"),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Export memories, corrections, and skills to JSON."""
    root = _root(path)
    store = Store(root)
    payload = {
        "version": __version__,
        "config": load_config(root).model_dump(),
        "memories": [m.model_dump(mode="json") for m in store.list_memories()],
        "corrections": [c.model_dump(mode="json") for c in store.list_corrections()],
        "skills": [s.model_dump(mode="json") for s in store.list_skills(active_only=False)],
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    console.print(f"[green]Exported[/green] {out}")


@app.command("import-data")
def import_cmd(
    source: Path = typer.Argument(..., exists=True, readable=True),
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Import a previously exported JSON dump."""
    root = _root(path)
    ensure_store(root)
    data = json.loads(source.read_text(encoding="utf-8"))
    store = Store(root)
    count = {"memories": 0, "corrections": 0, "skills": 0}
    for item in data.get("memories", []):
        store.upsert_memory(Memory.model_validate(item))
        count["memories"] += 1
    from pyrecall.models import Correction, Skill

    for item in data.get("corrections", []):
        store.add_correction(Correction.model_validate(item))
        count["corrections"] += 1
    for item in data.get("skills", []):
        store.upsert_skill(Skill.model_validate(item))
        count["skills"] += 1
    if "config" in data:
        save_config(ProjectConfig.model_validate(data["config"]), root)
    console.print(f"[green]Imported[/green] {count}")


@app.command("serve")
def serve_cmd(
    path: Path | None = typer.Option(None, "--path", "-p"),
) -> None:
    """Run the stdio tool bridge for compatible coding tools."""
    root = _root(path)
    ensure_store(root)
    serve_stdio(root)


if __name__ == "__main__":
    app()
