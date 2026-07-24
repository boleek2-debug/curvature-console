"""Read-only package review dialog for Curvature Console."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from curvature_console.infrastructure.package_review import (
    PackageAction,
    PackageReview,
)


class PackageReviewDialog(QDialog):
    """Display a complete package review without offering repository writes."""

    def __init__(
        self,
        review: PackageReview,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.review = review
        self.setWindowTitle("Package Review")
        self.setObjectName("packageReviewDialog")
        self.resize(980, 560)

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
            "APPLY ELIGIBLE — review only; writes are not implemented"
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

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close
        )
        self.buttons.setObjectName("packageReviewButtons")
        self.buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.package_label)
        layout.addWidget(self.repository_label)
        layout.addWidget(self.summary_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.table, 1)
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
