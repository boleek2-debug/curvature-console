"""Tests for the read-only B5.2E package review UI."""

from __future__ import annotations

import json
import os
import zipfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QMessageBox

from curvature_console.infrastructure.package_apply import (
    AppliedFile,
    PackageApplyResult,
)
from curvature_console.infrastructure.package_review import (
    PackageAction,
    PackageReviewer,
)
from curvature_console.infrastructure.state_store import (
    GeneratedDownloadRecord,
)
from curvature_console.main import create_application
from curvature_console.presentation.main_window import MainWindow
from curvature_console.presentation.package_review_dialog import (
    PackageReviewDialog,
)


def _write_package(
    package_path: Path,
    repository_id: str,
    files: list[dict[str, str]],
    payloads: dict[str, bytes],
) -> None:
    manifest = {
        "schema_version": 1,
        "package_type": "ui-test",
        "target_repository": repository_id,
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


def test_package_review_dialog_displays_all_classifications(
    tmp_path: Path,
) -> None:
    create_application(["package-review-dialog-test"])
    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "replace.txt").write_bytes(b"old")
    (repository / "same.txt").write_bytes(b"same")
    (repository / "conflict.txt").write_bytes(b"existing")

    package = tmp_path / "package.zip"
    _write_package(
        package,
        "curvature-console",
        [
            {"path": "create.txt", "action": "add"},
            {"path": "replace.txt", "action": "replace"},
            {"path": "same.txt", "action": "replace"},
            {"path": "conflict.txt", "action": "add"},
        ],
        {
            "create.txt": b"new",
            "replace.txt": b"new replacement",
            "same.txt": b"same",
            "conflict.txt": b"different",
        },
    )
    review = PackageReviewer().review(
        package,
        repository_id="curvature-console",
        repository_root=repository,
    )

    dialog = PackageReviewDialog(review)
    assert dialog.table.rowCount() == 4
    assert {
        dialog.table.item(row, 0).text()
        for row in range(dialog.table.rowCount())
    } == {"CREATE", "REPLACE", "SKIP", "CONFLICT"}
    assert "BLOCKED" in dialog.status_label.text()
    assert "Conflict: 1" in dialog.summary_label.text()
    dialog.close()


def test_department_review_button_requires_selected_zip(
    tmp_path: Path,
) -> None:
    create_application(["package-review-button-test"])
    window = MainWindow(
        state_path=tmp_path / "state.sqlite3",
        data_directory=tmp_path / "data",
        repository_roots={
            "curvature-console": tmp_path / "repository",
        },
    )
    panel = window.department_panels["core"]
    zip_path = tmp_path / "package.zip"
    text_path = tmp_path / "notes.txt"
    zip_path.write_bytes(b"zip")
    text_path.write_text("notes", encoding="utf-8")
    records = (
        GeneratedDownloadRecord(
            request_id="one",
            department_id="core",
            conversation_url="https://chatgpt.com/c/core",
            original_filename="notes.txt",
            saved_path=text_path,
            source_url="https://example/notes",
            captured_at="2026-07-24T00:00:00+00:00",
        ),
        GeneratedDownloadRecord(
            request_id="two",
            department_id="core",
            conversation_url="https://chatgpt.com/c/core",
            original_filename="package.zip",
            saved_path=zip_path,
            source_url="https://example/package",
            captured_at="2026-07-24T00:00:01+00:00",
        ),
    )
    panel.set_generated_downloads(records)

    assert not panel.package_review_button.isEnabled()
    panel.download_list.setCurrentRow(0)
    assert not panel.package_review_button.isEnabled()
    panel.download_list.setCurrentRow(1)
    assert panel.package_review_button.isEnabled()
    assert panel.selected_generated_download_path() == zip_path
    window.close()


def test_main_window_opens_review_for_registered_repository(
    tmp_path: Path,
    monkeypatch,
) -> None:
    create_application(["package-review-main-window-test"])
    repository = tmp_path / "repository"
    repository.mkdir()
    package = tmp_path / "package.zip"
    _write_package(
        package,
        "curvature-console",
        [{"path": "new.txt", "action": "add"}],
        {"new.txt": b"new"},
    )
    window = MainWindow(
        state_path=tmp_path / "state.sqlite3",
        data_directory=tmp_path / "data",
        repository_roots={"curvature-console": repository},
    )

    captured = []
    monkeypatch.setattr(
        "curvature_console.presentation.main_window."
        "PackageReviewDialog.exec",
        lambda dialog: captured.append(dialog.review),
    )

    window.review_generated_package("core", str(package))

    assert len(captured) == 1
    assert captured[0].repository_root == repository.resolve()
    assert captured[0].items[0].classified_action is (
        PackageAction.CREATE
    )
    assert not (repository / "new.txt").exists()
    window.close()


