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

        authoritative_context, included_documents = (
            self._task_authoritative_context_section(request.context)
        )
        sections = [
            self._header(request),
            self._authority_section(request),
            self._cross_department_routing_section(),
            self._task_context_rule_section(),
            authoritative_context,
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
            included_document_count=included_documents,
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
            self._cross_department_routing_section(),
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

    def _cross_department_routing_section(self) -> str:
        return "\n".join(
            [
                "## CROSS-DEPARTMENT AUTHORITY AND CONSOLE ROUTING",
                "",
                "Project owns Chronicle direction, scope, priorities and product decisions.",
                "Core owns Chronicle architecture, implementation, validation, persistence and tests.",
                "Research owns evidence, source acquisition, provenance and research conclusions.",
                "Console Development Unit owns Curvature Console, Browser Bridge, routing, handoff tooling, workflows, integrations, diagnostics, packages, artifacts and Console validation.",
                "",
                "Do not decide or implement work outside the current department's authority.",
                "When another production department must act, identify the required supervised handoff to Project, Core or Research.",
                "When Console capability or Console repair is required, identify one formal Console request instead of silently implementing Console changes.",
                "Use the most specific Console request type:",
                "- CONSOLE_TOOL_REQUEST — missing or changed Console capability.",
                "- CONSOLE_INTEGRATION_REQUEST — connection to a tool, service, repository or runtime.",
                "- CONSOLE_WORKFLOW_REQUEST — orchestration, routing or repeated operational flow.",
                "- CONSOLE_DEFECT — reproducible Console or Browser Bridge failure.",
                "- CONSOLE_DECISION_REQUEST — a Console architecture, policy or implementation decision requiring CDU authority.",
                "State the requesting department, problem or need, required input/output, constraints and acceptance criteria.",
                "Do not claim that a handoff or Console request was delivered unless Console confirms delivery.",
            ]
        )

    def _task_context_rule_section(self) -> str:
        return "\n".join(
            [
                "## EXISTING CONVERSATION CONTEXT",
                "",
                "This is a normal task in the department's existing ChatGPT "
                "conversation.",
                "Use the existing conversation history for continuity.",
                "The authoritative local Console state and handoff documents "
                "included below override stale ChatGPT Project Sources or older "
                "conversation statements when they conflict.",
                "The Console intentionally does not resend the full role, full "
                "repository documentation or local transcript for normal tasks.",
                "Request a Thread Handoff when full continuity context is needed "
                "in a new chat.",
            ]
        )

    def _task_authoritative_context_section(
        self,
        context: ContextLoadResult,
    ) -> tuple[str, int]:
        """Return the current local state required for a reliable task.

        ChatGPT Project Sources are not refreshed by the Console's local
        ``Refresh All Context`` action. A normal task therefore carries the two
        concise Console documents that define the verified state and exact next
        step. This prevents stale Project Sources from silently overriding the
        repository state that the user has just refreshed.
        """

        wanted_suffixes = (
            "00_CURVATURE_CONSOLE_CURRENT_STATE.md",
            "CURVATURE_CONSOLE_HANDOFF.md",
        )
        candidates = tuple(
            document
            for document in context.documents
            if any(
                document.label.endswith(suffix)
                for suffix in wanted_suffixes
            )
        )

        parts = [
            "## AUTHORITATIVE LOCAL CONSOLE CONTEXT",
            "",
            "The following documents were read from the local repositories "
            "when this task was prepared.",
        ]

        if not candidates:
            parts.extend(
                [
                    "",
                    "[No authoritative Console state documents were loaded]",
                ]
            )
            return "\n".join(parts), 0

        # Normal Task packages must stay lightweight. The current-state
        # document is authoritative and has first priority. Additional
        # documents are included only while the complete authoritative
        # section remains within the fixed character budget. Thread Handoff
        # packages continue to carry the full context through their separate
        # builder path.
        character_budget = 12_000
        included_count = 0
        used_characters = len("\n".join(parts))

        for document in candidates:
            document_block = "\n".join(
                [
                    "",
                    f"### {document.label}",
                    f"Source: {document.source_path}",
                    "",
                    document.content.rstrip(),
                ]
            )
            if (
                included_count > 0
                and used_characters + len(document_block) > character_budget
            ):
                parts.extend(
                    [
                        "",
                        (
                            "[Additional authoritative document omitted from "
                            "this normal Task package to keep the browser "
                            "payload bounded. Use Thread Handoff when its full "
                            "contents are required.]"
                        ),
                    ]
                )
                continue

            parts.append(document_block)
            used_characters += len(document_block)
            included_count += 1

        return "\n".join(parts), included_count

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
            "When another Curvature department must act, include one machine-readable "
            "handoff proposal block after your normal response. Do not claim that the "
            "handoff was sent; Console will capture it as a draft for user review.",
            "Use exactly this envelope, with valid JSON between the markers:",
            "BEGIN_CURVATURE_HANDOFF_PROPOSAL",
            '{"schema_version":1,"target_department_id":"project|core|research",'
            '"title":"...","reason":"...","task":"...",'
            '"relevant_context":"...","expected_output":"...",'
            '"acceptance_criteria":["..."]}',
            "END_CURVATURE_HANDOFF_PROPOSAL",
            "Never target the department that is producing the response.",
            "If no other department must act, do not include a proposal block.",
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
