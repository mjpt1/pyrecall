"""Project paths and configuration loading."""

from __future__ import annotations

import json
from pathlib import Path

from pyrecall.models import ProjectConfig

STORE_DIRNAME = ".pyrecall"
CONFIG_NAME = "config.json"
DB_NAME = "store.db"


def find_project_root(start: Path | None = None) -> Path:
    """Walk upward until a .pyrecall directory or config is found."""
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        store = candidate / STORE_DIRNAME
        if store.is_dir() or (store / CONFIG_NAME).exists():
            return candidate
    return current


def store_dir(root: Path | None = None) -> Path:
    return find_project_root(root) / STORE_DIRNAME


def config_path(root: Path | None = None) -> Path:
    return store_dir(root) / CONFIG_NAME


def db_path(root: Path | None = None) -> Path:
    return store_dir(root) / DB_NAME


def load_config(root: Path | None = None) -> ProjectConfig:
    path = config_path(root)
    if not path.exists():
        return ProjectConfig()
    data = json.loads(path.read_text(encoding="utf-8"))
    return ProjectConfig.model_validate(data)


def save_config(config: ProjectConfig, root: Path | None = None) -> Path:
    directory = store_dir(root)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / CONFIG_NAME
    path.write_text(config.model_dump_json(indent=2), encoding="utf-8")
    return path


def ensure_store(root: Path | None = None) -> Path:
    directory = store_dir(root)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "index").mkdir(exist_ok=True)
    return directory
