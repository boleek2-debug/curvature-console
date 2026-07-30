"""Tests for department-generated supervised handoff proposals."""

from __future__ import annotations

from curvature_console.infrastructure.handoff_proposal import (
    BEGIN_MARKER,
    END_MARKER,
    parse_handoff_proposals,
)


def _block(target: str = "core") -> str:
    return f'''{BEGIN_MARKER}
{{
  "schema_version": 1,
  "target_department_id": "{target}",
  "title": "Implement bounded intake",
  "reason": "Core owns production implementation.",
  "task": "Add validated proposal intake.",
  "relevant_context": "Existing Bridge Controls persist handoffs.",
  "expected_output": "Complete source and tests.",
  "acceptance_criteria": ["Valid drafts are persisted", "Nothing is auto-sent"]
}}
{END_MARKER}'''


def test_valid_proposal_is_parsed_and_rendered_for_review() -> None:
    result = parse_handoff_proposals(
        "Normal response.\n\n" + _block(),
        source_department_id="project",
    )

    assert result.errors == ()
    assert len(result.proposals) == 1
    proposal = result.proposals[0]
    assert proposal.target_department_id == "core"
    assert proposal.title == "Implement bounded intake"
    rendered = proposal.render_visible_message()
    assert "# Implement bounded intake" in rendered
    assert "## Acceptance criteria" in rendered
    assert "- Nothing is auto-sent" in rendered


def test_multiple_valid_proposals_are_preserved_in_response_order() -> None:
    result = parse_handoff_proposals(
        _block("core") + "\n" + _block("research"),
        source_department_id="project",
    )

    assert [item.target_department_id for item in result.proposals] == [
        "core",
        "research",
    ]


def test_same_department_target_is_rejected_without_losing_other_text() -> None:
    result = parse_handoff_proposals(
        "Explanation before.\n" + _block("project"),
        source_department_id="project",
    )

    assert result.proposals == ()
    assert len(result.errors) == 1
    assert "must be different" in result.errors[0]


def test_malformed_block_is_reported_and_never_becomes_a_draft() -> None:
    result = parse_handoff_proposals(
        f"{BEGIN_MARKER}\nnot-json\n{END_MARKER}",
        source_department_id="research",
    )

    assert result.proposals == ()
    assert len(result.errors) == 1
    assert "Expecting value" in result.errors[0]
