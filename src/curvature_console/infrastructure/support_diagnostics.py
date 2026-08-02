"""Read-only operational diagnostics for Curvature Console Development Unit."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RepositoryDiagnostic:
    """One repository's current Git state."""

    repository_id: str
    root: Path
    available: bool
    branch: str
    head: str
    origin_head: str
    status: str
    error: str = ""

    @property
    def is_clean(self) -> bool:
        return self.available and not self.status.strip()

    @property
    def is_synced(self) -> bool:
        return (
            self.available
            and bool(self.head)
            and self.head == self.origin_head
        )


@dataclass(frozen=True, slots=True)
class SupportDiagnosticReport:
    """Read-only operational snapshot for the Console Development Unit UI."""

    created_at: datetime
    repositories: tuple[RepositoryDiagnostic, ...]
    latest_runtime_log: Path | None
    latest_snapshot: Path | None

    def as_text(self) -> str:
        """Render a stable plain-text report suitable for attachment."""

        lines = [
            "CURVATURE CONSOLE DEVELOPMENT UNIT — DIAGNOSTIC REPORT",
            f"Created: {self.created_at.isoformat(timespec='seconds')}",
            "",
        ]
        for repository in self.repositories:
            lines.extend(
                [
                    f"Repository: {repository.repository_id}",
                    f"Root: {repository.root}",
                    f"Available: {'YES' if repository.available else 'NO'}",
                    f"Branch: {repository.branch or '-'}",
                    f"HEAD: {repository.head or '-'}",
                    f"origin/main: {repository.origin_head or '-'}",
                    f"Clean: {'YES' if repository.is_clean else 'NO'}",
                    f"Synced: {'YES' if repository.is_synced else 'NO'}",
                    "Status:",
                    repository.status.rstrip() or "(clean)",
                ]
            )
            if repository.error:
                lines.extend(["Error:", repository.error])
            lines.append("")

        lines.extend(
            [
                "Latest runtime log:",
                str(self.latest_runtime_log or "(none)"),
                "",
                "Latest snapshot:",
                str(self.latest_snapshot or "(none)"),
                "",
            ]
        )
        return "\n".join(lines)


class SupportDiagnosticsCollector:
    """Collect bounded, read-only diagnostics from local repositories."""

    def __init__(
        self,
        *,
        repository_roots: dict[str, Path],
        data_directory: Path,
    ) -> None:
        self.repository_roots = {
            repository_id: root.expanduser().resolve()
            for repository_id, root in repository_roots.items()
        }
        self.data_directory = data_directory.expanduser().resolve()

    def collect(self) -> SupportDiagnosticReport:
        """Return current repository, log and snapshot information."""

        repositories = tuple(
            self._collect_repository(repository_id, root)
            for repository_id, root in self.repository_roots.items()
        )
        return SupportDiagnosticReport(
            created_at=datetime.now(),
            repositories=repositories,
            latest_runtime_log=self._latest_file(
                self.data_directory / "logs",
                "*.log",
            ),
            latest_snapshot=self._latest_file(
                self.data_directory / "snapshots",
                "*.zip",
            ),
        )

    def write_report(self, report: SupportDiagnosticReport) -> Path:
        """Persist one diagnostic report outside the source tree."""

        output_directory = self.data_directory / "console-development" / "reports"
        output_directory.mkdir(parents=True, exist_ok=True)
        output_path = output_directory / (
            "console-development-diagnostic-"
            f"{report.created_at.strftime('%Y%m%d-%H%M%S')}.txt"
        )
        output_path.write_text(report.as_text(), encoding="utf-8")
        return output_path

    def _collect_repository(
        self,
        repository_id: str,
        root: Path,
    ) -> RepositoryDiagnostic:
        if not root.is_dir():
            return RepositoryDiagnostic(
                repository_id=repository_id,
                root=root,
                available=False,
                branch="",
                head="",
                origin_head="",
                status="",
                error="Repository root does not exist.",
            )

        try:
            branch = self._git(root, "branch", "--show-current")
            head = self._git(root, "rev-parse", "--short", "HEAD")
            origin_head = self._git(
                root,
                "rev-parse",
                "--short",
                "origin/main",
            )
            status = self._git(root, "status", "--short")
        except RuntimeError as exc:
            return RepositoryDiagnostic(
                repository_id=repository_id,
                root=root,
                available=False,
                branch="",
                head="",
                origin_head="",
                status="",
                error=str(exc),
            )

        return RepositoryDiagnostic(
            repository_id=repository_id,
            root=root,
            available=True,
            branch=branch,
            head=head,
            origin_head=origin_head,
            status=status,
        )

    @staticmethod
    def _git(root: Path, *arguments: str) -> str:
        result = subprocess.run(
            ["git", *arguments],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            message = result.stderr.strip() or result.stdout.strip()
            raise RuntimeError(
                f"git {' '.join(arguments)} failed: {message}"
            )
        return result.stdout.strip()

    @staticmethod
    def _latest_file(directory: Path, pattern: str) -> Path | None:
        if not directory.is_dir():
            return None
        candidates = [path for path in directory.glob(pattern) if path.is_file()]
        if not candidates:
            return None
        return max(candidates, key=lambda path: path.stat().st_mtime)
