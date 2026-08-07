from curvature_console.infrastructure.state_store import SQLiteStateStore


def test_operational_conversation_persists_transcript_and_status() -> None:
    store = SQLiteStateStore()
    store.create_operational_conversation(
        conversation_id="chain-1",
        source_request_id="source-1",
        title="Core needs CDU tool",
        participants=("core", "console-development"),
    )
    store.append_operational_message(
        conversation_id="chain-1",
        author_department_id="core",
        body="Need tool",
    )
    store.append_operational_message(
        conversation_id="chain-1",
        author_department_id="console-development",
        body="Tool ready",
    )
    store.update_operational_conversation_status("chain-1", "RESULT_READY")

    record = store.load_operational_conversation("chain-1")
    assert record is not None
    assert record.participants == ("core", "console-development")
    assert record.status == "RESULT_READY"
    assert [message.body for message in store.load_operational_messages("chain-1")] == [
        "Need tool",
        "Tool ready",
    ]
    assert store.count_operational_reviews() == 1


def test_operational_conversation_upsert_does_not_erase_messages() -> None:
    store = SQLiteStateStore()
    store.create_operational_conversation(
        conversation_id="chain-2",
        source_request_id="source-2",
        title="First title",
        participants=("project", "core"),
    )
    store.append_operational_message(
        conversation_id="chain-2",
        author_department_id="project",
        body="Original message",
    )
    store.create_operational_conversation(
        conversation_id="chain-2",
        source_request_id="source-2",
        title="Updated title",
        participants=("project", "core"),
    )

    record = store.load_operational_conversation("chain-2")
    assert record is not None
    assert record.title == "Updated title"
    assert len(store.load_operational_messages("chain-2")) == 1


def test_operator_message_and_terminal_status_are_persisted() -> None:
    store = SQLiteStateStore()
    store.create_operational_conversation(
        conversation_id="chain-review",
        source_request_id="source-review",
        title="Review result",
        participants=("core", "console-development"),
        status="RESULT_READY",
    )
    store.append_operational_message(
        conversation_id="chain-review",
        author_department_id="operator",
        body="Accepted by operator",
    )
    store.update_operational_conversation_status("chain-review", "ACCEPTED")

    record = store.load_operational_conversation("chain-review")
    assert record is not None
    assert record.status == "ACCEPTED"
    assert store.count_operational_reviews() == 0
    messages = store.load_operational_messages("chain-review")
    assert messages[-1].author_department_id == "operator"


def test_operational_continuation_reuses_record_and_increments_round() -> None:
    store = SQLiteStateStore()
    store.create_operational_conversation(
        conversation_id="chain-continuation",
        source_request_id="source-continuation",
        title="Stage one",
        participants=("core", "console-development"),
        status="RESULT_READY",
    )
    store.append_operational_message(
        conversation_id="chain-continuation",
        author_department_id="core",
        body="Initial result",
    )

    round_number = store.begin_operational_round(
        "chain-continuation", title="Stage two"
    )
    store.append_operational_message(
        conversation_id="chain-continuation",
        author_department_id="operator",
        body="Continue in the same conversation",
    )

    records = store.load_operational_conversations()
    assert len(records) == 1
    record = records[0]
    assert record.conversation_id == "chain-continuation"
    assert record.source_request_id == "source-continuation"
    assert record.title == "Stage two"
    assert record.status == "RUNNING"
    assert record.round_count == 2
    assert round_number == 2
    assert [message.body for message in store.load_operational_messages(
        "chain-continuation"
    )] == ["Initial result", "Continue in the same conversation"]


def test_operational_lifecycle_timestamps_are_persisted() -> None:
    store = SQLiteStateStore()
    store.create_operational_conversation(
        conversation_id="chain-lifecycle",
        source_request_id="source-lifecycle",
        title="Lifecycle",
        participants=("core", "console-development"),
    )

    store.update_operational_conversation_status(
        "chain-lifecycle", "RESULT_READY"
    )
    ready = store.load_operational_conversation("chain-lifecycle")
    assert ready is not None
    assert ready.result_ready_at is not None
    assert ready.closed_at is None

    store.update_operational_conversation_status(
        "chain-lifecycle", "ACCEPTED"
    )
    closed = store.load_operational_conversation("chain-lifecycle")
    assert closed is not None
    assert closed.result_ready_at == ready.result_ready_at
    assert closed.closed_at is not None


