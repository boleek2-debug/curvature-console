"""Tests for the supervised interdepartmental handoff domain model."""

from __future__ import annotations

import pytest

from curvature_console.infrastructure.handoff import (
    HandoffStatus,
    HandoffTransitionError,
    HandoffValidationError,
    available_handoff_transitions,
    create_handoff,
)


def test_create_handoff_starts_as_valid_draft() -> None:
    handoff = create_handoff(
        handoff_id="handoff-1",
        request_id="request-1",
        source_department_id="project",
        target_department_id="core",
        user_visible_message="Implement the approved schema.",
        created_at="2026-07-29T12:00:00+00:00",
    )

    assert handoff.status is HandoffStatus.DRAFT
    assert handoff.source_department_id == "project"
    assert handoff.target_department_id == "core"
    assert handoff.timeline == ()
    assert not handoff.is_terminal


@pytest.mark.parametrize(
    ("source", "target"),
    [
        ("unknown", "core"),
        ("project", "unknown"),
        ("core", "core"),
    ],
)
def test_create_handoff_rejects_invalid_department_routing(
    source: str,
    target: str,
) -> None:
    with pytest.raises(HandoffValidationError):
        create_handoff(
            request_id="request-1",
            source_department_id=source,
            target_department_id=target,
            user_visible_message="Message",
        )


def test_status_transitions_are_explicit_and_terminal() -> None:
    handoff = create_handoff(
        request_id="request-1",
        source_department_id="research",
        target_department_id="project",
        user_visible_message="Review evidence.",
    )

    handoff = handoff.transition(
        HandoffStatus.PENDING_APPROVAL,
        updated_at="2026-07-29T12:01:00+00:00",
    )
    handoff = handoff.transition(
        HandoffStatus.APPROVED,
        updated_at="2026-07-29T12:02:00+00:00",
    )
    handoff = handoff.transition(
        HandoffStatus.SENT,
        updated_at="2026-07-29T12:03:00+00:00",
    )
    handoff = handoff.transition(
        HandoffStatus.RECEIVED,
        updated_at="2026-07-29T12:04:00+00:00",
    )
    handoff = handoff.transition(
        HandoffStatus.ANSWERED,
        updated_at="2026-07-29T12:05:00+00:00",
    )
    handoff = handoff.transition(
        HandoffStatus.CLOSED,
        updated_at="2026-07-29T12:06:00+00:00",
    )

    assert handoff.is_terminal
    assert available_handoff_transitions(HandoffStatus.CLOSED) == ()
    with pytest.raises(HandoffTransitionError):
        handoff.transition(HandoffStatus.SENT)


def test_illegal_transition_is_rejected() -> None:
    handoff = create_handoff(
        request_id="request-1",
        source_department_id="project",
        target_department_id="research",
        user_visible_message="Research this topic.",
    )

    with pytest.raises(HandoffTransitionError):
        handoff.transition(HandoffStatus.RECEIVED)


def test_correspondence_timeline_is_visible_ordered_and_immutable() -> None:
    handoff = create_handoff(
        handoff_id="handoff-1",
        request_id="request-1",
        source_department_id="core",
        target_department_id="research",
        user_visible_message="Confirm the evidence requirements.",
        created_at="2026-07-29T12:00:00+00:00",
    )
    handoff = handoff.append_message(
        "core",
        "What evidence format is required?",
        message_id="message-1",
        created_at="2026-07-29T12:01:00+00:00",
    )
    handoff = handoff.append_message(
        "research",
        "Use source, claim, confidence and limitations.",
        message_id="message-2",
        created_at="2026-07-29T12:02:00+00:00",
    )

    assert [message.sequence for message in handoff.timeline] == [0, 1]
    assert [message.author_department_id for message in handoff.timeline] == [
        "core",
        "research",
    ]
    assert handoff.timeline[1].body.startswith("Use source")


