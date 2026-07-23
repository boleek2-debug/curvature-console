"""Build deterministic packages for automated ChatGPT delivery."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from curvature_console.infrastructure.context_loader import (
    ContextDocument,
    ContextLoadResult,
)
from curvature_console.presentation.attachment_record import (
    AttachmentRecord,
    format_size,
)


class TransferPackageMode(str, Enum):
    """Supported ChatGPT package modes."""

    TASK = "task"
    THREAD_HANDOFF = "thread_handoff"

    @property
    def display_name(self) -> str:
        if self is TransferPackageMode.TASK:
            return "Task Package"
        return "Thread Handoff Package"


@dataclass(frozen=True, slots=True)
class TransferPackagePolicy:
    """Mode-specific content limits."""

    conversation_character_limit: int
    document_character_limit: int | None

    @classmethod
    def for_mode(cls, mode: TransferPackageMode) -> "TransferPackagePolicy":
        if mode is TransferPackageMode.TASK:
            return cls(
                conversation_character_limit=1,
                document_character_limit=1,
            )
        return cls(
            conversation_character_limit=24_000,
            document_character_limit=None,
        )


@dataclass(frozen=True, slots=True)
class TransferPackageRequest:
    """Input required to build one department transfer package."""

    mode: TransferPackageMode
    department_id: str
    department_title: str
    responsibility: str
    context: ContextLoadResult
    conversation_text: str
    draft_text: str
    attachments: tuple[AttachmentRecord, ...]
    policy: TransferPackagePolicy | None = None


@dataclass(frozen=True, slots=True)
class TransferPackage:
    """One locally generated package for ChatGPT delivery."""

    mode: TransferPackageMode
    department_id: str
    text: str
    conversation_was_truncated: bool
    truncated_document_count: int
    included_document_count: int
    attachment_count: int


class TransferPackageBuilder:
    """Assemble deterministic packages without paid API operations."""

    def build(self, request: TransferPackageRequest) -> TransferPackage:
        """Return a complete package for the selected mode."""

        self._validate_request(request)

        if request.mode is TransferPackageMode.TASK:
            return self._build_task_package(request)

        return self._build_thread_handoff_package(request)

    def _build_task_package(
        self,
        request: TransferPackageRequest,
    ) -> TransferPackage:
        """Build a lightweight normal-task payload.

        Normal tasks run inside an existing departmental conversation in the
        shared ChatGPT Project. They intentionally do not resend the full role,
        repository documents or local conversation transcript.
        """

        sections = [
            self._header(request),
            self._authority_section(request),
            self._task_context_rule_section(),
            self._draft_section(request.draft_text),
            self._attachment_section(request.attachments),
            self._instructions_section(request),
        ]

        return TransferPackage(
            mode=request.mode,
            department_id=request.department_id,
            text="\n\n".join(
                section.rstrip() for section in sections
            ).rstrip() + "\n",
            conversation_was_truncated=False,
            truncated_document_count=0,
            included_document_count=0,
            attachment_count=len(request.attachments),
        )

    def _build_thread_handoff_package(
        self,
        request: TransferPackageRequest,
    ) -> TransferPackage:
        """Build the comprehensive continuity package for a new chat."""

        policy = request.policy or TransferPackagePolicy.for_mode(request.mode)

        conversation, conversation_truncated = self._bounded_text(
            request.conversation_text.strip(),
            policy.conversation_character_limit,
        )

        context_text, truncated_documents = self._context_section(
            request.context,
            policy.document_character_limit,
        )

        sections = [
            self._header(request),
            self._authority_section(request),
            context_text,
            self._conversation_section(
                conversation,
                conversation_truncated,
            ),
            self._draft_section(request.draft_text),
            self._attachment_section(request.attachments),
            self._instructions_section(request),
        ]

        return TransferPackage(
            mode=request.mode,
            department_id=request.department_id,
            text="\n\n".join(
                section.rstrip() for section in sections
            ).rstrip() + "\n",
            conversation_was_truncated=conversation_truncated,
            truncated_document_count=truncated_documents,
            included_document_count=request.context.loaded_count,
            attachment_count=len(request.attachments),
        )

    def _validate_request(self, request: TransferPackageRequest) -> None:
        if not request.department_id.strip():
            raise ValueError("Department id must not be empty.")
        if not request.department_title.strip():
            raise ValueError("Department title must not be empty.")
        if request.context.department_id != request.department_id:
            raise ValueError(
                "Context department does not match transfer-package department."
            )

        policy = request.policy or TransferPackagePolicy.for_mode(request.mode)
        if policy.conversation_character_limit < 1:
            raise ValueError("Conversation character limit must be positive.")
        if (
            policy.document_character_limit is not None
            and policy.document_character_limit < 1
        ):
            raise ValueError("Document character limit must be positive.")

    def _header(self, request: TransferPackageRequest) -> str:
        return "\n".join(
            [
                "# CURVATURE CONSOLE — CHATGPT TRANSFER PACKAGE",
                "",
                f"Package type: {request.mode.display_name}",
                f"Department: {request.department_title}",
                f"Department ID: {request.department_id}",
                "Delivery mode: Automated ChatGPT Plus browser bridge",
                "Paid API used by Console: NO",
                "Originating user action required: YES",
            ]
        )

    def _authority_section(self, request: TransferPackageRequest) -> str:
        return "\n".join(
            [
                "## DEPARTMENT AUTHORITY",
                "",
                f"Responsibility: {request.responsibility.strip()}",
                "",
                "Work strictly within this department's authority.",
                "Do not silently perform another department's work.",
                "When another department must act, identify the required handoff.",
            ]
        )

    def _task_context_rule_section(self) -> str:
        return "\n".join(
            [
                "## EXISTING CONVERSATION CONTEXT",
                "",
                "This is a normal task in the department's existing ChatGPT "
                "conversation.",
                "Use the conversation history and shared Project Sources already "
                "available in ChatGPT.",
                "The Console intentionally does not resend full role documents, "
                "repository documentation or local conversation history for "
                "normal tasks.",
                "Request a Thread Handoff when full continuity context is needed "
                "in a new chat.",
            ]
        )

    def _context_section(
        self,
        context: ContextLoadResult,
        document_limit: int | None,
    ) -> tuple[str, int]:
        parts = ["## LOADED DEPARTMENT CONTEXT"]
        truncated_count = 0

        if not context.documents:
            parts.extend(["", "[No context documents loaded]"])
        else:
            for document in context.documents:
                content = document.content.rstrip()
                truncated = False

                if (
                    document.label != "ROLE"
                    and document_limit is not None
                    and len(content) > document_limit
                ):
                    content, truncated = self._document_excerpt(
                        document,
                        document_limit,
                    )

                if truncated:
                    truncated_count += 1

                parts.extend(
                    [
                        "",
                        f"### {document.label}",
                        f"Source: {document.source_path}",
                        "",
                        content,
                    ]
                )

        if context.errors:
            parts.extend(
                [
                    "",
                    "### CONTEXT LOAD ERRORS",
                    "",
                    *[f"- {error}" for error in context.errors],
                ]
            )

        return "\n".join(parts), truncated_count

    def _document_excerpt(
        self,
        document: ContextDocument,
        limit: int,
    ) -> tuple[str, bool]:
        content = document.content.rstrip()
        if len(content) <= limit:
            return content, False

        marker = "\n\n[... middle omitted by bounded package ...]\n\n"
        available = max(2, limit - len(marker))
        beginning_length = available // 2
        ending_length = available - beginning_length

        return (
            content[:beginning_length].rstrip()
            + marker
            + content[-ending_length:].lstrip(),
            True,
        )

    def _conversation_section(
        self,
        conversation: str,
        truncated: bool,
    ) -> str:
        marker = (
            "[Older local conversation content omitted. "
            "The excerpt contains the newest retained characters.]\n\n"
            if truncated
            else ""
        )
        body = conversation.rstrip() or "[No local conversation recorded]"
        return "\n".join(
            [
                "## RECENT LOCAL CONVERSATION",
                "",
                f"{marker}{body}",
            ]
        )

    def _draft_section(self, draft_text: str) -> str:
        draft = draft_text.strip() or "[No current task draft]"
        return "\n".join(
            [
                "## CURRENT USER TASK",
                "",
                draft,
            ]
        )

    def _attachment_section(
        self,
        attachments: Iterable[AttachmentRecord],
    ) -> str:
        records = tuple(attachments)
        parts = [
            "## ATTACHMENT MANIFEST",
            "",
            "Files are listed locally but are not uploaded by the current "
            "browser bridge.",
            "State clearly when an attachment must be uploaded before work can "
            "continue.",
        ]

        if not records:
            parts.extend(["", "[No attachments queued]"])
            return "\n".join(parts)

        for index, record in enumerate(records, start=1):
            parts.extend(
                [
                    "",
                    f"{index}. {record.name}",
                    f"   Type: {record.suffix.upper()}",
                    f"   Size: {format_size(record.size_bytes)}",
                    f"   Local path: {record.path}",
                ]
            )

        return "\n".join(parts)

    def _instructions_section(self, request: TransferPackageRequest) -> str:
        lines = [
            "## RESPONSE INSTRUCTIONS",
            "",
            f"Respond as {request.department_title}.",
            "The CURRENT USER TASK is the immediate instruction and takes "
            "priority over general response style.",
            "If the CURRENT USER TASK requests an exact response, output "
            "exactly that response and nothing else.",
            "Treat attachment contents as unavailable until they are uploaded "
            "to this ChatGPT conversation.",
            "State clearly when a required attachment or fact is missing.",
            "Do not guess.",
            "Keep implementation code and project documentation in English.",
            "Development discussion with the user may remain in Polish.",
        ]

        if request.mode is TransferPackageMode.THREAD_HANDOFF:
            lines.extend(
                [
                    "",
                    "This package starts a new chat in the shared Curvature "
                    "ChatGPT Project.",
                    "Treat it as a continuity handoff from the previous thread.",
                    "Confirm the understood current state and exact next step "
                    "before continuing implementation.",
                ]
            )

        return "\n".join(lines)

    def _bounded_text(
        self,
        text: str,
        limit: int,
    ) -> tuple[str, bool]:
        if len(text) <= limit:
            return text, False
        return text[-limit:], True
