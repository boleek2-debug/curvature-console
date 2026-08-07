# Curvature Console Changelog


## 2026-08-06 — CDU-004B6 decision resolution candidate

- Persisted gated decision context and the exact blocked operational request.
- Added durable decision status, selected option and resolution timestamp.
- Added dynamic option selection with explicit machine action types to Operational Conversations.
- Pending gated decisions now use one Confirm decision action. The selected option determines APPROVE, REJECT, REVISE, LIMITED_APPROVAL or REQUEST_NON_MUTATING_PREVIEW behaviour. Repository preview is explicitly bounded to validation plus patch/diff preparation with no commit or push; other decision domains use revision or limited approval rather than a generic dry-run.
- REJECT closes without routing; approval and revision-style options return to the source with the exact selected scope.
- Existing Accept behaviour for ordinary completed results remains unchanged.
- Targeted persistence validation: 8 tests passed in the packaging environment; full target-environment validation remains required.

Status: Active
Version: 2.0.0
Owner: Curvature Console Development Unit
Last Updated: 2026-08-06


## 2026-08-06 — CDU-004B4 production-department operational conversations

- added explicit background operational-request blocks for Project, Core and Research;
- routed Project ↔ Core, Project ↔ Research and Core ↔ Research requests without operator message transport;
- preserved one durable operational conversation across automatic target replies, nested CDU escalation and source continuation;
- returned generated target artifacts to the requesting department with Console-observed size and SHA-256 metadata;
- retained supervised handoff proposals as a separate operator-approved workflow;
- added a six-hop safety limit and operator stop instead of an autonomous loop;
- added parser and all-pair regression coverage; full target-environment validation passed with 260 tests, and live Project → Core → Project, Project → Research → Project and Core → Research → Core routes all passed; CDU-004B4 is closed.

## 2026-08-06 — CDU-004B3 closure and thread-pressure handoff defect fix

- closed CDU-004B3 after 255 automated tests and live RESULT, BLOCKER and OPERATOR_DECISION verification;
- fixed Thread Pressure remaining bound to the pre-handoff transcript after a successful Thread Handoff;
- preserved cumulative Reply Viewer history across handoffs;
- added an explicit new-thread transcript marker so pressure is calculated only from the active thread epoch;
- persisted the marker in the normal department transcript so restart continuity keeps the reset;
- added regression coverage for direct panel behavior and Browser Bridge handoff success.

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

## 2026-08-05 — CDU-004B3 attention classification and meaningful notifications

- Added automatic classification of completed operational conversations as RESULT, BLOCKER or OPERATOR_DECISION.
- Explicit workflow markers take precedence; conservative blocker and decision phrases are used as fallback.
- Persisted the attention class and reason with each operational conversation.
- Operational Conversations now displays the classification and its reason.
- Toolbar review counts are grouped by decision, blocker and result instead of one undifferentiated number.
- Internal department-to-department transitions remain non-modal; only completed results, blockers and operator decisions surface as operator attention.
- Added persistence and classifier regression coverage.

## CDU-004B5 — authority and consequence decision gates

- Added pre-routing decision gates for operator-owned product direction, canon/art direction, cost, installation, security, repository mutation and unresolved cross-department conflict.
- Routine department consultation, validation and implementation analysis continue without operator interruption.
- Operator stops now include a concrete question, options and consequences rather than a generic decision marker.
- Operational target prompts explicitly prohibit departments from silently making operator-owned decisions.

### CDU-004B6 resolved-decision history-only UI hotfix

- Resolved gated decisions no longer expose Accept, Reject, Ask / Continue, Confirm decision, decision-option, or operator-comment controls.
- A resolved decision is now a read-only historical record; only the dialog Close action remains available.
- Added UI regression coverage for a rejected gated decision.

### CDU-004B6 operational attention counter and restart recovery hotfix

- Operational Conversations badge now uses correct singular/plural labels.
- Resolved gated-decision results are excluded from actionable attention counts.
- Conversations left RUNNING by a previous Console process are recovered as BLOCKED with explicit BLOCKER attention on startup.
- Added regression coverage for resolved-result counting and interrupted RUNNING recovery.

