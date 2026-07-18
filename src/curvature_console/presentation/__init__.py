"""Presentation layer for Curvature Console."""

from curvature_console.presentation.attachment_list import AttachmentList
from curvature_console.presentation.attachment_record import AttachmentRecord
from curvature_console.presentation.context_preview_dialog import (
    ContextPreviewDialog,
)
from curvature_console.presentation.department_panel import DepartmentPanel
from curvature_console.presentation.main_window import MainWindow

__all__ = [
    "AttachmentList",
    "AttachmentRecord",
    "ContextPreviewDialog",
    "DepartmentPanel",
    "MainWindow",
]
