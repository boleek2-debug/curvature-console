# Curvature Console Roadmap

Status: Active
Version: 4.0.0
Owner: Curvature Console Development Unit
Last Updated: 2026-08-07

## Completed foundation

The operational foundation includes departmental workspaces, persistence, Browser Bridge, URL routing, generated-file capture, package review and safe apply, supervised handoffs, return path, CDU diagnostics/chat, attachments, screenshot paste, downloads, identity migration and resilient attachment readiness.

## Current

### CDU-004B7 — Console-first reliability and recovery hardening

Status: ACTIVE.

CDU-004B6 is closed and pushed. The next milestone is a bounded reliability audit before any major new feature or external-tool integration. It verifies that queues, operational conversations, retries, recovery, artifacts, nested CDU escalation, decision gates, cancellation/hold/retry and Thread Pressure all reach safe, explicit states across restart and failure.

Current substage: **CDU-004B7C — Restart Reconciliation and Retry Safety**. B7A established the durable Browser Exchange Ledger and B7B closed in-session failure/cancel ghosts plus interrupted supervised-handoff transport states. B7C now classifies interrupted Browser Bridge attempts at startup: attempts with no durable evidence of submission become `RETRY_PENDING`, while attempts that may already have crossed the submission boundary become `RECONCILE_REQUIRED`. No automatic resend occurs.

Acceptance direction:

1. no orphaned process-bound workflow states after restart;
2. retries and resumptions remain idempotent and preserve stable logical identity;
3. no duplicate transport, artifact or operator action is created by recovery;
4. every stopped workflow exposes a clear operator-visible reason and safe next action;
5. automated regression coverage plus focused live interruption/recovery evidence;
6. current documentation and a clean repository snapshot before closure.

## Approved development direction

The capability-based Console-first plan in `docs/CURVATURE_CONSOLE_FIRST_ACTION_PLAN.md` remains authoritative. The agreed execution order after CDU-004B6 is now:

1. CDU-004B7 reliability/recovery hardening;
2. rebuild the main Console surface around work state;
3. run one real Chronicle end-to-end Console workflow;
4. formally promote Console to the primary Curvature operating interface;
5. implement the Tool Adapter Foundation;
6. integrate Godot and local build/test tooling first;
7. add Research source-intake tooling;
8. add Blender, ComfyUI and controlled image-to-3D asset pipelines;
9. add composite one-button workflows;
10. add the Chronicle Beta Feedback Hub when functional builds exist;
11. add voice playback/dictation after operational stability.

Project Value Monitor remains a deferred, non-blocking feature and may be scheduled only when it cannot slow the critical operational path.

## CDU-004 — Automatic Tool Escalation, Return and Documentation Closure

Deliver:

- structured missing-capability requests emitted by Project, Core and Research;
- automatic routing to Console Development Unit;
- shared-queue serialization;
- automatic result return to the source department;
- original-request linkage;
- captured artifact path reporting;
- operator approval gates for writes, installs, cost, security and scope;
- documentation updates as a mandatory completion condition;
- automated and live end-to-end verification.

## CDU-004A — Artifact Deduplication and Escalation Chain Control

Delivered logical artifact deduplication, bounded corrective escalation, automatic defect context and operator-stop semantics. Automated validation passed with 243 tests, and the 2026-08-05 live retest confirmed one logical artifact, duplicate suppression, automatic return and Core acceptance. Documentation closure is complete. Commit, push and a clean snapshot are the remaining repository closure steps.

### CDU-004B — Background interdepartmental conversations and Operator Review

- CDU-004B1: durable operational conversation records, transcript capture and review surface — closed after full validation and live restart evidence.
- CDU-004B2: Accept, Reject and Ask/Continue actions on the same conversation.
- CDU-004B3: automatic decision/blocker classification and meaningful final notifications.
- CDU-004B4: generalise operational conversations beyond automatic CDU escalation to Project, Core and Research collaboration — closed after 260 automated tests and live Project ↔ Core, Project ↔ Research and Core ↔ Research verification.
### CDU-004B2 — Operator Review — closed
- Accept, Reject and Ask / Continue in the durable conversation review surface.
- Persisted operator comments and review states.
- Reject and Ask return to the source department without creating a new unrelated workflow.

### CDU-004B2A — Same-conversation continuation and lifecycle visibility

Status: closed after automated validation and same-conversation live verification.

- Preserve one operational conversation across Ask / Continue rounds.
- Display start, last activity, result and closure timestamps.
- Display logical round count and an explicit lifecycle footer.
### CDU-004B2B — Exact completed-turn artifact capture
Status: closed after exact-message scoping and live stage-two verification.

### CDU-004B2C — Fresh artifact transport identity
Status: closed after full validation and live Ask/Continue plus Reject retests.

- Generate a unique physical transport filename for every artifact-producing round.
- Validate that the current CDU response attached the required transport object.
- Reject stale logical-name cards and missing fresh files.
- Map validated transport objects back to stable logical artifact names.
- Return Console-calculated size and SHA-256 to the source department.

### CDU-004B3 — Attention classification and meaningful final notifications

Status: closed after full validation and live verification.

- Classify completed operational responses as RESULT, BLOCKER or OPERATOR_DECISION.
- Persist the classification and explanation.
- Map classification to RESULT_READY, BLOCKED or AWAITING_OPERATOR_DECISION.
- Group toolbar review counts by attention type.
- Keep internal routing and progress transitions non-modal.
- Target-environment full regression and live examples of all three classes passed.
- Follow-up defect fixed: successful Thread Handoff now starts a fresh pressure epoch while preserving cumulative Reply Viewer history.

## CDU-004B5 — authority and consequence decision gates

Status: CLOSED after 265 automated tests and live routine-routing, visual-direction and repository-mutation verification.

## CDU-004B6 — decision resolution and workflow resume

Status: CLOSED after 279 automated tests, clean `git diff --check`, and live Core- and Project-source decision/recovery verification.

- Persist the exact gated request, decision domain, question, options and consequences.
- Present context-specific operator options in Operational Conversations.
- One Confirm decision control resolves the selected option.
- Explicit action types drive approval, rejection, revision, limited approval or non-mutating repository previews without parsing the visible label.
- Rejection closes without execution; continuation actions resume the owning source department while preserving the same conversation and source task.
- Acceptance authorizes only the selected bounded action; it never performs repository, security, cost or implementation actions directly.
- Resolved decisions are history-only; ordinary review separates local closure from source-department continuation.
- Interrupted `RUNNING` / `WAITING_SOURCE` conversations recover to `BLOCKED / BLOCKER` and can be abandoned locally without spawning a worker.
- Implementation-plan approval is intercepted before target routing; REVISE returns to Project, revision work proceeds to Core without a false gate, and revised-plan approval is gated again before any implementation begins.

## Later — Project Value Monitor

Non-blocking post-foundation Console feature: a daily Project Asset Value and Potential Company Valuation monitor with separate ranges/midpoints, confidence, daily change, history and evidence-based change drivers. It must not displace or slow operational workflow stabilization.
