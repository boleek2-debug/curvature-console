"""Tests for background interdepartmental operational requests."""

from curvature_console.infrastructure.operational_request import (
    BEGIN_MARKER,
    END_MARKER,
    parse_operational_requests,
)


def _block(target: str = "core") -> str:
    return f'''{BEGIN_MARKER}
{{
  "schema_version": 1,
  "target_department_id": "{target}",
  "title": "Assess implementation consequences",
  "task": "Assess feasibility without changing product direction.",
  "relevant_context": "Project owns approved intent; Core owns implementation.",
  "expected_output": "A bounded feasibility result.",
  "constraints": ["Do not make product decisions."],
  "acceptance_criteria": ["Risks are explicit", "A final workflow_state is returned"]
}}
{END_MARKER}'''


def test_valid_operational_request_is_parsed() -> None:
    parsed = parse_operational_requests(
        _block("core"), source_department_id="project"
    )
    assert parsed.errors == ()
    assert len(parsed.requests) == 1
    request = parsed.requests[0]
    assert request.target_department_id == "core"
    assert request.title == "Assess implementation consequences"
    assert "## Acceptance criteria" in request.render_request_body()


def test_all_production_department_pairs_are_supported() -> None:
    pairs = (
        ("project", "core"),
        ("project", "research"),
        ("core", "project"),
        ("core", "research"),
        ("research", "project"),
        ("research", "core"),
    )
    for source, target in pairs:
        parsed = parse_operational_requests(
            _block(target), source_department_id=source
        )
        assert parsed.errors == ()
        assert parsed.requests[0].target_department_id == target


def test_same_department_and_malformed_blocks_are_rejected() -> None:
    same = parse_operational_requests(
        _block("project"), source_department_id="project"
    )
    assert same.requests == ()
    assert "must be different" in same.errors[0]

    malformed = parse_operational_requests(
        f"{BEGIN_MARKER}\nnot-json\n{END_MARKER}",
        source_department_id="research",
    )
    assert malformed.requests == ()
    assert malformed.errors
