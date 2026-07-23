"""Load and validate workspace configuration files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class WorkspaceConfigError(ValueError):
    """Raised when a workspace configuration is missing or invalid."""


@dataclass(frozen=True, slots=True)
class WorkspaceSource:
    """One named repository root available to a workspace."""

    source_id: str
    root_path: Path


@dataclass(frozen=True, slots=True)
class WorkspaceDocument:
    """One document selected from a named workspace source."""

    source_id: str
    relative_path: Path


@dataclass(frozen=True, slots=True)
class WorkspaceConfig:
    """Configuration for one Curvature Console department."""

    department_id: str
    title: str
    role_file: Path

    # Legacy single-repository fields are retained for compatibility with
    # existing callers and tests. New workspace files should use `sources`.
    repository_path: Path
    documents: tuple[Path, ...]

    sources: tuple[WorkspaceSource, ...]
    document_sources: tuple[WorkspaceDocument, ...]

    def source_path(self, source_id: str) -> Path:
        """Return the configured root for one source identifier."""

        for source in self.sources:
            if source.source_id == source_id:
                return source.root_path
        raise KeyError(source_id)


def load_workspace_config(path: Path) -> WorkspaceConfig:
    """Load one YAML workspace configuration.

    Two formats are accepted:

    Legacy single-source format:

    ```yaml
    repository_path: ~/Curvature
    documents:
      - HANDOFF.md
    ```

    Multi-source format:

    ```yaml
    sources:
      curvature: ~/Curvature
      console: ~/curvature-console
    documents:
      - source: curvature
        path: HANDOFF.md
      - source: console
        path: CURVATURE_CONSOLE_HANDOFF.md
    ```
    """

    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise WorkspaceConfigError(
            f"Cannot read workspace config: {path}"
        ) from exc
    except yaml.YAMLError as exc:
        raise WorkspaceConfigError(
            f"Invalid YAML in workspace config: {path}"
        ) from exc

    if not isinstance(raw, dict):
        raise WorkspaceConfigError("Workspace config must contain a mapping.")

    department_id = _required_string(raw, "department_id")
    title = _required_string(raw, "title")
    role_file = Path(_required_string(raw, "role_file")).expanduser()

    raw_sources = raw.get("sources")
    if raw_sources is None:
        return _load_legacy_config(
            raw=raw,
            department_id=department_id,
            title=title,
            role_file=role_file,
        )

    sources = _parse_sources(raw_sources)
    document_sources = _parse_multi_source_documents(
        raw.get("documents"),
        source_ids={source.source_id for source in sources},
    )

    # The main Curvature repository remains the compatibility repository when
    # available. Otherwise use the first declared source.
    compatibility_source = next(
        (
            source
            for source in sources
            if source.source_id == "curvature"
        ),
        sources[0],
    )

    return WorkspaceConfig(
        department_id=department_id,
        title=title,
        role_file=role_file,
        repository_path=compatibility_source.root_path,
        documents=tuple(
            document.relative_path for document in document_sources
        ),
        sources=sources,
        document_sources=document_sources,
    )


def _load_legacy_config(
    raw: dict[str, Any],
    department_id: str,
    title: str,
    role_file: Path,
) -> WorkspaceConfig:
    repository_path = Path(
        _required_string(raw, "repository_path")
    ).expanduser()
    raw_documents = raw.get("documents")

    if not isinstance(raw_documents, list) or not all(
        isinstance(item, str) and item.strip()
        for item in raw_documents
    ):
        raise WorkspaceConfigError(
            "Workspace config field 'documents' must be a non-empty "
            "string list."
        )

    documents = tuple(Path(item.strip()) for item in raw_documents)
    source = WorkspaceSource(
        source_id="repository",
        root_path=repository_path,
    )

    return WorkspaceConfig(
        department_id=department_id,
        title=title,
        role_file=role_file,
        repository_path=repository_path,
        documents=documents,
        sources=(source,),
        document_sources=tuple(
            WorkspaceDocument(
                source_id=source.source_id,
                relative_path=document,
            )
            for document in documents
        ),
    )


def _parse_sources(raw_sources: Any) -> tuple[WorkspaceSource, ...]:
    if not isinstance(raw_sources, dict) or not raw_sources:
        raise WorkspaceConfigError(
            "Workspace config field 'sources' must be a non-empty mapping."
        )

    sources: list[WorkspaceSource] = []
    for source_id, raw_path in raw_sources.items():
        if not isinstance(source_id, str) or not source_id.strip():
            raise WorkspaceConfigError(
                "Workspace source identifiers must be non-empty strings."
            )
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise WorkspaceConfigError(
                f"Workspace source '{source_id}' must contain a path."
            )
        sources.append(
            WorkspaceSource(
                source_id=source_id.strip(),
                root_path=Path(raw_path.strip()).expanduser(),
            )
        )

    return tuple(sources)


def _parse_multi_source_documents(
    raw_documents: Any,
    source_ids: set[str],
) -> tuple[WorkspaceDocument, ...]:
    if not isinstance(raw_documents, list) or not raw_documents:
        raise WorkspaceConfigError(
            "Workspace config field 'documents' must be a non-empty list."
        )

    documents: list[WorkspaceDocument] = []
    for index, item in enumerate(raw_documents, start=1):
        if not isinstance(item, dict):
            raise WorkspaceConfigError(
                "Multi-source workspace documents must contain mappings "
                "with 'source' and 'path'."
            )

        source_id = item.get("source")
        raw_path = item.get("path")

        if not isinstance(source_id, str) or not source_id.strip():
            raise WorkspaceConfigError(
                f"Document {index} field 'source' must be a non-empty string."
            )
        source_id = source_id.strip()

        if source_id not in source_ids:
            raise WorkspaceConfigError(
                f"Document {index} references unknown source '{source_id}'."
            )

        if not isinstance(raw_path, str) or not raw_path.strip():
            raise WorkspaceConfigError(
                f"Document {index} field 'path' must be a non-empty string."
            )

        documents.append(
            WorkspaceDocument(
                source_id=source_id,
                relative_path=Path(raw_path.strip()),
            )
        )

    return tuple(documents)


def _required_string(raw: dict[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise WorkspaceConfigError(
            f"Workspace config field '{key}' must be a non-empty string."
        )
    return value.strip()
