from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_ROOT = REPO_ROOT / "config"
DEFAULT_WORKSPACE_NAME = "local"


def _config_path(workspace_name: str) -> Path:
    return CONFIG_ROOT / f"pilot_workspace.{workspace_name}.json"


def load_pilot_workspace(workspace_name: str = DEFAULT_WORKSPACE_NAME) -> dict[str, Any]:
    config_path = _config_path(workspace_name)
    if not config_path.exists():
        raise FileNotFoundError(f"Pilot workspace config {workspace_name} was not found at {config_path}")
    with config_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    payload["config_path"] = str(config_path)
    return payload


def resolve_workspace_path(path_key: str, workspace_name: str = DEFAULT_WORKSPACE_NAME) -> Path:
    workspace = load_pilot_workspace(workspace_name)
    if path_key not in workspace:
        raise KeyError(f"Workspace config {workspace_name} does not define {path_key}")
    return REPO_ROOT / workspace[path_key]


def ensure_workspace_dirs(workspace_name: str = DEFAULT_WORKSPACE_NAME) -> dict[str, str]:
    workspace = load_pilot_workspace(workspace_name)
    created: dict[str, str] = {}
    for key, value in workspace.items():
        if not key.endswith("_root"):
            continue
        path = REPO_ROOT / value
        path.mkdir(parents=True, exist_ok=True)
        created[key] = str(path)
    return created
