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

## 2026-08-05 — CDU-004B1 operational conversation foundation

- Added durable operational conversation and transcript persistence.
- Automatic department-to-CDU escalation chains now create a dedicated background conversation record.
- CDU replies, returned source-department replies and captured artifact paths are appended to the same transcript.
- Added an Operational Conversations review window and toolbar review counter.
- Internal exchanges remain non-modal; operator-facing review count appears only for result, blocker or decision states.
## 2026-08-05 — CDU-004B2 Operator Review
- Added Accept, Reject and Ask / Continue controls to Operational Conversations.
- Operator decisions are persisted in the existing conversation transcript.
- Reject and Ask require a comment and continue through the original source department route.
- Accept closes the review without creating another interdepartmental exchange.
- Review notifications remain limited to final results, blockers and operator decisions.

## 2026-08-05 — CDU-004B2A Same-conversation continuation and lifecycle visibility

- Reused the existing operational conversation ID for operator Ask / Continue rounds.
- Kept new technical request and escalation IDs inside the same durable conversation.
- Added persistent round counts and result/closure timestamps.
- Added visible lifecycle details and a clear end-of-conversation marker in Operator Review.
- Added regression coverage for continuation identity and lifecycle persistence.
## CDU-004B2B — Exact completed-turn artifact capture
- Browser Bridge now scopes generated-file capture to the exact assistant message confirmed by response identity.
- Prevents a later operational-conversation round from downloading a stale attachment card from an earlier CDU response.
- Added regression coverage for message-id-first turn resolution.

## 2026-08-05 — CDU-004B2C Fresh artifact transport identity

- Added a unique physical transport filename for each generated artifact in each operational-conversation round.
- CDU requests now distinguish stable logical filenames from one-use transport filenames.
- Console validates the exact transport filename before accepting a generated file.
- Accepted transport files are mapped back to collision-safe local versions of the logical filename.
- Automatic return metadata now includes the logical filename, actual byte count and SHA-256 calculated by Console.
- Stale or reused file cards are rejected instead of being reported to the source department as successful output.

## 2026-08-05 — CDU-004B1–B2C closure

- Full target validation passed with 251 tests and clean `git diff --check`.
- Live restart persistence, Accept, Ask / Continue and Reject paths passed.
- Same-conversation continuation preserved one operator-visible identity and one source task.
- Exact assistant-turn scoping prevented stale cross-turn attachment selection.
- Unique per-round transport filenames produced fresh physical file objects.
- Console verified actual byte counts and SHA-256 values before returning results to Core.
- Stage-two and rejected-result replacement artifacts were physically captured and verified.
- CDU-004B1, CDU-004B2, CDU-004B2A, CDU-004B2B and CDU-004B2C are closed.
