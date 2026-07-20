"""UI tests for browser-delivered Task and Thread Handoff packages."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QMessageBox

from curvature_console.infrastructure.context_loader import ContextLoadResult
from curvature_console.infrastructure.transfer_package import (
    TransferPackage,
    TransferPackageMode,
)
from curvature_console.main import create_application
from curvature_console.presentation.main_window import MainWindow


def test_each_department_exposes_both_send_buttons() -> None:
    create_application(["curvature-console-transfer-button-test"])
    window = MainWindow()

    for department_id, panel in window.department_panels.items():
        assert panel.task_package_button.isEnabled()
        assert panel.thread_handoff_button.isEnabled()
        assert panel.task_package_button.text() == "Send Task"
        assert panel.thread_handoff_button.text() == "Send Thread Handoff"
        assert panel.task_package_button.objectName() == (
            f"{department_id}TaskPackageButton"
        )
        assert panel.thread_handoff_button.objectName() == (
            f"{department_id}ThreadHandoffButton"
        )

    window.close()


def test_task_send_is_one_click(monkeypatch) -> None:
    create_application(["curvature-console-one-click-task-test"])
    window = MainWindow()
    panel = window.department_panels["core"]
    panel.input_editor.setPlainText("Current Core task")
    window.context_results["core"] = ContextLoadResult(
        department_id="core",
        documents=(),
        errors=(),
    )

    captured: list[TransferPackage] = []
    monkeypatch.setattr(window, "start_browser_exchange", captured.append)

    window.prepare_transfer_package("core", "task")

    assert len(captured) == 1
    assert captured[0].mode is TransferPackageMode.TASK
    assert "Current Core task" in captured[0].text
    window.close()


def test_thread_handoff_requires_confirmation(monkeypatch) -> None:
    create_application(["curvature-console-handoff-confirmation-test"])
    window = MainWindow()
    panel = window.department_panels["core"]
    panel.input_editor.setPlainText("Continue in a new thread")
    window.context_results["core"] = ContextLoadResult(
        department_id="core",
        documents=(),
        errors=(),
    )

    captured: list[TransferPackage] = []
    monkeypatch.setattr(window, "start_browser_exchange", captured.append)
    monkeypatch.setattr(
        "curvature_console.presentation.main_window.QMessageBox.warning",
        lambda *args, **kwargs: QMessageBox.StandardButton.Cancel,
    )

    window.prepare_transfer_package("core", "thread_handoff")
    assert captured == []

    monkeypatch.setattr(
        "curvature_console.presentation.main_window.QMessageBox.warning",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    window.prepare_transfer_package("core", "thread_handoff")

    assert len(captured) == 1
    assert captured[0].mode is TransferPackageMode.THREAD_HANDOFF
    window.close()


def test_browser_success_appends_and_persists_response(tmp_path) -> None:
    create_application(["curvature-console-browser-success-test"])
    state_path = tmp_path / "state.sqlite3"
    window = MainWindow(state_path=state_path, data_directory=tmp_path / "data")
    panel = window.department_panels["core"]
    panel.input_editor.setPlainText("Exact user task.")
    window._pending_tasks["core"] = "Exact user task."

    window._handle_browser_success(
        "core",
        "Curvature Core",
        "https://chatgpt.com/g/g-p-core/project",
        "https://chatgpt.com/c/core-chat",
        "Exact assistant response.\nSecond line.",
    )

    transcript = panel.conversation_view.toPlainText()
    assert "=== USER TASK ===\n\nExact user task." in transcript
    assert (
        "=== ASSISTANT RESPONSE ===\n\n"
        "Exact assistant response.\nSecond line."
    ) in transcript
    assert panel.input_editor.toPlainText() == ""

    persisted = window.state_store.load_department_state("core")
    assert persisted is not None
    assert persisted.conversation_text == transcript
    assert persisted.draft_text == ""

    route = window.state_store.load_chat_route("core")
    assert route is not None
    assert route.project_name == "Curvature Core"
    assert route.project_url == "https://chatgpt.com/g/g-p-core/project"
    assert route.active_conversation_url == (
        "https://chatgpt.com/c/core-chat"
    )

    window.close()


def test_missing_routes_are_bootstrapped_without_chat_titles(tmp_path) -> None:
    create_application(["curvature-console-route-bootstrap-test"])
    window = MainWindow(
        state_path=tmp_path / "state.sqlite3",
        data_directory=tmp_path / "data",
    )

    for department_id in ("project", "core", "research"):
        route = window.state_store.load_chat_route(department_id)
        assert route is not None
        assert route.project_name == "Curvature"
        assert route.project_url.endswith("/project")
        assert route.active_conversation_url.startswith(
            "https://chatgpt.com/c/"
        )

    window.close()


def test_only_active_department_is_locked_during_browser_operation() -> None:
    create_application(["curvature-console-panel-isolation-test"])
    window = MainWindow()

    window._set_browser_operation_busy(True, "core")

    assert not window.department_panels["core"].input_editor.isEnabled()
    assert window.department_panels["project"].input_editor.isEnabled()
    assert window.department_panels["research"].input_editor.isEnabled()

    window._set_browser_operation_busy(False, "core")

    assert window.department_panels["core"].input_editor.isEnabled()
    window.close()



def test_route_unverified_signal_exists() -> None:
    from curvature_console.infrastructure.browser_bridge import (
        BrowserBridgeConfig,
        BrowserExchangeRequest,
    )
    from curvature_console.presentation.browser_bridge_worker import (
        BrowserBridgeWorker,
    )

    worker = BrowserBridgeWorker(
        BrowserBridgeConfig.default(),
        BrowserExchangeRequest(
            department_id="core",
            message_text="task",
            create_new_thread=False,
            conversation_url="https://chatgpt.com/c/example",
        ),
    )

    assert hasattr(worker, "route_unverified")


def test_route_unverified_preserves_response_without_changing_route(
    tmp_path,
    monkeypatch,
) -> None:
    create_application(["curvature-console-route-diagnostic-test"])
    window = MainWindow(
        state_path=tmp_path / "state.sqlite3",
        data_directory=tmp_path / "data",
    )
    panel = window.department_panels["core"]
    original_route = window.state_store.load_chat_route("core")
    assert original_route is not None
    window._pending_tasks["core"] = "Diagnostic task"
    monkeypatch.setattr(
        "curvature_console.presentation.main_window.QMessageBox.warning",
        lambda *args, **kwargs: QMessageBox.StandardButton.Ok,
    )

    window._handle_browser_route_unverified(
        "core",
        "https://chatgpt.com/g/observed-route",
        "Observed response",
    )

    transcript = panel.conversation_view.toPlainText()
    assert "Diagnostic task" in transcript
    assert "Observed response" in transcript
    unchanged_route = window.state_store.load_chat_route("core")
    assert unchanged_route == original_route
    window.close()
