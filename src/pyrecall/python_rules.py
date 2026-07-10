"""Built-in Python workflow conventions seeded on init."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyrecall.models import Memory, MemoryKind, Skill

if TYPE_CHECKING:
    from pyrecall.store import Store

DEFAULT_SKILLS: list[Skill] = [
    Skill(
        name="prefer-pytest",
        rule=(
            "Prefer pytest over unittest. Use plain assert, fixtures, and "
            "parametrize instead of TestCase subclasses when adding tests."
        ),
        examples=[
            "def test_add(): assert add(1, 2) == 3",
            "@pytest.fixture\ndef client(): ...",
        ],
        tags=["python", "pytest", "testing"],
    ),
    Skill(
        name="type-hints-public-api",
        rule=(
            "Add type hints to public functions and methods. Prefer built-in "
            "generics (list[str], dict[str, int]) on Python 3.10+."
        ),
        examples=["def load(path: Path) -> dict[str, Any]:"],
        tags=["python", "typing"],
    ),
    Skill(
        name="pathlib-over-os-path",
        rule="Prefer pathlib.Path over os.path for filesystem paths in new code.",
        examples=["path = Path('data') / 'file.txt'"],
        tags=["python", "pathlib"],
    ),
    Skill(
        name="context-managers-for-io",
        rule=(
            "Open files and connections with context managers (with ...) "
            "so resources close reliably."
        ),
        examples=["with path.open(encoding='utf-8') as fh:"],
        tags=["python", "io"],
    ),
    Skill(
        name="no-bare-except",
        rule="Do not use bare except:. Catch specific exceptions or Exception with a reason.",
        examples=["except ValueError as exc:"],
        tags=["python", "errors"],
    ),
    Skill(
        name="pyproject-first",
        rule=(
            "Prefer pyproject.toml for project metadata and tool config "
            "(pytest, ruff, coverage) instead of scattering legacy ini files."
        ),
        examples=["[project]\nname = \"...\""],
        tags=["python", "packaging"],
    ),
]

DEFAULT_MEMORIES: list[Memory] = [
    Memory(
        kind=MemoryKind.CONVENTION,
        title="Python packaging baseline",
        body=(
            "Use src/ layout when shipping a library. Keep runtime dependencies "
            "in [project.dependencies] and test tools in optional-dependencies.dev."
        ),
        tags=["python", "packaging", "src-layout"],
    ),
    Memory(
        kind=MemoryKind.CONVENTION,
        title="Testing baseline",
        body=(
            "Put tests under tests/. Name files test_*.py. Keep unit tests free of "
            "network calls unless marked integration."
        ),
        tags=["python", "pytest"],
    ),
]


def seed_defaults(store: Store) -> dict[str, int]:
    skills_added = 0
    memories_added = 0
    for skill in DEFAULT_SKILLS:
        if store.find_skill_by_name(skill.name) is None:
            store.upsert_skill(skill)
            skills_added += 1
    existing_titles = {m.title for m in store.list_memories()}
    for memory in DEFAULT_MEMORIES:
        if memory.title not in existing_titles:
            store.upsert_memory(memory)
            memories_added += 1
    return {"skills": skills_added, "memories": memories_added}
