# Console Workflow Model

Status: Approved baseline
Version: 1.0.0
Owner: Curvature Console Development Unit

## Common lifecycle

```text
DRAFT
→ READY_FOR_REVIEW
→ APPROVED
→ QUEUED
→ PREPARING
→ RUNNING
→ VALIDATING
→ AWAITING_ACCEPTANCE
→ COMPLETED
```

Failure and control states:

```text
HELD | FAILED | CANCELLED | RETRY_PENDING | BLOCKED
```

## Browser exchange stages

```text
QUEUED
→ CONNECTING
→ NAVIGATING
→ UPLOADING
→ ENTERING_MESSAGE
→ SENDING
→ WAITING_FOR_RESPONSE
→ RECEIVING
→ CAPTURING_DOWNLOADS
→ PERSISTING
→ COMPLETED
```

## Approval rules

- sending a prepared request requires an explicit operator action;
- repository mutation requires package review and apply approval;
- commit and push require separate explicit operator approval;
- paid or externally hosted tools require explicit approval;
- retry never changes target, files or parameters silently.

## Recovery rules

- queued work survives restart;
- active work becomes interrupted and requires operator review;
- completed artifacts remain registered;
- attachments are not cleared until successful completion;
- incomplete upload means nothing is sent;
- resume occurs only from a defined safe checkpoint.

## Cross-department result return

The result is returned to the requesting department through a structured handoff with the same request identity, artifact references, validation evidence and unresolved blockers.

## Automatic Console capability escalation

A production department must not ask the operator to manually reproduce a missing-tool request. When it cannot continue because Console lacks a tool, integration or workflow, it emits `BEGIN_CURVATURE_CONSOLE_REQUEST` / `END_CURVATURE_CONSOLE_REQUEST` with schema version 1. Console validates the envelope, queues a CDU exchange, captures the CDU result and artifacts, then queues a continuation message back to the originating department.

This transport does not grant CDU authority over Chronicle direction, implementation or research conclusions. Repository writes, installation, new cost, security-sensitive execution and scope changes remain explicit operator approval gates.

## Automatic escalation chain

A chain records `SOURCE_REQUEST_ID`, `ESCALATION_CHAIN_ID` and `ESCALATION_ATTEMPT`. Attempt 1 is the initial CDU request. Attempt 2 is the only automatic corrective request and must be a bounded continuation of the same source task. A further request stops with operator action required instead of looping.
## Approved future operational-conversation model

Routine department communication will move from operator-approved message-by-message handoffs to durable operational conversations. Internal replies remain background activity. Operator-facing notifications occur only for final results, genuine operator decisions, controlled actions or terminal blockers.

The operator review surface must preserve the complete transcript and provide Accept, Reject and Ask or Continue. Reject and Ask resume the same conversation.

Autonomy is constrained by authority: the operator owns Chronicle vision; Project coordinates and specifies it; no department may silently establish missing creative decisions.

## Durable operational conversation foundation

An automatic Console escalation now owns a durable operational conversation identified by its escalation chain. The record stores the source request, participants, status and ordered transcript. Source requests, CDU responses, artifact paths and returned source-department decisions remain in one reviewable history across application restarts.

The first implementation exposes a non-modal Operational Conversations review window. Only conversations in result-ready, blocked or operator-decision states increment the toolbar review counter. Accept, Reject and Ask/Continue remain the next controlled workflow increment.
## Operator review transition
RESULT_READY, BLOCKED or AWAITING_OPERATOR_DECISION may transition to ACCEPTED through Accept. Reject and Ask / Continue append an operator message, transition to RUNNING, and queue a continuation to the original source department. The operational conversation ID and source request ID must remain unchanged. No per-message modal notification is created.

## Stable operational conversation identity

`OPERATIONAL_CONVERSATION_ID` is the durable operator-visible identity. Browser request IDs and escalation chain IDs may change between rounds, but they remain subordinate technical identifiers. Continuation must update the existing conversation to RUNNING, increment its round count, clear its prior result-ready marker for the active round and later set a new result-ready timestamp when work stops for operator review.
## Artifact capture scope
For every department exchange, the response waiter returns both normalized response text and the confirmed assistant `data-message-id`. File discovery is scoped to that exact assistant turn. A text match is a bounded fallback; selecting the last assistant locator is only a diagnostic fallback.

## Fresh artifact transport contract

Logical artifact identity and browser transport identity are separate. A logical name such as `report.txt` may remain stable across a conversation, but each artifact-producing round must use a unique physical transport name such as `report.round-2.<request-token>.txt`. CDU must generate a new file object under the exact transport name in the current assistant turn. Console rejects stale or unexpected names, maps a validated file to a collision-safe local version of the logical name and returns its observed byte count and SHA-256. Textual claims from a model do not substitute for captured-file validation.

## Closed Operator Review workflow

The durable Operator Review workflow is validated and closed for CDU escalation:

- Accept terminates the review without a follow-up departmental exchange.
- Ask / Continue and Reject append the operator instruction, return the same conversation to RUNNING and continue through the original source department.
- A new technical request may be created, but `OPERATIONAL_CONVERSATION_ID` and source task remain stable.
- Every artifact-producing round uses a unique transport filename and exact assistant-turn capture scope.
- Only Console-observed file bytes, size and SHA-256 may establish successful output.

The next workflow extension is automatic decision/blocker classification and meaningful final notifications.


## Operator attention classification

A completed operational conversation is classified into exactly one operator-attention type:

- `RESULT`: work completed and ready for review; lifecycle status `RESULT_READY`.
- `BLOCKER`: work cannot continue without resolving a concrete blocker; lifecycle status `BLOCKED`.
- `OPERATOR_DECISION`: a controlled decision or approval is required; lifecycle status `AWAITING_OPERATOR_DECISION`.

Explicit workflow-state markers are authoritative. Conservative textual markers are a fallback, and an otherwise completed response defaults to `RESULT`. The classification and reason are persisted with the conversation and displayed in Operator Review. Internal routing, automatic CDU exchanges and intermediate progress do not create modal operator notifications.
