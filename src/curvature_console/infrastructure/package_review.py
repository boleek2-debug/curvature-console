"""Read-only validation and classification of Curvature ZIP packages."""

from __future__ import annotations

import hashlib
import json
import stat
import zipfile
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Any, Final


MANIFEST_NAME: Final[str] = "CURVATURE_PACKAGE.json"
SUPPORTED_SCHEMA_VERSION: Final[int] = 1
ALLOWED_MANIFEST_ACTIONS: Final[frozenset[str]] = frozenset(
    {"add", "replace"}
)


class PackageReviewError(RuntimeError):
    """Raised when a package cannot be reviewed safely."""


class PackageAction(StrEnum):
    """Read-only action classification for one declared package file."""

    CREATE = "create"
    REPLACE = "replace"
    CONFLICT = "conflict"
    SKIP = "skip"


@dataclass(frozen=True, slots=True)
class PackageManifestFile:
    """One file declared by the machine-readable package manifest."""

    relative_path: PurePosixPath
    requested_action: str
    declared_sha256: str | None


@dataclass(frozen=True, slots=True)
class PackageManifest:
    """Validated package manifest metadata."""

    schema_version: int
    package_type: str
    target_repository: str
    files: tuple[PackageManifestFile, ...]


@dataclass(frozen=True, slots=True)
class PackageReviewItem:
    """One read-only package review result."""

    relative_path: PurePosixPath
    requested_action: str
    classified_action: PackageAction
    archive_size: int
    archive_sha256: str
    target_exists: bool
    target_sha256: str | None
    reason: str


@dataclass(frozen=True, slots=True)
class PackageReview:
    """Complete read-only review of one package against one repository."""

    package_path: Path
    repository_id: str
    repository_root: Path
    manifest: PackageManifest
    items: tuple[PackageReviewItem, ...]
    total_uncompressed_bytes: int

    @property
    def has_conflicts(self) -> bool:
        return any(
            item.classified_action is PackageAction.CONFLICT
            for item in self.items
        )

    @property
    def is_apply_eligible(self) -> bool:
        """Return whether later Apply work may offer explicit approval."""

        return not self.has_conflicts


