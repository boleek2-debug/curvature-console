"""Operational diagnostics dialog for Curvature Support Unit."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from curvature_console.infrastructure.support_diagnostics import (
    SupportDiagnosticReport,
    SupportDiagnosticsCollector,
)


class SupportUnitDialog(QDialog):
    """Show read-only operational state and create a diagnostic report."""

    def __init__(
        self,
        *,
        repository_roots: dict[str, Path],
        data_directory: Path,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Curvature Support Unit")
        self.setObjectName("supportUnitDialog")
        self.resize(900, 680)

        self.collector = SupportDiagnosticsCollector(
            repository_roots=repository_roots,
            data_directory=data_directory,
        )
        self.current_report: SupportDiagnosticReport | None = None

        heading = QLabel("Operational diagnostics")
        heading.setObjectName("supportUnitHeading")
        heading.setStyleSheet("font-size: 18px; font-weight: 600;")

        description = QLabel(
            "Read-only view of repository state, latest runtime log and "
            "latest Console snapshot. No Git or repository writes are "
            "performed by refresh."
        )
        description.setWordWrap(True)

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

        action_layout = QHBoxLayout()
        action_layout.addWidget(self.refresh_button)
        action_layout.addWidget(self.open_log_button)
        action_layout.addWidget(self.create_report_button)
        action_layout.addStretch(1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(heading)
        layout.addWidget(description)
        layout.addWidget(summary_group)
        layout.addLayout(action_layout)
        layout.addWidget(self.report_view, 1)
        layout.addWidget(buttons)

        self.refresh_diagnostics()

    def refresh_diagnostics(self) -> None:
        """Refresh the read-only diagnostic view."""

        self.current_report = self.collector.collect()
        self.report_view.setPlainText(self.current_report.as_text())

        repositories = self.current_report.repositories
        clean_count = sum(repository.is_clean for repository in repositories)
        synced_count = sum(repository.is_synced for repository in repositories)
        self.summary_label.setText(
            f"Repositories clean: {clean_count}/{len(repositories)}  |  "
            f"Synced with origin/main: {synced_count}/{len(repositories)}"
        )
        self.open_log_button.setEnabled(
            self.current_report.latest_runtime_log is not None
        )

    def open_latest_log(self) -> None:
        """Open the newest runtime log in the desktop's default viewer."""

        report = self.current_report
        if report is None or report.latest_runtime_log is None:
            QMessageBox.information(
                self,
                "No runtime log",
                "No runtime log is currently available.",
            )
            return
        QDesktopServices.openUrl(
            QUrl.fromLocalFile(str(report.latest_runtime_log))
        )

    def create_report(self) -> None:
        """Write the visible diagnostic report to the data directory."""

        report = self.current_report or self.collector.collect()
        try:
            output_path = self.collector.write_report(report)
        except OSError as exc:
            QMessageBox.critical(
                self,
                "Diagnostic report failed",
                f"Could not write diagnostic report:\n{exc}",
            )
            return

        QMessageBox.information(
            self,
            "Diagnostic report created",
            f"Saved to:\n{output_path}",
        )
