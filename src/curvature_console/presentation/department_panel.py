"""Reusable department panel for the three-panel desktop shell."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QElapsedTimer, QTimer, Qt, Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from curvature_console.infrastructure.context_loader import ContextLoadResult
from curvature_console.infrastructure.state_store import GeneratedDownloadRecord
from curvature_console.infrastructure.thread_pressure import (
    ThreadPressureEstimator,
    ThreadPressureLevel,
)
from curvature_console.presentation.attachment_list import AttachmentList


class DepartmentPanel(QFrame):
    """Display one department workspace inside Curvature Console."""

    focus_requested = Signal(str)
    context_refresh_requested = Signal(str)
    context_preview_requested = Signal(str)
    transfer_package_requested = Signal(str, str)
    package_review_requested = Signal(str, str)
    workspace_state_changed = Signal(str)
    replies_view_requested = Signal(str)
    abort_requested = Signal(str)

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
        self.responsibility = responsibility
        self.setObjectName(f"{department_id}Panel")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumWidth(300)

        self.title_label = QLabel(title)
        self.title_label.setObjectName(f"{department_id}Title")

        self.status_label = QLabel("STATUS: READY")
        self.status_label.setObjectName(f"{department_id}Status")

        self.activity_progress = QProgressBar()
        self.activity_progress.setObjectName(
            f"{department_id}ActivityProgress"
        )
        self.activity_progress.setRange(0, 0)
        self.activity_progress.setTextVisible(False)
        self.activity_progress.setMaximumHeight(8)
        self.activity_progress.hide()

        self.activity_label = QLabel("IDLE")
        self.activity_label.setObjectName(
            f"{department_id}ActivityIndicator"
        )
        self.activity_label.setStyleSheet(
            "color: #666; font-size: 11px;"
        )

        self._activity_stage = "Ready"
        self._activity_elapsed = QElapsedTimer()
        self._activity_timer = QTimer(self)
        self._activity_timer.setInterval(1000)
        self._activity_timer.timeout.connect(
            self._refresh_activity_indicator
        )

        self.thread_pressure_estimator = ThreadPressureEstimator()
        self.thread_pressure_snapshot = self.thread_pressure_estimator.estimate(
            conversation_text=""
        )
        self.thread_pressure_label = QLabel()
        self.thread_pressure_label.setObjectName(
            f"{department_id}ThreadPressure"
        )
        self.thread_pressure_label.setToolTip(
            "Advisory local estimate based on the Console transcript, "
            "current draft and attached file sizes. It is not ChatGPT's "
            "exact context usage or capacity."
        )
        self.thread_pressure_recommendation = QLabel()
        self.thread_pressure_recommendation.setObjectName(
            f"{department_id}ThreadPressureRecommendation"
        )
        self.thread_pressure_recommendation.setWordWrap(True)

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

        self._conversation_history_text = (
            f"{title} workspace is operational.\n\n"
            f"Responsibility: {responsibility}"
        )
        self._reply_count = 0
        self._last_read_reply_count = 0
        self.view_replies_button = QPushButton("View Replies")
        self.view_replies_button.setObjectName(f"{department_id}ViewRepliesButton")
        self.view_replies_button.setEnabled(False)
        self.view_replies_button.clicked.connect(self._request_replies_view)

        self.input_editor = QPlainTextEdit()
        self.input_editor.setObjectName(f"{department_id}Input")
        self.input_editor.setPlaceholderText(f"Message {title}...")
        self.input_editor.setMaximumHeight(110)
        self.input_editor.textChanged.connect(self._notify_state_changed)
        self.input_editor.textChanged.connect(self._update_thread_pressure)

        self.download_label = QLabel("Downloads: 0")
        self.download_label.setObjectName(f"{department_id}DownloadStatus")

        self.download_list = QListWidget()
        self.download_list.setObjectName(f"{department_id}DownloadList")
        self.download_list.setMaximumHeight(76)
        self.download_list.currentItemChanged.connect(
            self._update_package_review_button
        )

        self.package_review_button = QPushButton(
            "Review Selected Package"
        )
        self.package_review_button.setObjectName(
            f"{department_id}PackageReviewButton"
        )
        self.package_review_button.setToolTip(
            "Validate and classify the selected generated ZIP without "
            "writing to a repository."
        )
        self.package_review_button.setEnabled(False)
        self.package_review_button.clicked.connect(
            self._request_package_review
        )

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
        self.attachment_list.attachments_changed.connect(
            self._update_thread_pressure
        )

        self.task_package_button = QPushButton("Send Task")
        self.task_package_button.setObjectName(
            f"{department_id}TaskPackageButton"
        )
        self.task_package_button.setToolTip(
            "Preview and send a compact package to the current ChatGPT "
            "department project."
        )
        self.task_package_button.clicked.connect(
            self._request_task_package
        )

        self.thread_handoff_button = QPushButton("Send Thread Handoff")
        self.thread_handoff_button.setObjectName(
            f"{department_id}ThreadHandoffButton"
        )
        self.thread_handoff_button.setToolTip(
            "Preview and send a comprehensive handoff package to the same "
            "ChatGPT department project."
        )
        self.thread_handoff_button.clicked.connect(
            self._request_thread_handoff
        )

        self.abort_button = QPushButton("Abort Current Operation")
        self.abort_button.setObjectName(f"{department_id}AbortButton")
        self.abort_button.setStyleSheet("font-weight: 700; color: #b00020;")
        self.abort_button.clicked.connect(
            lambda: self.abort_requested.emit(self.department_id)
        )
        self.abort_button.hide()

        transfer_button_layout = QHBoxLayout()
        transfer_button_layout.addWidget(self.task_package_button)
        transfer_button_layout.addWidget(self.thread_handoff_button)

        layout = QVBoxLayout(self)
        layout.addLayout(header_layout)
        layout.addWidget(self.status_label)
        layout.addWidget(self.activity_progress)
        layout.addWidget(self.activity_label)
        layout.addWidget(self.thread_pressure_label)
        layout.addWidget(self.thread_pressure_recommendation)
        layout.addWidget(self.responsibility_label)
        layout.addWidget(self.context_label)
        layout.addWidget(self.context_files)
        layout.addLayout(context_button_layout)
        layout.addWidget(self.view_replies_button)
        layout.addWidget(self.input_editor)
        layout.addWidget(self.attachment_list)
        layout.addWidget(self.download_label)
        layout.addWidget(self.download_list)
        layout.addWidget(self.package_review_button)
        layout.addLayout(transfer_button_layout)
        layout.addWidget(self.abort_button)

        self._update_thread_pressure()


    def _update_thread_pressure(self, *_args) -> None:
        """Refresh this department's independent local pressure estimate."""

        snapshot = self.thread_pressure_estimator.estimate(
            conversation_text=self._conversation_history_text,
            draft_text=self.input_editor.toPlainText(),
            attachment_paths=(
                record.path for record in self.attachment_list.records
            ),
        )
        self.thread_pressure_snapshot = snapshot
        self.thread_pressure_label.setText(
            "THREAD PRESSURE: "
            f"{snapshot.level.value} · ~{snapshot.estimated_tokens:,} tokens"
        )
        self.thread_pressure_recommendation.setText(
            snapshot.handoff_recommendation
        )

        label_styles = {
            ThreadPressureLevel.GREEN: "color: #2e7d32; font-weight: 600;",
            ThreadPressureLevel.AMBER: "color: #a05a00; font-weight: 700;",
            ThreadPressureLevel.RED: "color: #b00020; font-weight: 700;",
        }
        recommendation_styles = {
            ThreadPressureLevel.GREEN: "",
            ThreadPressureLevel.AMBER: (
                "color: #7a4300; background: #fff4d6; padding: 4px; "
                "border: 1px solid #d69b2d;"
            ),
            ThreadPressureLevel.RED: (
                "color: #8a0018; background: #ffe5ea; padding: 4px; "
                "border: 1px solid #b00020; font-weight: 700;"
            ),
        }
        self.thread_pressure_label.setStyleSheet(label_styles[snapshot.level])
        self.thread_pressure_recommendation.setStyleSheet(
            recommendation_styles[snapshot.level]
        )

        if snapshot.level is ThreadPressureLevel.RED:
            self.thread_handoff_button.setText("Send Thread Handoff Now")
            self.thread_handoff_button.setStyleSheet(
                "font-weight: 700; border: 2px solid #b00020;"
            )
        elif snapshot.level is ThreadPressureLevel.AMBER:
            self.thread_handoff_button.setText(
                "Send Thread Handoff (Recommended)"
            )
            self.thread_handoff_button.setStyleSheet("font-weight: 700;")
        else:
            self.thread_handoff_button.setText("Send Thread Handoff")
            self.thread_handoff_button.setStyleSheet("")

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

    def set_browser_stage(self, stage: str) -> None:
        """Display the current browser lifecycle stage."""

        self._activity_stage = stage
        self.status_label.setText(f"STATUS: {stage.upper()}")
        self._refresh_activity_indicator()

    def set_browser_busy(self, busy: bool) -> None:
        """Reflect one active browser operation in this panel."""

        self.task_package_button.setEnabled(not busy)
        self.thread_handoff_button.setEnabled(not busy)
        self.input_editor.setEnabled(not busy)
        self.abort_button.setVisible(busy)
        self.abort_button.setEnabled(busy)

        if busy:
            self._activity_stage = "Connecting"
            self._activity_elapsed.start()
            self._activity_timer.start()
            self.activity_progress.show()
            self.activity_label.show()
            self.status_label.setText("STATUS: CONNECTING")
            self._refresh_activity_indicator()
        else:
            self._activity_timer.stop()
            self.activity_progress.hide()
            self.activity_label.setText("IDLE")
            self.activity_label.setStyleSheet(
                "color: #666; font-size: 11px;"
            )
            self._update_attachment_status(len(self.attachment_list.records))

    def _refresh_activity_indicator(self) -> None:
        """Show continuously changing proof that the UI event loop is alive."""

        if not self._activity_timer.isActive():
            return

        elapsed_seconds = max(
            0,
            self._activity_elapsed.elapsed() // 1000,
        )
        minutes, seconds = divmod(elapsed_seconds, 60)
        dots = "." * ((elapsed_seconds % 3) + 1)
        self.activity_label.setText(
            f"WORKING{dots} {self._activity_stage} · "
            f"{minutes:02d}:{seconds:02d}"
        )
        self.activity_label.setStyleSheet(
            "color: #1565c0; font-size: 11px; font-weight: 700;"
        )

    def conversation_text(self) -> str:
        return self._conversation_history_text

    def restore_conversation_text(self, conversation_text: str) -> None:
        self._conversation_history_text = conversation_text
        self._reply_count = conversation_text.count("=== ASSISTANT RESPONSE ===")
        self._refresh_reply_button()
        self._update_thread_pressure()

    def restore_reply_read_state(self, last_read_reply_count: int) -> None:
        """Restore the persisted number of replies already seen by the user."""

        self._last_read_reply_count = max(0, int(last_read_reply_count))
        self._refresh_reply_button()

    def append_browser_exchange(self, user_task: str, assistant_response: str) -> None:
        sections=[self._conversation_history_text.rstrip(),"=== USER TASK ===",
            user_task.strip() or "[No current task draft]","=== ASSISTANT RESPONSE ===",assistant_response]
        self._conversation_history_text="\n\n".join(x for x in sections if x!="")
        self._reply_count = self._conversation_history_text.count("=== ASSISTANT RESPONSE ===")
        self._refresh_reply_button()
        self._update_thread_pressure()

    def start_new_thread_exchange(self, user_task: str, assistant_response: str) -> None:
        self._conversation_history_text="\n\n".join(["=== NEW THREAD AFTER HANDOFF ===","=== USER TASK ===",
            user_task.strip() or "[No current task draft]","=== ASSISTANT RESPONSE ===",assistant_response])
        self._reply_count = 1
        self._last_read_reply_count = 0
        self._refresh_reply_button()
        self._update_thread_pressure()

    @property
    def last_read_reply_count(self) -> int:
        return self._last_read_reply_count

    @property
    def unread_reply_count(self) -> int:
        return max(0, self._reply_count - self._last_read_reply_count)

    def mark_replies_read(self) -> None:
        """Mark every currently saved reply as seen."""

        self._last_read_reply_count = self._reply_count
        self._refresh_reply_button()
        self._notify_state_changed()

    def _refresh_reply_button(self) -> None:
        if self._reply_count <= 0:
            self.view_replies_button.setText("View Replies")
            self.view_replies_button.setEnabled(False)
            self.view_replies_button.setStyleSheet("")
            return

        unread = self.unread_reply_count
        label = f"View Replies ({self._reply_count})"
        if unread:
            label += f" • {unread} new"
            self.view_replies_button.setStyleSheet(
                "font-weight: 700; border: 2px solid #1565c0; "
                "background: #e8f1ff;"
            )
        else:
            self.view_replies_button.setStyleSheet("")
        self.view_replies_button.setText(label)
        self.view_replies_button.setEnabled(True)

    def _request_replies_view(self) -> None:
        self.replies_view_requested.emit(self.department_id)


    def set_generated_downloads(
        self,
        records: tuple[GeneratedDownloadRecord, ...],
    ) -> None:
        """Display generated files captured for this department."""

        self.download_list.clear()
        for record in records:
            self.download_list.addItem(
                f"{record.original_filename} → {record.saved_path}"
            )
            item = self.download_list.item(
                self.download_list.count() - 1
            )
            item.setData(
                Qt.ItemDataRole.UserRole,
                str(record.saved_path),
            )
        self.download_label.setText(f"Downloads: {len(records)}")
        self._update_package_review_button()

    def selected_generated_download_path(self) -> Path | None:
        """Return the selected generated file path, if available."""

        item = self.download_list.currentItem()
        if item is None:
            return None
        raw_path = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(raw_path, str) or not raw_path:
            return None
        return Path(raw_path)

    def _update_package_review_button(self, *_args) -> None:
        path = self.selected_generated_download_path()
        self.package_review_button.setEnabled(
            path is not None and path.suffix.lower() == ".zip"
        )

    def _request_package_review(self) -> None:
        path = self.selected_generated_download_path()
        if path is None:
            return
        self.package_review_requested.emit(
            self.department_id,
            str(path),
        )

    def _request_focus(self) -> None:
        self.focus_requested.emit(self.department_id)

    def _request_context_refresh(self) -> None:
        self.context_refresh_requested.emit(self.department_id)

    def _request_context_preview(self) -> None:
        self.context_preview_requested.emit(self.department_id)

    def _request_task_package(self) -> None:
        self.transfer_package_requested.emit(self.department_id, "task")

    def _request_thread_handoff(self) -> None:
        self.transfer_package_requested.emit(
            self.department_id,
            "thread_handoff",
        )

    def _notify_state_changed(self) -> None:
        self.workspace_state_changed.emit(self.department_id)

    def _update_attachment_status(self, count: int) -> None:
        if count == 0:
            self.status_label.setText("STATUS: READY")
        else:
            self.status_label.setText(f"STATUS: READY · {count} ATTACHED")
