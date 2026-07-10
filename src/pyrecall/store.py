"""SQLite persistence for memories, corrections, and skills."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from pyrecall.models import Correction, Memory, MemoryKind, Skill, utcnow
from pyrecall.paths import db_path, ensure_store


def _dt(value: datetime | str | None) -> str:
    if value is None:
        return utcnow().isoformat()
    if isinstance(value, datetime):
        return value.isoformat()
    return value


class Store:
    def __init__(self, root: Path | None = None) -> None:
        ensure_store(root)
        self.root = root
        self.path = db_path(root)
        self._init_schema()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    title TEXT NOT NULL,
                    body TEXT NOT NULL,
                    tags TEXT NOT NULL DEFAULT '[]',
                    source_path TEXT,
                    language TEXT NOT NULL DEFAULT 'python',
                    score_hint REAL NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT NOT NULL DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS corrections (
                    id TEXT PRIMARY KEY,
                    rejected TEXT NOT NULL,
                    preferred TEXT NOT NULL,
                    context TEXT NOT NULL DEFAULT '',
                    reason TEXT NOT NULL DEFAULT '',
                    tags TEXT NOT NULL DEFAULT '[]',
                    skill_id TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS skills (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    rule TEXT NOT NULL,
                    examples TEXT NOT NULL DEFAULT '[]',
                    tags TEXT NOT NULL DEFAULT '[]',
                    hit_count INTEGER NOT NULL DEFAULT 0,
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_memories_kind ON memories(kind);
                CREATE INDEX IF NOT EXISTS idx_skills_active ON skills(active);
                """
            )

    def upsert_memory(self, memory: Memory) -> Memory:
        memory.updated_at = utcnow()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO memories (
                    id, kind, title, body, tags, source_path, language,
                    score_hint, created_at, updated_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    kind=excluded.kind,
                    title=excluded.title,
                    body=excluded.body,
                    tags=excluded.tags,
                    source_path=excluded.source_path,
                    language=excluded.language,
                    score_hint=excluded.score_hint,
                    updated_at=excluded.updated_at,
                    metadata=excluded.metadata
                """,
                (
                    memory.id,
                    memory.kind.value,
                    memory.title,
                    memory.body,
                    json.dumps(memory.tags),
                    memory.source_path,
                    memory.language,
                    memory.score_hint,
                    _dt(memory.created_at),
                    _dt(memory.updated_at),
                    json.dumps(memory.metadata),
                ),
            )
        return memory

    def get_memory(self, memory_id: str) -> Memory | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM memories WHERE id = ?", (memory_id,)
            ).fetchone()
        return self._row_to_memory(row) if row else None

    def list_memories(self, kind: MemoryKind | None = None) -> list[Memory]:
        with self.connect() as conn:
            if kind:
                rows = conn.execute(
                    "SELECT * FROM memories WHERE kind = ? ORDER BY updated_at DESC",
                    (kind.value,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM memories ORDER BY updated_at DESC"
                ).fetchall()
        return [self._row_to_memory(r) for r in rows]

    def delete_memory(self, memory_id: str) -> bool:
        with self.connect() as conn:
            cur = conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            return cur.rowcount > 0

    def add_correction(self, correction: Correction) -> Correction:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO corrections (
                    id, rejected, preferred, context, reason, tags, skill_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    correction.id,
                    correction.rejected,
                    correction.preferred,
                    correction.context,
                    correction.reason,
                    json.dumps(correction.tags),
                    correction.skill_id,
                    _dt(correction.created_at),
                ),
            )
        return correction

    def list_corrections(self) -> list[Correction]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM corrections ORDER BY created_at DESC"
            ).fetchall()
        return [self._row_to_correction(r) for r in rows]

    def upsert_skill(self, skill: Skill) -> Skill:
        skill.updated_at = utcnow()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO skills (
                    id, name, rule, examples, tags, hit_count, active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    rule=excluded.rule,
                    examples=excluded.examples,
                    tags=excluded.tags,
                    hit_count=excluded.hit_count,
                    active=excluded.active,
                    updated_at=excluded.updated_at
                """,
                (
                    skill.id,
                    skill.name,
                    skill.rule,
                    json.dumps(skill.examples),
                    json.dumps(skill.tags),
                    skill.hit_count,
                    1 if skill.active else 0,
                    _dt(skill.created_at),
                    _dt(skill.updated_at),
                ),
            )
        return skill

    def get_skill(self, skill_id: str) -> Skill | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM skills WHERE id = ?", (skill_id,)
            ).fetchone()
        return self._row_to_skill(row) if row else None

    def list_skills(self, active_only: bool = True) -> list[Skill]:
        with self.connect() as conn:
            if active_only:
                rows = conn.execute(
                    "SELECT * FROM skills WHERE active = 1 ORDER BY hit_count DESC, updated_at DESC"
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM skills ORDER BY updated_at DESC"
                ).fetchall()
        return [self._row_to_skill(r) for r in rows]

    def bump_skill(self, skill_id: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE skills SET hit_count = hit_count + 1, updated_at = ? WHERE id = ?",
                (_dt(utcnow()), skill_id),
            )

    def find_skill_by_name(self, name: str) -> Skill | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM skills WHERE lower(name) = lower(?) LIMIT 1",
                (name,),
            ).fetchone()
        return self._row_to_skill(row) if row else None

    def stats(self) -> dict[str, Any]:
        with self.connect() as conn:
            memories = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
            corrections = conn.execute("SELECT COUNT(*) FROM corrections").fetchone()[0]
            skills = conn.execute(
                "SELECT COUNT(*) FROM skills WHERE active = 1"
            ).fetchone()[0]
        return {
            "memories": memories,
            "corrections": corrections,
            "skills": skills,
            "db": str(self.path),
        }

    @staticmethod
    def _row_to_memory(row: sqlite3.Row) -> Memory:
        return Memory(
            id=row["id"],
            kind=MemoryKind(row["kind"]),
            title=row["title"],
            body=row["body"],
            tags=json.loads(row["tags"] or "[]"),
            source_path=row["source_path"],
            language=row["language"],
            score_hint=row["score_hint"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            metadata=json.loads(row["metadata"] or "{}"),
        )

    @staticmethod
    def _row_to_correction(row: sqlite3.Row) -> Correction:
        return Correction(
            id=row["id"],
            rejected=row["rejected"],
            preferred=row["preferred"],
            context=row["context"] or "",
            reason=row["reason"] or "",
            tags=json.loads(row["tags"] or "[]"),
            skill_id=row["skill_id"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    @staticmethod
    def _row_to_skill(row: sqlite3.Row) -> Skill:
        return Skill(
            id=row["id"],
            name=row["name"],
            rule=row["rule"],
            examples=json.loads(row["examples"] or "[]"),
            tags=json.loads(row["tags"] or "[]"),
            hit_count=row["hit_count"],
            active=bool(row["active"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
