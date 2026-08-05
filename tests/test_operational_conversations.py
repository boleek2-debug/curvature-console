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
