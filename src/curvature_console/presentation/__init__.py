"""Presentation layer for Curvature Console.

Presentation exports are loaded lazily so infrastructure modules may import
small presentation value objects without initialising MainWindow and creating
a circular import.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any


_EXPORTS: dict[str, tuple[str, str]] = {
    "AttachmentList": (
        "curvature_console.presentation.attachment_list",
        "AttachmentList",
    ),
    "AttachmentRecord": (
        "curvature_console.presentation.attachment_record",
        "AttachmentRecord",
    ),
    "ContextPreviewDialog": (
        "curvature_console.presentation.context_preview_dialog",
        "ContextPreviewDialog",
    ),
    "DepartmentPanel": (
        "curvature_console.presentation.department_panel",
        "DepartmentPanel",
    ),
    "MainWindow": (
        "curvature_console.presentation.main_window",
        "MainWindow",
    ),
}

__all__ = list(_EXPORTS)


def __getattr__(name: str) -> Any:
    """Load public presentation objects only when requested."""

    target = _EXPORTS.get(name)
    if target is None:
        raise AttributeError(
            f"module {__name__!r} has no attribute {name!r}"
        )

    module_name, attribute_name = target
    value = getattr(import_module(module_name), attribute_name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted((*globals(), *__all__))
