"""Context preview dialog for one department workspace."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from curvature_console.infrastructure.context_loader import ContextLoadResult


class ContextPreviewDialog(QDialog):
    """Display loaded context and load errors for one workspace."""

    def __init__(
        self,
        title: str,
        result: ContextLoadResult,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.setWindowTitle(f"{title} — Context Preview")
        self.resize(900, 700)

        summary = QLabel(
            f"Loaded documents: {result.loaded_count} · "
            f"Errors: {len(result.errors)}"
        )

        self.preview = QPlainTextEdit()
        self.preview.setObjectName("contextPreviewText")
        self.preview.setReadOnly(True)
        self.preview.setPlainText(result.preview_text())

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(summary)
        layout.addWidget(self.preview, 1)
        layout.addWidget(buttons)
