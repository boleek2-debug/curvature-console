"""Parse department-generated requests for Console Development Unit."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any

BEGIN_MARKER = "BEGIN_CURVATURE_CONSOLE_REQUEST"
END_MARKER = "END_CURVATURE_CONSOLE_REQUEST"
SCHEMA_VERSION = 1
ALLOWED_REQUEST_TYPES = frozenset(
    {
        "CONSOLE_TOOL_REQUEST",
        "CONSOLE_INTEGRATION_REQUEST",
        "CONSOLE_WORKFLOW_REQUEST",
        "CONSOLE_DEFECT",
        "CONSOLE_DECISION_REQUEST",
    }
)


class ConsoleRequestError(ValueError):
    """Raised when an automatic Console request block is malformed."""


@dataclass(frozen=True, slots=True)
class ConsoleRequest:
    """One validated request emitted by Project, Core or Research."""

    request_type: str
    title: str
    problem_or_need: str
    required_output: str
    constraints: tuple[str, ...]
    acceptance_criteria: tuple[str, ...]

    def render_request_body(self) -> str:
        constraints = "\n".join(f"- {item}" for item in self.constraints)
        criteria = "\n".join(
            f"- {item}" for item in self.acceptance_criteria
        )
        return "\n\n".join(
            (
                f"# {self.title}",
                f"## Problem or need\n{self.problem_or_need}",
                f"## Required output\n{self.required_output}",
                f"## Constraints\n{constraints}",
                f"## Acceptance criteria\n{criteria}",
            )
        )


_ARTIFACT_FILENAME_RE = re.compile(
    r"(?<![A-Za-z0-9._-])([A-Za-z0-9][A-Za-z0-9._-]*\.[A-Za-z0-9]{1,12})(?![A-Za-z0-9._-])"
)


@dataclass(frozen=True, slots=True)
class ArtifactTransportName:
    """Map one stable logical artifact name to a unique transport filename."""

    logical_filename: str
    transport_filename: str


def extract_artifact_filenames(request: ConsoleRequest) -> tuple[str, ...]:
    """Extract ordered logical output filenames declared by a CDU request."""

    texts = (request.required_output, *request.constraints, *request.acceptance_criteria)
    found: list[str] = []
    seen: set[str] = set()
    for text in texts:
        for match in _ARTIFACT_FILENAME_RE.finditer(text):
            filename = Path(match.group(1)).name
            key = filename.casefold()
            if key in seen:
                continue
            seen.add(key)
            found.append(filename)
    return tuple(found)


def build_artifact_transport_names(
    request: ConsoleRequest,
    *,
    request_id: str,
    round_number: int,
) -> tuple[ArtifactTransportName, ...]:
    """Build unique physical names so ChatGPT cannot reuse a stale file card."""

    token = re.sub(r"[^A-Za-z0-9]", "", request_id)[-10:] or "request"
    mappings: list[ArtifactTransportName] = []
    for logical_filename in extract_artifact_filenames(request):
        path = Path(logical_filename)
        transport = f"{path.stem}.round-{round_number}.{token}{path.suffix}"
        mappings.append(
            ArtifactTransportName(
                logical_filename=logical_filename,
                transport_filename=transport,
            )
        )
    return tuple(mappings)


@dataclass(frozen=True, slots=True)
class ConsoleRequestParseResult:
    requests: tuple[ConsoleRequest, ...]
    errors: tuple[str, ...]


def parse_console_requests(response_text: str) -> ConsoleRequestParseResult:
    """Parse all delimited CDU request blocks from an assistant response."""

    requests: list[ConsoleRequest] = []
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
            errors.append(
                f"Console request block {block_number}: missing {END_MARKER}."
            )
            break
        raw_body = response_text[body_start:end].strip()
        cursor = end + len(END_MARKER)
        try:
            payload = json.loads(raw_body)
            requests.append(_request_from_payload(payload))
        except (json.JSONDecodeError, ConsoleRequestError) as exc:
            errors.append(f"Console request block {block_number}: {exc}")

    return ConsoleRequestParseResult(
        requests=tuple(requests), errors=tuple(errors)
    )


def _request_from_payload(payload: Any) -> ConsoleRequest:
    if not isinstance(payload, dict):
        raise ConsoleRequestError("JSON root must be an object.")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ConsoleRequestError(
            f"schema_version must be {SCHEMA_VERSION}."
        )
    request_type = _required_text(payload, "request_type")
    if request_type not in ALLOWED_REQUEST_TYPES:
        raise ConsoleRequestError(
            f"Unsupported request_type: {request_type!r}."
        )
    return ConsoleRequest(
        request_type=request_type,
        title=_required_text(payload, "title"),
        problem_or_need=_required_text(payload, "problem_or_need"),
        required_output=_required_text(payload, "required_output"),
        constraints=_required_list(payload, "constraints"),
        acceptance_criteria=_required_list(payload, "acceptance_criteria"),
    )


def _required_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConsoleRequestError(f"{key} must be a non-empty string.")
    return value.strip()


def _required_list(payload: dict[str, Any], key: str) -> tuple[str, ...]:
    value = payload.get(key)
    if not isinstance(value, list) or not value:
        raise ConsoleRequestError(
            f"{key} must be a non-empty JSON array."
        )
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ConsoleRequestError(
                f"Every {key} item must be a non-empty string."
            )
        result.append(item.strip())
    return tuple(result)
