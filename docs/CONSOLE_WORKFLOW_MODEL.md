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
