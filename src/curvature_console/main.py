"""Application entry point for Curvature Console."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

from PySide6.QtWidgets import QApplication

from curvature_console.presentation.main_window import MainWindow


APPLICATION_NAME = "Curvature Console"


def create_application(argv: Sequence[str] | None = None) -> QApplication:
    """Return the single QApplication instance for the current process."""

    existing = QApplication.instance()
    if existing is not None:
        return existing

    arguments = list(argv) if argv is not None else sys.argv
    application = QApplication(arguments)
    application.setApplicationName(APPLICATION_NAME)
    return application


def create_main_window(
    state_path: Path | None = None,
    data_directory: Path | None = None,
) -> MainWindow:
    """Create the main Curvature Console window."""

    return MainWindow(
        application_name=APPLICATION_NAME,
        state_path=state_path,
        data_directory=data_directory,
    )


def main() -> int:
    """Launch Curvature Console."""

    application = create_application()
    data_directory = Path.cwd() / "data"
    window = create_main_window(
        state_path=data_directory / "curvature_console.sqlite3",
        data_directory=data_directory,
    )
    window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
