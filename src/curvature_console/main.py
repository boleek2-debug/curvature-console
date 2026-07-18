"""Application entry point for Curvature Console."""

from __future__ import annotations

import sys
from collections.abc import Sequence

from PySide6.QtWidgets import QApplication, QLabel, QMainWindow


APPLICATION_NAME = "Curvature Console"


class MainWindow(QMainWindow):
    """Minimal desktop window for the application foundation sprint."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APPLICATION_NAME)
        self.resize(1200, 720)

        placeholder = QLabel(
            "Curvature Console\n\n"
            "Project | Core | Research\n\n"
            "ASSISTANT-001B1 foundation is operational."
        )
        placeholder.setObjectName("foundationPlaceholder")
        placeholder.setMargin(24)
        self.setCentralWidget(placeholder)


def create_application(argv: Sequence[str] | None = None) -> QApplication:
    """Return the single QApplication instance for the current process."""

    existing = QApplication.instance()
    if existing is not None:
        return existing

    arguments = list(argv) if argv is not None else sys.argv
    application = QApplication(arguments)
    application.setApplicationName(APPLICATION_NAME)
    return application


def create_main_window() -> MainWindow:
    """Create the main Curvature Console window."""

    return MainWindow()


def main() -> int:
    """Launch Curvature Console."""

    application = create_application()
    window = create_main_window()
    window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