def test_operational_attention_is_persisted_and_counted() -> None:
    store = SQLiteStateStore()
    store.create_operational_conversation(
        conversation_id="chain-attention",
        source_request_id="source-attention",
        title="Needs decision",
        participants=("project", "console-development"),
    )
    store.update_operational_attention(
        "chain-attention",
        attention_kind="OPERATOR_DECISION",
        attention_reason="Repository write approval required.",
    )
    store.update_operational_conversation_status(
        "chain-attention", "AWAITING_OPERATOR_DECISION"
    )

    record = store.load_operational_conversation("chain-attention")
    assert record is not None
    assert record.attention_kind == "OPERATOR_DECISION"
    assert record.attention_reason == "Repository write approval required."
    assert store.count_operational_attention() == {"OPERATOR_DECISION": 1}


def test_gated_operational_decision_persists_and_resolves() -> None:
    store = SQLiteStateStore()
    store.create_operational_conversation(
        conversation_id="decision-1",
        source_request_id="source-1",
        title="Choose direction",
        participants=("project", "research"),
    )
    store.save_operational_decision(
        "decision-1",
        domain="CANON_OR_ART",
        question="Keep ASCII+?",
        options=("Keep ASCII+", "Replace ASCII+"),
        consequences=("Preserve identity", "Change identity"),
        action_types=("APPROVE", "REJECT"),
        blocked_request_body="original request",
        source_department_id="project",
        target_department_id="research",
    )

    pending = store.load_operational_conversation("decision-1")
    assert pending is not None
    assert pending.decision_status == "PENDING"
    assert pending.decision_options == ("Keep ASCII+", "Replace ASCII+")
    assert pending.decision_action_types == ("APPROVE", "REJECT")
    assert pending.blocked_source_department_id == "project"
    assert pending.blocked_target_department_id == "research"

    store.resolve_operational_decision(
        "decision-1",
        status="APPROVED",
        selected_option="Keep ASCII+",
        selected_action_type="APPROVE",
    )
    resolved = store.load_operational_conversation("decision-1")
    assert resolved is not None
    assert resolved.decision_status == "APPROVED"
    assert resolved.selected_option == "Keep ASCII+"
    assert resolved.selected_action_type == "APPROVE"
    assert resolved.resolved_at is not None


def test_rejected_operational_decision_closes_conversation() -> None:
    store = SQLiteStateStore()
    store.create_operational_conversation(
        conversation_id="decision-2",
        source_request_id="source-2",
        title="Repository mutation",
        participants=("core", "project"),
    )
    store.update_operational_conversation_status("decision-2", "REJECTED")
    record = store.load_operational_conversation("decision-2")
    assert record is not None
    assert record.closed_at is not None


def test_resolved_gated_decision_is_history_only_in_dialog(tmp_path) -> None:
    import os

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    from curvature_console.main import create_application
    from curvature_console.presentation.operational_conversations_dialog import (
        OperationalConversationsDialog,
    )

    create_application(["curvature-console-resolved-decision-dialog-test"])
    store = SQLiteStateStore(tmp_path / "state.sqlite3")
    store.create_operational_conversation(
        conversation_id="resolved-decision-ui",
        source_request_id="source-ui",
        title="Resolved repository mutation",
        participants=("core", "project"),
        status="AWAITING_OPERATOR_DECISION",
    )
    store.save_operational_decision(
        "resolved-decision-ui",
        domain="REPOSITORY_MUTATION",
        question="Authorize mutation?",
        options=("Approve mutation", "Reject mutation"),
        consequences=("Repository changes", "Repository unchanged"),
        action_types=("APPROVE", "REJECT"),
        blocked_request_body="blocked request",
        source_department_id="core",
        target_department_id="project",
    )
    store.resolve_operational_decision(
        "resolved-decision-ui",
        status="REJECTED",
        selected_option="Reject mutation",
        selected_action_type="REJECT",
    )
    store.update_operational_conversation_status(
        "resolved-decision-ui", "REJECTED"
    )

    dialog = OperationalConversationsDialog(state_store=store)
    dialog.show()
    dialog.refresh()

    assert not dialog.decision_option_label.isVisible()
    assert not dialog.decision_option.isVisible()
    assert not dialog.confirm_decision_button.isVisible()
    assert not dialog.review_note_label.isVisible()
    assert not dialog.review_note.isVisible()
    assert not dialog.validation_label.isVisible()
    assert not dialog.accept_button.isVisible()
    assert not dialog.reject_button.isVisible()
    assert not dialog.ask_button.isVisible()
    assert not dialog.abandon_button.isVisible()

    dialog.close()
    store.close()


