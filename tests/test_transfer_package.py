"""Tests for Task and Thread Handoff package generation."""

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
        else "Exact next step: implement B5.1."
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
                label="HANDOFF.md",
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
) -> TransferPackageRequest:
    attachment = tmp_path / "failure.log"
    attachment.write_text("failure details", encoding="utf-8")

    return TransferPackageRequest(
        mode=mode,
        department_id="core",
        department_title="Curvature Core",
        responsibility="Architecture, implementation and tests.",
        context=_context(long_document),
        conversation_text=conversation,
        draft_text="Implement the transfer package.",
        attachments=(AttachmentRecord(path=attachment),),
        policy=policy,
    )


def test_task_package_contains_required_content(tmp_path: Path) -> None:
    package = TransferPackageBuilder().build(_request(tmp_path))

    assert package.mode is TransferPackageMode.TASK
    assert package.department_id == "core"
    assert package.included_document_count == 2
    assert package.attachment_count == 1
    assert "Package type: Task Package" in package.text
    assert "You are Curvature Core." in package.text
    assert "Implement the transfer package." in package.text
    assert "failure.log" in package.text


def test_task_package_compacts_long_non_role_documents(
    tmp_path: Path,
) -> None:
    package = TransferPackageBuilder().build(
        _request(tmp_path, long_document=True)
    )

    assert package.truncated_document_count == 1
    assert "BEGIN-" in package.text
    assert "-END" in package.text
    assert "middle omitted by compact Task Package" in package.text
    assert len(package.text) < 7_000


def test_thread_handoff_keeps_full_documents(tmp_path: Path) -> None:
    package = TransferPackageBuilder().build(
        _request(
            tmp_path,
            mode=TransferPackageMode.THREAD_HANDOFF,
            long_document=True,
        )
    )

    assert package.mode is TransferPackageMode.THREAD_HANDOFF
    assert package.truncated_document_count == 0
    assert "Package type: Thread Handoff Package" in package.text
    assert "x" * 10_000 in package.text
    assert "continuity handoff from the previous thread" in package.text


def test_builder_is_deterministic(tmp_path: Path) -> None:
    request = _request(tmp_path)
    builder = TransferPackageBuilder()

    assert builder.build(request).text == builder.build(request).text


def test_conversation_keeps_newest_characters_when_bounded(
    tmp_path: Path,
) -> None:
    package = TransferPackageBuilder().build(
        _request(
            tmp_path,
            conversation="OLDER-" + ("x" * 30) + "-NEWEST",
            policy=TransferPackagePolicy(
                conversation_character_limit=12,
                document_character_limit=4_000,
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


def test_empty_content_is_marked_explicitly() -> None:
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

    assert "[No local conversation recorded]" in package.text
    assert "[No current task draft]" in package.text
    assert "[No attachments queued]" in package.text

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
