# Curvature Console Handoff

Status: Active
Version: 3.0.0
Owner: Curvature Console Development Unit
Last Updated: 2026-08-04

## Current verified base

```text
Repository: ~/curvature-console
Branch: main
HEAD: 2aad8a866ef78660d1c5369d88334bac49611016
origin/main: same
Working tree: clean in supplied snapshot
```

## Closed milestones

- Support Unit chat, attachments, screenshot paste and downloads;
- Support Unit to Console Development Unit identity migration;
- preserved conversation route and legacy state compatibility;
- resilient automatic attachment readiness;
- 226 automated tests and live end-to-end CDU verification before push.

## Active milestone

```text
CDU-001B — Authoritative Console Development Unit documentation
```

Deliver the approved CDU documentation suite in `docs/` and update root repository references.

## Next milestone

```text
CDU-002 — Shared Sequential Browser Bridge Queue
```

The queue will accept independent Project, Core, Research and CDU requests while allowing only one active Browser Bridge exchange at a time.

## Authority

CDU owns Console development and integration. It does not decide Chronicle direction, implementation or research conclusions.

## CDU-004 current implementation unit

Automatic Tool Escalation and Return is prepared for validation.

Expected live flow:

Project/Core/Research task → department emits structured Console request → shared Browser Bridge queue sends it to CDU → CDU result and captured artifact paths return automatically to the source department → source department resumes its original task.

Closure requires automated tests, live verification, current documentation, clean repository state and confirmed source-department continuation.
