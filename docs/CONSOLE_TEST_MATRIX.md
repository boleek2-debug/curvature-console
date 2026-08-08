# Console Test Matrix

Status: Active
Version: 1.1.0
Owner: Curvature Console Development Unit
Last Updated: 2026-08-08

## Current regression areas

| Area | Automated | Live | Required evidence |
|---|---:|---:|---|
| Department routing | Yes | Yes | exact URL and origin panel |
| CDU routing/migration | Yes | Yes | same conversation and preserved state |
| Attachments | Yes | Yes | single, multiple, screenshot, failure-before-send |
| Generated downloads | Yes | Yes | filename, collision handling, department inbox |
| Package review/apply | Yes | Yes | classification, backup, rollback, result metadata |
| Handoffs | Yes | Yes | lifecycle, delivery, return, same identity |
| Restart continuity | Yes | Yes | drafts, routes, records, attachments |
| Git safety | Partial | Manual | no unintended runtime files or push |
| Cost safeguards | Policy | Manual | no paid provider without approval |

## Future adapter tests

Every adapter requires:

- discovery and version detection;
- health check;
- valid invocation;
- invalid input rejection;
- timeout and cancellation;
- retry safety;
- stdout/stderr or equivalent logs;
- artifact registration;
- licence/cost metadata;
- restart recovery where applicable.

## Release gate

A milestone closes when automated validation, `git diff --check`, expected file scope and proportionate functional/live evidence pass. Deliberate destructive or narrow-window fault injection may be deferred when deterministic regression tests cover the safety invariant and the remaining live case is explicitly tracked for opportunistic validation during normal use.

## CDU-004 automatic escalation

- valid Console request envelope parses;
- unsupported request type is rejected;
- every department package includes automatic escalation instructions;
- automatic CDU request preserves source department and source request ID;
- CDU result is queued back to the source department;
- captured artifact paths are included in the return;
- shared queue prevents parallel Browser Bridge workers;
- operator approval remains required for controlled actions;
- documentation closure is present in the CDU execution prompt.

## CDU-004A

- identical artifact exposed through fetch and native-download channels is captured once;
- collision suffixes such as `(1)` and local `-2` do not create a second logical artifact when content hashes match;
- escalation chain preserves source request, chain ID and attempt number;
- one corrective CONSOLE_DEFECT attempt receives latest snapshot and runtime log;
- third automatic escalation is blocked and surfaced for operator action.
## 2026-08-05 CDU-004A live evidence

- automatic Core request detection: PASS;
- automatic Core → CDU routing: PASS;
- generated artifact capture: PASS;
- equivalent fetch/native capture suppression by SHA-256: PASS;
- logical artifact count equals one: PASS;
- automatic CDU → Core return: PASS;
- Core exact filename/content/hash verification and acceptance: PASS;
- escalation loop prevention in the successful path: PASS;
- full automated suite: 243 passed;
- `git diff --check`: PASS.

## Planned Console-first acceptance areas

Future milestones must add regression and live coverage for durable operational conversations, notification suppression, Conversation Review, Accept/Reject/Ask continuation, operator-owned vision gates, restart recovery and complete multi-department Console-first execution.

## CDU-004B1 operational conversation foundation

- SQLite operational conversation create/update/load: targeted automated PASS in packaging environment.
- Ordered durable transcript: targeted automated PASS in packaging environment.
- Result-ready review counter: targeted automated PASS in packaging environment.
- Qt review dialog and full regression suite: required in project Conda environment.
- Live automatic Core → CDU → Core transcript capture across restart: required before milestone closure.
## CDU-004B2 Operator Review
- Persist operator-authored transcript entries and terminal ACCEPTED state.
- Accept without mandatory comment.
- Reject and Ask / Continue require operator text.
- Reject and Ask preserve conversation ID and source request ID when routed back.
- Review count excludes accepted conversations.
- Live Accept, Ask / Continue and Reject tests: PASS.

## CDU-004B2A

- Same operational conversation reused across Ask / Continue: automated coverage added.
- Source request remains stable while technical request IDs change: covered by persistence test.
- Round count increments without duplicating transcript records: automated coverage added.
- Result-ready and closure timestamps persist: automated coverage added.
- Lifecycle details visible in Operator Review: target-environment live test required.
## CDU-004B2B
- Exact confirmed assistant message selected by message ID: automated PASS.
- Stale file card from earlier round excluded from capture scope: regression covered.
- Live stage-one → Ask/Continue → stage-two artifact-content test: PASS.

## CDU-004B2C

