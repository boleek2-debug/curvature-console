"""Large reply-history viewer for one Curvature department."""
from __future__ import annotations
from dataclasses import dataclass
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (QDialog,QHBoxLayout,QLabel,QListWidget,QListWidgetItem,
    QPlainTextEdit,QPushButton,QSplitter,QVBoxLayout,QWidget)

@dataclass(frozen=True, slots=True)
class ReplyExchange:
    task: str
    reply: str

def parse_reply_exchanges(transcript: str) -> tuple[ReplyExchange, ...]:
    exchanges=[]
    for block in transcript.split("=== USER TASK ===")[1:]:
        if "=== ASSISTANT RESPONSE ===" not in block: continue
        task, reply = block.split("=== ASSISTANT RESPONSE ===",1)
        exchanges.append(ReplyExchange(task.strip(), reply.strip()))
    return tuple(exchanges)

class ReplyViewerDialog(QDialog):
    def __init__(self, *, department_title: str, transcript: str, parent: QWidget|None=None):
        super().__init__(parent)
        self.setWindowTitle(f"{department_title} — Replies")
        self.setModal(True); self.resize(1080,720)
        self.exchanges=parse_reply_exchanges(transcript)
        self.summary_label=QLabel(); self.summary_label.setObjectName("replyViewerSummary")
        self.reply_list=QListWidget(); self.reply_list.setObjectName("replyViewerList")
        self.task_view=QPlainTextEdit(); self.task_view.setObjectName("replyViewerTask"); self.task_view.setReadOnly(True)
        self.reply_view=QPlainTextEdit(); self.reply_view.setObjectName("replyViewerReply"); self.reply_view.setReadOnly(True)
        self.copy_reply_button=QPushButton("Copy Reply"); self.copy_reply_button.setObjectName("copyReplyButton")
        self.close_button=QPushButton("Close")
        self.reply_list.currentRowChanged.connect(self._show_exchange)
        self.copy_reply_button.clicked.connect(self._copy_current_reply)
        self.close_button.clicked.connect(self.accept)
        detail=QVBoxLayout(); detail.addWidget(QLabel("Your task")); detail.addWidget(self.task_view,1)
        detail.addWidget(QLabel("Reply")); detail.addWidget(self.reply_view,3)
        detail_widget=QWidget(); detail_widget.setLayout(detail)
        splitter=QSplitter(Qt.Orientation.Horizontal); splitter.addWidget(self.reply_list); splitter.addWidget(detail_widget); splitter.setSizes([300,780])
        buttons=QHBoxLayout(); buttons.addWidget(self.copy_reply_button); buttons.addStretch(); buttons.addWidget(self.close_button)
        layout=QVBoxLayout(self); layout.addWidget(self.summary_label); layout.addWidget(splitter,1); layout.addLayout(buttons)
        self._populate()
    def _populate(self):
        count=len(self.exchanges); self.summary_label.setText(f"Saved replies: {count}"); self.copy_reply_button.setEnabled(count>0)
        for i, ex in enumerate(self.exchanges,1):
            preview=" ".join(ex.task.split()); preview=preview if len(preview)<=70 else preview[:67]+"..."
            self.reply_list.addItem(QListWidgetItem(f"{i}. {preview or '[No task text]'}"))
        if count: self.reply_list.setCurrentRow(count-1)
        else: self.task_view.setPlainText("[No saved task]"); self.reply_view.setPlainText("[No saved reply]")
    def _show_exchange(self,row:int):
        if row<0 or row>=len(self.exchanges):
            self.task_view.clear(); self.reply_view.clear(); self.copy_reply_button.setEnabled(False); return
        ex=self.exchanges[row]; self.task_view.setPlainText(ex.task); self.reply_view.setPlainText(ex.reply); self.copy_reply_button.setEnabled(True)
    def _copy_current_reply(self):
        QGuiApplication.clipboard().setText(self.reply_view.toPlainText())
