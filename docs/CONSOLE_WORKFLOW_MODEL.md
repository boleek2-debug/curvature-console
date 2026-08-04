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
