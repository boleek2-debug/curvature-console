"""Classify completed operational conversations by operator attention need."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import re


class OperationalAttentionKind(StrEnum):
    """Why a completed operational conversation needs operator attention."""

    RESULT = "RESULT"
    BLOCKER = "BLOCKER"
    OPERATOR_DECISION = "OPERATOR_DECISION"


@dataclass(frozen=True, slots=True)
class OperationalAttention:
    """Classification result persisted with one operational conversation."""

    kind: OperationalAttentionKind
    reason: str


_EXPLICIT_STATE_RE = re.compile(
    r"(?:workflow_state|operational_state|attention_type)\s*[:=]\s*"
    r"(RESULT|RESULT_READY|BLOCKER|BLOCKED|OPERATOR_DECISION|"
    r"AWAITING_OPERATOR_DECISION)",
    re.IGNORECASE,
)

_DECISION_MARKERS = (
    "operator approval required",
    "operator decision required",
    "requires operator approval",
    "requires operator decision",
    "awaiting operator decision",
    "awaiting operator approval",
    "decision request",
    "must be approved by the operator",
)

_BLOCKER_MARKERS = (
    "blocker",
    "blocked",
    "cannot continue",
    "unable to continue",
    "cannot proceed",
    "unable to proceed",
    "missing required",
    "route is unavailable",
    "validation failed",
    "fresh-artifact transport validation failed",
)


def classify_operational_attention(response_text: str) -> OperationalAttention:
    """Return a conservative attention class for one completed response.

    Explicit workflow markers win. Otherwise decision and blocker phrases are
    recognised conservatively; all other completed responses are results.
    """

    text = response_text.strip()
    match = _EXPLICIT_STATE_RE.search(text)
    if match:
        value = match.group(1).upper()
        if value in {"BLOCKER", "BLOCKED"}:
            return OperationalAttention(
                OperationalAttentionKind.BLOCKER,
                "The response explicitly reports a blocker.",
            )
        if value in {"OPERATOR_DECISION", "AWAITING_OPERATOR_DECISION"}:
            return OperationalAttention(
                OperationalAttentionKind.OPERATOR_DECISION,
                "The response explicitly requests an operator decision.",
            )
        return OperationalAttention(
            OperationalAttentionKind.RESULT,
            "The response explicitly reports a completed result.",
        )

    lowered = text.casefold()
    for marker in _DECISION_MARKERS:
        if marker in lowered:
            return OperationalAttention(
                OperationalAttentionKind.OPERATOR_DECISION,
                f"Detected operator-decision marker: {marker}.",
            )
    for marker in _BLOCKER_MARKERS:
        if marker in lowered:
            return OperationalAttention(
                OperationalAttentionKind.BLOCKER,
                f"Detected blocker marker: {marker}.",
            )
    return OperationalAttention(
        OperationalAttentionKind.RESULT,
        "Completed response contains no blocker or operator-decision marker.",
    )


def status_for_attention(attention: OperationalAttention) -> str:
    """Map attention classification to the persisted lifecycle status."""

    if attention.kind is OperationalAttentionKind.BLOCKER:
        return "BLOCKED"
    if attention.kind is OperationalAttentionKind.OPERATOR_DECISION:
        return "AWAITING_OPERATOR_DECISION"
    return "RESULT_READY"
