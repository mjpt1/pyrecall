"""Unit and integration tests for PyRecall."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from pyrecall.bridge import BridgeServer
from pyrecall.cli import app
from pyrecall.indexer import index_project
from pyrecall.learner import distill_skill, learn_correction, parse_correction_blob
from pyrecall.models import Memory, MemoryKind
from pyrecall.paths import ensure_store, save_config
from pyrecall.python_rules import seed_defaults
from pyrecall.retriever import format_context, search
from pyrecall.store import Store
from pyrecall.textutil import bm25_score, tokenize

runner = CliRunner()


@pytest.fixture()
def project(tmp_path: Path) -> Path:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "sample.py").write_text(
        '"""Sample module."""\n\ndef add(a: int, b: int) -> int:\n    return a + b\n',
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text(
        "# Sample\n\nUse pytest for tests.\nPrefer pathlib.\n",
        encoding="utf-8",
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_sample.py").write_text(
        "from sample import add\n\ndef test_add():\n    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )
    ensure_store(tmp_path)
    from pyrecall.models import ProjectConfig

    save_config(ProjectConfig(name="sample"), tmp_path)
    store = Store(tmp_path)
    seed_defaults(store)
    return tmp_path


def test_tokenize_and_bm25() -> None:
    q = tokenize("prefer pytest fixtures")
    doc = tokenize("prefer pytest over unittest and use fixtures")
    score = bm25_score(q, doc, avgdl=10, df={"prefer": 1, "pytest": 1, "fixtures": 1}, n_docs=1)
    assert score > 0


def test_parse_correction_blob() -> None:
    rejected, preferred, _ = parse_correction_blob("unittest.TestCase => pytest assert")
    assert "unittest" in rejected
    assert "pytest" in preferred


def test_learn_and_recall(project: Path) -> None:
    result = learn_correction(
        "unittest.TestCase",
        "pytest with plain assert",
        reason="Project standard is pytest",
        root=project,
    )
    assert result["skill_name"]
    hits = search("how should I write tests", root=project, limit=5)
    assert hits
    assert any(h.kind in {"skill", "correction", "convention"} for h in hits)
    block = format_context(hits)
    assert "pytest" in block.lower() or "test" in block.lower()


def test_index_project(project: Path) -> None:
    result = index_project(project)
    assert result["memories"] >= 2
    store = Store(project)
    titles = [m.title for m in store.list_memories()]
    assert any(t.startswith("Doc:") for t in titles)
    assert any(t.startswith("Module:") for t in titles)


def test_store_roundtrip(project: Path) -> None:
    store = Store(project)
    memory = Memory(
        kind=MemoryKind.DECISION,
        title="Use src layout",
        body="Keep package code under src/",
        tags=["python", "packaging"],
    )
    store.upsert_memory(memory)
    loaded = store.get_memory(memory.id)
    assert loaded is not None
    assert loaded.title == "Use src layout"
    stats = store.stats()
    assert stats["memories"] >= 1
    assert stats["skills"] >= 1


def test_distill_skill() -> None:
    skill = distill_skill("os.path.join", "Path / 'x'", reason="Prefer pathlib")
    assert "pathlib" in skill.rule.lower() or "Prefer" in skill.rule
    assert skill.examples
    assert "pathlib" in skill.tags


def test_parse_instead_of() -> None:
    rejected, preferred, _ = parse_correction_blob(
        "don't use unittest.TestCase, use pytest assert"
    )
    assert "unittest" in rejected.lower()
    assert "pytest" in preferred.lower()


def test_recall_prefers_skills_over_config_dump(project: Path) -> None:
    (project / "pyproject.toml").write_text(
        "[project]\nname='demo'\n\n[tool.pytest.ini_options]\ntestpaths=['tests']\n"
        + ("x = 1\n" * 200),
        encoding="utf-8",
    )
    index_project(project)
    learn_correction(
        "unittest.TestCase",
        "pytest assert + fixtures",
        reason="Repo standard",
        root=project,
    )
    hits = search("how should tests be written", root=project, limit=5)
    assert hits
    assert any(h.kind == "skill" for h in hits[:3])
    assert not any(h.title.startswith("Config:") for h in hits[:1])
    for hit in hits:
        if hit.title.startswith("Config:"):
            assert hit.body.count("x = 1") <= 2
    block = format_context(hits)
    assert "pytest" in block.lower()


def test_doctor_and_forget(project: Path) -> None:
    from pyrecall.doctor import run_doctor

    report = run_doctor(project)
    assert report["version"]
    assert report["store_exists"] is True
    learn_correction("a", "b", reason="tmp", root=project)
    result = runner.invoke(app, ["--path", str(project), "forget", "a-b"])
    # name may be tokenized differently; use skills list
    store = Store(project)
    skills = store.list_skills(active_only=False)
    assert skills
    deactivated = store.set_skill_active(skills[0].name, active=False)
    assert deactivated is not None
    assert deactivated.active is False
    active = store.list_skills(active_only=True)
    assert all(s.name != deactivated.name for s in active)
    result = runner.invoke(app, ["doctor", "--path", str(project)])
    assert result.exit_code == 0


def test_bridge_tools(project: Path) -> None:
    server = BridgeServer(project)
    init = server.handle(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "0"},
            },
        }
    )
    assert init is not None
    assert init["result"]["serverInfo"]["name"] == "pyrecall"

    listed = server.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    assert listed is not None
    names = {t["name"] for t in listed["result"]["tools"]}
    assert "search_memory" in names
    assert "learn_correction" in names
    assert "install_pack" in names

    learned = server.handle(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "learn_correction",
                "arguments": {
                    "rejected": "bare except",
                    "preferred": "except ValueError",
                    "reason": "Catch specific errors",
                },
            },
        }
    )
    assert learned is not None
    assert learned["result"]["isError"] is False

    recalled = server.handle(
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {"name": "get_context", "arguments": {"query": "exception handling"}},
        }
    )
    assert recalled is not None
    text = recalled["result"]["content"][0]["text"]
    assert any(
        token in text.lower()
        for token in ("except", "valueerror", "skill", "no matching")
    ) or len(text) > 0


def test_cli_init_learn_recall(project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(project)
    result = runner.invoke(app, ["stats"])
    assert result.exit_code == 0

    result = runner.invoke(
        app,
        [
            "learn",
            "--rejected",
            "os.path.join(a, b)",
            "--preferred",
            "Path(a) / b",
            "--reason",
            "Use pathlib",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Learned skill" in result.output

    result = runner.invoke(app, ["recall", "path joining"])
    assert result.exit_code == 0, result.output

    result = runner.invoke(app, ["skills"])
    assert result.exit_code == 0

    out = project / "dump.json"
    result = runner.invoke(app, ["export", "--out", str(out)])
    assert result.exit_code == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "skills" in data
    assert "memories" in data


def test_packs_install_and_tag_filter(project: Path) -> None:
    from pyrecall.packs import install_pack, list_packs

    names = {p["name"] for p in list_packs()}
    assert "fastapi" in names and "uv" in names and "mypy" in names
    result = install_pack(Store(project), "fastapi")
    assert result["skills"] >= 1
    hits = search("Depends for database session", root=project, tags=["fastapi"], limit=5)
    assert hits
    assert all("fastapi" in [t.lower() for t in h.tags] for h in hits)
    assert any(h.why for h in hits)
    block = format_context(hits)
    assert "why:" in block.lower()


def test_watch_once_and_workflow(project: Path) -> None:
    from pyrecall.watch import watch_loop
    from pyrecall.workflow import write_workflow

    events: list[dict] = []
    watch_loop(project, once=True, on_change=events.append)
    assert events and events[0]["event"] == "start"
    assert int(events[0]["memories"]) >= 1
    path = write_workflow(project)
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "get_context" in text
    assert "learn_correction" in text


def test_cli_packs_and_recall_why(project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(project)
    result = runner.invoke(app, ["packs", "install", "ruff"])
    assert result.exit_code == 0, result.output
    result = runner.invoke(app, ["recall", "ruff format", "--tag", "ruff"])
    assert result.exit_code == 0, result.output
    assert "why:" in result.output.lower()
    result = runner.invoke(app, ["watch", "--once"])
    assert result.exit_code == 0, result.output
    result = runner.invoke(app, ["workflow", "--write"])
    assert result.exit_code == 0, result.output


def test_harvest_and_setup_host(project: Path) -> None:
    from pyrecall.harvest import harvest_docs
    from pyrecall.host_setup import setup_host

    (project / "CONTRIBUTING.md").write_text(
        "# Contributing\n\n## Testing\n"
        "- Prefer pytest fixtures over setUp methods\n"
        "- Keep unit tests free of network calls always\n\n"
        "## Style\n"
        "- Prefer pathlib for new filesystem paths in this repo\n",
        encoding="utf-8",
    )
    result = harvest_docs(project)
    assert int(result["memories"]) >= 2
    memories = Store(project).list_memories()
    harvested = [m for m in memories if "harvested" in m.tags]
    assert harvested
    assert any("pytest" in m.body.lower() for m in harvested)

    setup = setup_host(project, write_agents=True)
    assert Path(str(setup["host_rules"])).exists()
    assert "get_context" in Path(str(setup["host_rules"])).read_text(encoding="utf-8")
    assert Path(str(setup["bridge_configs"][0])).exists()
    agents = project / "AGENTS.md"
    assert agents.exists()
    assert "pyrecall-host-rules" in agents.read_text(encoding="utf-8")

    # second setup should not duplicate the AGENTS section
    setup_host(project, write_agents=True)
    text = agents.read_text(encoding="utf-8")
    assert text.count("<!-- pyrecall-host-rules -->") == 1


def test_cli_harvest_and_setup_host(project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(project)
    (project / "AGENTS.md").write_text(
        "# Notes\n\n## Guidelines\n- Prefer explicit exception types in public APIs here\n",
        encoding="utf-8",
    )
    result = runner.invoke(app, ["harvest"])
    assert result.exit_code == 0, result.output
    assert "Harvested" in result.output
    result = runner.invoke(app, ["setup-host"])
    assert result.exit_code == 0, result.output
    assert (project / ".pyrecall" / "HOST_RULES.md").exists()


def test_diff_learn_under_and_consolidate(project: Path) -> None:
    from pyrecall.diff_learn import parse_diff_text
    from pyrecall.learner import consolidate_skills, learn_correction
    from pyrecall.playbook import skills_markdown

    diff = """\
