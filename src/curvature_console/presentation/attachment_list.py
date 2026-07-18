"""Attachment queue widget for one department workspace."""

from __future__ import annotations

import tempfile
from collections.abc import Iterable
from pathlib import Path
from uuid import uuid4

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from curvature_console.presentation.attachment_record import AttachmentRecord


class AttachmentList(QWidget):
    """Manage an attachment queue for one department."""

    attachment_count_changed = Signal(int)
    attachments_changed = Signal()

    def __init__(
        self,
        department_id: str,
        attachment_storage_dir: Path | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.department_id = department_id
        self.attachment_storage_dir = (
            attachment_storage_dir.expanduser()
            if attachment_storage_dir is not None
            else None
        )
        self.setObjectName(f"{department_id}AttachmentArea")
        self.setAcceptDrops(True)

        self._records: list[AttachmentRecord] = []

        self.header_label = QLabel("Attachments: 0")
        self.header_label.setObjectName(f"{department_id}AttachmentHeader")

        self.list_widget = QListWidget()
        self.list_widget.setObjectName(f"{department_id}AttachmentList")
        self.list_widget.setMaximumHeight(120)
        self.list_widget.setSelectionMode(
            QListWidget.SelectionMode.ExtendedSelection
        )

        self.add_files_button = QPushButton("Add Files")
        self.add_files_button.setObjectName(f"{department_id}AddFilesButton")
        self.add_files_button.clicked.connect(self.choose_files)

        self.paste_screenshot_button = QPushButton("Paste Screenshot")
        self.paste_screenshot_button.setObjectName(
            f"{department_id}PasteScreenshotButton"
        )
        self.paste_screenshot_button.clicked.connect(
            self.paste_screenshot_from_clipboard
        )

        self.remove_selected_button = QPushButton("Remove Selected")
        self.remove_selected_button.setObjectName(
            f"{department_id}RemoveAttachmentButton"
        )
        self.remove_selected_button.clicked.connect(self.remove_selected)

        self.clear_button = QPushButton("Clear")
        self.clear_button.setObjectName(f"{department_id}ClearAttachmentsButton")
        self.clear_button.clicked.connect(self.clear_attachments)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_files_button)
        button_layout.addWidget(self.paste_screenshot_button)
        button_layout.addWidget(self.remove_selected_button)
        button_layout.addWidget(self.clear_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.header_label)
        layout.addWidget(self.list_widget)
        layout.addLayout(button_layout)

        self._refresh_state(emit_change=False)

    @property
    def records(self) -> tuple[AttachmentRecord, ...]:
        """Return an immutable view of queued attachments."""

        return tuple(self._records)

    def choose_files(self) -> None:
        """Open a file picker and queue the selected files."""

        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Add attachments",
            str(Path.home()),
            "All files (*)",
        )
        self.add_paths(Path(path) for path in paths)

    def add_paths(self, paths: Iterable[Path]) -> None:
        """Queue existing files, ignoring duplicates and missing paths."""

        existing = {record.path.resolve() for record in self._records}
        changed = False

        for raw_path in paths:
            path = Path(raw_path).expanduser()
            if not path.is_file():
                continue

            resolved = path.resolve()
            if resolved in existing:
                continue

            record = AttachmentRecord(path=resolved)
            self._records.append(record)
            existing.add(resolved)
            self._add_record_item(record)
            changed = True

        self._refresh_state(emit_change=changed)

    def restore_records(
        self,
        records: Iterable[AttachmentRecord],
    ) -> None:
        """Restore attachment metadata without deleting source files."""

        self._records.clear()
        self.list_widget.clear()

        for record in records:
            if not record.path.is_file():
                continue
            self._records.append(record)
            self._add_record_item(record)

        self._refresh_state(emit_change=False)

    def paste_screenshot_from_clipboard(self) -> bool:
        """Save a clipboard image and queue it."""

        clipboard = QApplication.clipboard()
        image = clipboard.image()

        if image.isNull():
            return False

        if self.attachment_storage_dir is None:
            storage_dir = Path(tempfile.gettempdir())
            temporary = True
        else:
            storage_dir = self.attachment_storage_dir
            storage_dir.mkdir(parents=True, exist_ok=True)
            temporary = False

        target = (
            storage_dir
            / f"curvature-console-{self.department_id}-{uuid4().hex}.png"
        )

        if not image.save(str(target), "PNG"):
            return False

        record = AttachmentRecord(path=target, temporary=temporary)
        self._records.append(record)
        self._add_record_item(record)
        self._refresh_state(emit_change=True)
        return True

    def remove_selected(self) -> None:
        """Remove selected attachments from this department queue."""

        selected_rows = sorted(
            {self.list_widget.row(item) for item in self.list_widget.selectedItems()},
            reverse=True,
        )

        for row in selected_rows:
            record = self._records.pop(row)
            self.list_widget.takeItem(row)
            self._delete_managed_file(record)

        self._refresh_state(emit_change=bool(selected_rows))

    def clear_attachments(self) -> None:
        """Remove all queued attachments."""

        changed = bool(self._records)

        for record in self._records:
            self._delete_managed_file(record)

        self._records.clear()
        self.list_widget.clear()
        self._refresh_state(emit_change=changed)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        paths = [
            Path(url.toLocalFile())
            for url in event.mimeData().urls()
            if url.isLocalFile()
        ]
        self.add_paths(paths)
        event.acceptProposedAction()

    def _add_record_item(self, record: AttachmentRecord) -> None:
        item = QListWidgetItem(record.display_text())
        item.setData(Qt.ItemDataRole.UserRole, str(record.path))
        item.setToolTip(str(record.path))
        self.list_widget.addItem(item)

    def _refresh_state(self, emit_change: bool) -> None:
        count = len(self._records)
        self.header_label.setText(f"Attachments: {count}")
        self.remove_selected_button.setEnabled(count > 0)
        self.clear_button.setEnabled(count > 0)
        self.attachment_count_changed.emit(count)
        if emit_change:
            self.attachments_changed.emit()

    def _delete_managed_file(self, record: AttachmentRecord) -> None:
        should_delete = record.temporary

        if self.attachment_storage_dir is not None:
            try:
                record.path.resolve().relative_to(
                    self.attachment_storage_dir.resolve()
                )
            except ValueError:
                pass
            else:
                should_delete = True

        if not should_delete:
            return

        try:
            record.path.unlink(missing_ok=True)
        except OSError:
            pass
