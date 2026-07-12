"""Optional skill packs for common Python stacks."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyrecall.models import Memory, MemoryKind, Skill

if TYPE_CHECKING:
    from pyrecall.store import Store

PACK_SKILLS: dict[str, list[Skill]] = {
    "ruff": [
        Skill(
            name="ruff-format-lint",
            rule=(
                "Use ruff for lint and format. Prefer fixing via ruff check --fix "
                "and ruff format instead of hand-editing style-only noise."
            ),
            examples=["ruff check --fix .", "ruff format ."],
            tags=["python", "ruff", "lint"],
        ),
        Skill(
            name="ruff-pyproject-config",
            rule=(
                "Keep ruff settings in pyproject.toml under [tool.ruff] rather than "
                "scattered .flake8 / setup.cfg lint sections."
            ),
            examples=["[tool.ruff]\nline-length = 100"],
            tags=["python", "ruff", "packaging"],
        ),
    ],
    "fastapi": [
        Skill(
            name="fastapi-deps-over-globals",
            rule=(
                "Prefer FastAPI Depends() for shared resources (DB sessions, settings) "
                "instead of importing module-level globals inside route handlers."
            ),
            examples=["def get_db(): ...\n@app.get('/')\ndef home(db=Depends(get_db)): ..."],
            tags=["python", "fastapi", "api"],
        ),
        Skill(
            name="fastapi-pydantic-models",
            rule=(
                "Validate request/response bodies with Pydantic models. Do not parse "
                "JSON dicts by hand in route functions."
            ),
            examples=["class ItemIn(BaseModel):\n    name: str"],
            tags=["python", "fastapi", "pydantic"],
        ),
        Skill(
            name="fastapi-http-exceptions",
            rule=(
                "Raise HTTPException (or domain errors mapped in exception handlers) "
                "for API failures. Avoid returning ad-hoc error dicts with 200."
            ),
            examples=["raise HTTPException(status_code=404, detail='Not found')"],
            tags=["python", "fastapi", "errors"],
        ),
    ],
    "django": [
        Skill(
            name="django-orm-over-raw-sql",
            rule=(
                "Prefer the Django ORM and QuerySet API for routine queries. Use "
                "raw SQL only when the ORM cannot express the query cleanly."
            ),
            examples=["Book.objects.filter(author=user).select_related('publisher')"],
            tags=["python", "django", "orm"],
        ),
        Skill(
            name="django-migrations-first",
            rule=(
                "Change models via migrations (makemigrations / migrate). Never edit "
                "applied migration history by hand on shared branches."
            ),
            examples=["python manage.py makemigrations", "python manage.py migrate"],
            tags=["python", "django", "migrations"],
        ),
        Skill(
            name="django-settings-modules",
            rule=(
                "Keep environment-specific settings in dedicated modules or env vars. "
                "Do not hard-code secrets in settings.py."
            ),
            examples=["SECRET_KEY = os.environ['DJANGO_SECRET_KEY']"],
            tags=["python", "django", "settings"],
        ),
    ],
    "sqlalchemy": [
        Skill(
            name="sqlalchemy-session-scoped",
            rule=(
                "Use a scoped/request-bound Session (or sessionmaker context) and "
                "close/rollback on errors. Avoid long-lived global sessions."
            ),
            examples=[
                "with Session(engine) as session:\n"
                "    session.add(obj)\n"
                "    session.commit()"
            ],
            tags=["python", "sqlalchemy", "db"],
        ),
        Skill(
            name="sqlalchemy-2-style",
            rule=(
                "Prefer SQLAlchemy 2.0 style select()/execute() APIs over legacy "
                "Query.get() patterns in new code."
            ),
            examples=["session.execute(select(User).where(User.id == id)).scalar_one()"],
            tags=["python", "sqlalchemy"],
        ),
    ],
    "uv": [
        Skill(
            name="uv-over-pip-install",
            rule=(
                "Prefer uv for installing and locking dependencies in this project "
                "when uv is available (uv sync / uv run) instead of ad-hoc pip installs."
            ),
            examples=["uv sync", "uv run pytest"],
            tags=["python", "uv", "packaging"],
        ),
        Skill(
            name="uv-lockfile",
            rule="Commit the uv lockfile and install from it in CI for reproducible builds.",
            examples=["uv lock", "uv sync --frozen"],
            tags=["python", "uv", "packaging"],
        ),
    ],
    "poetry": [
        Skill(
            name="poetry-pyproject",
            rule=(
                "Manage dependencies with Poetry via pyproject.toml. Prefer "
                "`poetry add` / `poetry lock` over editing dependency lists by hand."
            ),
            examples=["poetry add httpx", "poetry install"],
            tags=["python", "poetry", "packaging"],
        ),
    ],
    "mypy": [
        Skill(
            name="mypy-public-api",
            rule=(
                "Keep public APIs mypy-clean. Prefer explicit Optional/| None and "
                "avoid bare Any on exported functions."
            ),
            examples=["def load(path: Path) -> dict[str, str]:"],
            tags=["python", "mypy", "typing"],
        ),
        Skill(
            name="pyright-compatible-hints",
            rule=(
                "Write type hints that satisfy both mypy and pyright: built-in generics "
                "on 3.10+, no type comments in new code."
            ),
            examples=["items: list[str] = []"],
            tags=["python", "mypy", "pyright", "typing"],
        ),
    ],
    "celery": [
        Skill(
            name="celery-task-idempotent",
            rule=(
                "Celery tasks should be idempotent where possible. Pass IDs/args, not "
                "ORM objects; retry with explicit backoff on transient failures."
            ),
            examples=[
                "@app.task(bind=True, max_retries=3)\n"
                "def send_mail(self, user_id: int): ..."
            ],
            tags=["python", "celery", "async"],
        ),
    ],
    "pytest-asyncio": [
        Skill(
            name="pytest-asyncio-mode",
            rule=(
                "For async tests use pytest-asyncio with asyncio_mode=auto (or mark "
                "async tests explicitly). Avoid mixing sync TestClient with async routes "
                "without an async client."
            ),
            examples=["@pytest.mark.asyncio\nasync def test_ok():\n    assert await ping()"],
            tags=["python", "pytest", "asyncio", "testing"],
        ),
    ],
}

PACK_MEMORIES: dict[str, list[Memory]] = {
    "ruff": [
        Memory(
            kind=MemoryKind.CONVENTION,
            title="Ruff as default linter",
            body="This project uses ruff for lint and format. Match existing [tool.ruff] settings.",
            tags=["python", "ruff", "pack"],
        )
    ],
    "fastapi": [
        Memory(
            kind=MemoryKind.CONVENTION,
            title="FastAPI service style",
            body=(
                "Routes stay thin: validate with Pydantic, inject deps, delegate to "
                "service functions. Keep HTTP concerns at the API boundary."
            ),
            tags=["python", "fastapi", "pack"],
        )
    ],
    "django": [
        Memory(
            kind=MemoryKind.CONVENTION,
            title="Django app layout",
            body=(
                "Business logic lives in models/services, not fat views. Prefer "
                "class-based or function views consistently with the existing apps."
            ),
            tags=["python", "django", "pack"],
        )
    ],
    "sqlalchemy": [
        Memory(
            kind=MemoryKind.CONVENTION,
            title="SQLAlchemy access pattern",
            body=(
                "All DB access goes through Session helpers. Commit explicitly; "
                "rollback on exceptions."
            ),
            tags=["python", "sqlalchemy", "pack"],
        )
    ],
    "uv": [
        Memory(
            kind=MemoryKind.CONVENTION,
            title="uv toolchain",
            body="Prefer uv sync/run for local and CI installs when this pack is enabled.",
            tags=["python", "uv", "pack"],
        )
    ],
    "poetry": [
        Memory(
            kind=MemoryKind.CONVENTION,
            title="Poetry dependency management",
            body="Dependencies and scripts live in pyproject.toml under Poetry conventions.",
            tags=["python", "poetry", "pack"],
        )
    ],
    "mypy": [
        Memory(
            kind=MemoryKind.CONVENTION,
            title="Static typing baseline",
            body="Public APIs should pass mypy/pyright; tighten types instead of silencing.",
            tags=["python", "mypy", "pack"],
        )
    ],
    "celery": [
        Memory(
            kind=MemoryKind.CONVENTION,
            title="Celery task style",
            body="Background work goes through Celery tasks with serializable arguments.",
            tags=["python", "celery", "pack"],
        )
    ],
    "pytest-asyncio": [
        Memory(
            kind=MemoryKind.CONVENTION,
            title="Async test style",
            body="Async tests use pytest-asyncio markers/mode consistent with the repo.",
            tags=["python", "pytest", "asyncio", "pack"],
        )
    ],
}


def list_packs() -> list[dict[str, str | int]]:
    return [
        {
            "name": name,
            "skills": len(PACK_SKILLS.get(name, [])),
            "memories": len(PACK_MEMORIES.get(name, [])),
        }
        for name in sorted(PACK_SKILLS)
    ]


def install_pack(store: Store, name: str) -> dict[str, int]:
    key = name.strip().lower()
    if key not in PACK_SKILLS:
        known = ", ".join(sorted(PACK_SKILLS))
        raise ValueError(f"Unknown pack '{name}'. Available: {known}")

    skills_added = 0
    memories_added = 0
    for skill in PACK_SKILLS[key]:
        if store.find_skill_by_name(skill.name) is None:
            store.upsert_skill(skill)
            skills_added += 1
    existing_titles = {m.title for m in store.list_memories()}
    for memory in PACK_MEMORIES.get(key, []):
        if memory.title not in existing_titles:
            store.upsert_memory(memory)
            memories_added += 1
    return {"skills": skills_added, "memories": memories_added}
