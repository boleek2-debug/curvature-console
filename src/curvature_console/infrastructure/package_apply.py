"""Explicit, rollback-capable application of reviewed Curvature packages."""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from curvature_console.infrastructure.package_review import (
    PackageAction,
    PackageReview,
    PackageReviewer,
)


class PackageApplyError(RuntimeError):
    """Raised when a reviewed package cannot be applied safely."""


@dataclass(frozen=True, slots=True)
class AppliedFile:
    """One file outcome from a successful package application."""

    relative_path: str
    action: PackageAction
    backup_path: Path | None


@dataclass(frozen=True, slots=True)
class PackageApplyResult:
    """Verified result of one explicitly approved package application."""

    repository_id: str
    repository_root: Path
    package_path: Path
    backup_directory: Path
    applied_files: tuple[AppliedFile, ...]
    skipped_paths: tuple[str, ...]
    git_status: str
    git_diff: str

    @property
    def changed_count(self) -> int:
        return len(self.applied_files)


class PackageApplier:
    """Apply one eligible review with backups, atomic writes and rollback."""

    def __init__(
        self,
        *,
        reviewer: PackageReviewer,
        backup_root: Path | None = None,
    ) -> None:
        self.reviewer = reviewer
        self.backup_root = (
            backup_root
            if backup_root is not None
            else Path(
                "~/.local/share/curvature-console/package-backups"
            )
        ).expanduser()

    def apply(self, review: PackageReview) -> PackageApplyResult:
        """Revalidate and apply a package after external explicit approval."""

        current_review = self.reviewer.review(
            review.package_path,
            repository_id=review.repository_id,
            repository_root=review.repository_root,
        )
        self._verify_review_is_current(
            original=review,
            current=current_review,
        )

        if not current_review.is_apply_eligible:
            raise PackageApplyError(
                "Package application is blocked by conflicts."
            )

        changing_items = tuple(
            item
            for item in current_review.items
            if item.classified_action
            in {PackageAction.CREATE, PackageAction.REPLACE}
        )
        skipped_paths = tuple(
            item.relative_path.as_posix()
            for item in current_review.items
            if item.classified_action is PackageAction.SKIP
        )

        backup_directory = self._create_backup_directory(current_review)
        applied: list[AppliedFile] = []
        created_targets: list[Path] = []
        replaced_targets: list[tuple[Path, Path, int]] = []

        try:
            with zipfile.ZipFile(
                current_review.package_path,
                mode="r",
            ) as archive:
                for item in changing_items:
                    relative = item.relative_path.as_posix()
                    content = archive.read(relative)
                    target = (
                        current_review.repository_root
                        / Path(*item.relative_path.parts)
                    )
                    self._verify_target_inside_repository(
                        target=target,
                        repository_root=current_review.repository_root,
                    )

                    backup_path: Path | None = None
                    original_mode: int | None = None

                    if item.classified_action is PackageAction.REPLACE:
                        if not target.is_file():
                            raise PackageApplyError(
                                "Replace target changed after review: "
                                f"{relative}"
                            )
                        original_mode = stat.S_IMODE(target.stat().st_mode)
                        backup_path = (
                            backup_directory
                            / "replaced"
                            / Path(*item.relative_path.parts)
                        )
                        backup_path.parent.mkdir(
                            parents=True,
                            exist_ok=True,
                        )
                        shutil.copy2(target, backup_path)
                        replaced_targets.append(
                            (target, backup_path, original_mode)
                        )
                    else:
                        if target.exists():
                            raise PackageApplyError(
                                "Create target appeared after review: "
                                f"{relative}"
                            )
                        created_targets.append(target)

                    target.parent.mkdir(parents=True, exist_ok=True)
                    self._atomic_write(
                        target=target,
                        content=content,
                        mode=original_mode,
                    )
                    applied.append(
                        AppliedFile(
                            relative_path=relative,
                            action=item.classified_action,
                            backup_path=backup_path,
                        )
                    )

            self._write_apply_metadata(
                review=current_review,
                backup_directory=backup_directory,
                applied=tuple(applied),
                skipped_paths=skipped_paths,
            )
        except Exception as exc:
            rollback_error = self._rollback(
                created_targets=created_targets,
                replaced_targets=replaced_targets,
            )
            if rollback_error is not None:
                raise PackageApplyError(
                    "Package apply failed and rollback was incomplete. "
                    f"Apply error: {exc}; rollback error: {rollback_error}"
                ) from exc
            raise PackageApplyError(
                f"Package apply failed; repository was rolled back: {exc}"
            ) from exc

        git_status, git_diff = self._git_change_report(
            current_review.repository_root
        )

        return PackageApplyResult(
            repository_id=current_review.repository_id,
            repository_root=current_review.repository_root,
            package_path=current_review.package_path,
            backup_directory=backup_directory,
            applied_files=tuple(applied),
            skipped_paths=skipped_paths,
            git_status=git_status,
            git_diff=git_diff,
        )

    def _verify_review_is_current(
        self,
        *,
        original: PackageReview,
        current: PackageReview,
    ) -> None:
        if (
            original.package_path != current.package_path
            or original.repository_id != current.repository_id
            or original.repository_root != current.repository_root
            or original.manifest != current.manifest
            or original.items != current.items
        ):
            raise PackageApplyError(
                "Package or repository state changed after review. "
                "Run Package Review again before applying."
            )

    def _create_backup_directory(
        self,
        review: PackageReview,
    ) -> Path:
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
        safe_package_name = "".join(
            character
            if character.isalnum() or character in {"-", "_", "."}
            else "_"
            for character in review.package_path.stem
        )
        directory = (
            self.backup_root
            / review.repository_id
            / f"{timestamp}-{safe_package_name}-{uuid4().hex[:8]}"
        )
        directory.mkdir(parents=True, exist_ok=False)
        return directory

    def _verify_target_inside_repository(
        self,
        *,
        target: Path,
        repository_root: Path,
    ) -> None:
        resolved = target.resolve(strict=False)
        try:
            resolved.relative_to(repository_root)
        except ValueError as exc:
            raise PackageApplyError(
                f"Target escapes repository root: {target}"
            ) from exc

    def _atomic_write(
        self,
        *,
        target: Path,
        content: bytes,
        mode: int | None,
    ) -> None:
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                prefix=f".{target.name}.",
                suffix=".curvature-part",
                dir=target.parent,
                delete=False,
            ) as temporary:
                temporary.write(content)
                temporary.flush()
                os.fsync(temporary.fileno())
                temporary_path = Path(temporary.name)

            if mode is not None:
                temporary_path.chmod(mode)
            os.replace(temporary_path, target)
            temporary_path = None
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

    def _rollback(
        self,
        *,
        created_targets: list[Path],
        replaced_targets: list[tuple[Path, Path, int]],
    ) -> Exception | None:
        try:
            for target in reversed(created_targets):
                target.unlink(missing_ok=True)
                self._remove_empty_parent_directories(target.parent)

            for target, backup_path, original_mode in reversed(
                replaced_targets
            ):
                target.parent.mkdir(parents=True, exist_ok=True)
                self._atomic_write(
                    target=target,
                    content=backup_path.read_bytes(),
                    mode=original_mode,
                )
        except Exception as exc:
            return exc
        return None

    def _remove_empty_parent_directories(self, directory: Path) -> None:
        while directory != directory.parent:
            try:
                directory.rmdir()
            except OSError:
                return
            directory = directory.parent

    def _write_apply_metadata(
        self,
        *,
        review: PackageReview,
        backup_directory: Path,
        applied: tuple[AppliedFile, ...],
        skipped_paths: tuple[str, ...],
    ) -> None:
        metadata = {
            "schema_version": 1,
            "applied_at": datetime.now(UTC).isoformat(),
            "repository_id": review.repository_id,
            "repository_root": str(review.repository_root),
            "package_path": str(review.package_path),
            "package_type": review.manifest.package_type,
            "applied_files": [
                {
                    "path": item.relative_path,
                    "action": item.action.value,
                    "backup_path": (
                        str(item.backup_path)
                        if item.backup_path is not None
                        else None
                    ),
                }
                for item in applied
            ],
            "skipped_paths": list(skipped_paths),
        }
        metadata_path = backup_directory / "APPLY_RESULT.json"
        metadata_path.write_text(
            json.dumps(metadata, indent=2) + "\n",
            encoding="utf-8",
        )

    def _git_change_report(
        self,
        repository_root: Path,
    ) -> tuple[str, str]:
        try:
            status = subprocess.run(
                [
                    "git",
                    "status",
                    "--short",
                    "--untracked-files=all",
                ],
                cwd=repository_root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.rstrip()
            diff = subprocess.run(
                ["git", "diff", "--no-ext-diff", "--"],
                cwd=repository_root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.rstrip()
        except (OSError, subprocess.CalledProcessError) as exc:
            return (
                "[Git status unavailable]",
                f"[Git diff unavailable: {exc}]",
            )

        return (status or "[working tree clean]", diff or "[no Git diff]")
