"""UI tests for Curvature Console Development Unit."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from curvature_console.main import create_application
from curvature_console.presentation.main_window import MainWindow
from curvature_console.presentation.support_unit_dialog import ConsoleDevelopmentUnitDialog


def _repository(tmp_path: Path, name: str) -> Path:
    repository = tmp_path / name
    repository.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=repository,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Curvature Test"],
        cwd=repository,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"],
        cwd=repository,
        check=True,
    )
    (repository / "README.md").write_text(name, encoding="utf-8")
    subprocess.run(
        ["git", "add", "README.md"],
        cwd=repository,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "baseline"],
        cwd=repository,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "update-ref", "refs/remotes/origin/main", "HEAD"],
        cwd=repository,
        check=True,
    )
    return repository


def test_support_unit_button_is_next_to_bridge_controls(tmp_path: Path) -> None:
    create_application(["curvature-console-support-unit-test"])
    console = _repository(tmp_path, "console")
    project = _repository(tmp_path, "project")
    window = MainWindow(
        data_directory=tmp_path / "data",
        state_path=tmp_path / "state.sqlite3",
        repository_roots={
            "curvature-console": console,
            "Curvature": project,
        },
    )

    assert window.support_unit_button.text() == "Console Development Unit"
    assert window.support_unit_button.objectName() == "supportUnitButton"
    assert window.handoff_controls_button.parent() is window.support_unit_button.parent()
    window.close()


def test_support_unit_dialog_renders_repository_state(tmp_path: Path) -> None:
    create_application(["curvature-console-support-dialog-test"])
    console = _repository(tmp_path, "console")
    dialog = ConsoleDevelopmentUnitDialog(
        repository_roots={"curvature-console": console},
        data_directory=tmp_path / "data",
    )

    assert "Repositories clean: 1/1" in dialog.summary_label.text()
    assert "Repository: curvature-console" in dialog.report_view.toPlainText()
    assert not dialog.open_log_button.isEnabled()
    dialog.close()


def test_support_unit_dialog_has_dedicated_chat_controls(tmp_path: Path) -> None:
    create_application(["curvature-console-support-chat-test"])
    console = _repository(tmp_path, "console")
    dialog = ConsoleDevelopmentUnitDialog(
        repository_roots={"curvature-console": console},
        data_directory=tmp_path / "data",
        conversation_text="Earlier support exchange",
        draft_text="Draft issue",
    )

    assert dialog.tabs.count() == 2
    assert dialog.tabs.tabText(1) == "Console Development Chat"
    assert dialog.chat_view.toPlainText() == "Earlier support exchange"
    assert dialog.chat_input.toPlainText() == "Draft issue"
    assert dialog.send_button.text() == "Send to Console Development"
    assert dialog.attach_report_checkbox.isChecked()
    assert dialog.attach_log_checkbox.isChecked()
    assert dialog.chat_splitter.objectName() == "supportUnitChatSplitter"
    assert not dialog.chat_splitter.childrenCollapsible()
    assert dialog.chat_splitter.orientation().name == "Vertical"
    assert dialog.chat_input.minimumHeight() == 90
    assert dialog.chat_input.maximumHeight() == 130
    dialog.close()


def test_support_unit_chat_emits_message_and_diagnostic_attachment(
    tmp_path: Path,
) -> None:
    create_application(["curvature-console-support-send-test"])
    console = _repository(tmp_path, "console")
    dialog = ConsoleDevelopmentUnitDialog(
        repository_roots={"curvature-console": console},
        data_directory=tmp_path / "data",
    )
    captured: list[tuple[str, tuple[Path, ...]]] = []
    dialog.send_requested.connect(
        lambda message, paths: captured.append((message, tuple(paths)))
    )
    dialog.attach_log_checkbox.setChecked(False)
    dialog.chat_input.setPlainText("Diagnose the bridge failure")

    dialog._emit_send_request()

    assert captured[0][0] == "Diagnose the bridge failure"
    assert len(captured[0][1]) == 1
    assert captured[0][1][0].name.startswith("console-development-diagnostic-")
    assert captured[0][1][0].is_file()
    dialog.close()


def test_support_unit_chat_appends_exchange_and_clears_draft(
    tmp_path: Path,
) -> None:
    create_application(["curvature-console-support-append-test"])
    console = _repository(tmp_path, "console")
    dialog = ConsoleDevelopmentUnitDialog(
        repository_roots={"curvature-console": console},
        data_directory=tmp_path / "data",
    )
    dialog.chat_input.setPlainText("Question")

    dialog.append_exchange("Question", "Answer")

    transcript = dialog.chat_view.toPlainText()
    assert "YOU\nQuestion" in transcript
    assert "CONSOLE DEVELOPMENT\nAnswer" in transcript
    assert dialog.chat_input.toPlainText() == ""
    dialog.close()


def test_support_unit_chat_includes_manual_attachments(tmp_path: Path) -> None:
    create_application(["curvature-console-support-manual-attachment-test"])
    console = _repository(tmp_path, "console")
    attachment = tmp_path / "screen.png"
    attachment.write_bytes(b"png")
    dialog = ConsoleDevelopmentUnitDialog(
        repository_roots={"curvature-console": console},
        data_directory=tmp_path / "data",
    )
    captured: list[tuple[str, tuple[Path, ...]]] = []
    dialog.send_requested.connect(
        lambda message, paths: captured.append((message, tuple(paths)))
    )
    dialog.attach_report_checkbox.setChecked(False)
    dialog.attach_log_checkbox.setChecked(False)
    dialog.attachment_list.add_paths((attachment,))
    dialog.chat_input.setPlainText("Inspect this screenshot")

    dialog._emit_send_request()

    assert captured == [("Inspect this screenshot", (attachment.resolve(),))]
    assert dialog.attachment_list.paste_screenshot_button.text() == "Paste Screenshot"
    dialog.close()


def test_support_unit_dialog_displays_generated_downloads(tmp_path: Path) -> None:
    from curvature_console.infrastructure.state_store import GeneratedDownloadRecord

    create_application(["curvature-console-support-download-test"])
    console = _repository(tmp_path, "console")
    generated = tmp_path / "result.zip"
    generated.write_bytes(b"zip")
    record = GeneratedDownloadRecord(
        request_id="support-1",
        department_id="console-development",
        conversation_url="https://chatgpt.com/c/1",
        original_filename="result.zip",
        saved_path=generated,
        source_url="https://example.invalid/result.zip",
        captured_at="2026-08-01T12:00:00+00:00",
    )
    dialog = ConsoleDevelopmentUnitDialog(
        repository_roots={"curvature-console": console},
        data_directory=tmp_path / "data",
        download_records=(record,),
    )

    assert dialog.download_list.count() == 1
    assert "result.zip" in dialog.download_list.item(0).text()
    assert dialog.open_download_button.isEnabled()
    assert dialog.open_download_folder_button.isEnabled()
    dialog.close()


def test_console_development_unit_restores_legacy_support_state(tmp_path: Path) -> None:
    create_application(["curvature-console-cdu-migration-test"])
    console = _repository(tmp_path, "console")
    state_path = tmp_path / "state.sqlite3"
    window = MainWindow(
        data_directory=tmp_path / "data",
        state_path=state_path,
        repository_roots={"curvature-console": console},
    )
    window.state_store.save_department_state(
        "support", "Legacy support conversation", "Legacy draft"
    )

    # Exercise the same compatibility lookup used when the dialog opens,
    # without starting a modal event loop.
    persisted = (
        window.state_store.load_department_state("console-development")
        or window.state_store.load_department_state("support")
    )

    assert persisted is not None
    assert persisted.conversation_text == "Legacy support conversation"
    assert persisted.draft_text == "Legacy draft"
    window.close()
