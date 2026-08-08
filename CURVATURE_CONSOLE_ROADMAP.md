# Curvature Console Roadmap

Status: Active
Version: 4.2.0
Owner: Curvature Console Development Unit
Last Updated: 2026-08-08

## Completed foundation

The operational foundation includes departmental workspaces, persistence, Browser Bridge, URL routing, generated-file capture, package review and safe apply, supervised handoffs, return path, CDU diagnostics/chat, attachments, screenshot paste, downloads, identity migration and resilient attachment readiness.

## Current

### CDU-004B8 — Main Console Work-State Surface

Status: **ACTIVE**.

Goal:

Rebuild the main Console operator experience around meaningful work state while preserving all critical existing departmental workflows and authority boundaries.

The new surface is an operator shell above the existing Project, Core, Research and CDU workspaces. It must not become a shallow dashboard that hides necessary controls.

### CDU-004B8A — Operator Surface Contract

Status: **COMPLETED / APPROVED**.

Before UI implementation, define and accept the first-class operator requirements:

- Project remains directly usable as the primary operator-facing workspace;
- Task Package, Thread Handoff and thread-continuity controls remain easy to reach;
- Active Work and Operator Attention aggregate meaningful cross-department state;
- Core generated output exposes controlled Package Review / Apply entry points without autonomous repository-write authority;
- Research exposes first-class Add Sources / Attach Materials input, queue state and future knowledge/evidence access;
- department drill-down and authority isolation remain intact;
- artifacts/results and CDU/system status remain accessible;
- the legacy departmental view remains available during functional evaluation.

Accepted B8 implementation sequence:

1. B8A — Operator Surface Contract;
2. B8B — Read-only Work-State Prototype;
3. B8C — Project and Continuity Integration;
4. B8D — Core Output / Package Review Integration;
5. B8E — Research Source Intake Integration;
6. B8F — Attention / Results / Department Drill-down;
7. B8G — Functional Evaluation.

B8G is a real-use evaluation gate: accept, adjust or redesign the new surface before making it the default.

Next substage:

```text
CDU-004B8B — Read-only Work-State Prototype
```

B8B must be non-destructive and must preserve the legacy departmental view while the new work-state surface is evaluated.

After B8, run one real Chronicle Console-first end-to-end workflow before formal Console-first promotion.


## Approved development direction

The capability-based Console-first plan in `docs/CURVATURE_CONSOLE_FIRST_ACTION_PLAN.md` remains authoritative. The agreed execution order after CDU-004B6 is now:

1. CDU-004B7 reliability/recovery hardening;
2. complete CDU-004B8 Main Console Work-State Surface (B8A–B8G);
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