class PackageReviewer:
    """Validate a package without extracting or modifying repositories."""

    def __init__(
        self,
        *,
        max_file_bytes: int = 64 * 1024 * 1024,
        max_total_bytes: int = 256 * 1024 * 1024,
        max_compression_ratio: float = 200.0,
    ) -> None:
        if max_file_bytes < 1:
            raise ValueError("max_file_bytes must be positive.")
        if max_total_bytes < 1:
            raise ValueError("max_total_bytes must be positive.")
        if max_compression_ratio <= 0:
            raise ValueError("max_compression_ratio must be positive.")

        self.max_file_bytes = max_file_bytes
        self.max_total_bytes = max_total_bytes
        self.max_compression_ratio = max_compression_ratio

    def manifest_target_repository(
        self,
        package_path: Path,
    ) -> str:
        """Read and validate the package target without repository access."""

        package_path = package_path.expanduser().resolve()
        if not package_path.is_file():
            raise PackageReviewError(
                f"Package file not found: {package_path}"
            )

        try:
            archive = zipfile.ZipFile(package_path, mode="r")
        except (OSError, zipfile.BadZipFile) as exc:
            raise PackageReviewError(
                f"Cannot open ZIP package: {package_path}"
            ) from exc

        with archive:
            entries = self._validate_archive_entries(archive)
            manifest = self._load_manifest(archive, entries)
            return manifest.target_repository

    def review(
        self,
        package_path: Path,
        *,
        repository_id: str,
        repository_root: Path,
    ) -> PackageReview:
        """Return a complete review without writing any package content."""

        package_path = package_path.expanduser().resolve()
        repository_root = repository_root.expanduser().resolve()

        if not package_path.is_file():
            raise PackageReviewError(
                f"Package file not found: {package_path}"
            )
        if not repository_id.strip():
            raise PackageReviewError("Repository id must not be empty.")
        if not repository_root.is_dir():
            raise PackageReviewError(
                f"Repository root not found: {repository_root}"
            )

        try:
            archive = zipfile.ZipFile(package_path, mode="r")
        except (OSError, zipfile.BadZipFile) as exc:
            raise PackageReviewError(
                f"Cannot open ZIP package: {package_path}"
            ) from exc

        with archive:
            entries = self._validate_archive_entries(archive)
            manifest = self._load_manifest(archive, entries)

            if manifest.target_repository != repository_id:
                raise PackageReviewError(
                    "Package target repository mismatch: "
                    f"manifest={manifest.target_repository!r}, "
                    f"selected={repository_id!r}."
                )

            payload_entries = {
                name: info
                for name, info in entries.items()
                if name != MANIFEST_NAME
            }
            declared_paths = {
                item.relative_path.as_posix()
                for item in manifest.files
            }
            actual_paths = set(payload_entries)

            undeclared = sorted(actual_paths - declared_paths)
            if undeclared:
                raise PackageReviewError(
                    "ZIP contains undeclared payload files: "
                    + ", ".join(undeclared)
                )

            missing = sorted(declared_paths - actual_paths)
            if missing:
                raise PackageReviewError(
                    "Manifest declares missing payload files: "
                    + ", ".join(missing)
                )

            review_items = tuple(
                self._review_file(
                    archive=archive,
                    archive_info=payload_entries[
                        manifest_file.relative_path.as_posix()
                    ],
                    manifest_file=manifest_file,
                    repository_root=repository_root,
                )
                for manifest_file in manifest.files
            )

            return PackageReview(
                package_path=package_path,
                repository_id=repository_id,
                repository_root=repository_root,
                manifest=manifest,
                items=review_items,
                total_uncompressed_bytes=sum(
                    item.archive_size for item in review_items
                ),
            )

    def _validate_archive_entries(
        self,
        archive: zipfile.ZipFile,
    ) -> dict[str, zipfile.ZipInfo]:
        entries: dict[str, zipfile.ZipInfo] = {}
        total_size = 0

        for info in archive.infolist():
            if info.flag_bits & 0x1:
                raise PackageReviewError(
                    f"Encrypted ZIP entries are not supported: {info.filename}"
                )

            if info.is_dir():
                self._safe_relative_path(info.filename.rstrip("/"))
                continue

            relative_path = self._safe_relative_path(info.filename)
            canonical = relative_path.as_posix()

            if canonical in entries:
                raise PackageReviewError(
                    f"Duplicate ZIP entry: {canonical}"
                )

            unix_mode = (info.external_attr >> 16) & 0xFFFF
            if unix_mode and stat.S_ISLNK(unix_mode):
                raise PackageReviewError(
                    f"Symlink ZIP entry is not allowed: {canonical}"
                )

            if info.file_size > self.max_file_bytes:
                raise PackageReviewError(
                    f"ZIP entry exceeds size limit: {canonical}"
                )

            total_size += info.file_size
            if total_size > self.max_total_bytes:
                raise PackageReviewError(
                    "ZIP package exceeds total uncompressed size limit."
                )

            compressed_size = max(info.compress_size, 1)
            ratio = info.file_size / compressed_size
            if ratio > self.max_compression_ratio:
                raise PackageReviewError(
                    f"Suspicious ZIP compression ratio: {canonical}"
                )

            entries[canonical] = info

        if MANIFEST_NAME not in entries:
            raise PackageReviewError(
                f"ZIP root must contain {MANIFEST_NAME}."
            )

        return entries

    def _load_manifest(
        self,
        archive: zipfile.ZipFile,
        entries: dict[str, zipfile.ZipInfo],
    ) -> PackageManifest:
        try:
            raw_bytes = archive.read(entries[MANIFEST_NAME])
            raw = json.loads(raw_bytes.decode("utf-8"))
        except (KeyError, UnicodeError, json.JSONDecodeError) as exc:
            raise PackageReviewError(
                f"{MANIFEST_NAME} is not valid UTF-8 JSON."
            ) from exc

        if not isinstance(raw, dict):
            raise PackageReviewError("Package manifest must be a JSON object.")

        schema_version = raw.get("schema_version")
        if schema_version != SUPPORTED_SCHEMA_VERSION:
            raise PackageReviewError(
                "Unsupported package schema version: "
                f"{schema_version!r}."
            )

        package_type = self._required_string(raw, "package_type")
        target_repository = self._required_string(
            raw,
            "target_repository",
        )

        raw_files = raw.get("files")
        if not isinstance(raw_files, list) or not raw_files:
            raise PackageReviewError(
                "Manifest field 'files' must be a non-empty list."
            )

        files: list[PackageManifestFile] = []
        seen_paths: set[str] = set()

        for index, raw_file in enumerate(raw_files, start=1):
            if not isinstance(raw_file, dict):
                raise PackageReviewError(
                    f"Manifest file entry {index} must be an object."
                )

            raw_path = self._required_string(raw_file, "path")
            relative_path = self._safe_relative_path(raw_path)
            canonical = relative_path.as_posix()

            if canonical == MANIFEST_NAME:
                raise PackageReviewError(
                    f"{MANIFEST_NAME} cannot declare itself as payload."
                )
            if canonical in seen_paths:
                raise PackageReviewError(
                    f"Duplicate manifest file path: {canonical}"
                )
            seen_paths.add(canonical)

            requested_action = self._required_string(
                raw_file,
                "action",
            ).lower()
            if requested_action not in ALLOWED_MANIFEST_ACTIONS:
                raise PackageReviewError(
                    "Unsupported manifest action for "
                    f"{canonical}: {requested_action!r}."
                )

            declared_sha256 = raw_file.get("sha256")
            if declared_sha256 is not None:
                if not isinstance(declared_sha256, str):
                    raise PackageReviewError(
                        f"sha256 must be a string for {canonical}."
                    )
                declared_sha256 = declared_sha256.strip().lower()
                if not self._is_sha256(declared_sha256):
                    raise PackageReviewError(
                        f"Invalid sha256 for {canonical}."
                    )

            files.append(
                PackageManifestFile(
                    relative_path=relative_path,
                    requested_action=requested_action,
                    declared_sha256=declared_sha256,
                )
            )

        return PackageManifest(
            schema_version=schema_version,
            package_type=package_type,
            target_repository=target_repository,
            files=tuple(files),
        )

    def _review_file(
        self,
        *,
        archive: zipfile.ZipFile,
        archive_info: zipfile.ZipInfo,
        manifest_file: PackageManifestFile,
        repository_root: Path,
    ) -> PackageReviewItem:
        archive_content = archive.read(archive_info)
        archive_sha256 = hashlib.sha256(archive_content).hexdigest()

        if (
            manifest_file.declared_sha256 is not None
            and manifest_file.declared_sha256 != archive_sha256
        ):
            raise PackageReviewError(
                "Declared sha256 does not match payload: "
                f"{manifest_file.relative_path.as_posix()}"
            )

        target = (
            repository_root
            / Path(*manifest_file.relative_path.parts)
        )
        resolved_target = target.resolve(strict=False)
        try:
            resolved_target.relative_to(repository_root)
        except ValueError as exc:
            raise PackageReviewError(
                "Target path escapes repository through filesystem links: "
                f"{manifest_file.relative_path.as_posix()}"
            ) from exc

        target_exists = target.exists()
        if target_exists and not target.is_file():
            return PackageReviewItem(
                relative_path=manifest_file.relative_path,
                requested_action=manifest_file.requested_action,
                classified_action=PackageAction.CONFLICT,
                archive_size=len(archive_content),
                archive_sha256=archive_sha256,
                target_exists=True,
                target_sha256=None,
                reason="Target exists but is not a regular file.",
            )

        target_sha256: str | None = None
        if target_exists:
            try:
                target_sha256 = self._file_sha256(target)
            except OSError as exc:
                raise PackageReviewError(
                    f"Cannot read target file: {target}"
                ) from exc

        action, reason = self._classify(
            requested_action=manifest_file.requested_action,
            target_exists=target_exists,
            archive_sha256=archive_sha256,
            target_sha256=target_sha256,
        )

        return PackageReviewItem(
            relative_path=manifest_file.relative_path,
            requested_action=manifest_file.requested_action,
            classified_action=action,
            archive_size=len(archive_content),
            archive_sha256=archive_sha256,
            target_exists=target_exists,
            target_sha256=target_sha256,
            reason=reason,
        )

    def _classify(
        self,
        *,
        requested_action: str,
        target_exists: bool,
        archive_sha256: str,
        target_sha256: str | None,
    ) -> tuple[PackageAction, str]:
        if requested_action == "add":
            if target_exists:
                if target_sha256 == archive_sha256:
                    return (
                        PackageAction.SKIP,
                        "Declared add already exists with identical content.",
                    )
                return (
                    PackageAction.CONFLICT,
                    "Declared add would overwrite an existing file.",
                )
            return (PackageAction.CREATE, "New repository file.")

        if not target_exists:
            return (
                PackageAction.CONFLICT,
                "Declared replace target does not exist.",
            )
        if target_sha256 == archive_sha256:
            return (
                PackageAction.SKIP,
                "Existing file already matches package content.",
            )
        return (PackageAction.REPLACE, "Existing file would be replaced.")

    def _safe_relative_path(self, raw_path: str) -> PurePosixPath:
        if not isinstance(raw_path, str):
            raise PackageReviewError("Package path must be a string.")
        if not raw_path or "\x00" in raw_path:
            raise PackageReviewError("Package path is empty or contains NUL.")
        if "\\" in raw_path:
            raise PackageReviewError(
                f"Backslashes are not allowed in package paths: {raw_path!r}"
            )

        path = PurePosixPath(raw_path)
        if path.is_absolute():
            raise PackageReviewError(
                f"Absolute package path is not allowed: {raw_path}"
            )
        if not path.parts:
            raise PackageReviewError("Package path must not be empty.")
        if any(part in {"", ".", ".."} for part in path.parts):
            raise PackageReviewError(
                f"Unsafe package path: {raw_path}"
            )
        if ":" in path.parts[0]:
            raise PackageReviewError(
                f"Drive-qualified package path is not allowed: {raw_path}"
            )

        return path

    def _required_string(
        self,
        mapping: dict[str, Any],
        key: str,
    ) -> str:
        value = mapping.get(key)
        if not isinstance(value, str) or not value.strip():
            raise PackageReviewError(
                f"Manifest field {key!r} must be a non-empty string."
            )
        return value.strip()

    def _file_sha256(self, path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _is_sha256(self, value: str) -> bool:
        return len(value) == 64 and all(
            character in "0123456789abcdef"
            for character in value
        )
