# Console Development Unit State Snapshot

Status: Operational
Version: 1.1.0
Owner: Curvature Console Development Unit
Last Updated: 2026-08-04

## Repository

```text
Repository: ~/curvature-console
Branch: main
Verified commit: 0abfee2da345effa4e8293478abbcfcc11b72772
origin/main: same
Working tree at supplied snapshot: clean
```

## Verified baseline

- 231 automated tests passed after CDU-002B;
- `git diff --check` passed;
- CDU identity migration and resilient attachments live PASS;
- generated downloads live PASS;
- normal department and CDU requests share one FIFO Browser Bridge queue;
- supervised handoff delivery, progress update and return path use the same queue;
- active and queued operations have controlled cancellation semantics.

## Current milestone

CDU-003 — Formal Console requests and authority routing.

## CDU-003 package scope

- approved request types: `CONSOLE_TOOL_REQUEST`, `CONSOLE_INTEGRATION_REQUEST`, `CONSOLE_WORKFLOW_REQUEST`, `CONSOLE_DEFECT`, `CONSOLE_DECISION_REQUEST`;
- requesting department metadata for Operator, Project, Core, Research and CDU;
- formal request template using the fields from `CONSOLE_TOOL_REQUEST_PROTOCOL.md`;
- explicit routing boundary included in every formal CDU transfer package;
- no autonomous cross-department execution: required work outside CDU authority must be identified as a handoff.

## Immediate next step

Apply, validate and live-test one formal request from a production department to CDU. Then execute the Console-first migration workflow test before declaring the browser chat fallback-only.

## Known follow-up

Generated-file cards can expose multiple equivalent controls, causing duplicate captures. Collision handling is safe, but candidate de-duplication remains a future optimisation rather than a current blocker.


## CDU-003A prepared

Shared authority boundaries and formal Console request routing are now propagated into every Project, Core and Research Task Package and Thread Handoff Package. Local validation and live package inspection remain required before commit.
