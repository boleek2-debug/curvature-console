"""Tests for read-only Curvature package review and validation."""

from __future__ import annotations

import hashlib
import json
import stat
import warnings
import zipfile
from pathlib import Path

import pytest

from curvature_console.infrastructure.package_review import (
    MANIFEST_NAME,
    PackageAction,
    PackageReviewError,
    PackageReviewer,
)


def _write_package(
    path: Path,
    *,
    target_repository: str = "curvature-console",
    manifest_files: list[dict[str, str]] | None = None,
    payloads: dict[str, bytes] | None = None,
) -> None:
    payloads = payloads or {"new.txt": b"new content"}
    manifest_files = manifest_files or [
        {"path": name, "action": "add"}
        for name in payloads
    ]
    manifest = {
        "schema_version": 1,
        "package_type": "test-package",
        "target_repository": target_repository,
        "files": manifest_files,
    }

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            MANIFEST_NAME,
            json.dumps(manifest),
        )
        for name, content in payloads.items():
            archive.writestr(name, content)


def test_review_classifies_create_replace_skip_and_conflict(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "replace.txt").write_text("old", encoding="utf-8")
    (repository / "same.txt").write_text("same", encoding="utf-8")
    (repository / "conflict.txt").write_text(
        "existing",
        encoding="utf-8",
    )

    package = tmp_path / "package.zip"
    _write_package(
        package,
        manifest_files=[
            {"path": "create.txt", "action": "add"},
            {"path": "replace.txt", "action": "replace"},
            {"path": "same.txt", "action": "replace"},
            {"path": "conflict.txt", "action": "add"},
        ],
        payloads={
            "create.txt": b"create",
            "replace.txt": b"replacement",
            "same.txt": b"same",
            "conflict.txt": b"different",
        },
    )

    review = PackageReviewer().review(
        package,
        repository_id="curvature-console",
        repository_root=repository,
    )

    assert [
        item.classified_action for item in review.items
    ] == [
        PackageAction.CREATE,
        PackageAction.REPLACE,
        PackageAction.SKIP,
        PackageAction.CONFLICT,
    ]
    assert review.has_conflicts
    assert not review.is_apply_eligible
    assert not (repository / "create.txt").exists()
    assert (repository / "replace.txt").read_text(
        encoding="utf-8"
    ) == "old"


def test_identical_declared_add_is_safe_skip(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "same.txt").write_bytes(b"same")

    package = tmp_path / "package.zip"
    _write_package(
        package,
        manifest_files=[{"path": "same.txt", "action": "add"}],
        payloads={"same.txt": b"same"},
    )

    review = PackageReviewer().review(
        package,
        repository_id="curvature-console",
        repository_root=repository,
    )

    assert review.items[0].classified_action is PackageAction.SKIP
    assert review.is_apply_eligible


