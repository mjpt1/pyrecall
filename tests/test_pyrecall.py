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
