# Console Development Unit State Snapshot

Status: Operational
Version: 1.2.0
Owner: Curvature Console Development Unit
Last Updated: 2026-08-05

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

## 2026-08-04 — CDU-004 prepared

Baseline commit: `bf3fc85`.

Prepared changes add automatic department-to-CDU escalation and automatic CDU-to-source return. Targeted parser and transfer-package tests: 23 passed. Full project validation and live end-to-end verification remain required before commit and push.

## Prepared next state — CDU-004A

Base commit: `5add1e5`

Prepared changes add generated-artifact deduplication, bounded two-attempt escalation chains, automatic defect snapshot/log attachments and terminal operator-stop semantics. Local validation and live verification are pending.
## 2026-08-05 — CDU-004A live verification PASS

Working base commit: `5add1e5`.

Evidence:

- 243 automated tests passed;
- `git diff --check` passed;
- Core emitted the structured request automatically;
- Console routed it to CDU automatically;
- CDU generated `console-first-automatic-test.txt`;
- the Estuary and native-download representations had the same SHA-256 and the duplicate was suppressed;
- exactly one 37-byte artifact was returned;
- Core verified filename, UTF-8 content and SHA-256 and accepted the retest;
- no corrective escalation loop occurred.

Remaining closure work: update documentation, commit, push and produce a clean snapshot.

## Approved next direction

The full capability-based development sequence is recorded in `docs/CURVATURE_CONSOLE_FIRST_ACTION_PLAN.md`. The next implementation area after CDU-004A closure is durable background interdepartmental conversation and operator review, with operator-owned vision and consequence-based approval gates.
