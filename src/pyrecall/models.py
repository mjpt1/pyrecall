"""Data models for PyRecall."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return uuid4().hex


class MemoryKind(str, Enum):
    DECISION = "decision"
    CONVENTION = "convention"
    CORRECTION = "correction"
    NOTE = "note"
    DOC = "doc"
    SKILL = "skill"


class Memory(BaseModel):
    id: str = Field(default_factory=new_id)
    kind: MemoryKind
    title: str
    body: str
    tags: list[str] = Field(default_factory=list)
    source_path: str | None = None
    language: str = "python"
    score_hint: float = 0.0
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Correction(BaseModel):
    id: str = Field(default_factory=new_id)
    rejected: str
    preferred: str
    context: str = ""
    reason: str = ""
    tags: list[str] = Field(default_factory=list)
    skill_id: str | None = None
    created_at: datetime = Field(default_factory=utcnow)


class Skill(BaseModel):
    id: str = Field(default_factory=new_id)
    name: str
    rule: str
    examples: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    hit_count: int = 0
    active: bool = True
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class SearchHit(BaseModel):
    id: str
    kind: str
    title: str
    body: str
    score: float
    tags: list[str] = Field(default_factory=list)
    source_path: str | None = None
    why: list[str] = Field(default_factory=list)


class ProjectConfig(BaseModel):
    name: str = "project"
    language: str = "python"
    include_globs: list[str] = Field(
        default_factory=lambda: [
            "**/*.py",
            "**/*.md",
            "**/*.rst",
            "**/pyproject.toml",
            "**/setup.cfg",
            "**/tox.ini",
            "**/.python-version",
            "**/CONTRIBUTING*",
            "**/AGENTS.md",
            "**/CONVENTIONS.md",
        ]
    )
    exclude_globs: list[str] = Field(
        default_factory=lambda: [
            "**/.git/**",
            "**/.venv/**",
            "**/venv/**",
            "**/__pycache__/**",
            "**/node_modules/**",
            "**/dist/**",
            "**/build/**",
            "**/.pyrecall/**",
            "**/.tox/**",
            "**/.mypy_cache/**",
            "**/.pytest_cache/**",
            "**/site-packages/**",
        ]
    )
    max_file_bytes: int = 512_000
    share_skills: bool = False
