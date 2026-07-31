"""Supervised controls for persisted interdepartmental handoffs."""

from __future__ import annotations

from uuid import uuid4

from PySide6.QtCore import QElapsedTimer, QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
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


class HandoffDeliveryProgressDialog(QDialog):
    """Visible stage and elapsed-time feedback for one delivery."""

    def __init__(
        self,
        *,
        target_department_id: str,
        handoff_title: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("handoffDeliveryProgressDialog")
        self.setWindowTitle("Controlled delivery in progress")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setModal(True)
        self.setMinimumWidth(520)
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)

        target_label = _DEPARTMENT_LABELS.get(
            target_department_id,
            target_department_id.upper(),
        )
        self.summary_label = QLabel(
            f"Delivering to {target_label}: {handoff_title}"
        )
        self.summary_label.setObjectName("handoffProgressSummary")
        self.summary_label.setWordWrap(True)

        self.stage_label = QLabel("Preparing controlled delivery…")
        self.stage_label.setObjectName("handoffProgressStage")

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("handoffProgressBar")
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setTextVisible(False)

        self.elapsed_label = QLabel("Elapsed: 00:00")
        self.elapsed_label.setObjectName("handoffProgressElapsed")

        self._elapsed = QElapsedTimer()
        self._elapsed.start()
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._refresh_elapsed)
        self._timer.start()

        layout = QVBoxLayout(self)
        layout.addWidget(self.summary_label)
        layout.addWidget(self.stage_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.elapsed_label)

    def set_stage(self, stage: str) -> None:
        self.stage_label.setText(stage + "…")

    def finish(self) -> None:
        self._timer.stop()
        self.accept()

    def _refresh_elapsed(self) -> None:
        total_seconds = max(0, self._elapsed.elapsed() // 1000)
        minutes, seconds = divmod(total_seconds, 60)
        self.elapsed_label.setText(
            f"Elapsed: {minutes:02d}:{seconds:02d}"
        )


class HandoffDeliveryConfirmationDialog(QDialog):
    """Resizable delivery confirmation with scrollable handoff details."""

    def __init__(
        self,
        *,
        target_department_id: str,
        handoff_title: str,
        handoff_message: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("handoffDeliveryConfirmationDialog")
        self.setWindowTitle("Engage controlled delivery?")
        self.setSizeGripEnabled(True)
        self.setMinimumSize(520, 360)
        self.resize(760, 520)

        target_label = _DEPARTMENT_LABELS.get(
            target_department_id,
            target_department_id.upper(),
        )
        self.summary_label = QLabel(
            "Send this approved handoff exactly once to "
            f"{target_label}?"
        )
        self.summary_label.setObjectName("handoffDeliverySummary")
        self.summary_label.setWordWrap(True)

        title_label = QLabel(handoff_title)
        title_label.setObjectName("handoffDeliveryTitle")
        title_label.setWordWrap(True)
        title_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        details = QPlainTextEdit()
        details.setObjectName("handoffDeliveryDetails")
        details.setReadOnly(True)
        details.setPlainText(handoff_message)
        details.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Yes
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.setObjectName("handoffDeliveryButtons")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        yes_button = buttons.button(QDialogButtonBox.StandardButton.Yes)
        if yes_button is not None:
            yes_button.setText("Deliver once")
            yes_button.setDefault(False)
        cancel_button = buttons.button(
            QDialogButtonBox.StandardButton.Cancel
        )
        if cancel_button is not None:
            cancel_button.setDefault(True)
            cancel_button.setFocus()

        layout = QVBoxLayout(self)
        layout.addWidget(self.summary_label)
        layout.addWidget(title_label)
        layout.addWidget(details, 1)
        layout.addWidget(buttons)


def confirm_handoff_return(
    *,
    parent: QWidget | None,
    source_department_id: str,
    reply_text: str,
) -> bool:
    """Return whether the operator approved one reply return."""

    dialog = HandoffDeliveryConfirmationDialog(
        target_department_id=source_department_id,
        handoff_title="Return captured reply to source",
        handoff_message=reply_text,
        parent=parent,
    )
    dialog.setWindowTitle("Return captured reply?")
    dialog.summary_label.setText(
        "Return this captured target reply exactly once to "
        + _DEPARTMENT_LABELS.get(
            source_department_id, source_department_id.upper()
        )
        + "?"
    )
    buttons = dialog.findChild(QDialogButtonBox, "handoffDeliveryButtons")
    if buttons is not None:
        yes_button = buttons.button(QDialogButtonBox.StandardButton.Yes)
        if yes_button is not None:
            yes_button.setText("Return once")
    return dialog.exec() == QDialog.DialogCode.Accepted

class HandoffUpdateDialog(QDialog):
    """Edit and explicitly approve one same-handoff progress update."""

    def __init__(
        self,
        *,
        target_department_id: str,
        handoff_title: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("handoffUpdateDialog")
        self.setWindowTitle("Send same-handoff progress update?")
        self.setSizeGripEnabled(True)
        self.setMinimumSize(560, 420)
        self.resize(780, 560)

        target_label = _DEPARTMENT_LABELS.get(
            target_department_id, target_department_id.upper()
        )
        summary = QLabel(
            "Send one operator-approved progress update to "
            f"{target_label} while preserving the current handoff?"
        )
        summary.setWordWrap(True)

        title = QLabel(handoff_title)
        title.setObjectName("handoffUpdateTitle")
        title.setWordWrap(True)

        self.update_editor = QPlainTextEdit()
        self.update_editor.setObjectName("handoffUpdateEditor")
        self.update_editor.setPlaceholderText(
            "Enter evidence, decisions, blockers or instructions for the "
            "next target-department step..."
        )

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Yes
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.setObjectName("handoffUpdateButtons")
        buttons.accepted.connect(self._accept_non_empty)
        buttons.rejected.connect(self.reject)
        send_button = buttons.button(QDialogButtonBox.StandardButton.Yes)
        if send_button is not None:
            send_button.setText("Send update once")
            send_button.setDefault(False)
        cancel_button = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if cancel_button is not None:
            cancel_button.setDefault(True)
            cancel_button.setFocus()

        layout = QVBoxLayout(self)
        layout.addWidget(summary)
        layout.addWidget(title)
        layout.addWidget(self.update_editor, 1)
        layout.addWidget(buttons)

    @property
    def update_text(self) -> str:
        return self.update_editor.toPlainText().strip()

    def _accept_non_empty(self) -> None:
        if not self.update_text:
            QMessageBox.warning(
                self,
                "Progress update required",
                "Enter the progress update before sending it.",
            )
            return
        self.accept()


def request_handoff_update(
    *,
    parent: QWidget | None,
    target_department_id: str,
    handoff_message: str,
) -> str | None:
    """Return one explicitly approved update, or None when cancelled."""

    first_line = handoff_message.splitlines()[0] if handoff_message else ""
    title = first_line.lstrip("# ").strip() or "Open handoff"
    dialog = HandoffUpdateDialog(
        target_department_id=target_department_id,
        handoff_title=title,
        parent=parent,
    )
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None
    return dialog.update_text

def confirm_handoff_delivery(
    *,
    parent: QWidget | None,
    target_department_id: str,
    handoff_message: str,
) -> bool:
    """Return whether the operator explicitly confirmed one delivery."""

    first_line = handoff_message.splitlines()[0] if handoff_message else ""
    handoff_title = first_line.lstrip("# " ).strip() or "Approved handoff"
    dialog = HandoffDeliveryConfirmationDialog(
        target_department_id=target_department_id,
        handoff_title=handoff_title,
        handoff_message=handoff_message,
        parent=parent,
    )
    return dialog.exec() == QDialog.DialogCode.Accepted


class HandoffControlsDialog(QDialog):
    """Create, supervise and explicitly request one handoff delivery."""

    deliver_requested = Signal(str)
    return_requested = Signal(str)
    update_requested = Signal(str, str)

    """Create and supervise handoffs without sending browser messages."""

    def __init__(
        self,
        state_store: SQLiteStateStore,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.state_store = state_store
        self._records: tuple[HandoffRecord, ...] = ()
        self.setWindowTitle("Supervised Communication Hub")
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

        self.continue_button = QPushButton("Continue in Target")
        self.continue_button.setObjectName("continueHandoffButton")
        self.continue_button.setToolTip(
            "Accept this reply as a progress update and keep the handoff open."
        )
        self.continue_button.clicked.connect(
            lambda: self._transition_selected(HandoffStatus.IN_PROGRESS)
        )

        self.update_button = QPushButton("Send Update to Target")
        self.update_button.setObjectName("updateHandoffButton")
        self.update_button.setToolTip(
            "Send one supervised progress update to the target while "
            "keeping the same handoff open."
        )
        self.update_button.clicked.connect(self.update_selected)

        self.return_button = QPushButton("Return to Source")
        self.return_button.setObjectName("returnHandoffButton")
        self.return_button.setToolTip(
            "Return the latest captured target reply once to the source department."
        )
        self.return_button.clicked.connect(self.return_selected)

        self.close_button = QPushButton("Close")
        self.close_button.setObjectName("closeHandoffButton")
        self.close_button.setToolTip(
            "Close this handoff only when the requested work is complete."
        )
        self.close_button.clicked.connect(
            lambda: self._transition_selected(HandoffStatus.CLOSED)
        )

        self.stop_button = QPushButton("Stop")
        self.stop_button.setObjectName("stopHandoffButton")
        self.stop_button.clicked.connect(
            lambda: self._transition_selected(HandoffStatus.STOPPED)
        )

        form = QFormLayout()
        form.addRow("Source", self.source_combo)
        form.addRow("Target", self.target_combo)
        form.addRow("Instruction", self.message_editor)

        preparation_row = QHBoxLayout()
        for button in (
            self.new_button,
            self.edit_button,
            self.submit_button,
            self.approve_button,
            self.reject_button,
            self.redirect_button,
        ):
            preparation_row.addWidget(button)

        decision_row = QHBoxLayout()
        for button in (
            self.deliver_button,
            self.continue_button,
            self.update_button,
            self.return_button,
            self.hold_button,
            self.close_button,
            self.stop_button,
        ):
            decision_row.addWidget(button)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.addWidget(self.status_label)
        right_layout.addLayout(form)
        right_layout.addLayout(preparation_row)
        right_layout.addLayout(decision_row)
        right_layout.addWidget(QLabel("Complete visible timeline"))
        right_layout.addWidget(self.timeline_view, 1)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.handoff_list)
        splitter.addWidget(right)
        splitter.setSizes([300, 680])

        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel(
                "Department-generated drafts appear here automatically. "
                "Nothing crosses a department boundary without your explicit "
                "approval and delivery confirmation."
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
            first_line = record.user_visible_message.splitlines()[0]
            summary = first_line.lstrip("# ").strip()
            self.handoff_list.addItem(
                f"{record.status.value.upper()} · "
                f"{record.source_department_id} → "
                f"{record.target_department_id} · "
                f"{summary[:55]}"
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

    def update_selected(self) -> None:
        """Request one same-handoff progress update to the target."""

        record = self.selected_record
        if record is None:
            return
        if record.status is not HandoffStatus.IN_PROGRESS:
            self._show_error(
                "Only an in-progress handoff may receive a progress update."
            )
            return
        update_text = request_handoff_update(
            parent=self,
            target_department_id=record.target_department_id,
            handoff_message=record.user_visible_message,
        )
        if update_text is None:
            return
        self.update_requested.emit(record.handoff_id, update_text)

    def return_selected(self) -> None:
        """Request one supervised return of the latest target reply."""

        record = self.selected_record
        if record is None:
            return
        if record.status not in {
            HandoffStatus.AWAITING_USER_DECISION,
            HandoffStatus.ANSWERED,
        }:
            self._show_error(
                "Only a captured reply awaiting decision may be returned."
            )
            return
        self.return_requested.emit(record.handoff_id)

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
                HandoffStatus.AWAITING_USER_DECISION,
                HandoffStatus.IN_PROGRESS,
                HandoffStatus.UPDATE_SENT,
                HandoffStatus.RETURN_SENT,
                HandoffStatus.RETURNED,
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
        self.continue_button.setEnabled(
            status
            in {
                HandoffStatus.AWAITING_USER_DECISION,
                HandoffStatus.ANSWERED,
                HandoffStatus.RETURNED,
            }
        )
        self.update_button.setEnabled(
            status is HandoffStatus.IN_PROGRESS
        )
        self.return_button.setEnabled(
            status
            in {
                HandoffStatus.AWAITING_USER_DECISION,
                HandoffStatus.ANSWERED,
            }
        )
        self.close_button.setEnabled(
            status
            in {
                HandoffStatus.AWAITING_USER_DECISION,
                HandoffStatus.ANSWERED,
                HandoffStatus.IN_PROGRESS,
                HandoffStatus.RETURNED,
            }
        )
        self.stop_button.setEnabled(
            record is not None and not record.is_terminal
        )

    def _show_error(self, message: str) -> None:
        QMessageBox.warning(self, "Handoff action rejected", message)
