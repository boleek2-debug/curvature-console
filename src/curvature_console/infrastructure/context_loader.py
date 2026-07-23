"""Build previewable context packages for department workspaces."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from curvature_console.configuration.workspace_config import WorkspaceConfig
from curvature_console.infrastructure.repository_reader import (
    RepositoryReadError,
    RepositoryReader,
)


@dataclass(frozen=True, slots=True)
class ContextDocument:
    """One loaded context document."""

    label: str
    source_path: Path
    content: str


@dataclass(frozen=True, slots=True)
class ContextLoadResult:
    """Result of loading context for one workspace."""

    department_id: str
    documents: tuple[ContextDocument, ...]
    errors: tuple[str, ...]

    @property
    def loaded_count(self) -> int:
        return len(self.documents)

    def preview_text(self) -> str:
        """Return a readable combined context preview."""

        parts: list[str] = []

        for document in self.documents:
            parts.append(
                f"===== {document.label} =====\n"
                f"Source: {document.source_path}\n\n"
                f"{document.content.rstrip()}"
            )

        if self.errors:
            parts.append(
                "===== LOAD ERRORS =====\n"
                + "\n".join(f"- {error}" for error in self.errors)
            )

        return "\n\n".join(parts)


class WorkspaceContextLoader:
    """Load role and documents from one or more safe repository roots."""

    def load(self, config: WorkspaceConfig) -> ContextLoadResult:
        documents: list[ContextDocument] = []
        errors: list[str] = []

        role_path = config.role_file.expanduser()

        try:
            role_content = role_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"Cannot read role file {role_path}: {exc}")
        else:
            documents.append(
                ContextDocument(
                    label="ROLE",
                    source_path=role_path,
                    content=role_content,
                )
            )

        readers = {
            source.source_id: RepositoryReader(source.root_path)
            for source in config.sources
        }

        for document_config in config.document_sources:
            reader = readers[document_config.source_id]
            source_root = config.source_path(document_config.source_id)
            relative_path = document_config.relative_path

            try:
                content = reader.read_text(relative_path)
            except RepositoryReadError as exc:
                errors.append(
                    f"[{document_config.source_id}] {exc}"
                )
                continue

            documents.append(
                ContextDocument(
                    label=(
                        f"{document_config.source_id}:"
                        f"{relative_path}"
                    ),
                    source_path=source_root / relative_path,
                    content=content,
                )
            )

        return ContextLoadResult(
            department_id=config.department_id,
            documents=tuple(documents),
            errors=tuple(errors),
        )
