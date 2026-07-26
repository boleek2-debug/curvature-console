"""Runtime file logging for Curvature Console."""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path

LOGGER_NAME = "curvature_console"


def configure_runtime_logging(data_directory: Path) -> Path:
    """Configure one timestamped log file for the current application run."""

    log_directory = data_directory / "logs"
    log_directory.mkdir(parents=True, exist_ok=True)
    log_path = log_directory / (
        f"console-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"
    )

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    for handler in tuple(logger.handlers):
        logger.removeHandler(handler)
        try:
            handler.close()
        except Exception:
            pass

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logger.info("Curvature Console runtime logging started")
    logger.info("Runtime log file: %s", log_path)
    return log_path


def get_runtime_logger(component: str) -> logging.Logger:
    """Return a component logger under the Curvature Console namespace."""

    return logging.getLogger(f"{LOGGER_NAME}.{component}")
