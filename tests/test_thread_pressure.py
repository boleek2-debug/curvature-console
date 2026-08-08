"""Tests for independent local thread-pressure estimation."""

from __future__ import annotations

from pathlib import Path

from curvature_console.infrastructure.thread_pressure import (
    ACTIVE_THREAD_HANDOFF_MARKER,
    ThreadPressureEstimator,
    ThreadPressureLevel,
    active_thread_conversation_text,
)


def test_green_pressure_for_small_local_workload() -> None:
    snapshot = ThreadPressureEstimator().estimate("small transcript", "draft")

    assert snapshot.level is ThreadPressureLevel.GREEN
    assert snapshot.estimated_tokens > 0
    assert "comfortable" in snapshot.handoff_recommendation


def test_amber_and_red_thresholds_are_deterministic() -> None:
    estimator = ThreadPressureEstimator()

    amber = estimator.estimate("x" * (estimator.AMBER_THRESHOLD * 4))
    red = estimator.estimate("x" * (estimator.RED_THRESHOLD * 4))

    assert amber.level is ThreadPressureLevel.AMBER
    assert red.level is ThreadPressureLevel.RED
    assert "strongly recommended" in red.handoff_recommendation


def test_attachment_sizes_contribute_to_pressure(tmp_path: Path) -> None:
    attachment = tmp_path / "research.bin"
    attachment.write_bytes(b"x" * 400)

    snapshot = ThreadPressureEstimator().estimate(
        conversation_text="",
        attachment_paths=(attachment, tmp_path / "missing.bin"),
    )

    assert snapshot.attachment_bytes == 400
    assert snapshot.attachment_tokens == 100
    assert snapshot.estimated_tokens == 100


def test_pressure_snapshot_exposes_handoff_actions() -> None:
    estimator = ThreadPressureEstimator()

    green = estimator.estimate("small")
    amber = estimator.estimate("x" * (estimator.AMBER_THRESHOLD * 4))
    red = estimator.estimate("x" * (estimator.RED_THRESHOLD * 4))

    assert not green.should_prepare_handoff
    assert not green.should_avoid_regular_task
    assert amber.should_prepare_handoff
    assert not amber.should_avoid_regular_task
    assert red.should_prepare_handoff
    assert red.should_avoid_regular_task


def test_active_thread_text_uses_only_latest_handoff_epoch() -> None:
    transcript = (
        ("old-history " * 1000)
        + "\n\n"
        + ACTIVE_THREAD_HANDOFF_MARKER
        + "\n\n=== USER TASK ===\nnew task"
        + "\n\n=== ASSISTANT RESPONSE ===\nnew answer"
    )

    active = active_thread_conversation_text(transcript)

    assert active.startswith(ACTIVE_THREAD_HANDOFF_MARKER)
    assert "old-history" not in active
    assert "new task" in active
    assert "new answer" in active


def test_active_thread_text_uses_latest_marker_when_multiple_handoffs_exist() -> None:
    transcript = (
        "first"
        + ACTIVE_THREAD_HANDOFF_MARKER
        + "second"
        + ACTIVE_THREAD_HANDOFF_MARKER
        + "third"
    )

    assert active_thread_conversation_text(transcript) == (
        ACTIVE_THREAD_HANDOFF_MARKER + "third"
    )
