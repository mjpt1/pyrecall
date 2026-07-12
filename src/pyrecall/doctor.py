"""Environment diagnostics for installs and local store health."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from pyrecall import __version__
from pyrecall.paths import db_path, find_project_root, store_dir
from pyrecall.store import Store


def run_doctor(root: Path | None = None) -> dict:
    project = find_project_root(root)
    scripts_hint = Path(sys.prefix) / "Scripts" if os.name == "nt" else Path(sys.prefix) / "bin"
    ver = f"Python{sys.version_info.major}{sys.version_info.minor}"
    user_scripts = (
        Path(os.environ.get("APPDATA", "")) / "Python" / ver / "Scripts"
        if os.name == "nt"
        else None
    )

    exe = shutil.which("pyrecall")
    path_ok = exe is not None
    store_path = store_dir(project)
    database = db_path(project)

    advice: list[str] = []
    if not path_ok:
        if os.name == "nt":
            target = user_scripts or scripts_hint
            advice.append(
                f"Command `pyrecall` is not on PATH. Use `python -m pyrecall ...` "
                f"or add this folder to User PATH: {target}"
            )
            advice.append(
                "PowerShell (current window): "
                f'$env:Path += ";{target}"'
            )
        else:
            advice.append(
                "Command `pyrecall` is not on PATH. Use `python -m pyrecall ...` "
                f"or ensure {scripts_hint} is on PATH."
            )
    if not store_path.exists():
        advice.append("No .pyrecall/ yet — run `pyrecall init` in your project.")
    elif not database.exists():
        advice.append("Store folder exists but database is missing — run `pyrecall init`.")

    store_health: dict[str, object] = {}
    if database.exists():
        store = Store(project)
        skills = store.list_skills(active_only=False)
        active = [s for s in skills if s.active]
        inactive = [s for s in skills if not s.active]
        unused = [s for s in active if s.hit_count == 0 and "correction" in s.tags]
        corrections = store.list_corrections()
        orphan_corrections = [
            c for c in corrections if c.skill_id and not any(s.id == c.skill_id for s in skills)
        ]
        memories = store.list_memories()
        harvested = [m for m in memories if "harvested" in m.tags]
        indexed = [m for m in memories if "indexed" in m.tags]

        store_health = {
            "skills_active": len(active),
            "skills_inactive": len(inactive),
            "skills_unused_corrections": len(unused),
            "corrections": len(corrections),
            "orphan_corrections": len(orphan_corrections),
            "memories": len(memories),
            "harvested": len(harvested),
            "indexed": len(indexed),
        }
        if unused:
            names = ", ".join(s.name for s in unused[:5])
            advice.append(
                f"{len(unused)} learned correction skill(s) never recalled "
                f"(e.g. {names}). Consider `pyrecall forget <name>` if stale."
            )
        if orphan_corrections:
            advice.append(
                f"{len(orphan_corrections)} correction(s) point at missing skills — "
                "re-run `pyrecall learn` for those pairs if needed."
            )
        if not harvested and (project / "README.md").exists():
            advice.append("Docs not harvested yet — run `pyrecall harvest`.")
        if indexed == [] and (project / "src").exists():
            advice.append("No indexed memories — run `pyrecall index` or `pyrecall watch`.")
        if len(active) >= 8:
            advice.append(
                "Many active skills — run `pyrecall consolidate` to merge near-duplicates."
            )

    if not advice:
        advice.append("Looks good.")

    return {
        "version": __version__,
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "pyrecall_on_path": path_ok,
        "pyrecall_exe": exe,
        "project_root": str(project),
        "store_dir": str(store_path),
        "store_exists": store_path.exists(),
        "db_exists": database.exists(),
        "store_health": store_health,
        "advice": advice,
    }