def test_timeline_rejects_non_participant_author() -> None:
    handoff = create_handoff(
        request_id="request-1",
        source_department_id="core",
        target_department_id="research",
        user_visible_message="Confirm evidence.",
    )

    with pytest.raises(HandoffValidationError):
        handoff.append_message("project", "I should not be inserted.")



def test_approval_is_separate_from_browser_delivery() -> None:
    handoff = create_handoff(
        request_id="request-approval",
        source_department_id="project",
        target_department_id="core",
        user_visible_message="Implement this.",
    )
    handoff = handoff.transition(HandoffStatus.PENDING_APPROVAL)
    handoff = handoff.transition(HandoffStatus.APPROVED)

    assert handoff.status is HandoffStatus.APPROVED
    assert HandoffStatus.SENT in available_handoff_transitions(
        HandoffStatus.APPROVED
    )


def test_only_draft_instruction_can_be_edited() -> None:
    handoff = create_handoff(
        request_id="request-edit",
        source_department_id="project",
        target_department_id="research",
        user_visible_message="Old instruction.",
    )
    edited = handoff.edit_visible_message("New instruction.")

    assert edited.user_visible_message == "New instruction."

    pending = edited.transition(HandoffStatus.PENDING_APPROVAL)
    with pytest.raises(HandoffTransitionError):
        pending.edit_visible_message("Too late.")


def test_redirect_is_bounded_to_supervised_pre_delivery_states() -> None:
    handoff = create_handoff(
        request_id="request-redirect",
        source_department_id="project",
        target_department_id="core",
        user_visible_message="Route this.",
    )

    redirected = handoff.redirect("research")
    assert redirected.target_department_id == "research"

    approved = redirected.transition(
        HandoffStatus.PENDING_APPROVAL
    ).transition(HandoffStatus.APPROVED)
    with pytest.raises(HandoffTransitionError):
        approved.redirect("core")


def test_reply_decision_and_return_lifecycle_remains_open_until_close() -> None:
    handoff = create_handoff(
        request_id="request-return",
        source_department_id="project",
        target_department_id="core",
        user_visible_message="Implement a multi-sprint task.",
    )
    handoff = handoff.transition(HandoffStatus.PENDING_APPROVAL)
    handoff = handoff.transition(HandoffStatus.APPROVED)
    handoff = handoff.transition(HandoffStatus.SENT)
    handoff = handoff.transition(HandoffStatus.RECEIVED)
    handoff = handoff.transition(HandoffStatus.AWAITING_USER_DECISION)

    assert not handoff.is_terminal
    assert HandoffStatus.IN_PROGRESS in available_handoff_transitions(
        handoff.status
    )
    assert HandoffStatus.RETURN_SENT in available_handoff_transitions(
        handoff.status
    )

    returned = handoff.transition(HandoffStatus.RETURN_SENT).transition(
        HandoffStatus.RETURNED
    )
    assert not returned.is_terminal
    assert returned.transition(HandoffStatus.IN_PROGRESS).status is HandoffStatus.IN_PROGRESS


def test_in_progress_handoff_can_send_one_progress_update() -> None:
    handoff = create_handoff(
        request_id="request-progress-update",
        source_department_id="project",
        target_department_id="core",
        user_visible_message="Implement the approved work package.",
    )
    handoff = handoff.transition(HandoffStatus.PENDING_APPROVAL)
    handoff = handoff.transition(HandoffStatus.APPROVED)
    handoff = handoff.transition(HandoffStatus.SENT)
    handoff = handoff.transition(HandoffStatus.RECEIVED)
    handoff = handoff.transition(HandoffStatus.AWAITING_USER_DECISION)
    handoff = handoff.transition(HandoffStatus.IN_PROGRESS)

    updating = handoff.transition(HandoffStatus.UPDATE_SENT)
    answered = updating.transition(HandoffStatus.AWAITING_USER_DECISION)

    assert updating.status is HandoffStatus.UPDATE_SENT
    assert answered.status is HandoffStatus.AWAITING_USER_DECISION
