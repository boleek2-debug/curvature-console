"""Tests for lightweight Task and full Thread Handoff packages."""

from __future__ import annotations

from pathlib import Path

import pytest

from curvature_console.infrastructure.context_loader import (
    ContextDocument,
    ContextLoadResult,
)
from curvature_console.infrastructure.transfer_package import (
    TransferPackageBuilder,
    TransferPackageMode,
    TransferPackagePolicy,
    TransferPackageRequest,
)
from curvature_console.presentation.attachment_record import AttachmentRecord


def _context(long_document: bool = False) -> ContextLoadResult:
    handoff = (
        "BEGIN-" + ("x" * 10_000) + "-END"
        if long_document
        else "Exact next step: implement B5.2D."
    )
    return ContextLoadResult(
        department_id="core",
        documents=(
            ContextDocument(
                label="ROLE",
                source_path=Path("/roles/core.md"),
                content="You are Curvature Core.",
            ),
            ContextDocument(
                label="console:00_CURVATURE_CONSOLE_CURRENT_STATE.md",
                source_path=Path(
                    "/console/00_CURVATURE_CONSOLE_CURRENT_STATE.md"
                ),
                content="Status: Operational. Tests: 121 passed.",
            ),
            ContextDocument(
                label="console:CURVATURE_CONSOLE_HANDOFF.md",
                source_path=Path("/console/CURVATURE_CONSOLE_HANDOFF.md"),
                content="Exact next step: normal Curvature work.",
            ),
            ContextDocument(
                label="curvature:HANDOFF.md",
                source_path=Path("/repo/HANDOFF.md"),
                content=handoff,
            ),
        ),
        errors=(),
    )


def _request(
    tmp_path: Path,
    mode: TransferPackageMode = TransferPackageMode.TASK,
    long_document: bool = False,
    conversation: str = "Previous local conversation.",
    policy: TransferPackagePolicy | None = None,
    department_id: str = "core",
    department_title: str = "Curvature Core",
) -> TransferPackageRequest:
    attachment = tmp_path / "failure.log"
    attachment.write_text("failure details", encoding="utf-8")

    context = _context(long_document)
    if department_id != "core":
        context = ContextLoadResult(
            department_id=department_id,
            documents=context.documents,
            errors=context.errors,
        )

    return TransferPackageRequest(
        mode=mode,
        department_id=department_id,
        department_title=department_title,
        responsibility="Architecture, implementation and tests.",
        context=context,
        conversation_text=conversation,
        draft_text="Implement the transfer package.",
        attachments=(AttachmentRecord(path=attachment),),
        policy=policy,
    )


@pytest.mark.parametrize(
    ("department_id", "department_title"),
    (
        ("project", "Curvature Project"),
        ("core", "Curvature Core"),
        ("research", "Curvature Research"),
    ),
)
def test_task_package_is_lightweight_for_every_department(
    tmp_path: Path,
    department_id: str,
    department_title: str,
) -> None:
    package = TransferPackageBuilder().build(
        _request(
            tmp_path,
            mode=TransferPackageMode.TASK,
            long_document=True,
            conversation="LOCAL-CONVERSATION-MUST-NOT-BE-SENT",
            department_id=department_id,
            department_title=department_title,
        )
    )

    assert package.mode is TransferPackageMode.TASK
    assert package.department_id == department_id
    assert package.included_document_count == 2
    assert package.truncated_document_count == 0
    assert package.conversation_was_truncated is False
    assert "Package type: Task Package" in package.text
    assert f"Department: {department_title}" in package.text
    assert "Implement the transfer package." in package.text
    assert "failure.log" in package.text
    assert "You are Curvature Core." not in package.text
    assert "BEGIN-" not in package.text
    assert "-END" not in package.text
    assert "LOCAL-CONVERSATION-MUST-NOT-BE-SENT" not in package.text
    assert "EXISTING CONVERSATION CONTEXT" in package.text
    assert "AUTHORITATIVE LOCAL CONSOLE CONTEXT" in package.text
    assert "Status: Operational. Tests: 121 passed." in package.text
    assert "Exact next step: normal Curvature work." in package.text
    assert "override stale ChatGPT Project Sources" in package.text
    assert len(package.text) < 10_000


