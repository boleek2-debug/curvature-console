"""UI tests for Task and Thread Handoff packages."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from curvature_console.infrastructure.context_loader import ContextLoadResult
from curvature_console.infrastructure.transfer_package import (
    TransferPackage,
    TransferPackageMode,
)
from curvature_console.main import create_application
from curvature_console.presentation.main_window import MainWindow
from curvature_console.presentation.transfer_package_dialog import (
    TransferPackageDialog,
)


def test_each_department_exposes_both_package_buttons() -> None:
    create_application(["curvature-console-transfer-button-test"])
    window = MainWindow()

    for department_id, panel in window.department_panels.items():
        assert panel.task_package_button.isEnabled()
        assert panel.thread_handoff_button.isEnabled()
        assert panel.task_package_button.objectName() == (
            f"{department_id}TaskPackageButton"
        )
        assert panel.thread_handoff_button.objectName() == (
            f"{department_id}ThreadHandoffButton"
        )

    window.close()


def test_dialog_copies_exact_package_text() -> None:
    create_application(["curvature-console-clipboard-test"])
    package = TransferPackage(
        mode=TransferPackageMode.TASK,
        department_id="core",
        text="exact transfer package\n",
        conversation_was_truncated=False,
        truncated_document_count=1,
        included_document_count=2,
        attachment_count=0,
    )
    dialog = TransferPackageDialog("Curvature Core", package)

    dialog.copy_to_clipboard()

    assert QApplication.clipboard().text() == package.text
    assert dialog.copy_button.text() == "Copied"
    assert "Task Package" in dialog.windowTitle()
    dialog.close()


def test_main_window_builds_selected_package_mode(monkeypatch) -> None:
    create_application(["curvature-console-transfer-window-test"])
    window = MainWindow()
    panel = window.department_panels["core"]
    panel.input_editor.setPlainText("Current Core task")
    window.context_results["core"] = ContextLoadResult(
        department_id="core",
        documents=(),
        errors=(),
    )

    captured: list[object] = []

    class FakeDialog:
        def __init__(self, department_title, package, parent=None):
            captured.append(package)

        def exec(self):
            return 0

    monkeypatch.setattr(
        "curvature_console.presentation.main_window.TransferPackageDialog",
        FakeDialog,
    )

    window.prepare_transfer_package("core", "task")
    window.prepare_transfer_package("core", "thread_handoff")

    assert captured[0].mode is TransferPackageMode.TASK
    assert captured[1].mode is TransferPackageMode.THREAD_HANDOFF
    assert "Current Core task" in captured[0].text

    window.close()
