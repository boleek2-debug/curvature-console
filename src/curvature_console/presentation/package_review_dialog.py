"""Package review and explicit safe-apply dialog."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from curvature_console.infrastructure.package_apply import (
    PackageApplyError,
    PackageApplyResult,
)
from curvature_console.infrastructure.package_review import (
    PackageAction,
    PackageReview,
)


class PackageReviewDialog(QDialog):
    """Display package review and require one explicit Apply approval."""

    def __init__(
        self,
        review: PackageReview,
        apply_callback: Callable[
            [PackageReview],
            PackageApplyResult,
        ]
        | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.review = review
        self.apply_callback = apply_callback
        self.apply_result: PackageApplyResult | None = None

        self.setWindowTitle("Package Review")
        self.setObjectName("packageReviewDialog")
        self.resize(1040, 680)

        self.package_label = QLabel(
            f"Package: {review.package_path}"
        )
        self.package_label.setObjectName("packageReviewPackage")

        self.repository_label = QLabel(
            "Target repository: "
            f"{review.repository_id} → {review.repository_root}"
        )
        self.repository_label.setObjectName(
            "packageReviewRepository"
        )

        self.summary_label = QLabel(self._summary_text())
        self.summary_label.setObjectName("packageReviewSummary")
        self.summary_label.setWordWrap(True)

        self.status_label = QLabel(
            "APPLY ELIGIBLE — explicit approval is required"
            if review.is_apply_eligible
            else "BLOCKED — package contains one or more conflicts"
        )
        self.status_label.setObjectName("packageReviewStatus")

        self.table = QTableWidget(len(review.items), 6)
        self.table.setObjectName("packageReviewTable")
        self.table.setHorizontalHeaderLabels(
            [
                "Action",
                "Requested",
                "Path",
                "Size",
                "Target",
                "Reason",
            ]
        )
        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.table.setAlternatingRowColors(True)

        for row, item in enumerate(review.items):
            values = (
                item.classified_action.value.upper(),
                item.requested_action.upper(),
                item.relative_path.as_posix(),
                str(item.archive_size),
                "exists" if item.target_exists else "missing",
                item.reason,
            )
            for column, value in enumerate(values):
                cell = QTableWidgetItem(value)
                cell.setData(
                    Qt.ItemDataRole.UserRole,
                    item.classified_action.value,
                )
                self.table.setItem(row, column, cell)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.Stretch,
        )
        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            4,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            5,
            QHeaderView.ResizeMode.Stretch,
        )

        self.result_label = QLabel("Post-apply Git report")
        self.result_label.setObjectName("packageApplyResultLabel")
        self.result_label.setVisible(False)

        self.result_text = QPlainTextEdit()
        self.result_text.setObjectName("packageApplyResultText")
        self.result_text.setReadOnly(True)
        self.result_text.setVisible(False)
        self.result_text.setMaximumBlockCount(10000)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close
        )
        self.buttons.setObjectName("packageReviewButtons")
        self.buttons.rejected.connect(self.reject)

        self.apply_button = QPushButton("Apply Package")
        self.apply_button.setObjectName("packageApplyButton")
        self.apply_button.setEnabled(
            review.is_apply_eligible
            and apply_callback is not None
        )
        self.apply_button.clicked.connect(self._confirm_and_apply)
        self.buttons.addButton(
            self.apply_button,
            QDialogButtonBox.ButtonRole.AcceptRole,
        )

        layout = QVBoxLayout(self)
        layout.addWidget(self.package_label)
        layout.addWidget(self.repository_label)
        layout.addWidget(self.summary_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.table, 1)
        layout.addWidget(self.result_label)
        layout.addWidget(self.result_text, 1)
        layout.addWidget(self.buttons)

    def _summary_text(self) -> str:
        counts = {
            action: sum(
                item.classified_action is action
                for item in self.review.items
            )
            for action in PackageAction
        }
        return (
            f"Files: {len(self.review.items)} · "
            f"Create: {counts[PackageAction.CREATE]} · "
            f"Replace: {counts[PackageAction.REPLACE]} · "
            f"Skip: {counts[PackageAction.SKIP]} · "
            f"Conflict: {counts[PackageAction.CONFLICT]} · "
            "Uncompressed payload: "
            f"{self.review.total_uncompressed_bytes} bytes"
        )

    def _confirm_and_apply(self) -> None:
        if self.apply_callback is None:
            return

        answer = QMessageBox.warning(
            self,
            "Apply package to repository?",
            "This will write the reviewed CREATE and REPLACE files to:\n\n"
            f"{self.review.repository_root}\n\n"
            "Replaced files will be backed up. No commit or push will be "
            "performed automatically.",
            QMessageBox.StandardButton.Apply
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Apply:
            return

        self.apply_button.setEnabled(False)
        try:
            result = self.apply_callback(self.review)
        except (PackageApplyError, OSError) as exc:
            QMessageBox.critical(
                self,
                "Package apply failed",
                str(exc),
            )
            self.apply_button.setEnabled(
                self.review.is_apply_eligible
            )
            return

        self.apply_result = result
        self.status_label.setText(
            "APPLIED — repository changed; review the Git diff before "
            "committing"
        )
        self.result_label.setVisible(True)
        self.result_text.setVisible(True)
        self.result_text.setPlainText(self._result_text(result))
        self.table.setEnabled(False)

    def _result_text(self, result: PackageApplyResult) -> str:
        applied_lines = "\n".join(
            f"- {item.action.value.upper()}: {item.relative_path}"
            for item in result.applied_files
        ) or "- No repository files changed"

        skipped_lines = "\n".join(
            f"- SKIP: {path}" for path in result.skipped_paths
        ) or "- No skipped files"

        return (
            f"Backup directory:\n{result.backup_directory}\n\n"
            f"Applied files:\n{applied_lines}\n\n"
            f"Skipped files:\n{skipped_lines}\n\n"
            f"Git status --short:\n{result.git_status}\n\n"
            f"Git diff:\n{result.git_diff}"
        )
