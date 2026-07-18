"""Reusable department panel for the three-panel desktop shell."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class DepartmentPanel(QFrame):
    """Display one department workspace inside Curvature Console."""

    focus_requested = Signal(str)

    def __init__(
        self,
        department_id: str,
        title: str,
        responsibility: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.department_id = department_id
        self.setObjectName(f"{department_id}Panel")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumWidth(260)

        self.title_label = QLabel(title)
        self.title_label.setObjectName(f"{department_id}Title")

        self.status_label = QLabel("STATUS: READY FOR B2")
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
        self.input_editor.setMaximumHeight(120)

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
        layout.addWidget(self.conversation_view, 1)
        layout.addWidget(self.input_editor)
        layout.addWidget(self.send_button)

    def _request_focus(self) -> None:
        self.focus_requested.emit(self.department_id)
