"""Parse department-generated background operational collaboration requests."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

from curvature_console.infrastructure.handoff import DEPARTMENT_IDS

BEGIN_MARKER = "BEGIN_CURVATURE_OPERATIONAL_REQUEST"
END_MARKER = "END_CURVATURE_OPERATIONAL_REQUEST"
SCHEMA_VERSION = 1


class OperationalRequestError(ValueError):
    """Raised when a background collaboration request is malformed."""


@dataclass(frozen=True, slots=True)
class OperationalRequest:
    """One validated background request from one production department to another."""

    target_department_id: str
    title: str
    task: str
    relevant_context: str
    expected_output: str
    constraints: tuple[str, ...]
    acceptance_criteria: tuple[str, ...]

    def render_request_body(self) -> str:
        constraints = "\n".join(f"- {item}" for item in self.constraints) or "- none"
        criteria = "\n".join(f"- {item}" for item in self.acceptance_criteria)
        return "\n\n".join(
            (
                f"# {self.title}",
                f"## Task\n{self.task}",
                f"## Relevant context\n{self.relevant_context}",
                f"## Expected output\n{self.expected_output}",
                f"## Constraints\n{constraints}",
                f"## Acceptance criteria\n{criteria}",
            )
        )


@dataclass(frozen=True, slots=True)
class OperationalRequestParseResult:
    requests: tuple[OperationalRequest, ...]
    errors: tuple[str, ...]


def parse_operational_requests(
    response_text: str,
    *,
    source_department_id: str,
) -> OperationalRequestParseResult:
    """Parse all explicit background collaboration blocks in response order."""

    if source_department_id not in DEPARTMENT_IDS:
        raise OperationalRequestError(
            f"Unknown source department: {source_department_id!r}."
        )

    requests: list[OperationalRequest] = []
    errors: list[str] = []
    cursor = 0
    block_number = 0
    while True:
        begin = response_text.find(BEGIN_MARKER, cursor)
        if begin < 0:
            break
        block_number += 1
        body_start = begin + len(BEGIN_MARKER)
        end = response_text.find(END_MARKER, body_start)
        if end < 0:
            errors.append(f"Request block {block_number}: missing {END_MARKER}.")
            break
        raw_body = response_text[body_start:end].strip()
        cursor = end + len(END_MARKER)
        try:
            payload = json.loads(raw_body)
            requests.append(
                _request_from_payload(
                    payload,
                    source_department_id=source_department_id,
                )
            )
        except (json.JSONDecodeError, OperationalRequestError) as exc:
            errors.append(f"Request block {block_number}: {exc}")

    return OperationalRequestParseResult(tuple(requests), tuple(errors))


def _request_from_payload(
    payload: Any,
    *,
    source_department_id: str,
) -> OperationalRequest:
    if not isinstance(payload, dict):
        raise OperationalRequestError("JSON root must be an object.")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise OperationalRequestError(f"schema_version must be {SCHEMA_VERSION}.")

    target = _required_text(payload, "target_department_id")
    if target not in DEPARTMENT_IDS:
        raise OperationalRequestError(f"Unknown target_department_id: {target!r}.")
    if target == source_department_id:
        raise OperationalRequestError("Source and target departments must be different.")

    constraints_value = payload.get("constraints", [])
    if not isinstance(constraints_value, list):
        raise OperationalRequestError("constraints must be a JSON array.")
    constraints = tuple(_clean_list_item(item, "constraints") for item in constraints_value)

    criteria_value = payload.get("acceptance_criteria")
    if not isinstance(criteria_value, list) or not criteria_value:
        raise OperationalRequestError(
            "acceptance_criteria must be a non-empty JSON array."
        )
    criteria = tuple(
        _clean_list_item(item, "acceptance_criteria")
        for item in criteria_value
    )

    return OperationalRequest(
        target_department_id=target,
        title=_required_text(payload, "title"),
        task=_required_text(payload, "task"),
        relevant_context=_required_text(payload, "relevant_context"),
        expected_output=_required_text(payload, "expected_output"),
        constraints=constraints,
        acceptance_criteria=criteria,
    )


def _required_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise OperationalRequestError(f"{key} must be a non-empty string.")
    return value.strip()


def _clean_list_item(value: Any, key: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise OperationalRequestError(
            f"Every {key} item must be a non-empty string."
        )
    return value.strip()
