"""Application entry point for Curvature Console."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

from PySide6.QtWidgets import QApplication

from curvature_console.infrastructure.runtime_logging import (
    configure_runtime_logging,
    get_runtime_logger,
)
from curvature_console.presentation.main_window import MainWindow


APPLICATION_NAME = "Curvature Console"
PROJECT_ROOT = Path(__file__).resolve().parents[2]


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
    config_directory: Path | None = None,
) -> MainWindow:
    """Create the main Curvature Console window."""

    return MainWindow(
        application_name=APPLICATION_NAME,
        state_path=state_path,
        data_directory=data_directory,
        config_directory=config_directory,
    )


def main() -> int:
    """Launch Curvature Console from any current working directory."""

    application = create_application()
    data_directory = PROJECT_ROOT / "data"
    log_path = configure_runtime_logging(data_directory)
    logger = get_runtime_logger("main")
    logger.info("Application start")
    logger.info("Project root: %s", PROJECT_ROOT)
    logger.info("Data directory: %s", data_directory)
    logger.info("Runtime log: %s", log_path)

    window = create_main_window(
        state_path=data_directory / "curvature_console.sqlite3",
        data_directory=data_directory,
        config_directory=PROJECT_ROOT / "config" / "workspaces",
    )
    window.show()
    try:
        return application.exec()
    except Exception:
        logger.exception("Unhandled application exception")
        raise
    finally:
        logger.info("Application stopped")


if __name__ == "__main__":
    raise SystemExit(main())