def test_main_window_rejects_unregistered_repository(
    tmp_path: Path,
    monkeypatch,
) -> None:
    create_application(["package-review-unknown-repository-test"])
    package = tmp_path / "package.zip"
    _write_package(
        package,
        "unknown-repository",
        [{"path": "new.txt", "action": "add"}],
        {"new.txt": b"new"},
    )
    window = MainWindow(
        state_path=tmp_path / "state.sqlite3",
        data_directory=tmp_path / "data",
        repository_roots={},
    )

    messages: list[str] = []
    monkeypatch.setattr(
        QMessageBox,
        "critical",
        lambda _parent, _title, message: messages.append(message),
    )

    window.review_generated_package("core", str(package))

    assert messages
    assert "No approved local repository" in messages[0]
    window.close()


def test_apply_button_disabled_for_conflicted_review(
    tmp_path: Path,
) -> None:
    create_application(["blocked-apply-button-test"])
    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "existing.txt").write_bytes(b"old")
    package = tmp_path / "package.zip"
    _write_package(
        package,
        "curvature-console",
        [{"path": "existing.txt", "action": "add"}],
        {"existing.txt": b"new"},
    )
    review = PackageReviewer().review(
        package,
        repository_id="curvature-console",
        repository_root=repository,
    )

    dialog = PackageReviewDialog(
        review,
        apply_callback=lambda _review: None,
    )

    assert not dialog.apply_button.isEnabled()
    dialog.close()


def test_explicit_apply_confirmation_runs_callback_and_shows_git_diff(
    tmp_path: Path,
    monkeypatch,
) -> None:
    create_application(["eligible-apply-button-test"])
    repository = tmp_path / "repository"
    repository.mkdir()
    package = tmp_path / "package.zip"
    _write_package(
        package,
        "curvature-console",
        [{"path": "new.txt", "action": "add"}],
        {"new.txt": b"new"},
    )
    review = PackageReviewer().review(
        package,
        repository_id="curvature-console",
        repository_root=repository,
    )
    backup = tmp_path / "backup"
    backup.mkdir()
    calls = []

    result = PackageApplyResult(
        repository_id="curvature-console",
        repository_root=repository,
        package_path=package,
        backup_directory=backup,
        applied_files=(
            AppliedFile(
                relative_path="new.txt",
                action=PackageAction.CREATE,
                backup_path=None,
            ),
        ),
        skipped_paths=(),
        git_status="?? new.txt",
        git_diff="diff --git a/new.txt b/new.txt",
    )

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda *args, **kwargs: QMessageBox.StandardButton.Apply,
    )
    dialog = PackageReviewDialog(
        review,
        apply_callback=lambda supplied_review: (
            calls.append(supplied_review) or result
        ),
    )

    assert dialog.apply_button.isEnabled()
    dialog._confirm_and_apply()

    assert calls == [review]
    assert dialog.apply_result == result
    assert "APPLIED" in dialog.status_label.text()
    assert "?? new.txt" in dialog.result_text.toPlainText()
    assert not dialog.apply_button.isEnabled()
    dialog.close()


def test_cancelled_apply_does_not_run_callback(
    tmp_path: Path,
    monkeypatch,
) -> None:
    create_application(["cancelled-apply-test"])
    repository = tmp_path / "repository"
    repository.mkdir()
    package = tmp_path / "package.zip"
    _write_package(
        package,
        "curvature-console",
        [{"path": "new.txt", "action": "add"}],
        {"new.txt": b"new"},
    )
    review = PackageReviewer().review(
        package,
        repository_id="curvature-console",
        repository_root=repository,
    )
    calls = []

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda *args, **kwargs: QMessageBox.StandardButton.Cancel,
    )
    dialog = PackageReviewDialog(
        review,
        apply_callback=lambda supplied_review: calls.append(
            supplied_review
        ),
    )

    dialog._confirm_and_apply()

    assert calls == []
    assert dialog.apply_result is None
    dialog.close()


def test_default_repository_roots_include_main_curvature_repository(
    tmp_path: Path,
    monkeypatch,
) -> None:
    create_application(["default-package-targets-test"])
    monkeypatch.chdir(tmp_path)

    window = MainWindow(
        state_path=tmp_path / "state.sqlite3",
        data_directory=tmp_path / "data",
    )

    assert window.repository_roots == {
        "curvature-console": tmp_path.resolve(),
        "Curvature": Path("/home/seb/Curvature").resolve(),
    }
    window.close()
