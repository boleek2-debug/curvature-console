"""Preview and copy one manual ChatGPT transfer package."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from curvature_console.infrastructure.transfer_package import TransferPackage


class TransferPackageDialog(QDialog):
    """Display a generated package and copy it to the clipboard."""

    def __init__(
        self,
        department_title: str,
        package: TransferPackage,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.package = package

        self.setWindowTitle(
            f"{department_title} — {package.mode.display_name}"
        )
        self.resize(980, 760)

        self.summary_label = QLabel(
            f"Mode: {package.mode.display_name} · "
            f"Documents: {package.included_document_count} · "
            f"Truncated documents: {package.truncated_document_count} · "
            f"Attachments: {package.attachment_count} · "
            f"Conversation truncated: "
            f"{'yes' if package.conversation_was_truncated else 'no'}"
        )
        self.summary_label.setObjectName("transferPackageSummary")

        self.preview = QPlainTextEdit()
        self.preview.setObjectName("transferPackagePreview")
        self.preview.setReadOnly(True)
        self.preview.setPlainText(package.text)

        self.copy_button = QPushButton("Copy to Clipboard")
        self.copy_button.setObjectName("copyTransferPackageButton")
        self.copy_button.clicked.connect(self.copy_to_clipboard)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.summary_label)
        layout.addWidget(self.preview, 1)
        layout.addWidget(self.copy_button)
        layout.addWidget(buttons)

    def copy_to_clipboard(self) -> None:
        """Copy the unmodified package text to the system clipboard."""

        QApplication.clipboard().setText(self.package.text)
        self.copy_button.setText("Copied")