- Logical artifact filename extraction and deduplication: automated PASS.
- Unique transport filename differs between rounds and requests: automated PASS.
- Exact assistant-turn capture remains required: covered by CDU-004B2B regression tests.
- Stale logical-name attachment rejection: PASS through unique transport identity.
- Transport-to-logical local mapping with Console-calculated byte count and SHA-256: live PASS.
- Live stage-one → Ask/Continue → stage-two artifact-content test: PASS.
- Live Reject → corrected stage-two artifact test: PASS.
- Full target suite: 251 passed.
- `git diff --check`: PASS.

## CDU-004B3

- Explicit RESULT / BLOCKER / OPERATOR_DECISION markers: targeted automated PASS.
- Conservative blocker and operator-decision phrase fallback: targeted automated PASS.
- Normal completed response defaults to RESULT: targeted automated PASS.
- Attention kind and reason persist in SQLite: targeted automated PASS.
- Review counts grouped by attention kind: targeted automated PASS.
- Full Qt regression suite: required in the project Conda environment because PySide6 is unavailable in the packaging environment.
- Live verification must demonstrate one result, one blocker and one operator-decision response without modal noise during internal transitions.

## Thread Handoff pressure reset regression

- successful Thread Handoff preserves cumulative reply history;
- a new-thread marker is appended to the persisted transcript;
- Thread Pressure uses only the transcript after the latest marker;
- restart continuity preserves the fresh pressure epoch;
- normal non-handoff replies continue to accumulate pressure in the active epoch.

## CDU-004B4

- explicit operational-request parser accepts all six directed Project/Core/Research pairs;
- malformed, unknown-target and same-department requests are rejected;
- supervised handoff proposal parser remains unchanged and operator-approved;
- one durable conversation ID is reused across target return, nested CDU escalation and source continuation;
- target artifacts are returned with observed size and SHA-256 metadata;
- six-hop safety limit terminates in OPERATOR_DECISION rather than looping;
- targeted non-Qt tests: PASS in packaging environment;
- full target-environment regression suite: 260 tests PASS;
- live Project → Core → Project: PASS;
- live Project → Research → Project: PASS;
- live Core → Research → Core: PASS;
- final status and attention classification for all three representative routes: RESULT_READY / RESULT;
- CDU-004B4 closure: PASS.

## CDU-004B5 decision gates

- routine operational request does not trigger operator gate
- product-direction request triggers structured operator decision
- repository mutation triggers structured operator decision
- installation decision preserves question/options/consequences through attention classification
- live validation pending


## CDU-004B6 decision resolution

- Decision context persistence and reload: PASS.
- Resolution status, selected option, explicit action type and timestamp persistence: PASS.
- Option/action cardinality and repository APPROVE/REJECT/REQUEST_NON_MUTATING_PREVIEW mapping: PASS.
- Rejected decision closes lifecycle without routing: PASS.
- Full target-environment regression: 279 tests PASS.
- `git diff --check`: PASS.
- Live Core APPROVE resume to source: PASS.
- Live Core REJECT without routing: PASS.
- Live Core REQUEST_NON_MUTATING_PREVIEW return to source with no commit/push authority: PASS.
- Live causal operator audit logging: PASS.
- Live Project REVISE end-to-end path: PASS.
- Live revised-plan APPROVE path: PASS.

## CDU-004B6 resolved-decision history-only UI

- Resolved REJECTED gated decision hides all review and decision controls: automated UI regression added.
- Dialog Close remains the only available action after resolution.
- Live regression: PASS; resolved gated decisions expose history only and Close.

## CDU-004B6 attention badge and interrupted RUNNING recovery

- Resolved gated RESULT_READY conversation is not counted as actionable operator attention: automated PASS.
- Ordinary unresolved RESULT_READY conversation remains countable: existing coverage retained.
- RUNNING conversation recovered after Console restart becomes BLOCKED / BLOCKER: automated PASS.
- Badge singular/plural rendering for decision/blocker/result: PASS in target UI validation.

## CDU-004B6 ordinary-review action semantics and audit trail

- Ordinary review exposes Close as accepted / Return to source / Request clarification or continue / Close as abandoned: automated UI regression added.
- Close as abandoned requires a reason, persists an operator message, closes as CANCELLED and creates no pending browser exchange: automated regression added.
- Runtime audit emits operator_action_submitted, operator_action_persisted and operator_action_closed_without_resume for local abandonment: automated regression added.
- Runtime audit emits operator_resume_enqueued only for actions that actually resume the source department: live-log PASS.

## CDU-004B6 interrupted operational recovery

- `RUNNING` after restart → `BLOCKED / BLOCKER`.
- `WAITING_SOURCE` after restart → `BLOCKED / BLOCKER`.
- Startup audit log records the recovery count and covered statuses.

### CDU-004B6 — implementation plan approval gate

