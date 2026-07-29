"""Structured supervised handoff domain model for Curvature Console."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import Enum
from typing import Iterable
from uuid import uuid4


DEPARTMENT_IDS = frozenset({"project", "core", "research"})


class HandoffStatus(str, Enum):
    """Lifecycle states for one supervised interdepartmental handoff."""

    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    SENT = "sent"
    RECEIVED = "received"
    ANSWERED = "answered"
    CLOSED = "closed"
    REJECTED = "rejected"
    HELD = "held"
    STOPPED = "stopped"


TERMINAL_HANDOFF_STATUSES = frozenset(
    {
        HandoffStatus.CLOSED,
        HandoffStatus.REJECTED,
        HandoffStatus.STOPPED,
    }
)


_ALLOWED_TRANSITIONS = {
    HandoffStatus.DRAFT: frozenset(
        {
            HandoffStatus.PENDING_APPROVAL,
            HandoffStatus.REJECTED,
            HandoffStatus.STOPPED,
        }
    ),
    HandoffStatus.PENDING_APPROVAL: frozenset(
        {
            HandoffStatus.DRAFT,
            HandoffStatus.SENT,
            HandoffStatus.REJECTED,
            HandoffStatus.HELD,
            HandoffStatus.STOPPED,
        }
    ),
    HandoffStatus.SENT: frozenset(
        {
            HandoffStatus.RECEIVED,
            HandoffStatus.HELD,
            HandoffStatus.STOPPED,
        }
    ),
    HandoffStatus.RECEIVED: frozenset(
        {
            HandoffStatus.ANSWERED,
            HandoffStatus.HELD,
            HandoffStatus.STOPPED,
        }
    ),
    HandoffStatus.ANSWERED: frozenset(
        {
            HandoffStatus.SENT,
            HandoffStatus.CLOSED,
            HandoffStatus.HELD,
            HandoffStatus.STOPPED,
        }
    ),
    HandoffStatus.HELD: frozenset(
        {
            HandoffStatus.PENDING_APPROVAL,
            HandoffStatus.SENT,
            HandoffStatus.RECEIVED,
            HandoffStatus.ANSWERED,
            HandoffStatus.REJECTED,
            HandoffStatus.STOPPED,
        }
    ),
    HandoffStatus.CLOSED: frozenset(),
    HandoffStatus.REJECTED: frozenset(),
    HandoffStatus.STOPPED: frozenset(),
}


class HandoffValidationError(ValueError):
    """Raised when handoff data violates a domain invariant."""


class HandoffTransitionError(ValueError):
    """Raised when a requested lifecycle transition is not allowed."""


@dataclass(frozen=True, slots=True)
class HandoffMessage:
    """One immutable visible message in a handoff correspondence timeline."""

    message_id: str
    handoff_id: str
    sequence: int
    author_department_id: str
    body: str
    created_at: str


@dataclass(frozen=True, slots=True)
class HandoffRecord:
    """One supervised handoff and its complete visible correspondence."""

    handoff_id: str
    request_id: str
    source_department_id: str
    target_department_id: str
    status: HandoffStatus
    created_at: str
    updated_at: str
    user_visible_message: str
    timeline: tuple[HandoffMessage, ...] = ()

    @property
    def is_terminal(self) -> bool:
        """Return whether no further status transition is allowed."""

        return self.status in TERMINAL_HANDOFF_STATUSES

    def can_transition_to(self, status: HandoffStatus) -> bool:
        """Return whether the requested lifecycle transition is allowed."""

        return status in _ALLOWED_TRANSITIONS[self.status]

    def transition(
        self,
        status: HandoffStatus,
        *,
        updated_at: str | None = None,
    ) -> HandoffRecord:
        """Return a copy moved to an allowed lifecycle state."""

        if not self.can_transition_to(status):
            raise HandoffTransitionError(
                f"Cannot transition handoff from "
                f"{self.status.value!r} to {status.value!r}."
            )
        return replace(
            self,
            status=status,
            updated_at=updated_at or _utc_now(),
        )

    def append_message(
        self,
        author_department_id: str,
        body: str,
        *,
        message_id: str | None = None,
        created_at: str | None = None,
    ) -> HandoffRecord:
        """Return a copy with one additional visible timeline message."""

        _validate_department_id(author_department_id)
        if author_department_id not in {
            self.source_department_id,
            self.target_department_id,
        }:
            raise HandoffValidationError(
                "Message author must be the source or target department."
            )
        clean_body = body.strip()
        if not clean_body:
            raise HandoffValidationError("Handoff message body cannot be empty.")

        timestamp = created_at or _utc_now()
        message = HandoffMessage(
            message_id=message_id or f"message-{uuid4().hex}",
            handoff_id=self.handoff_id,
            sequence=len(self.timeline),
            author_department_id=author_department_id,
            body=clean_body,
            created_at=timestamp,
        )
        return replace(
            self,
            timeline=(*self.timeline, message),
            updated_at=timestamp,
        )


def create_handoff(
    *,
    request_id: str,
    source_department_id: str,
    target_department_id: str,
    user_visible_message: str,
    handoff_id: str | None = None,
    created_at: str | None = None,
) -> HandoffRecord:
    """Create one validated draft handoff."""

    clean_request_id = request_id.strip()
    if not clean_request_id:
        raise HandoffValidationError("request_id cannot be empty.")

    _validate_department_id(source_department_id)
    _validate_department_id(target_department_id)
    if source_department_id == target_department_id:
        raise HandoffValidationError(
            "Source and target departments must be different."
        )

    clean_message = user_visible_message.strip()
    if not clean_message:
        raise HandoffValidationError(
            "user_visible_message cannot be empty."
        )

    timestamp = created_at or _utc_now()
    return HandoffRecord(
        handoff_id=handoff_id or f"handoff-{uuid4().hex}",
        request_id=clean_request_id,
        source_department_id=source_department_id,
        target_department_id=target_department_id,
        status=HandoffStatus.DRAFT,
        created_at=timestamp,
        updated_at=timestamp,
        user_visible_message=clean_message,
    )


def available_handoff_transitions(
    status: HandoffStatus,
) -> tuple[HandoffStatus, ...]:
    """Return allowed next states in stable value order."""

    return tuple(sorted(_ALLOWED_TRANSITIONS[status], key=lambda item: item.value))


def validate_timeline(messages: Iterable[HandoffMessage]) -> None:
    """Validate stable, zero-based timeline sequencing."""

    for expected_sequence, message in enumerate(messages):
        if message.sequence != expected_sequence:
            raise HandoffValidationError(
                "Timeline sequence must be contiguous and zero-based."
            )


def _validate_department_id(department_id: str) -> None:
    if department_id not in DEPARTMENT_IDS:
        raise HandoffValidationError(
            f"Unknown department_id: {department_id!r}."
        )


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()
