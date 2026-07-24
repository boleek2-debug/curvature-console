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
    request_id = "request-success"
    from curvature_console.presentation.main_window import (
        PendingBrowserExchange,
    )
    window._pending_exchanges[request_id] = PendingBrowserExchange(
        request_id=request_id,
        department_id="core",
        user_task="Exact user task.",
    )

    window._handle_browser_success(
        request_id,
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
            request_id="request-signal-test",
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
    request_id = "request-route-unverified"
    from curvature_console.presentation.main_window import (
        PendingBrowserExchange,
    )
    window._pending_exchanges[request_id] = PendingBrowserExchange(
        request_id=request_id,
        department_id="core",
        user_task="Diagnostic task",
    )
    monkeypatch.setattr(
        "curvature_console.presentation.main_window.QMessageBox.warning",
        lambda *args, **kwargs: QMessageBox.StandardButton.Ok,
    )

    window._handle_browser_route_unverified(
        request_id,
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


def test_stale_request_result_is_ignored(tmp_path) -> None:
    create_application(["curvature-console-stale-request-test"])
    window = MainWindow(
        state_path=tmp_path / "state.sqlite3",
        data_directory=tmp_path / "data",
    )
    panel = window.department_panels["core"]
    before = panel.conversation_view.toPlainText()

    window._handle_browser_success(
        "unknown-request",
        "core",
        "Curvature",
        "https://chatgpt.com/g/project/project",
        "https://chatgpt.com/c/core",
        "must not be stored",
    )

    assert panel.conversation_view.toPlainText() == before
    window.close()


def test_request_id_and_department_must_both_match(tmp_path) -> None:
    create_application(["curvature-console-request-binding-test"])
    window = MainWindow(
        state_path=tmp_path / "state.sqlite3",
        data_directory=tmp_path / "data",
    )
    from curvature_console.presentation.main_window import (
        PendingBrowserExchange,
    )

    window._pending_exchanges["request-1"] = PendingBrowserExchange(
        request_id="request-1",
        department_id="core",
        user_task="Core task",
    )

    assert window._pending_exchange("request-1", "core") is not None
    assert window._pending_exchange("request-1", "research") is None
    assert window._pending_exchange("request-2", "core") is None
    window.close()


def test_browser_success_displays_and_persists_generated_download(
    tmp_path,
) -> None:
    from curvature_console.infrastructure.browser_bridge import CapturedDownload
    from curvature_console.presentation.main_window import PendingBrowserExchange

    create_application(["curvature-console-download-success-test"])
    state_path = tmp_path / "state.sqlite3"
    window = MainWindow(state_path=state_path, data_directory=tmp_path / "data")
    request_id = "request-download"
    saved_path = tmp_path / "download-inbox" / "result.zip"
    saved_path.parent.mkdir()
    saved_path.write_bytes(b"zip")
    window._pending_exchanges[request_id] = PendingBrowserExchange(
        request_id=request_id,
        department_id="core",
        user_task="Create a file.",
    )

    window._handle_browser_success(
        request_id,
        "core",
        "Curvature",
        "https://chatgpt.com/g/project/project",
        "https://chatgpt.com/c/core",
        "File created.",
        (
            CapturedDownload(
                original_filename="result.zip",
                saved_path=saved_path,
                source_url="sandbox:/mnt/data/result.zip",
            ),
        ),
    )

    panel = window.department_panels["core"]
    assert panel.download_label.text() == "Downloads: 1"
    assert "result.zip" in panel.download_list.item(0).text()
    assert window.state_store.load_generated_downloads("core")[0].saved_path == saved_path

    window.close()


def test_red_pressure_warns_before_regular_task(monkeypatch) -> None:
    create_application(["curvature-console-red-task-warning-test"])
    window = MainWindow()
    panel = window.department_panels["core"]
    panel.input_editor.setPlainText(
        "x" * (panel.thread_pressure_estimator.RED_THRESHOLD * 4)
    )
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

    window.prepare_transfer_package("core", "task")
    assert captured == []

    monkeypatch.setattr(
        "curvature_console.presentation.main_window.QMessageBox.warning",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    window.prepare_transfer_package("core", "task")
    assert len(captured) == 1
    assert captured[0].mode is TransferPackageMode.TASK
    window.close()


def test_verified_handoff_starts_fresh_active_transcript(tmp_path) -> None:
    create_application(["curvature-console-handoff-reset-test"])
    window = MainWindow(
        state_path=tmp_path / "state.sqlite3",
        data_directory=tmp_path / "data",
    )
    panel = window.department_panels["core"]
    panel.conversation_view.setPlainText("old thread " * 30_000)
    old_estimate = panel.thread_pressure_snapshot.estimated_tokens

    from curvature_console.presentation.main_window import (
        PendingBrowserExchange,
    )

    request_id = "request-handoff-success"
    window._pending_exchanges[request_id] = PendingBrowserExchange(
        request_id=request_id,
        department_id="core",
        user_task="Continue from handoff.",
        mode=TransferPackageMode.THREAD_HANDOFF,
    )

    window._handle_browser_success(
        request_id,
        "core",
        "Curvature",
        "https://chatgpt.com/g/project/project",
        "https://chatgpt.com/c/new-core-thread",
        "HANDOFF_ACCEPTED",
    )

    transcript = panel.conversation_view.toPlainText()
    assert transcript.startswith("=== NEW THREAD AFTER HANDOFF ===")
    assert "old thread" not in transcript
    assert "HANDOFF_ACCEPTED" in transcript
    assert panel.thread_pressure_snapshot.estimated_tokens < old_estimate
    assert panel.thread_pressure_snapshot.level.value == "GREEN"

    route = window.state_store.load_chat_route("core")
    assert route is not None
    assert route.active_conversation_url == (
        "https://chatgpt.com/c/new-core-thread"
    )
    window.close()