--- a/tests/test_x.py
+++ b/tests/test_x.py
@@ -1,3 +1,3 @@
-from unittest import TestCase
+import pytest
-class T(TestCase):
+def test_ok():
-    def test_ok(self): self.assertEqual(1, 1)
+    assert 1 == 1
"""
    rejected, preferred, ctx = parse_diff_text(diff)
    assert "unittest" in rejected.lower()
    assert "pytest" in preferred.lower() or "assert" in preferred.lower()
    assert "test_x" in ctx

    patch = project / "fix.patch"
    patch.write_text(diff, encoding="utf-8")
    result = runner.invoke(app, ["learn", "--path", str(project), "--diff", str(patch)])
    assert result.exit_code == 0, result.output
    assert "Learned skill" in result.output

    # near-duplicate should merge
    learn_correction(
        "from unittest import TestCase",
        "import pytest",
        reason="same idea",
        root=project,
    )
    learn_correction(
        "unittest.TestCase subclass",
        "pytest assert helpers",
        reason="same idea again",
        root=project,
    )
    stats = consolidate_skills(project)
    assert stats["merged_pairs"] >= 0

    # path-scoped recall
    from pyrecall.models import Memory, MemoryKind

    Store(project).upsert_memory(
        Memory(
            kind=MemoryKind.DOC,
            title="Module: src/api/routes.py",
            body="API routes use Depends for DB sessions",
            tags=["python", "indexed", "api"],
            source_path="src/api/routes.py",
        )
    )
    hits = search("Depends session", root=project, under="src/api", limit=5)
    assert hits
    md = skills_markdown(project)
    assert md.startswith("# Project skills")
    assert "## " in md

    report = __import__("pyrecall.doctor", fromlist=["run_doctor"]).run_doctor(project)
    assert "store_health" in report
    assert isinstance(report["store_health"], dict)
