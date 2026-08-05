"""Review durable interdepartmental operational conversations."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from curvature_console.infrastructure.state_store import (
    OperationalConversationRecord,
    SQLiteStateStore,
)


class OperationalConversationsDialog(QDialog):
    """Display transcripts and collect one operator review decision."""

    review_action_requested = Signal(str, str, str)

    REVIEWABLE_STATUSES = {
        "RESULT_READY",
        "BLOCKED",
        "AWAITING_OPERATOR_DECISION",
        "REJECTED",
    }

    def __init__(
        self,
        *,
        state_store: SQLiteStateStore,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.state_store = state_store
        self.setWindowTitle("Operational Conversations")
        self.resize(1100, 760)

        self.conversation_list = QListWidget()
        self.conversation_list.setObjectName("operationalConversationList")
        self.conversation_list.currentItemChanged.connect(
            self._show_selected_conversation
        )

        self.summary_label = QLabel("Select a conversation")
        self.summary_label.setObjectName("operationalConversationSummary")
        self.summary_label.setWordWrap(True)

        self.transcript = QTextBrowser()
        self.transcript.setObjectName("operationalConversationTranscript")
        self.transcript.setOpenExternalLinks(False)

        self.review_note = QTextEdit()
        self.review_note.setObjectName("operationalConversationReviewNote")
        self.review_note.setPlaceholderText(
            "Optional for Accept. Required for Reject and Ask / Continue."
        )
        self.review_note.setMaximumHeight(110)

        self.validation_label = QLabel("")
        self.validation_label.setObjectName("operationalConversationValidation")
        self.validation_label.setWordWrap(True)

        self.accept_button = QPushButton("Accept")
        self.accept_button.setObjectName("acceptOperationalConversationButton")
        self.accept_button.clicked.connect(
            lambda: self._submit_review_action("ACCEPT")
        )

        self.reject_button = QPushButton("Reject")
        self.reject_button.setObjectName("rejectOperationalConversationButton")
        self.reject_button.clicked.connect(
            lambda: self._submit_review_action("REJECT")
        )

        self.ask_button = QPushButton("Ask / Continue")
        self.ask_button.setObjectName("askOperationalConversationButton")
        self.ask_button.clicked.connect(
            lambda: self._submit_review_action("ASK")
        )

        refresh_button = QPushButton("Refresh")
        refresh_button.setObjectName("refreshOperationalConversationsButton")
        refresh_button.clicked.connect(self.refresh)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)

        left = QVBoxLayout()
        left.addWidget(QLabel("Conversations"))
        left.addWidget(self.conversation_list, 1)
        left.addWidget(refresh_button)

        action_row = QHBoxLayout()
        action_row.addWidget(self.accept_button)
        action_row.addWidget(self.reject_button)
        action_row.addWidget(self.ask_button)

        right = QVBoxLayout()
        right.addWidget(self.summary_label)
        right.addWidget(self.transcript, 1)
        right.addWidget(QLabel("Operator comment or question"))
        right.addWidget(self.review_note)
        right.addWidget(self.validation_label)
        right.addLayout(action_row)
        right.addWidget(close_button)

        layout = QHBoxLayout(self)
        layout.addLayout(left, 1)
        layout.addLayout(right, 2)

        self.refresh()

    def refresh(self) -> None:
        selected_id = self._selected_conversation_id()
        self.conversation_list.clear()
        records = self.state_store.load_operational_conversations()
        for record in records:
            item = QListWidgetItem(self._item_text(record))
            item.setData(256, record.conversation_id)
            self.conversation_list.addItem(item)
            if record.conversation_id == selected_id:
                self.conversation_list.setCurrentItem(item)
        if self.conversation_list.count() and self.conversation_list.currentRow() < 0:
            self.conversation_list.setCurrentRow(0)
        elif not self.conversation_list.count():
            self.summary_label.setText("No operational conversations yet.")
            self.transcript.clear()
            self._set_review_enabled(False)

    def _selected_conversation_id(self) -> str | None:
        item = self.conversation_list.currentItem()
        return str(item.data(256)) if item is not None else None

    @staticmethod
    def _item_text(record: OperationalConversationRecord) -> str:
        participants = " ↔ ".join(record.participants)
        lifecycle = (
            f"Started: {record.created_at} | Updated: {record.updated_at} | "
            f"Rounds: {record.round_count}"
        )
        if record.result_ready_at:
            lifecycle += f" | Result: {record.result_ready_at}"
        if record.closed_at:
            lifecycle += f" | Closed: {record.closed_at}"
        return (
            f"[{record.status}] {record.title}\n{participants}\n{lifecycle}"
        )

    def _show_selected_conversation(self, current: object, previous: object) -> None:
        del previous
        self.validation_label.clear()
        self.review_note.clear()
        if current is None:
            self._set_review_enabled(False)
            return
        conversation_id = str(current.data(256))
        record = self.state_store.load_operational_conversation(conversation_id)
        if record is None:
            self._set_review_enabled(False)
            return
        participants = " ↔ ".join(record.participants)
        lifecycle_lines = [
            f"Started: {record.created_at}",
            f"Last activity: {record.updated_at}",
            f"Rounds: {record.round_count}",
        ]
        if record.result_ready_at:
            lifecycle_lines.append(
                f"Result reached: {record.result_ready_at}"
            )
        if record.closed_at:
            lifecycle_lines.append(f"Closed: {record.closed_at}")
        self.summary_label.setText(
            f"{record.title}\nStatus: {record.status}\n"
            f"Participants: {participants}\n"
            f"Source request: {record.source_request_id}\n"
            + "\n".join(lifecycle_lines)
        )
        messages = self.state_store.load_operational_messages(conversation_id)
        rendered: list[str] = []
        for message in messages:
            rendered.append(
                f"<h3>{self._escape(message.author_department_id)}</h3>"
                f"<p><small>{self._escape(message.created_at)}</small></p>"
                f"<pre style='white-space: pre-wrap'>{self._escape(message.body)}</pre>"
            )
        footer_lines = [
            "<hr>",
            "<h3>Operational conversation lifecycle</h3>",
            f"<p>Status: <b>{self._escape(record.status)}</b><br>",
            f"Rounds: {record.round_count}<br>",
            f"Started: {self._escape(record.created_at)}<br>",
            f"Last activity: {self._escape(record.updated_at)}",
        ]
        if record.result_ready_at:
            footer_lines.append(
                f"<br>Result reached: {self._escape(record.result_ready_at)}"
            )
        if record.closed_at:
            footer_lines.append(
                f"<br>Conversation closed: {self._escape(record.closed_at)}"
            )
        footer_lines.append("</p><hr>")
        rendered.extend(footer_lines)
        self.transcript.setHtml("\n".join(rendered))
        self._set_review_enabled(record.status in self.REVIEWABLE_STATUSES)

    def _set_review_enabled(self, enabled: bool) -> None:
        self.review_note.setEnabled(enabled)
        self.accept_button.setEnabled(enabled)
        self.reject_button.setEnabled(enabled)
        self.ask_button.setEnabled(enabled)

    def _submit_review_action(self, action: str) -> None:
        conversation_id = self._selected_conversation_id()
        if conversation_id is None:
            return
        comment = self.review_note.toPlainText().strip()
        if action in {"REJECT", "ASK"} and not comment:
            self.validation_label.setText(
                "Reject and Ask / Continue require an operator comment."
            )
            return
        self.validation_label.setText("Submitting operator review...")
        self.review_action_requested.emit(conversation_id, action, comment)

    @staticmethod
    def _escape(text: str) -> str:
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
