"""Read text documents from a configured repository."""

from __future__ import annotations

from pathlib import Path


class RepositoryReadError(RuntimeError):
    """Raised when a configured repository document cannot be read safely."""


class RepositoryReader:
    """Provide read-only access to text files inside a repository root."""

    def __init__(self, repository_path: Path) -> None:
        self.repository_path = repository_path.expanduser().resolve()

    def read_text(self, relative_path: Path) -> str:
        """Read one UTF-8 text file contained inside the repository."""

        target = (self.repository_path / relative_path).resolve()

        try:
            target.relative_to(self.repository_path)
        except ValueError as exc:
            raise RepositoryReadError(
                f"Document escapes repository root: {relative_path}"
            ) from exc

        if not target.is_file():
            raise RepositoryReadError(f"Document not found: {relative_path}")

        try:
            return target.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise RepositoryReadError(
                f"Cannot read document: {relative_path}"
            ) from exc
