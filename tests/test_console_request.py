"""Tests for automatic Console Development request envelopes."""

from curvature_console.infrastructure.console_request import parse_console_requests


def test_valid_console_request_is_parsed() -> None:
    response = (
        "Normal response.\nBEGIN_CURVATURE_CONSOLE_REQUEST\n"
        '{"schema_version":1,"request_type":"CONSOLE_TOOL_REQUEST",'
        '"title":"Add missing tool","problem_or_need":"Core is blocked.",'
        '"required_output":"One Console capability.",'
        '"constraints":["No paid API"],'
        '"acceptance_criteria":["Core can resume"]}'
        "\nEND_CURVATURE_CONSOLE_REQUEST"
    )
    result = parse_console_requests(response)

    assert not result.errors
    assert len(result.requests) == 1
    request = result.requests[0]
    assert request.request_type == "CONSOLE_TOOL_REQUEST"
    assert request.title == "Add missing tool"
    assert "Core is blocked" in request.render_request_body()


def test_invalid_console_request_is_rejected() -> None:
    response = (
        "BEGIN_CURVATURE_CONSOLE_REQUEST\n"
        '{"schema_version":1,"request_type":"UNKNOWN"}'
        "\nEND_CURVATURE_CONSOLE_REQUEST"
    )
    result = parse_console_requests(response)

    assert not result.requests
    assert len(result.errors) == 1
    assert "Unsupported request_type" in result.errors[0]


def test_download_signature_collapses_browser_collision_suffixes(tmp_path) -> None:
    from curvature_console.infrastructure.browser_bridge import (
        _download_content_signature,
    )

    first = tmp_path / "console-first-automatic-test.txt"
    duplicate = tmp_path / "console-first-automatic-test(1).txt"
    first.write_text("CONSOLE_FIRST_AUTOMATIC_ESCALATION_OK", encoding="utf-8")
    duplicate.write_text("CONSOLE_FIRST_AUTOMATIC_ESCALATION_OK", encoding="utf-8")

    assert _download_content_signature(first, first.name) == (
        _download_content_signature(duplicate, duplicate.name)
    )
