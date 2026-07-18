"""Application foundation tests."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from curvature_console import __version__
from curvature_console.main import APPLICATION_NAME, MainWindow, create_application


def test_package_version() -> None:
    assert __version__ == "0.1.0"


def test_application_and_main_window_can_be_created() -> None:
    application = create_application(["curvature-console-test"])

    assert isinstance(application, QApplication)
    assert application.applicationName() == APPLICATION_NAME

    window = MainWindow()

    assert window.windowTitle() == APPLICATION_NAME
    assert window.centralWidget() is not None

    window.close()
