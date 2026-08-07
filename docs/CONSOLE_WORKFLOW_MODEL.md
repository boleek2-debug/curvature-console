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

- every Browser Bridge exchange is durably recorded as `QUEUED` before worker execution;
- active transport progress is persisted independently from the higher-level operational conversation;
- B7A records transport truth but does not automatically reconstruct or resend an interrupted worker;
- B7C must reconcile non-terminal ledger entries after restart before any retry, so a possibly submitted request is never blindly duplicated;
- completed artifacts remain registered;
- attachments are not cleared until successful completion;
- incomplete upload means nothing is sent;
- resume occurs only from a defined safe checkpoint.

### Durable Browser Exchange lifecycle

```text
QUEUED
→ STARTED
→ SUBMITTED
→ RESPONSE_RECEIVED
→ COMPLETED
```

Terminal alternatives are `FAILED`, `CANCELLED` and `ROUTE_UNVERIFIED`. The ledger stores the logical workflow identifier separately from the Browser Bridge request ID, plus requested/observed route, confirmation marker, timestamps, failure reason and the cancellation submission boundary. This execution ledger does not replace operational-conversation state; it records transport attempts underneath it.

### Failure / cancel closure

A terminal transport failure does not silently leave the logical workflow in a process-owned state. When a Browser Bridge exchange belonging to an operational conversation fails or is cancelled while that conversation is `RUNNING` or `WAITING_SOURCE`, the conversation becomes `BLOCKED`, receives `BLOCKER` attention and records the reason in its timeline. Cancelling transport is therefore distinct from explicitly abandoning the workflow.

Supervised handoffs whose transport-only states survive a process restart are reconciled conservatively: `SENT`, `RETURN_SENT` and `UPDATE_SENT` become `HELD`. They are never automatically resent at B7B.

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

## Thread Handoff and local pressure epochs

A successful Thread Handoff changes the active ChatGPT conversation route and starts a new local pressure epoch. The full Reply Viewer transcript remains cumulative for operator history. Console appends an explicit `=== NEW THREAD AFTER HANDOFF ===` marker and calculates Thread Pressure only from the latest marker onward. Because the marker is stored in the normal persisted transcript, restart does not reconnect pressure to the replaced thread.

## Production-department operational requests

Project, Core and Research may open a background operational conversation by emitting one explicit `BEGIN_CURVATURE_OPERATIONAL_REQUEST` JSON block. The block names the target department, task, context, expected output, constraints and acceptance criteria. This is separate from `BEGIN_CURVATURE_HANDOFF_PROPOSAL`: supervised handoffs remain operator-approved and are not silently converted into autonomous routing.

Console creates or resumes one durable conversation, appends the source request, sends it to the target department, captures the target response and artifacts, and returns the result to the original source. The source may emit one further operational request in the same round when another department contribution is genuinely required. Nested CDU escalation stays inside the same operational conversation. The workflow stops at RESULT, BLOCKER or OPERATOR_DECISION, or at a six-hop safety limit that requires operator review.

Supported production routes are Project ↔ Core, Project ↔ Research and Core ↔ Research. Ordinary internal transitions remain non-modal; only terminal attention states increment Operator Review.

## Authority and consequence gate

Before an operational request is routed, Console evaluates whether the request crosses an operator-owned boundary. Routine consultation, research, implementation analysis and validation continue automatically. Product direction, scope, canon, art direction, financial commitment, installation, security-sensitive action, shared repository mutation and unresolved departmental conflict become `AWAITING_OPERATOR_DECISION` before target execution. The stop records a decision domain, concrete question, options and consequences.
