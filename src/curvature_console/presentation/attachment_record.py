"""Attachment metadata used by department panels."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AttachmentRecord:
    """Describe one attachment queued in a department workspace."""

    path: Path
    temporary: bool = False

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def size_bytes(self) -> int:
        try:
            return self.path.stat().st_size
        except OSError:
            return 0

    @property
    def suffix(self) -> str:
        suffix = self.path.suffix.lower().lstrip(".")
        return suffix or "file"

    def display_text(self) -> str:
        return f"{self.name} · {self.suffix.upper()} · {format_size(self.size_bytes)}"


def format_size(size_bytes: int) -> str:
    """Return a compact human-readable file size."""

    units = ("B", "KB", "MB", "GB")
    size = float(max(0, size_bytes))

    for unit in units:
        if size < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024

    return f"{size_bytes} B"