@pytest.mark.parametrize(
    "unsafe_path",
    [
        "../escape.txt",
        "/absolute.txt",
        "folder/../../escape.txt",
        r"folder\escape.txt",
        "C:/drive.txt",
    ],
)
def test_rejects_unsafe_manifest_paths(
    tmp_path: Path,
    unsafe_path: str,
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    package = tmp_path / "package.zip"
    _write_package(
        package,
        manifest_files=[{"path": unsafe_path, "action": "add"}],
        payloads={"safe.txt": b"content"},
    )

    with pytest.raises(PackageReviewError):
        PackageReviewer().review(
            package,
            repository_id="curvature-console",
            repository_root=repository,
        )


def test_rejects_undeclared_payload(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    package = tmp_path / "package.zip"
    _write_package(
        package,
        manifest_files=[{"path": "declared.txt", "action": "add"}],
        payloads={
            "declared.txt": b"declared",
            "hidden.txt": b"hidden",
        },
    )

    with pytest.raises(
        PackageReviewError,
        match="undeclared payload",
    ):
        PackageReviewer().review(
            package,
            repository_id="curvature-console",
            repository_root=repository,
        )


def test_rejects_missing_declared_payload(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    package = tmp_path / "package.zip"
    _write_package(
        package,
        manifest_files=[
            {"path": "missing.txt", "action": "add"}
        ],
        payloads={"other.txt": b"content"},
    )

    with pytest.raises(PackageReviewError):
        PackageReviewer().review(
            package,
            repository_id="curvature-console",
            repository_root=repository,
        )


def test_rejects_repository_identity_mismatch(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    package = tmp_path / "package.zip"
    _write_package(package, target_repository="Curvature")

    with pytest.raises(
        PackageReviewError,
        match="target repository mismatch",
    ):
        PackageReviewer().review(
            package,
            repository_id="curvature-console",
            repository_root=repository,
        )


def test_rejects_symlink_zip_entry(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    package = tmp_path / "package.zip"

    manifest = {
        "schema_version": 1,
        "package_type": "symlink-test",
        "target_repository": "curvature-console",
        "files": [{"path": "link.txt", "action": "add"}],
    }
    link_info = zipfile.ZipInfo("link.txt")
    link_info.create_system = 3
    link_info.external_attr = (
        (stat.S_IFLNK | 0o777) << 16
    )

    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr(MANIFEST_NAME, json.dumps(manifest))
        archive.writestr(link_info, "../outside.txt")

    with pytest.raises(PackageReviewError, match="Symlink"):
        PackageReviewer().review(
            package,
            repository_id="curvature-console",
            repository_root=repository,
        )


def test_rejects_target_path_escaping_through_symlink(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    outside = tmp_path / "outside"
    repository.mkdir()
    outside.mkdir()
    (repository / "linked").symlink_to(
        outside,
        target_is_directory=True,
    )

    package = tmp_path / "package.zip"
    _write_package(
        package,
        manifest_files=[
            {"path": "linked/escape.txt", "action": "add"}
        ],
        payloads={"linked/escape.txt": b"escape"},
    )

    with pytest.raises(
        PackageReviewError,
        match="filesystem links",
    ):
        PackageReviewer().review(
            package,
            repository_id="curvature-console",
            repository_root=repository,
        )


def test_rejects_duplicate_zip_entries(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    package = tmp_path / "package.zip"
    manifest = {
        "schema_version": 1,
        "package_type": "duplicate-test",
        "target_repository": "curvature-console",
        "files": [{"path": "same.txt", "action": "add"}],
    }

    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="Duplicate name: 'same.txt'",
            category=UserWarning,
        )
        with zipfile.ZipFile(package, "w") as archive:
            archive.writestr(MANIFEST_NAME, json.dumps(manifest))
            archive.writestr("same.txt", b"first")
            archive.writestr("same.txt", b"second")

    with pytest.raises(PackageReviewError, match="Duplicate ZIP entry"):
        PackageReviewer().review(
            package,
            repository_id="curvature-console",
            repository_root=repository,
        )


def test_optional_sha256_is_verified(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    package = tmp_path / "package.zip"
    content = b"verified"
    digest = hashlib.sha256(content).hexdigest()
    _write_package(
        package,
        manifest_files=[
            {
                "path": "verified.txt",
                "action": "add",
                "sha256": digest,
            }
        ],
        payloads={"verified.txt": content},
    )

    review = PackageReviewer().review(
        package,
        repository_id="curvature-console",
        repository_root=repository,
    )

    assert review.items[0].archive_sha256 == digest


def test_rejects_incorrect_sha256(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    package = tmp_path / "package.zip"
    _write_package(
        package,
        manifest_files=[
            {
                "path": "verified.txt",
                "action": "add",
                "sha256": "0" * 64,
            }
        ],
        payloads={"verified.txt": b"not zero hash"},
    )

    with pytest.raises(PackageReviewError, match="sha256"):
        PackageReviewer().review(
            package,
            repository_id="curvature-console",
            repository_root=repository,
        )


def test_rejects_zip_bomb_ratio(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    package = tmp_path / "package.zip"
    _write_package(
        package,
        payloads={"large.txt": b"A" * 100_000},
    )

    with pytest.raises(
        PackageReviewError,
        match="compression ratio",
    ):
        PackageReviewer(max_compression_ratio=2.0).review(
            package,
            repository_id="curvature-console",
            repository_root=repository,
        )