def test_resolved_gated_results_are_not_counted_as_actionable_attention() -> None:
    store = SQLiteStateStore()
    store.create_operational_conversation(
        conversation_id="resolved-result",
        source_request_id="source-resolved",
        title="Resolved gated result",
        participants=("core", "project"),
        status="RESULT_READY",
    )
    store.save_operational_decision(
        "resolved-result",
        domain="REPOSITORY_MUTATION",
        question="Approve?",
        options=("Approve", "Reject"),
        consequences=("Mutate", "No change"),
        action_types=("APPROVE", "REJECT"),
        blocked_request_body="request",
        source_department_id="core",
        target_department_id="project",
    )
    store.resolve_operational_decision(
        "resolved-result",
        status="APPROVED",
        selected_option="Approve",
        selected_action_type="APPROVE",
    )
    store.update_operational_attention(
        "resolved-result",
        attention_kind="RESULT",
        attention_reason="Completed result.",
    )
    store.update_operational_conversation_status("resolved-result", "RESULT_READY")

    assert store.count_operational_attention() == {}
    assert store.count_operational_reviews() == 0


def test_running_conversations_are_recovered_as_blocked_after_restart() -> None:
    store = SQLiteStateStore()
    store.create_operational_conversation(
        conversation_id="interrupted-running",
        source_request_id="source-running",
        title="Interrupted work",
        participants=("core", "console-development"),
        status="RUNNING",
    )

    recovered = store.recover_interrupted_operational_conversations()

    assert recovered == 1
    record = store.load_operational_conversation("interrupted-running")
    assert record is not None
    assert record.status == "BLOCKED"
    assert record.attention_kind == "BLOCKER"
    assert "restarted" in (record.attention_reason or "").lower()
    assert store.count_operational_attention() == {"BLOCKER": 1}


def test_waiting_source_conversations_are_recovered_as_blocked_after_restart() -> None:
    store = SQLiteStateStore()
    store.create_operational_conversation(
        conversation_id="interrupted-waiting-source",
        source_request_id="source-waiting",
        title="Interrupted return",
        participants=("core", "research"),
        status="WAITING_SOURCE",
    )

    recovered = store.recover_interrupted_operational_conversations()

    assert recovered == 1
    record = store.load_operational_conversation("interrupted-waiting-source")
    assert record is not None
    assert record.status == "BLOCKED"
    assert record.attention_kind == "BLOCKER"
    assert "waiting for an in-process department return" in (
        record.attention_reason or ""
    ).lower()
    assert store.count_operational_attention() == {"BLOCKER": 1}


def test_ordinary_review_uses_explicit_operator_action_labels(tmp_path) -> None:
    import os

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    from curvature_console.main import create_application
    from curvature_console.presentation.operational_conversations_dialog import (
        OperationalConversationsDialog,
    )

    create_application(["curvature-console-ordinary-review-label-test"])
    store = SQLiteStateStore(tmp_path / "state.sqlite3")
    store.create_operational_conversation(
        conversation_id="ordinary-review-ui",
        source_request_id="source-ui",
        title="Ordinary result",
        participants=("core", "project"),
        status="RESULT_READY",
    )

    dialog = OperationalConversationsDialog(state_store=store)
    dialog.show()
    dialog.refresh()

    assert dialog.accept_button.text() == "Close as accepted"
    assert dialog.reject_button.text() == "Return to source"
    assert dialog.ask_button.text() == "Request clarification / continue"
    assert dialog.abandon_button.text() == "Close as abandoned"
    assert dialog.accept_button.isVisible()
    assert dialog.reject_button.isVisible()
    assert dialog.ask_button.isVisible()
    assert dialog.abandon_button.isVisible()

    dialog.close()
    store.close()


def test_close_as_abandoned_is_local_and_audited(tmp_path, caplog) -> None:
    import logging
    import os

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    from curvature_console.main import create_application
    from curvature_console.presentation.main_window import MainWindow

    create_application(["curvature-console-abandon-review-test"])
    window = MainWindow(
        state_path=tmp_path / "state.sqlite3",
        data_directory=tmp_path / "data",
        config_directory=tmp_path / "config",
    )
    window.state_store.create_operational_conversation(
        conversation_id="abandoned-review",
        source_request_id="source-abandoned",
        title="Dead conversation",
        participants=("core", "project"),
        status="BLOCKED",
    )

    with caplog.at_level(
        logging.INFO,
        logger="curvature_console.presentation.main_window",
    ):
        window._handle_operational_review_action(
            "abandoned-review",
            "ABANDON",
            "dead wątek",
            "",
        )

    record = window.state_store.load_operational_conversation("abandoned-review")
    assert record is not None
    assert record.status == "CANCELLED"
    assert record.closed_at is not None
    assert not window._pending_exchanges
    messages = window.state_store.load_operational_messages("abandoned-review")
    assert messages[-1].author_department_id == "operator"
    assert "Closed as abandoned" in messages[-1].body
    assert "dead wątek" in messages[-1].body
    assert "operator_action_submitted" in caplog.text
    assert "action=ABANDON" in caplog.text
    assert "operator_action_persisted" in caplog.text
    assert "operator_action_closed_without_resume" in caplog.text
    assert "operator_resume_enqueued" not in caplog.text

    window.close()
