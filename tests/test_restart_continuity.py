"""End-to-end restart continuity tests for ASSISTANT-001B4."""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from curvature_console.main import create_application
from curvature_console.presentation.main_window import MainWindow


def test_window_restores_drafts_attachments_and_focus(
    tmp_path: Path,
) -> None:
    application = create_application(["curvature-console-restart-test"])

    database = tmp_path / "state.sqlite3"
    data_directory = tmp_path / "data"
    attachment = tmp_path / "core.log"
    attachment.write_text("failure details", encoding="utf-8")

    first = MainWindow(
        state_path=database,
        data_directory=data_directory,
    )
    first.show()
    application.processEvents()

    first.department_panels["core"].input_editor.setPlainText(
        "Continue implementing persistence."
    )
    first.department_panels["core"].conversation_view.setPlainText(
        "Core conversation transcript"
    )
    first.department_panels["core"].attachment_list.add_paths([attachment])

    first.splitter.setSizes([250, 700, 550])
    application.processEvents()

    persisted_sizes = first.splitter.sizes()
    assert len(persisted_sizes) == 3
    assert all(size > 0 for size in persisted_sizes)

    first.focus_department("core")
    first.save_all_state()
    first.state_store.close()
    first.hide()

    second = MainWindow(
        state_path=database,
        data_directory=data_directory,
    )

    assert second.focused_department_id == "core"
    assert (
        second.department_panels["core"].input_editor.toPlainText()
        == "Continue implementing persistence."
    )
    assert (
        second.department_panels["core"].conversation_view.toPlainText()
        == "Core conversation transcript"
    )
    assert [
        record.name
        for record in second.department_panels["core"].attachment_list.records
    ] == ["core.log"]
    assert second._three_panel_sizes == persisted_sizes

    second.state_store.close()


def test_three_departments_keep_separate_drafts(tmp_path: Path) -> None:
    create_application(["curvature-console-separate-state-test"])

    database = tmp_path / "state.sqlite3"

    first = MainWindow(state_path=database, data_directory=tmp_path / "data")
    first.department_panels["project"].input_editor.setPlainText(
        "Project draft"
    )
    first.department_panels["core"].input_editor.setPlainText("Core draft")
    first.department_panels["research"].input_editor.setPlainText(
        "Research draft"
    )
    first.save_all_state()
    first.state_store.close()

    second = MainWindow(state_path=database, data_directory=tmp_path / "data")

    assert (
        second.department_panels["project"].input_editor.toPlainText()
        == "Project draft"
    )
    assert (
        second.department_panels["core"].input_editor.toPlainText()
        == "Core draft"
    )
    assert (
        second.department_panels["research"].input_editor.toPlainText()
        == "Research draft"
    )

    second.state_store.close()
