"""Environment diagnostics for installs and local store health."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from pyrecall import __version__
from pyrecall.paths import db_path, find_project_root, store_dir


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
    store = store_dir(project)
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
                'PowerShell (current window): '
                f'$env:Path += ";{target}"'
            )
        else:
            advice.append(
                "Command `pyrecall` is not on PATH. Use `python -m pyrecall ...` "
                f"or ensure {scripts_hint} is on PATH."
            )
    if not store.exists():
        advice.append("No .pyrecall/ yet — run `pyrecall init` in your project.")
    elif not database.exists():
        advice.append("Store folder exists but database is missing — run `pyrecall init`.")

    if not advice:
        advice.append("Looks good.")

    return {
        "version": __version__,
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "pyrecall_on_path": path_ok,
        "pyrecall_exe": exe,
        "project_root": str(project),
        "store_dir": str(store),
        "store_exists": store.exists(),
        "db_exists": database.exists(),
        "advice": advice,
    }
