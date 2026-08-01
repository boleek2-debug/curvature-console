"""Tests for Curvature Support Unit diagnostics."""

from __future__ import annotations

import subprocess
from pathlib import Path

from curvature_console.infrastructure.support_diagnostics import (
    SupportDiagnosticsCollector,
)


def _git(repository: Path, *arguments: str) -> None:
    subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    )


def _repository(tmp_path: Path) -> Path:
    repository = tmp_path / "repository"
    repository.mkdir()
    _git(repository, "init", "-b", "main")
    _git(repository, "config", "user.name", "Curvature Test")
    _git(repository, "config", "user.email", "test@example.invalid")
    (repository / "tracked.txt").write_text("baseline", encoding="utf-8")
    _git(repository, "add", "tracked.txt")
    _git(repository, "commit", "-m", "baseline")
    _git(repository, "update-ref", "refs/remotes/origin/main", "HEAD")
    return repository


def test_collects_clean_synced_repository_and_latest_artifacts(
    tmp_path: Path,
) -> None:
    repository = _repository(tmp_path)
    data_directory = tmp_path / "data"
    log_directory = data_directory / "logs"
    snapshot_directory = data_directory / "snapshots"
    log_directory.mkdir(parents=True)
    snapshot_directory.mkdir(parents=True)
    older_log = log_directory / "console-older.log"
    latest_log = log_directory / "console-latest.log"
    older_log.write_text("old", encoding="utf-8")
    latest_log.write_text("new", encoding="utf-8")
    latest_log.touch()
    snapshot = snapshot_directory / "snapshot.zip"
    snapshot.write_bytes(b"zip")

    report = SupportDiagnosticsCollector(
        repository_roots={"curvature-console": repository},
        data_directory=data_directory,
    ).collect()

    diagnostic = report.repositories[0]
    assert diagnostic.available
    assert diagnostic.branch == "main"
    assert diagnostic.is_clean
    assert diagnostic.is_synced
    assert report.latest_runtime_log == latest_log
    assert report.latest_snapshot == snapshot
    assert "CURVATURE SUPPORT UNIT" in report.as_text()


def test_dirty_repository_is_reported(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    (repository / "tracked.txt").write_text("changed", encoding="utf-8")

    report = SupportDiagnosticsCollector(
        repository_roots={"curvature-console": repository},
        data_directory=tmp_path / "data",
    ).collect()

    diagnostic = report.repositories[0]
    assert not diagnostic.is_clean
    assert "tracked.txt" in diagnostic.status


def test_write_report_uses_runtime_data_directory(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    collector = SupportDiagnosticsCollector(
        repository_roots={"curvature-console": repository},
        data_directory=tmp_path / "data",
    )

    output_path = collector.write_report(collector.collect())

    assert output_path.parent == tmp_path / "data" / "support-reports"
    assert output_path.read_text(encoding="utf-8").startswith(
        "CURVATURE SUPPORT UNIT"
    )
