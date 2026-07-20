"""Preview and approve one automated ChatGPT transfer package."""

from __future__ import annotations

from PySide6.QtWidgets import (
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
    """Display a generated package before explicit browser delivery."""

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

        self.send_button = QPushButton("Send to ChatGPT")
        self.send_button.setObjectName("sendTransferPackageButton")
        self.send_button.setToolTip(
            "Send this exact package through the dedicated logged-in Chrome "
            "profile."
        )
        self.send_button.clicked.connect(self.accept)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.summary_label)
        layout.addWidget(self.preview, 1)
        layout.addWidget(self.send_button)
        layout.addWidget(buttons)
