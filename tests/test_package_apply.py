"""Tests for explicit rollback-capable package application."""

from __future__ import annotations

import json
import subprocess
import zipfile
from pathlib import Path

import pytest

from curvature_console.infrastructure.package_apply import (
    PackageApplyError,
    PackageApplier,
)
from curvature_console.infrastructure.package_review import (
    PackageReviewer,
)


def _write_package(
    package_path: Path,
    *,
    files: list[dict[str, str]],
    payloads: dict[str, bytes],
) -> None:
    manifest = {
        "schema_version": 1,
        "package_type": "apply-test",
        "target_repository": "curvature-console",
        "files": files,
    }
    with zipfile.ZipFile(
        package_path,
        "w",
        zipfile.ZIP_DEFLATED,
    ) as archive:
        archive.writestr(
            "CURVATURE_PACKAGE.json",
            json.dumps(manifest),
        )
        for name, content in payloads.items():
            archive.writestr(name, content)


def _review(package: Path, repository: Path):
    return PackageReviewer().review(
        package,
        repository_id="curvature-console",
        repository_root=repository,
    )


def test_apply_creates_replaces_skips_and_backs_up(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "replace.txt").write_bytes(b"old")
    (repository / "same.txt").write_bytes(b"same")

    subprocess.run(
        ["git", "init"],
        cwd=repository,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "add", "."],
        cwd=repository,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Curvature Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-m",
            "baseline",
        ],
        cwd=repository,
        check=True,
        capture_output=True,
    )

    package = tmp_path / "package.zip"
    _write_package(
        package,
        files=[
            {"path": "new/create.txt", "action": "add"},
            {"path": "replace.txt", "action": "replace"},
            {"path": "same.txt", "action": "replace"},
        ],
        payloads={
            "new/create.txt": b"created",
            "replace.txt": b"replacement",
            "same.txt": b"same",
        },
    )

    reviewer = PackageReviewer()
    review = reviewer.review(
        package,
        repository_id="curvature-console",
        repository_root=repository,
    )
    result = PackageApplier(
        reviewer=reviewer,
        backup_root=tmp_path / "backups",
    ).apply(review)

    assert (repository / "new/create.txt").read_bytes() == b"created"
    assert (repository / "replace.txt").read_bytes() == b"replacement"
    assert (repository / "same.txt").read_bytes() == b"same"
    assert result.changed_count == 2
    assert result.skipped_paths == ("same.txt",)

    replace_result = next(
        item
        for item in result.applied_files
        if item.relative_path == "replace.txt"
    )
    assert replace_result.backup_path is not None
    assert replace_result.backup_path.read_bytes() == b"old"
    assert (result.backup_directory / "APPLY_RESULT.json").is_file()
    assert "new/create.txt" in result.git_status
    assert "replace.txt" in result.git_diff


def test_apply_rejects_conflicted_review_without_writes(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "existing.txt").write_bytes(b"old")
    package = tmp_path / "package.zip"
    _write_package(
        package,
        files=[{"path": "existing.txt", "action": "add"}],
        payloads={"existing.txt": b"new"},
    )

    review = _review(package, repository)

    with pytest.raises(PackageApplyError, match="blocked"):
        PackageApplier(
            reviewer=PackageReviewer(),
            backup_root=tmp_path / "backups",
        ).apply(review)

    assert (repository / "existing.txt").read_bytes() == b"old"


def test_apply_rejects_stale_review(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "replace.txt").write_bytes(b"old")
    package = tmp_path / "package.zip"
    _write_package(
        package,
        files=[{"path": "replace.txt", "action": "replace"}],
        payloads={"replace.txt": b"new"},
    )
    reviewer = PackageReviewer()
    review = reviewer.review(
        package,
        repository_id="curvature-console",
        repository_root=repository,
    )

    (repository / "replace.txt").write_bytes(b"changed-after-review")

    with pytest.raises(PackageApplyError, match="changed after review"):
        PackageApplier(
            reviewer=reviewer,
            backup_root=tmp_path / "backups",
        ).apply(review)

    assert (repository / "replace.txt").read_bytes() == (
        b"changed-after-review"
    )


def test_apply_rolls_back_created_and_replaced_files(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "replace.txt").write_bytes(b"old")
    package = tmp_path / "package.zip"
    _write_package(
        package,
        files=[
            {"path": "replace.txt", "action": "replace"},
            {"path": "new.txt", "action": "add"},
        ],
        payloads={
            "replace.txt": b"replacement",
            "new.txt": b"created",
        },
    )

    reviewer = PackageReviewer()
    review = reviewer.review(
        package,
        repository_id="curvature-console",
        repository_root=repository,
    )
    applier = PackageApplier(
        reviewer=reviewer,
        backup_root=tmp_path / "backups",
    )
    original_atomic_write = applier._atomic_write
    calls = 0

    def failing_atomic_write(*, target, content, mode):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("simulated write failure")
        return original_atomic_write(
            target=target,
            content=content,
            mode=mode,
        )

    monkeypatch.setattr(applier, "_atomic_write", failing_atomic_write)

    with pytest.raises(PackageApplyError, match="rolled back"):
        applier.apply(review)

    assert (repository / "replace.txt").read_bytes() == b"old"
    assert not (repository / "new.txt").exists()


def test_apply_does_not_commit_or_push(
    tmp_path: Path,
) -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "src/curvature_console/infrastructure/package_apply.py"
    ).read_text(encoding="utf-8")

    assert '"commit"' not in source
    assert '"push"' not in source


def test_git_report_lists_untracked_files_not_only_directories(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    subprocess.run(
        ["git", "init"],
        cwd=repository,
        check=True,
        capture_output=True,
    )
    nested = repository / "new" / "created.txt"
    nested.parent.mkdir()
    nested.write_text("created", encoding="utf-8")

    applier = PackageApplier(
        reviewer=PackageReviewer(),
        backup_root=tmp_path / "backups",
    )
    status, _diff = applier._git_change_report(repository)

    assert "?? new/created.txt" in status
