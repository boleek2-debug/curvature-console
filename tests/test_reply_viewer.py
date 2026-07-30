from __future__ import annotations
import os
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
from curvature_console.main import create_application
from curvature_console.presentation.department_panel import DepartmentPanel
from curvature_console.presentation.reply_viewer_dialog import ReplyViewerDialog, parse_reply_exchanges

def test_parse_reply_exchanges():
    e=parse_reply_exchanges("=== USER TASK ===\nT1\n=== ASSISTANT RESPONSE ===\nR1\n=== USER TASK ===\nT2\n=== ASSISTANT RESPONSE ===\nR2")
    assert [(x.task,x.reply) for x in e]==[("T1","R1"),("T2","R2")]

def test_panel_compact_receipt():
    create_application(["reply-panel"])
    p=DepartmentPanel("core","Curvature Core","Implementation.")
    p.append_browser_exchange("Task","Reply")
    assert p.conversation_view.toPlainText()=="Reply received"
    assert p.view_replies_button.text()=="View Replies (1)"
    assert p.view_replies_button.isEnabled()
    assert "Reply" in p.conversation_text()

def test_restore_reactivates_button():
    create_application(["reply-restore"])
    p=DepartmentPanel("project","Curvature Project","Direction.")
    p.restore_conversation_text("=== USER TASK ===\nTask\n=== ASSISTANT RESPONSE ===\nReply")
    assert p.view_replies_button.isEnabled()
    assert p.view_replies_button.text()=="View Replies (1)"

def test_dialog_selects_latest():
    create_application(["reply-dialog"])
    d=ReplyViewerDialog(department_title="Curvature Research", transcript="=== USER TASK ===\nT1\n=== ASSISTANT RESPONSE ===\nR1\n=== USER TASK ===\nT2\n=== ASSISTANT RESPONSE ===\nR2")
    assert d.reply_list.currentRow()==1
    assert d.task_view.toPlainText()=="T2"
    assert d.reply_view.toPlainText()=="R2"
