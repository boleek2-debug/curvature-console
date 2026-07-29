"""Supervised controls for persisted interdepartmental handoffs."""

from __future__ import annotations

from uuid import uuid4

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from curvature_console.infrastructure.handoff import (
    HandoffRecord,
    HandoffStatus,
    HandoffTransitionError,
    HandoffValidationError,
    create_handoff,
)
from curvature_console.infrastructure.state_store import SQLiteStateStore


_DEPARTMENT_LABELS = {
    "project": "Curvature Project",
    "core": "Curvature Core",
    "research": "Curvature Research",
}


class HandoffControlsDialog(QDialog):
    """Create, supervise and explicitly request one handoff delivery."""

    deliver_requested = Signal(str)

    """Create and supervise handoffs without sending browser messages."""

    def __init__(
        self,
        state_store: SQLiteStateStore,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.state_store = state_store
        self._records: tuple[HandoffRecord, ...] = ()
        self.setWindowTitle("B5.5B Bridge Controls")
        self.resize(980, 650)

        self.handoff_list = QListWidget()
        self.handoff_list.setObjectName("handoffList")
        self.handoff_list.currentRowChanged.connect(self._show_selected)

        self.source_combo = QComboBox()
        self.source_combo.setObjectName("handoffSource")
        self.target_combo = QComboBox()
        self.target_combo.setObjectName("handoffTarget")
        for department_id, label in _DEPARTMENT_LABELS.items():
            self.source_combo.addItem(label, department_id)
            self.target_combo.addItem(label, department_id)
        self.target_combo.setCurrentIndex(1)

        self.message_editor = QPlainTextEdit()
        self.message_editor.setObjectName("handoffMessage")
        self.message_editor.setPlaceholderText(
            "Visible instruction for the target department..."
        )
        self.message_editor.setMaximumHeight(120)

        self.status_label = QLabel("No handoff selected")
        self.status_label.setObjectName("handoffStatus")

        self.timeline_view = QPlainTextEdit()
        self.timeline_view.setObjectName("handoffTimeline")
        self.timeline_view.setReadOnly(True)

        self.new_button = QPushButton("Create Draft")
        self.new_button.setObjectName("createHandoffButton")
        self.new_button.clicked.connect(self.create_draft)

        self.edit_button = QPushButton("Save Edit")
        self.edit_button.setObjectName("editHandoffButton")
        self.edit_button.clicked.connect(self.edit_selected)

        self.submit_button = QPushButton("Request Approval")
        self.submit_button.setObjectName("submitHandoffButton")
        self.submit_button.clicked.connect(
            lambda: self._transition_selected(
                HandoffStatus.PENDING_APPROVAL
            )
        )

        self.approve_button = QPushButton("Approve")
        self.approve_button.setObjectName("approveHandoffButton")
        self.approve_button.clicked.connect(
            lambda: self._transition_selected(HandoffStatus.APPROVED)
        )

        self.reject_button = QPushButton("Reject")
        self.reject_button.setObjectName("rejectHandoffButton")
        self.reject_button.clicked.connect(
            lambda: self._transition_selected(HandoffStatus.REJECTED)
        )

        self.hold_button = QPushButton("Hold")
        self.hold_button.setObjectName("holdHandoffButton")
        self.hold_button.clicked.connect(
            lambda: self._transition_selected(HandoffStatus.HELD)
        )

        self.redirect_button = QPushButton("Redirect")
        self.redirect_button.setObjectName("redirectHandoffButton")
        self.redirect_button.clicked.connect(self.redirect_selected)

        self.deliver_button = QPushButton("Deliver")
        self.deliver_button.setObjectName("deliverHandoffButton")
        self.deliver_button.setToolTip(
            "Send this approved handoff once to the target department."
        )
        self.deliver_button.clicked.connect(self.deliver_selected)

        self.stop_button = QPushButton("Stop")
        self.stop_button.setObjectName("stopHandoffButton")
        self.stop_button.clicked.connect(
            lambda: self._transition_selected(HandoffStatus.STOPPED)
        )

        form = QFormLayout()
        form.addRow("Source", self.source_combo)
        form.addRow("Target", self.target_combo)
        form.addRow("Instruction", self.message_editor)

        control_row = QHBoxLayout()
        for button in (
            self.new_button,
            self.edit_button,
            self.submit_button,
            self.approve_button,
            self.reject_button,
            self.hold_button,
            self.redirect_button,
            self.deliver_button,
            self.stop_button,
        ):
            control_row.addWidget(button)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.addWidget(self.status_label)
        right_layout.addLayout(form)
        right_layout.addLayout(control_row)
        right_layout.addWidget(QLabel("Complete visible timeline"))
        right_layout.addWidget(self.timeline_view, 1)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.handoff_list)
        splitter.addWidget(right)
        splitter.setSizes([300, 680])

        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel(
                "Supervised controls only — no browser message is sent "
                "from this dialog."
            )
        )
        layout.addWidget(splitter, 1)

        self.reload()

    @property
    def selected_record(self) -> HandoffRecord | None:
        row = self.handoff_list.currentRow()
        if row < 0 or row >= len(self._records):
            return None
        return self._records[row]

    def reload(self, selected_handoff_id: str | None = None) -> None:
        self._records = self.state_store.load_handoffs()
        self.handoff_list.clear()
        selected_row = -1
        for index, record in enumerate(self._records):
            self.handoff_list.addItem(
                f"{record.status.value.upper()} · "
                f"{record.source_department_id} → "
                f"{record.target_department_id} · "
                f"{record.user_visible_message[:55]}"
            )
            if record.handoff_id == selected_handoff_id:
                selected_row = index
        if selected_row >= 0:
            self.handoff_list.setCurrentRow(selected_row)
        elif self._records:
            self.handoff_list.setCurrentRow(0)
        else:
            self._show_selected(-1)

    def create_draft(self) -> None:
        try:
            record = create_handoff(
                request_id=f"handoff-ui-{uuid4().hex}",
                source_department_id=self.source_combo.currentData(),
                target_department_id=self.target_combo.currentData(),
                user_visible_message=self.message_editor.toPlainText(),
            )
            record = record.append_message(
                record.source_department_id,
                "Draft created: " + record.user_visible_message,
            )
            self.state_store.save_handoff(record)
            self.reload(record.handoff_id)
        except HandoffValidationError as exc:
            self._show_error(str(exc))

    def edit_selected(self) -> None:
        record = self.selected_record
        if record is None:
            return
        try:
            updated = record.edit_visible_message(
                self.message_editor.toPlainText()
            )
            updated = updated.append_message(
                updated.source_department_id,
                "Draft instruction edited: "
                + updated.user_visible_message,
            )
            self.state_store.save_handoff(updated)
            self.reload(updated.handoff_id)
        except (HandoffValidationError, HandoffTransitionError) as exc:
            self._show_error(str(exc))

    def redirect_selected(self) -> None:
        record = self.selected_record
        if record is None:
            return
        try:
            updated = record.redirect(self.target_combo.currentData())
            updated = updated.append_message(
                updated.source_department_id,
                "Redirected to "
                + _DEPARTMENT_LABELS[updated.target_department_id],
            )
            self.state_store.save_handoff(updated)
            self.reload(updated.handoff_id)
        except (HandoffValidationError, HandoffTransitionError) as exc:
            self._show_error(str(exc))

    def deliver_selected(self) -> None:
        """Request exactly one delivery of an approved handoff."""

        record = self.selected_record
        if record is None:
            return
        if record.status is not HandoffStatus.APPROVED:
            self._show_error("Only an approved handoff may be delivered.")
            return
        self.deliver_requested.emit(record.handoff_id)

    def _transition_selected(self, status: HandoffStatus) -> None:
        record = self.selected_record
        if record is None:
            return
        try:
            updated = record.transition(status)
            updated = updated.append_message(
                updated.source_department_id,
                f"Control action: {status.value}",
            )
            self.state_store.save_handoff(updated)
            self.reload(updated.handoff_id)
        except HandoffTransitionError as exc:
            self._show_error(str(exc))

    def _show_selected(self, row: int) -> None:
        record = self.selected_record
        if record is None:
            self.status_label.setText("No handoff selected")
            self.timeline_view.clear()
            self._update_controls(None)
            return

        self.status_label.setText(
            f"{record.handoff_id} · STATUS: {record.status.value.upper()}"
        )
        self.source_combo.setCurrentIndex(
            self.source_combo.findData(record.source_department_id)
        )
        self.target_combo.setCurrentIndex(
            self.target_combo.findData(record.target_department_id)
        )
        self.message_editor.setPlainText(record.user_visible_message)
        self.timeline_view.setPlainText(
            "\n\n".join(
                f"[{message.sequence}] {message.created_at}\n"
                f"{message.author_department_id.upper()}: {message.body}"
                for message in record.timeline
            )
        )
        self._update_controls(record)

    def _update_controls(self, record: HandoffRecord | None) -> None:
        status = record.status if record is not None else None
        self.edit_button.setEnabled(status is HandoffStatus.DRAFT)
        self.submit_button.setEnabled(status is HandoffStatus.DRAFT)
        self.approve_button.setEnabled(
            status is HandoffStatus.PENDING_APPROVAL
        )
        self.reject_button.setEnabled(
            status
            in {
                HandoffStatus.DRAFT,
                HandoffStatus.PENDING_APPROVAL,
            }
        )
        self.hold_button.setEnabled(
            status
            in {
                HandoffStatus.PENDING_APPROVAL,
                HandoffStatus.APPROVED,
                HandoffStatus.SENT,
                HandoffStatus.RECEIVED,
                HandoffStatus.ANSWERED,
            }
        )
        self.redirect_button.setEnabled(
            status
            in {
                HandoffStatus.DRAFT,
                HandoffStatus.PENDING_APPROVAL,
                HandoffStatus.HELD,
            }
        )
        self.deliver_button.setEnabled(
            status is HandoffStatus.APPROVED
        )
        self.stop_button.setEnabled(
            record is not None and not record.is_terminal
        )

    def _show_error(self, message: str) -> None:
        QMessageBox.warning(self, "Handoff action rejected", message)