def test_thread_handoff_keeps_full_documents_and_conversation(
    tmp_path: Path,
) -> None:
    package = TransferPackageBuilder().build(
        _request(
            tmp_path,
            mode=TransferPackageMode.THREAD_HANDOFF,
            long_document=True,
            conversation="Previous local conversation.",
        )
    )

    assert package.mode is TransferPackageMode.THREAD_HANDOFF
    assert package.included_document_count == 4
    assert package.truncated_document_count == 0
    assert "Package type: Thread Handoff Package" in package.text
    assert "You are Curvature Core." in package.text
    assert "x" * 10_000 in package.text
    assert "Previous local conversation." in package.text
    assert "continuity handoff from the previous thread" in package.text


def test_builder_is_deterministic(tmp_path: Path) -> None:
    request = _request(tmp_path)
    builder = TransferPackageBuilder()

    assert builder.build(request).text == builder.build(request).text


def test_handoff_conversation_keeps_newest_characters_when_bounded(
    tmp_path: Path,
) -> None:
    package = TransferPackageBuilder().build(
        _request(
            tmp_path,
            mode=TransferPackageMode.THREAD_HANDOFF,
            conversation="OLDER-" + ("x" * 30) + "-NEWEST",
            policy=TransferPackagePolicy(
                conversation_character_limit=12,
                document_character_limit=None,
            ),
        )
    )

    assert package.conversation_was_truncated is True
    assert "OLDER-" not in package.text
    assert "-NEWEST" in package.text


def test_context_department_must_match_request(tmp_path: Path) -> None:
    request = _request(tmp_path)
    mismatched = TransferPackageRequest(
        mode=request.mode,
        department_id="research",
        department_title=request.department_title,
        responsibility=request.responsibility,
        context=request.context,
        conversation_text=request.conversation_text,
        draft_text=request.draft_text,
        attachments=request.attachments,
    )

    with pytest.raises(ValueError, match="Context department"):
        TransferPackageBuilder().build(mismatched)


def test_empty_task_content_is_marked_explicitly() -> None:
    request = TransferPackageRequest(
        mode=TransferPackageMode.TASK,
        department_id="core",
        department_title="Curvature Core",
        responsibility="Implementation.",
        context=_context(),
        conversation_text="",
        draft_text="",
        attachments=(),
    )

    package = TransferPackageBuilder().build(request)

    assert "[No current task draft]" in package.text
    assert "[No attachments queued]" in package.text
    assert "[No local conversation recorded]" not in package.text


def test_response_instructions_prioritise_exact_user_task(
    tmp_path: Path,
) -> None:
    package = TransferPackageBuilder().build(_request(tmp_path))

    assert (
        "The CURRENT USER TASK is the immediate instruction"
        in package.text
    )
    assert (
        "If the CURRENT USER TASK requests an exact response"
        in package.text
    )
    assert "exactly that response and nothing else" in package.text


def test_task_omits_stale_main_project_documents_but_includes_console_state(
    tmp_path: Path,
) -> None:
    package = TransferPackageBuilder().build(_request(tmp_path))

    assert "Status: Operational. Tests: 121 passed." in package.text
    assert "Exact next step: normal Curvature work." in package.text
    assert "Exact next step: implement B5.2D." not in package.text
    assert "curvature:HANDOFF.md" not in package.text


def test_task_marks_missing_authoritative_context_explicitly(
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)
    context = ContextLoadResult(
        department_id="core",
        documents=(
            ContextDocument(
                label="ROLE",
                source_path=Path("/roles/core.md"),
                content="You are Curvature Core.",
            ),
        ),
        errors=(),
    )
    request = TransferPackageRequest(
        mode=request.mode,
        department_id=request.department_id,
        department_title=request.department_title,
        responsibility=request.responsibility,
        context=context,
        conversation_text=request.conversation_text,
        draft_text=request.draft_text,
        attachments=request.attachments,
    )

    package = TransferPackageBuilder().build(request)

    assert package.included_document_count == 0
    assert (
        "[No authoritative Console state documents were loaded]"
        in package.text
    )



