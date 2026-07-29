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
        HandoffStatus.SENT,
        updated_at="2026-07-29T12:02:00+00:00",
    )
    handoff = handoff.transition(
        HandoffStatus.RECEIVED,
        updated_at="2026-07-29T12:03:00+00:00",
    )
    handoff = handoff.transition(
        HandoffStatus.ANSWERED,
        updated_at="2026-07-29T12:04:00+00:00",
    )
    handoff = handoff.transition(
        HandoffStatus.CLOSED,
        updated_at="2026-07-29T12:05:00+00:00",
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
