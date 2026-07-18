"""Load and validate workspace configuration files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class WorkspaceConfigError(ValueError):
    """Raised when a workspace configuration is missing or invalid."""


@dataclass(frozen=True, slots=True)
class WorkspaceConfig:
    """Configuration for one Curvature Console department."""

    department_id: str
    title: str
    role_file: Path
    repository_path: Path
    documents: tuple[Path, ...]


def load_workspace_config(path: Path) -> WorkspaceConfig:
    """Load one YAML workspace configuration."""

    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise WorkspaceConfigError(f"Cannot read workspace config: {path}") from exc
    except yaml.YAMLError as exc:
        raise WorkspaceConfigError(f"Invalid YAML in workspace config: {path}") from exc

    if not isinstance(raw, dict):
        raise WorkspaceConfigError("Workspace config must contain a mapping.")

    department_id = _required_string(raw, "department_id")
    title = _required_string(raw, "title")
    role_file = Path(_required_string(raw, "role_file")).expanduser()
    repository_path = Path(
        _required_string(raw, "repository_path")
    ).expanduser()

    raw_documents = raw.get("documents")
    if not isinstance(raw_documents, list) or not all(
        isinstance(item, str) and item.strip() for item in raw_documents
    ):
        raise WorkspaceConfigError(
            "Workspace config field 'documents' must be a non-empty string list."
        )

    documents = tuple(Path(item) for item in raw_documents)

    return WorkspaceConfig(
        department_id=department_id,
        title=title,
        role_file=role_file,
        repository_path=repository_path,
        documents=documents,
    )


def _required_string(raw: dict[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise WorkspaceConfigError(
            f"Workspace config field '{key}' must be a non-empty string."
        )
    return value.strip()
