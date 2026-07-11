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
