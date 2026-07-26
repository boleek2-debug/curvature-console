"""Application foundation tests."""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from curvature_console import __version__
from curvature_console.main import (
    APPLICATION_NAME,
    PROJECT_ROOT,
    MainWindow,
    create_application,
    create_main_window,
)


def test_package_version() -> None:
    assert __version__ == "0.1.0"


def test_project_root_points_to_repository_root() -> None:
    assert (PROJECT_ROOT / "pyproject.toml").is_file()


def test_application_and_main_window_can_be_created() -> None:
    application = create_application(["curvature-console-test"])

    assert isinstance(application, QApplication)
    assert application.applicationName() == APPLICATION_NAME

    window = create_main_window()

    assert isinstance(window, MainWindow)
    assert window.windowTitle() == APPLICATION_NAME
    assert window.centralWidget() is not None

    window.close()


def test_main_window_accepts_explicit_directories(tmp_path: Path) -> None:
    application = create_application(["curvature-console-path-test"])
    config_directory = tmp_path / "config"
    data_directory = tmp_path / "data"

    window = create_main_window(
        state_path=data_directory / "state.sqlite3",
        data_directory=data_directory,
        config_directory=config_directory,
    )

    assert isinstance(application, QApplication)
    assert window.config_directory == config_directory
    assert window.data_directory == data_directory
    window.close()


def test_main_configures_runtime_logging_before_window_creation(
    tmp_path,
    monkeypatch,
) -> None:
    import curvature_console.main as main_module

    captured = {}

    monkeypatch.setattr(main_module, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        main_module,
        "configure_runtime_logging",
        lambda data_directory: captured.setdefault(
            "log_path", data_directory / "logs" / "console-test.log"
        ),
    )

    class FakeApplication:
        def exec(self):
            return 0

    class FakeWindow:
        def show(self):
            captured["shown"] = True

    monkeypatch.setattr(
        main_module,
        "create_application",
        lambda: FakeApplication(),
    )
    monkeypatch.setattr(
        main_module,
        "create_main_window",
        lambda **kwargs: FakeWindow(),
    )

    assert main_module.main() == 0
    assert captured["log_path"] == (
        tmp_path / "data" / "logs" / "console-test.log"
    )
    assert captured["shown"] is True
