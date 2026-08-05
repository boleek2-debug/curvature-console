# Curvature Console Changelog

Status: Active
Version: 2.0.0
Owner: Curvature Console Development Unit
Last Updated: 2026-08-05

## 2026-08-04 — CDU-001A / CDU-001A1

Completed and pushed:

- Support Unit renamed to Console Development Unit;
- existing conversation route and legacy state preserved;
- new `CONSOLE_DEV_CASE_ID` identity;
- new report and inbox paths under `console-development`;
- screenshot, automatic attachments and generated downloads live-verified;
- resilient readiness handling for transient attachment `unknown` states;
- 226 automated tests passed before final live verification;
- commit `2aad8a8` pushed and clean snapshot created.

## 2026-08-04 — CDU-001B

Prepared authoritative CDU documentation suite and root documentation references. Validation and live review pending.

## Historical record

Earlier detailed milestone history remains available in Git history and prior snapshots. New CDU documentation is authoritative for current Console direction.


## 2026-08-04 — CDU-002A Shared Browser Bridge Queue Foundation

- Added FIFO sequential queue for normal department and Console Development exchanges.
- Added toolbar queue status showing active department and waiting count.
- Preserved one active Browser Bridge worker at a time.
- Added regression tests for queue ordering and automatic continuation.
- Deferred supervised handoff queue integration to CDU-002B.

## CDU-002B — Shared queue for supervised handoffs

- Routed approved handoff delivery, same-handoff progress updates and supervised returns through the shared sequential Browser Bridge queue.
- Deferred modal handoff progress display until the queued exchange actually becomes active.
- Added operator cancellation handling for active and queued department exchanges.
- Preserved the single-active-exchange invariant and failure-to-held handoff safety behavior.

## CDU-003 — Formal Console requests and authority routing

- added approved Console request types to the Console Development workspace;
- added requesting-department metadata for Operator, Project, Core, Research and CDU;
- added an insertable formal request template covering the approved protocol fields;
- added explicit authority-routing instructions to Console Development requests;
- preserved the shared Browser Bridge queue and the dedicated CDU conversation route.

## 2026-08-04 — CDU-003A shared authority and routing propagation

- Added one shared cross-department authority and Console-routing section to every normal Task Package and Thread Handoff Package.
- Project, Core and Research now receive the same explicit ownership boundaries and the five formal Console request types.
- Added regression coverage for all three departments in both transfer-package modes.

## 2026-08-04 — CDU-004 Automatic Tool Escalation and Return

Prepared:

- machine-readable Console request envelope for Project, Core and Research;
- automatic routing of missing-tool, integration, workflow, defect and decision requests to Console Development Unit;
- automatic return of the CDU response and captured artifact paths to the originating department;
- source-task continuation without operator copy/paste;
- documentation-closure requirement included in automatic CDU requests;
- parser and transfer-package regression tests.

## 2026-08-04 — CDU-004A Artifact deduplication and escalation chain control

- duplicate captures of one logical generated artifact are suppressed by canonical filename, size and SHA-256;
- automatic escalation chains carry a stable chain identifier and attempt number;
- automatic corrective escalation is limited to two CDU attempts before operator action is required;
- CONSOLE_DEFECT escalation automatically attaches the latest Console snapshot and runtime log;
- automatic return metadata preserves the originating request and chain.
## 2026-08-05 — CDU-004A live verification and Console-first action plan

- full validation passed with 243 tests and clean `git diff --check`;
- live Core → CDU → Core retest passed;
- identical Estuary and native-download captures were reduced to one logical artifact;
- Core verified exact filename, content and SHA-256 and accepted the result;
- no escalation loop occurred;
- added the approved capability-based Console-first action plan for the whole Curvature organisation;
- documented operator-owned vision, autonomous departmental collaboration, meaningful decision gates, separate operational conversations, Conversation Review and later voice accessibility.
