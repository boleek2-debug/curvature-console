"""Operational diagnostics and browser-mediated chat for Support Unit."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QProgressBar,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from curvature_console.infrastructure.state_store import GeneratedDownloadRecord
from curvature_console.presentation.attachment_list import AttachmentList
from curvature_console.presentation.attachment_record import AttachmentRecord

from curvature_console.infrastructure.support_diagnostics import (
    SupportDiagnosticReport,
    SupportDiagnosticsCollector,
)


class SupportUnitDialog(QDialog):
    """Cross-cutting diagnostics hub with a dedicated Support chat route."""

    send_requested = Signal(str, object)

    def __init__(
        self,
        *,
        repository_roots: dict[str, Path],
        data_directory: Path,
        conversation_text: str = "",
        draft_text: str = "",
        attachment_records: tuple[AttachmentRecord, ...] = (),
        download_records: tuple[GeneratedDownloadRecord, ...] = (),
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Curvature Support Unit")
        self.setObjectName("supportUnitDialog")
        self.resize(1100, 860)

        self.collector = SupportDiagnosticsCollector(
            repository_roots=repository_roots,
            data_directory=data_directory,
        )
        self.current_report: SupportDiagnosticReport | None = None

        heading = QLabel("Curvature Support Unit")
        heading.setObjectName("supportUnitHeading")
        heading.setStyleSheet("font-size: 18px; font-weight: 600;")

        description = QLabel(
            "Operational diagnostics and a dedicated ChatGPT support route. "
            "Messages are sent only after an explicit operator action."
        )
        description.setWordWrap(True)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("supportUnitTabs")
        self.tabs.addTab(self._build_diagnostics_tab(), "Diagnostics")
        self.tabs.addTab(self._build_chat_tab(conversation_text, draft_text), "Support Chat")
        self.attachment_list.restore_records(attachment_records)
        self.set_generated_downloads(download_records)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(heading)
        layout.addWidget(description)
        layout.addWidget(self.tabs, 1)
        layout.addWidget(buttons)

        self.refresh_diagnostics()

    def _build_diagnostics_tab(self) -> QWidget:
        page = QWidget()
        self.summary_label = QLabel()
        self.summary_label.setObjectName("supportUnitSummary")
        self.summary_label.setWordWrap(True)

        summary_group = QGroupBox("Current state")
        summary_layout = QVBoxLayout(summary_group)
        summary_layout.addWidget(self.summary_label)

        self.report_view = QPlainTextEdit()
        self.report_view.setObjectName("supportUnitReportView")
        self.report_view.setReadOnly(True)
        self.report_view.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        self.refresh_button = QPushButton("Refresh diagnostics")
        self.refresh_button.setObjectName("supportUnitRefreshButton")
        self.refresh_button.clicked.connect(self.refresh_diagnostics)

        self.open_log_button = QPushButton("Open latest bridge log")
        self.open_log_button.setObjectName("supportUnitOpenLogButton")
        self.open_log_button.clicked.connect(self.open_latest_log)

        self.create_report_button = QPushButton("Create diagnostic report")
        self.create_report_button.setObjectName("supportUnitCreateReportButton")
        self.create_report_button.clicked.connect(self.create_report)

        actions = QHBoxLayout()
        actions.addWidget(self.refresh_button)
        actions.addWidget(self.open_log_button)
        actions.addWidget(self.create_report_button)
        actions.addStretch(1)

        layout = QVBoxLayout(page)
        layout.addWidget(summary_group)
        layout.addLayout(actions)
        layout.addWidget(self.report_view, 1)
        return page

    def _build_chat_tab(self, conversation_text: str, draft_text: str) -> QWidget:
        page = QWidget()
        self.chat_view = QPlainTextEdit()
        self.chat_view.setObjectName("supportUnitChatView")
        self.chat_view.setReadOnly(True)
        self.chat_view.setPlainText(conversation_text)

        self.chat_input = QPlainTextEdit()
        self.chat_input.setObjectName("supportUnitChatInput")
        self.chat_input.setPlaceholderText("Describe the issue or next Console task...")
        self.chat_input.setPlainText(draft_text)
        self.chat_input.setMinimumHeight(90)
        self.chat_input.setMaximumHeight(130)

        self.attachment_list = AttachmentList(
            department_id="support",
            attachment_storage_dir=(
                self.collector.data_directory / "attachments" / "support"
            ),
        )
        self.attachment_list.setObjectName("supportAttachmentArea")

        self.download_list = QListWidget()
        self.download_list.setObjectName("supportDownloadList")
        self.download_list.setMaximumHeight(110)
        self.open_download_button = QPushButton("Open selected file")
        self.open_download_button.setObjectName("supportOpenDownloadButton")
        self.open_download_button.clicked.connect(self.open_selected_download)
        self.open_download_folder_button = QPushButton("Open downloads folder")
        self.open_download_folder_button.setObjectName("supportOpenDownloadFolderButton")
        self.open_download_folder_button.clicked.connect(self.open_downloads_folder)
        download_actions = QHBoxLayout()
        download_actions.addWidget(self.open_download_button)
        download_actions.addWidget(self.open_download_folder_button)
        download_actions.addStretch(1)

        self.attach_report_checkbox = QCheckBox("Attach current diagnostic report")
        self.attach_report_checkbox.setObjectName("supportAttachReportCheckbox")
        self.attach_report_checkbox.setChecked(True)
        self.attach_log_checkbox = QCheckBox("Attach latest runtime/validation log")
        self.attach_log_checkbox.setObjectName("supportAttachLogCheckbox")
        self.attach_log_checkbox.setChecked(True)

        self.send_button = QPushButton("Send to Support")
        self.send_button.setObjectName("supportUnitSendButton")
        self.send_button.clicked.connect(self._emit_send_request)

        self.activity_label = QLabel("IDLE")
        self.activity_label.setObjectName("supportUnitActivityLabel")
        self.activity_progress = QProgressBar()
        self.activity_progress.setObjectName("supportUnitActivityProgress")
        self.activity_progress.setRange(0, 0)
        self.activity_progress.setVisible(False)

        options = QHBoxLayout()
        options.addWidget(self.attach_report_checkbox)
        options.addWidget(self.attach_log_checkbox)
        options.addStretch(1)
        options.addWidget(self.send_button)

        lower_panel = QWidget()
        lower_layout = QVBoxLayout(lower_panel)
        lower_layout.setContentsMargins(0, 0, 0, 0)
        lower_layout.addWidget(QLabel("Message to Support"))
        lower_layout.addWidget(self.chat_input)
        lower_layout.addWidget(self.attachment_list)
        lower_layout.addLayout(options)
        lower_layout.addWidget(QLabel("Generated downloads"))
        lower_layout.addWidget(self.download_list)
        lower_layout.addLayout(download_actions)
        lower_layout.addWidget(self.activity_label)
        lower_layout.addWidget(self.activity_progress)

        self.chat_splitter = QSplitter(Qt.Orientation.Vertical)
        self.chat_splitter.setObjectName("supportUnitChatSplitter")
        self.chat_splitter.setChildrenCollapsible(False)
        self.chat_splitter.addWidget(self.chat_view)
        self.chat_splitter.addWidget(lower_panel)
        self.chat_splitter.setStretchFactor(0, 3)
        self.chat_splitter.setStretchFactor(1, 2)
        self.chat_splitter.setSizes([520, 300])

        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Dedicated Support conversation"))
        layout.addWidget(self.chat_splitter, 1)
        return page

    def _emit_send_request(self) -> None:
        message = self.chat_input.toPlainText().strip()
        if not message:
            QMessageBox.information(self, "Support message required", "Enter a message first.")
            return

        attachments: list[Path] = [
            record.path for record in self.attachment_list.records
        ]
        report = self.current_report or self.collector.collect()
        if self.attach_report_checkbox.isChecked():
            try:
                attachments.append(self.collector.write_report(report))
            except OSError as exc:
                QMessageBox.critical(self, "Diagnostic report failed", str(exc))
                return
        if self.attach_log_checkbox.isChecked() and report.latest_runtime_log is not None:
            attachments.append(report.latest_runtime_log)

        self.send_requested.emit(message, tuple(dict.fromkeys(attachments)))

    def set_busy(self, busy: bool, stage: str = "") -> None:
        self.send_button.setEnabled(not busy)
        self.chat_input.setReadOnly(busy)
        self.attachment_list.setEnabled(not busy)
        self.activity_progress.setVisible(busy)
        self.activity_label.setText((stage or "WORKING") if busy else "IDLE")

    def set_stage(self, stage: str) -> None:
        self.activity_label.setText(f"WORKING — {stage}")

    def append_exchange(self, user_text: str, response_text: str) -> None:
        existing = self.chat_view.toPlainText().rstrip()
        block = f"YOU\n{user_text.strip()}\n\nSUPPORT\n{response_text.strip()}"
        self.chat_view.setPlainText(f"{existing}\n\n{block}".strip())
        self.chat_view.verticalScrollBar().setValue(self.chat_view.verticalScrollBar().maximum())
        self.chat_input.clear()

    def conversation_text(self) -> str:
        return self.chat_view.toPlainText()

    def draft_text(self) -> str:
        return self.chat_input.toPlainText()

    def attachment_records(self) -> tuple[AttachmentRecord, ...]:
        return self.attachment_list.records

    def clear_sent_attachments(self) -> None:
        self.attachment_list.clear_attachments()

    def set_generated_downloads(
        self, records: tuple[GeneratedDownloadRecord, ...]
    ) -> None:
        self.download_list.clear()
        for record in records:
            self.download_list.addItem(
                f"{record.original_filename} → {record.saved_path}"
            )
            item = self.download_list.item(self.download_list.count() - 1)
            item.setData(256, str(record.saved_path))
        available = bool(records)
        self.open_download_button.setEnabled(available)
        self.open_download_folder_button.setEnabled(available)

    def _selected_download_path(self) -> Path | None:
        item = self.download_list.currentItem()
        if item is None and self.download_list.count():
            item = self.download_list.item(0)
        if item is None:
            return None
        raw_path = item.data(256)
        return Path(raw_path) if isinstance(raw_path, str) and raw_path else None

    def open_selected_download(self) -> None:
        path = self._selected_download_path()
        if path is None or not path.is_file():
            QMessageBox.information(self, "No download selected", "Select an available file first.")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def open_downloads_folder(self) -> None:
        path = self._selected_download_path()
        folder = path.parent if path is not None else self.collector.data_directory / "inbox" / "support"
        folder.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    def refresh_diagnostics(self) -> None:
        self.current_report = self.collector.collect()
        self.report_view.setPlainText(self.current_report.as_text())
        repositories = self.current_report.repositories
        clean_count = sum(repository.is_clean for repository in repositories)
        synced_count = sum(repository.is_synced for repository in repositories)
        self.summary_label.setText(
            f"Repositories clean: {clean_count}/{len(repositories)}  |  "
            f"Synced with origin/main: {synced_count}/{len(repositories)}"
        )
        self.open_log_button.setEnabled(self.current_report.latest_runtime_log is not None)

    def open_latest_log(self) -> None:
        report = self.current_report
        if report is None or report.latest_runtime_log is None:
            QMessageBox.information(self, "No runtime log", "No runtime log is currently available.")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(report.latest_runtime_log)))

    def create_report(self) -> None:
        report = self.current_report or self.collector.collect()
        try:
            output_path = self.collector.write_report(report)
        except OSError as exc:
            QMessageBox.critical(self, "Diagnostic report failed", f"Could not write diagnostic report:\n{exc}")
            return
        QMessageBox.information(self, "Diagnostic report created", f"Saved to:\n{output_path}")
