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
