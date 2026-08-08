"""Local advisory thread-pressure estimation for Curvature Console."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable


ACTIVE_THREAD_HANDOFF_MARKER = "=== NEW THREAD AFTER HANDOFF ==="


def active_thread_conversation_text(conversation_text: str) -> str:
    """Return only the transcript belonging to the current ChatGPT thread.

    Console keeps cumulative department history for operator review. A successful
    Thread Handoff appends ACTIVE_THREAD_HANDOFF_MARKER; pressure must be
    calculated only from the newest marker onward.
    """

    if ACTIVE_THREAD_HANDOFF_MARKER not in conversation_text:
        return conversation_text
    _, _, active_text = conversation_text.rpartition(
        ACTIVE_THREAD_HANDOFF_MARKER
    )
    return ACTIVE_THREAD_HANDOFF_MARKER + active_text


class ThreadPressureLevel(str, Enum):
    """Advisory pressure state derived only from local Console data."""

    GREEN = "GREEN"
    AMBER = "AMBER"
    RED = "RED"


@dataclass(frozen=True, slots=True)
class ThreadPressureSnapshot:
    """One immutable local estimate for a department conversation."""

    level: ThreadPressureLevel
    estimated_tokens: int
    conversation_tokens: int
    draft_tokens: int
    attachment_tokens: int
    attachment_bytes: int

    @property
    def handoff_recommendation(self) -> str:
        """Return the advisory handoff message for this pressure level."""

        if self.level is ThreadPressureLevel.RED:
            return "Thread Handoff strongly recommended before more work."
        if self.level is ThreadPressureLevel.AMBER:
            return "Prepare a Thread Handoff soon."
        return "Current thread has comfortable local headroom."

    @property
    def should_prepare_handoff(self) -> bool:
        """Return whether the current local estimate warrants handoff action."""

        return self.level is not ThreadPressureLevel.GREEN

    @property
    def should_avoid_regular_task(self) -> bool:
        """Return whether a regular task should require a strong warning."""

        return self.level is ThreadPressureLevel.RED


class ThreadPressureEstimator:
    """Estimate pressure without claiming ChatGPT's exact context capacity."""

    CHARS_PER_TOKEN = 4
    AMBER_THRESHOLD = 50_000
    RED_THRESHOLD = 80_000

    def estimate(
        self,
        conversation_text: str,
        draft_text: str = "",
        attachment_paths: Iterable[Path] = (),
    ) -> ThreadPressureSnapshot:
        """Estimate local workload from transcript, draft and attachments."""

        conversation_tokens = self._text_tokens(conversation_text)
        draft_tokens = self._text_tokens(draft_text)
        attachment_bytes = self._attachment_bytes(attachment_paths)
        attachment_tokens = self._byte_tokens(attachment_bytes)
        estimated_tokens = (
            conversation_tokens + draft_tokens + attachment_tokens
        )

        if estimated_tokens >= self.RED_THRESHOLD:
            level = ThreadPressureLevel.RED
        elif estimated_tokens >= self.AMBER_THRESHOLD:
            level = ThreadPressureLevel.AMBER
        else:
            level = ThreadPressureLevel.GREEN

        return ThreadPressureSnapshot(
            level=level,
            estimated_tokens=estimated_tokens,
            conversation_tokens=conversation_tokens,
            draft_tokens=draft_tokens,
            attachment_tokens=attachment_tokens,
            attachment_bytes=attachment_bytes,
        )

    def _text_tokens(self, value: str) -> int:
        return self._byte_tokens(len(value))

    def _byte_tokens(self, value: int) -> int:
        if value <= 0:
            return 0
        return (value + self.CHARS_PER_TOKEN - 1) // self.CHARS_PER_TOKEN

    def _attachment_bytes(self, paths: Iterable[Path]) -> int:
        total = 0
        for raw_path in paths:
            path = Path(raw_path).expanduser()
            try:
                if path.is_file():
                    total += path.stat().st_size
            except OSError:
                continue
        return total
