"""Tests for the ASSISTANT-001B2 three-panel desktop shell."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QPlainTextEdit, QSplitter

from curvature_console.main import create_application
from curvature_console.presentation.main_window import MainWindow


@pytest.fixture
def window() -> MainWindow:
    create_application(["curvature-console-three-panel-test"])
    main_window = MainWindow()
    main_window.show()
    yield main_window
    main_window.close()


def test_three_department_panels_exist_and_are_visible(window: MainWindow) -> None:
    assert set(window.department_panels) == {"project", "core", "research"}
    assert isinstance(window.splitter, QSplitter)
    assert window.splitter.count() == 3

    for panel in window.department_panels.values():
        assert panel.isVisible()


def test_each_department_has_independent_conversation_and_input(
    window: MainWindow,
) -> None:
    input_objects = []
    restored_transcripts: dict[str, str] = {}

    for department_id, panel in window.department_panels.items():
        assert not hasattr(panel, "conversation_view")
        assert isinstance(panel.input_editor, QPlainTextEdit)
        assert not panel.input_editor.isReadOnly()
        assert panel.input_editor.objectName() == f"{department_id}Input"

        transcript = f"{department_id} independent transcript"
        panel.restore_conversation_text(transcript)
        restored_transcripts[department_id] = panel.conversation_text()
        input_objects.append(panel.input_editor)

    assert restored_transcripts == {
        "project": "project independent transcript",
        "core": "core independent transcript",
        "research": "research independent transcript",
    }
    assert len({id(item) for item in input_objects}) == 3


def test_focus_and_restore_preserve_all_panels(window: MainWindow) -> None:
    window.department_panels["core"].input_editor.setPlainText(
        "Preserve this Core draft."
    )

    window.focus_department("core")

    assert window.focused_department_id == "core"
    assert window.department_panels["core"].isVisible()
    assert not window.department_panels["project"].isVisible()
    assert not window.department_panels["research"].isVisible()
    assert window.restore_button.isEnabled()

    window.restore_three_panel_view()

    assert window.focused_department_id is None
    assert all(panel.isVisible() for panel in window.department_panels.values())
    assert not window.restore_button.isEnabled()
    assert (
        window.department_panels["core"].input_editor.toPlainText()
        == "Preserve this Core draft."
    )


def test_unknown_department_cannot_be_focused(window: MainWindow) -> None:
    with pytest.raises(ValueError, match="Unknown department"):
        window.focus_department("unknown")


def test_each_department_has_independent_thread_pressure_indicator(
    window: MainWindow,
) -> None:
    project = window.department_panels["project"]
    core = window.department_panels["core"]
    research = window.department_panels["research"]

    for department_id, panel in window.department_panels.items():
        assert panel.thread_pressure_label.objectName() == (
            f"{department_id}ThreadPressure"
        )
        assert "THREAD PRESSURE: GREEN" in panel.thread_pressure_label.text()
        assert "exact context" in panel.thread_pressure_label.toolTip()

    core.input_editor.setPlainText("x" * 200_000)

    assert "THREAD PRESSURE: AMBER" in core.thread_pressure_label.text()
    assert "THREAD PRESSURE: GREEN" in project.thread_pressure_label.text()
    assert "THREAD PRESSURE: GREEN" in research.thread_pressure_label.text()


def test_thread_pressure_changes_handoff_call_to_action(window: MainWindow) -> None:
    core = window.department_panels["core"]
    estimator = core.thread_pressure_estimator

    core.input_editor.setPlainText("x" * (estimator.AMBER_THRESHOLD * 4))
    assert "AMBER" in core.thread_pressure_label.text()
    assert core.thread_handoff_button.text() == (
        "Send Thread Handoff (Recommended)"
    )
    assert "Prepare" in core.thread_pressure_recommendation.text()

    core.input_editor.setPlainText("x" * (estimator.RED_THRESHOLD * 4))
    assert "RED" in core.thread_pressure_label.text()
    assert core.thread_handoff_button.text() == "Send Thread Handoff Now"
    assert "strongly recommended" in (
        core.thread_pressure_recommendation.text()
    )

    core.input_editor.clear()
    assert core.thread_handoff_button.text() == "Send Thread Handoff"


def test_busy_panel_shows_live_activity_indicator(window: MainWindow) -> None:
    panel = window.department_panels["core"]

    panel.set_browser_busy(True)
    panel.set_browser_stage("Waiting for response")

    assert panel.activity_progress.isVisible()
    assert panel.activity_progress.minimum() == 0
    assert panel.activity_progress.maximum() == 0
    assert panel._activity_timer.isActive()
    assert "WORKING" in panel.activity_label.text()
    assert "Waiting for response" in panel.activity_label.text()

    panel.set_browser_busy(False)

    assert not panel.activity_progress.isVisible()
    assert not panel._activity_timer.isActive()
    assert panel.activity_label.text() == "IDLE"