def test_task_bounds_authoritative_context_at_document_boundaries(
    tmp_path: Path,
) -> None:
    oversized_handoff = "HANDOFF-START-" + ("h" * 10_000) + "-HANDOFF-END"
    context = ContextLoadResult(
        department_id="core",
        documents=(
            ContextDocument(
                label="console:00_CURVATURE_CONSOLE_CURRENT_STATE.md",
                source_path=Path(
                    "/console/00_CURVATURE_CONSOLE_CURRENT_STATE.md"
                ),
                content="CURRENT-STATE-" + ("s" * 7_000),
            ),
            ContextDocument(
                label="console:CURVATURE_CONSOLE_HANDOFF.md",
                source_path=Path("/console/CURVATURE_CONSOLE_HANDOFF.md"),
                content=oversized_handoff,
            ),
        ),
        errors=(),
    )
    request = TransferPackageRequest(
        mode=TransferPackageMode.TASK,
        department_id="core",
        department_title="Curvature Core",
        responsibility="Implementation.",
        context=context,
        conversation_text="",
        draft_text="Run a normal task.",
        attachments=(),
    )

    package = TransferPackageBuilder().build(request)

    assert "CURRENT-STATE-" in package.text
    assert "HANDOFF-START-" not in package.text
    assert "Additional authoritative document omitted" in package.text
    assert package.included_document_count == 1


def test_thread_handoff_keeps_full_documents_despite_task_budget(
    tmp_path: Path,
) -> None:
    package = TransferPackageBuilder().build(
        _request(
            tmp_path,
            mode=TransferPackageMode.THREAD_HANDOFF,
            long_document=True,
        )
    )

    assert "BEGIN-" in package.text
    assert "-END" in package.text
    assert "Additional authoritative document omitted" not in package.text


def test_response_instructions_define_supervised_handoff_proposal_envelope(
    tmp_path: Path,
) -> None:
    package = TransferPackageBuilder().build(_request(tmp_path))

    assert "BEGIN_CURVATURE_HANDOFF_PROPOSAL" in package.text
    assert "END_CURVATURE_HANDOFF_PROPOSAL" in package.text
    assert '"target_department_id":"project|core|research"' in package.text
    assert "Console will capture it as a draft for user review" in package.text
    assert "Do not claim that the handoff was sent" in package.text

@pytest.mark.parametrize(
    ("department_id", "department_title"),
    (
        ("project", "Curvature Project"),
        ("core", "Curvature Core"),
        ("research", "Curvature Research"),
    ),
)
@pytest.mark.parametrize(
    "mode",
    (TransferPackageMode.TASK, TransferPackageMode.THREAD_HANDOFF),
)
def test_every_department_package_contains_shared_authority_and_console_routing(
    tmp_path: Path,
    department_id: str,
    department_title: str,
    mode: TransferPackageMode,
) -> None:
    package = TransferPackageBuilder().build(
        _request(
            tmp_path,
            mode=mode,
            department_id=department_id,
            department_title=department_title,
        )
    )

    assert "CROSS-DEPARTMENT AUTHORITY AND CONSOLE ROUTING" in package.text
    assert "Project owns Chronicle direction" in package.text
    assert "Core owns Chronicle architecture" in package.text
    assert "Research owns evidence" in package.text
    assert "Console Development Unit owns Curvature Console" in package.text
    assert "CONSOLE_TOOL_REQUEST" in package.text
    assert "CONSOLE_INTEGRATION_REQUEST" in package.text
    assert "CONSOLE_WORKFLOW_REQUEST" in package.text
    assert "CONSOLE_DEFECT" in package.text
    assert "CONSOLE_DECISION_REQUEST" in package.text
    assert "Do not claim that a handoff or Console request was delivered" in package.text


def test_package_instructs_department_to_escalate_missing_console_capability(
    tmp_path: Path,
) -> None:
    package = TransferPackageBuilder().build(_request(tmp_path))

    assert "BEGIN_CURVATURE_CONSOLE_REQUEST" in package.text
    assert "END_CURVATURE_CONSOLE_REQUEST" in package.text
    assert "Console will route it automatically to CDU" in package.text
    assert "do not ask the operator to copy it" in package.text