### CDU-004B6 operator-review semantics and audit trail correction

- Renamed ordinary review actions to describe their actual effects: Close as accepted, Return to source, Request clarification / continue, and Close as abandoned.
- Added Close as abandoned as a local terminal action. It records the operator reason, closes the conversation as CANCELLED, starts no worker and creates no follow-up result requiring acceptance.
- Return to source remains the explicit corrective round and requires an operator comment.
- Added causal runtime audit events for submitted and persisted operator actions, local closure without resume, and queued source-department resume.
- Added regression coverage for explicit action labels and local abandoned closure without a browser exchange.

## 2026-08-06 — CDU-004B6 orphaned WAITING_SOURCE recovery

- Startup recovery now converts both `RUNNING` and `WAITING_SOURCE` operational conversations to `BLOCKED / BLOCKER` because neither can retain a live in-process worker after Console termination.
- Startup writes `operational_recovery_complete` with the recovered count and covered statuses.

## 2026-08-07 — CDU-004B6 Project-source plan approval interception

- Added a dedicated `IMPLEMENTATION_PLAN_APPROVAL` decision domain.
- Approval/authorization decisions about an implementation plan are intercepted before the target department worker is queued.
- Routine requests to prepare an implementation plan remain ungated.
- Added an `operational_decision_gate_intercepted` runtime audit event so live routing evidence shows the gate firing before any target worker.
- Added regression tests for both approval interception and routine plan preparation.
### 2026-08-07 — CDU-004B6 implementation-plan revision routing fix
- Narrowed `IMPLEMENTATION_PLAN_APPROVAL` detection to explicit approval/authorization actions in the request title/task.
- Revision work such as `Revise Chronicle implementation plan` is no longer gated merely because context or expected output mentions a later approval decision.
- Explicit approval of a revised implementation plan remains gated.
- Added regression coverage for both the false-positive revision case and explicit revised-plan approval.

### 2026-08-07 — CDU-004B6 direction-context false-positive fix
- Product-direction and canon/art gates now evaluate the requested action (title/task), not descriptive context, constraints or acceptance criteria.
- Revision work may reference the existing approved product direction as a preservation constraint without creating a false operator decision.
- An explicit product-direction or canon/art change requested in the title/task remains gated.
- Added regression coverage for the live `Revise Chronicle implementation plan` false-positive and for an explicit direction change inside revision work.

## 2026-08-07 — CDU-004B6 closure

- Closed CDU-004B6 decision resolution and workflow resume after full target validation with 279 passing tests and clean `git diff --check`.
- Live Core-source decision paths verified APPROVE, REJECT and REQUEST_NON_MUTATING_PREVIEW semantics, including source-department resume and no automatic repository mutation.
- Resolved gated decisions are history-only; ordinary review now separates local acceptance/abandonment from corrective return and clarification.
- Runtime audit logging now records operator submission, persistence, local closure or exact queued resume causality.
- Restart recovery converts orphaned `RUNNING` and `WAITING_SOURCE` conversations to `BLOCKED / BLOCKER`; live abandonment then closes locally without any worker.
- Live Project-source implementation-plan flow verified interception before Core, REVISE returning to Project, revision work routing normally to Core, Core returning the amended plan to Project, and a revised-plan APPROVE gate returning authorization to Project without starting implementation.
- False-positive `IMPLEMENTATION_PLAN_APPROVAL` and `PRODUCT_DIRECTION` interceptions on revision work were eliminated with targeted regression coverage.
- Project Value Monitor was recorded as a deferred, non-blocking post-foundation backlog item.

## 2026-08-07 — Post-B6 roadmap alignment

- Updated authoritative roadmaps and state snapshot to the clean post-push B6 commit `21643599e7e735a22ae5d6ecafe78bea9fcc5c22`.
- Declared CDU-004B7 Console-first reliability and recovery hardening as the active milestone.
- Recorded the agreed sequence through work-state UI, real Chronicle E2E, Console-first promotion and later tool integrations.
- Reordered planned integrations to put Godot/local build-test tooling and Research source intake before Blender/ComfyUI/image-to-3D composite pipelines.
- Kept Project Value Monitor explicitly deferred and non-blocking.
