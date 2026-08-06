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
    decision_question: str | None = None
    decision_options: tuple[str, ...] = ()
    decision_consequences: tuple[str, ...] = ()


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
            question = _extract_scalar(text, "operator_decision")
            options = _extract_list(text, "operator_options")
            consequences = _extract_list(text, "operator_consequences")
            detail = "The response explicitly requests an operator decision."
            if question:
                detail += f" Question: {question}"
            if options:
                detail += " Options: " + " | ".join(options)
            if consequences:
                detail += " Consequences: " + " | ".join(consequences)
            return OperationalAttention(
                OperationalAttentionKind.OPERATOR_DECISION,
                detail,
                decision_question=question,
                decision_options=options,
                decision_consequences=consequences,
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


def _extract_scalar(text: str, key: str) -> str | None:
    match = re.search(rf"(?im)^\s*{re.escape(key)}\s*[:=]\s*(.+?)\s*$", text)
    return match.group(1).strip() if match else None


def _extract_list(text: str, key: str) -> tuple[str, ...]:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if re.match(rf"^\s*{re.escape(key)}\s*[:=]\s*$", line, re.IGNORECASE):
            values: list[str] = []
            for candidate in lines[index + 1:]:
                match = re.match(r"^\s*-\s+(.+?)\s*$", candidate)
                if not match:
                    break
                values.append(match.group(1).strip())
            return tuple(values)
    return ()
