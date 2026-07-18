"""Reusable department panel for the three-panel desktop shell."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from curvature_console.infrastructure.context_loader import ContextLoadResult
from curvature_console.presentation.attachment_list import AttachmentList


class DepartmentPanel(QFrame):
    """Display one department workspace inside Curvature Console."""

    focus_requested = Signal(str)
    context_refresh_requested = Signal(str)
    context_preview_requested = Signal(str)
    workspace_state_changed = Signal(str)

    def __init__(
        self,
        department_id: str,
        title: str,
        responsibility: str,
        attachment_storage_dir: Path | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.department_id = department_id
        self.setObjectName(f"{department_id}Panel")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumWidth(300)

        self.title_label = QLabel(title)
        self.title_label.setObjectName(f"{department_id}Title")

        self.status_label = QLabel("STATUS: READY")
        self.status_label.setObjectName(f"{department_id}Status")

        self.responsibility_label = QLabel(responsibility)
        self.responsibility_label.setObjectName(f"{department_id}Responsibility")
        self.responsibility_label.setWordWrap(True)

        self.focus_button = QPushButton("Focus")
        self.focus_button.setObjectName(f"{department_id}FocusButton")
        self.focus_button.clicked.connect(self._request_focus)

        header_layout = QHBoxLayout()
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.focus_button)

        self.context_label = QLabel("Context: not loaded")
        self.context_label.setObjectName(f"{department_id}ContextStatus")

        self.context_files = QListWidget()
        self.context_files.setObjectName(f"{department_id}ContextFiles")
        self.context_files.setMaximumHeight(92)

        self.refresh_context_button = QPushButton("Refresh Context")
        self.refresh_context_button.setObjectName(
            f"{department_id}RefreshContextButton"
        )
        self.refresh_context_button.clicked.connect(
            self._request_context_refresh
        )

        self.preview_context_button = QPushButton("Preview Context")
        self.preview_context_button.setObjectName(
            f"{department_id}PreviewContextButton"
        )
        self.preview_context_button.setEnabled(False)
        self.preview_context_button.clicked.connect(
            self._request_context_preview
        )

        context_button_layout = QHBoxLayout()
        context_button_layout.addWidget(self.refresh_context_button)
        context_button_layout.addWidget(self.preview_context_button)

        self.conversation_view = QPlainTextEdit()
        self.conversation_view.setObjectName(f"{department_id}Conversation")
        self.conversation_view.setReadOnly(True)
        self.conversation_view.setPlainText(
            f"{title} workspace is operational.\n\n"
            f"Responsibility: {responsibility}"
        )

        self.input_editor = QPlainTextEdit()
        self.input_editor.setObjectName(f"{department_id}Input")
        self.input_editor.setPlaceholderText(f"Message {title}...")
        self.input_editor.setMaximumHeight(110)
        self.input_editor.textChanged.connect(self._notify_state_changed)

        self.attachment_list = AttachmentList(
            department_id=department_id,
            attachment_storage_dir=attachment_storage_dir,
        )
        self.attachment_list.attachment_count_changed.connect(
            self._update_attachment_status
        )
        self.attachment_list.attachments_changed.connect(
            self._notify_state_changed
        )

        self.send_button = QPushButton("Send")
        self.send_button.setObjectName(f"{department_id}SendButton")
        self.send_button.setEnabled(False)
        self.send_button.setToolTip(
            "AI integration will be added in ASSISTANT-001B5."
        )

        layout = QVBoxLayout(self)
        layout.addLayout(header_layout)
        layout.addWidget(self.status_label)
        layout.addWidget(self.responsibility_label)
        layout.addWidget(self.context_label)
        layout.addWidget(self.context_files)
        layout.addLayout(context_button_layout)
        layout.addWidget(self.conversation_view, 1)
        layout.addWidget(self.input_editor)
        layout.addWidget(self.attachment_list)
        layout.addWidget(self.send_button)

    def set_context_result(self, result: ContextLoadResult) -> None:
        """Display the current context loading result."""

        self.context_files.clear()

        for document in result.documents:
            self.context_files.addItem(document.label)

        self.context_label.setText(
            f"Context: {result.loaded_count} loaded · "
            f"{len(result.errors)} errors"
        )
        self.preview_context_button.setEnabled(
            bool(result.documents or result.errors)
        )

    def _request_focus(self) -> None:
        self.focus_requested.emit(self.department_id)

    def _request_context_refresh(self) -> None:
        self.context_refresh_requested.emit(self.department_id)

    def _request_context_preview(self) -> None:
        self.context_preview_requested.emit(self.department_id)

    def _notify_state_changed(self) -> None:
        self.workspace_state_changed.emit(self.department_id)

    def _update_attachment_status(self, count: int) -> None:
        if count == 0:
            self.status_label.setText("STATUS: READY")
        else:
            self.status_label.setText(f"STATUS: READY · {count} ATTACHED")