- PASS (targeted): explicit implementation-plan approval request produces `IMPLEMENTATION_PLAN_APPROVAL` with `APPROVE / REJECT / REVISE`.
- PASS (targeted): revision option is `Request a revised implementation plan.`
- PASS (targeted): routine implementation-plan preparation remains ungated.
- LIVE PASS: Project outbound plan-approval request logs `operational_decision_gate_intercepted` before any Core worker; selecting REVISE resumes Project.
### CDU-004B6 implementation-plan intent discrimination
- PASS: explicit implementation-plan approval is intercepted before target routing.
- PASS: `Revise Chronicle implementation plan` with future-approval wording is not intercepted.
- PASS: explicit approval of a revised implementation plan remains intercepted.

### CDU-004B6 product-direction context discrimination
- PASS (targeted): `Revise Chronicle implementation plan` is not gated merely because constraints say to preserve the approved Chronicle product direction.
- PASS (targeted): an explicit product-direction decision in revision title/task remains gated.
- LIVE PASS: after operator REVISE, `Revise Chronicle implementation plan` routes to Core without `IMPLEMENTATION_PLAN_APPROVAL` or `PRODUCT_DIRECTION` interception; Core returns the revised plan to Project.

## CDU-004B6 closure evidence — 2026-08-07

- Full target suite: 279 passed.
- `git diff --check`: PASS.
- Core-source APPROVE: PASS.
- Core-source REJECT: PASS.
- Core-source non-mutating preview: PASS for decision routing/constraints/no mutation; real local validation/patch generation was outside the ChatGPT worker's filesystem capability and was not claimed.
- Interrupted `WAITING_SOURCE` recovery: PASS (`operational_recovery_complete recovered_count=1`).
- Close as abandoned after recovery: PASS; `operator_action_submitted` → `operator_action_persisted` → `operator_action_closed_without_resume`, no worker.
- Project-source initial implementation-plan approval interception before Core: PASS.
- REVISE resumes Project: PASS.
- Revision work routes Project → Core without false-positive gate: PASS.
- Revised plan returns Core → Project: PASS.
- Revised-plan APPROVE is gated before Core and resumes Project: PASS.
- No tested approval path automatically starts implementation, commit, push or merge.
- CDU-004B6 closure: PASS.

## CDU-004B7A — durable Browser Exchange Ledger

- SQLite ledger survives close/reopen with request/workflow identity and lifecycle timestamps: PASS.
- Cancellation boundary preserves pre-submission truth: PASS.
- Shared queue persists `QUEUED` before worker execution: PASS.
- Queued cancellation records terminal transport state and reason: PASS.
- Included in full target regression suite.

## CDU-004B7B — failure / cancel state closure

- Queued operational Browser Bridge cancellation closes process-bound workflow state immediately: PASS.
- Active Browser Bridge failure closes process-bound workflow state and records blocker reason/timeline evidence: PASS.
- Interrupted supervised handoffs recover to safe held state: PASS.
- Recovery is idempotent: PASS.
- Included in full target regression suite.

## CDU-004B7C — restart reconciliation and retry safety

- interrupted `QUEUED` and pre-submission `STARTED` Browser exchanges become `RETRY_PENDING`: PASS;
- interrupted `SUBMITTED` and `RESPONSE_RECEIVED` exchanges become `RECONCILE_REQUIRED`: PASS;
- terminal Browser exchanges remain unchanged: PASS;
- explicit `SAFE_RETRY` versus `RECONCILE_BEFORE_RETRY` disposition persists: PASS;
- repeated reconciliation is idempotent: PASS;
- startup performs no automatic resend: PASS;
- full target suite: **288 passed**;
- `git diff --check`: **PASS**.

## CDU-004B7D — opportunistic live interruption evidence

Status: **NON-BLOCKING / OPERATIONAL OBSERVATION**.

- Do not deliberately force narrow crash timing when doing so adds disproportionate operational risk or time.
- Normal functional restart/use remains in scope.
- If a natural interruption occurs, capture the relevant SQLite ledger row and matching runtime log.
- Verify that no automatic resend occurred and that the recovery disposition matched durable submission evidence.
- Any defect discovered from real-world evidence must receive a deterministic regression test.
- B7 milestone closure does not depend on manufacturing an artificial crash.

## CDU-004B7 closure

- Full target suite: **288 passed**.
- `git diff --check`: **PASS**.
- Pushed checkpoint: `6101810957763035bc71a657e036597ec66697d7`.
- Recovery safety invariants covered deterministically: **PASS**.
- Deliberate crash-boundary matrix: deferred to opportunistic operational validation.
- CDU-004B7 closure: **PASS**.
