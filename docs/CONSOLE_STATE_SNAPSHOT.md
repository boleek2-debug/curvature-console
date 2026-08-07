# Console Development Unit State Snapshot

Status: Operational
Version: 1.3.0
Owner: Curvature Console Development Unit
Last Updated: 2026-08-07

## Repository

```text
Repository: ~/curvature-console
Branch: main
Verified commit: 21643599e7e735a22ae5d6ecafe78bea9fcc5c22
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

CDU-004B7 — Console-first reliability and recovery hardening.

## CDU-003 package scope

- approved request types: `CONSOLE_TOOL_REQUEST`, `CONSOLE_INTEGRATION_REQUEST`, `CONSOLE_WORKFLOW_REQUEST`, `CONSOLE_DEFECT`, `CONSOLE_DECISION_REQUEST`;
- requesting department metadata for Operator, Project, Core, Research and CDU;
- formal request template using the fields from `CONSOLE_TOOL_REQUEST_PROTOCOL.md`;
- explicit routing boundary included in every formal CDU transfer package;
- no autonomous cross-department execution: required work outside CDU authority must be identified as a handoff.

## Immediate next step

Perform a bounded reliability/recovery audit of the operational foundation before adding a major feature. Test restart, interruption, retry and idempotency across queues, operational conversations, artifacts, nested CDU escalation, decision gates, cancellation/hold/retry and Thread Pressure. Defects found become regression tests. After B7 closure, rebuild the main Console work-state surface, then run one real Chronicle Console-first end-to-end workflow before promotion.

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


## CDU-004B1–B2C closure state

CDU-004B1 durable operational conversations, CDU-004B2 Operator Review, CDU-004B2A same-conversation lifecycle, CDU-004B2B exact completed-turn capture and CDU-004B2C fresh artifact transport identity are closed.

Closure evidence:

- full target validation: 251 tests passed;
- `git diff --check`: PASS;
- durable conversation persisted across restart;
- Accept closed without an extra departmental exchange;
- Ask / Continue preserved one operator-visible conversation and one source task;
- stage two used a unique round-two transport filename and a new Estuary object;
- captured stage-two bytes were `SAME_THREAD_STAGE_TWO`, SHA-256 `42c363c8f22cbe2077e0eb0ae0a26abe852dc91b0e288f8f211bd43c627b2b0f`;
- Reject preserved the same conversation and source task, superseded stage one and returned a fresh round-two artifact;
- captured reject-stage-two bytes were `REJECT_STAGE_TWO`, SHA-256 `ef686f7b0e25a727a1113d6e6d56114a8ecb23f92257269ec3d2efd8d0512b06`;
- exact assistant `data-message-id` scoping and Console-observed file metadata were used throughout.

Current next milestone: CDU-004B3 decision/blocker classification and meaningful final notifications. Repository closure still requires the approved commit, push and clean snapshot.

## 2026-08-06 — CDU-004B4 closed

CDU-004B4 adds explicit durable background collaboration among Project, Core and Research. All six directed department pairs are accepted by the operational-request parser. Requests route through the shared Browser Bridge queue, target replies and generated artifacts return automatically to the original source, nested CDU escalation preserves the operational conversation ID, and terminal responses reuse the existing RESULT/BLOCKER/OPERATOR_DECISION review model. Supervised handoff proposals remain unchanged and operator-approved. A six-hop limit prevents autonomous loops. Full target-environment validation passed with 260 tests. Live Project → Core → Project, Project → Research → Project and Core → Research → Core routes all completed with RESULT_READY and the correct RESULT classification. CDU-004B4 is closed.

## CDU-004B5 candidate state

Authority- and consequence-based operational decision gates are implemented for validation. Routine production collaboration remains autonomous; operator-owned direction, cost, installation, security, repository mutation and unresolved conflict stop before target execution with structured decision details.


## CDU-004B6 implementation candidate — 2026-08-06

The current candidate stores decision domain, question, context-specific options, consequences, explicit action types, exact blocked request, source and target departments, resolution state, selected option and timestamp. Pending gated decisions expose one Confirm decision control. The option action type determines whether Console resumes, rejects, requests revision, applies a limited approval or asks for non-mutating repository preview. Ordinary completed-result review remains separate. Full target validation and revised live workflow evidence remain outstanding.

### CDU-004B6 UI invariant: resolved decisions are history only

Once a gated operator decision leaves PENDING state, Operational Conversations displays its selected option, action, status, and timestamps as read-only history. Decision selectors, comments, Confirm decision, Accept, Reject, and Ask / Continue are hidden. The only remaining dialog action is Close.

### CDU-004B6 attention/recovery correction

Operational attention badges now represent only conversations with an available operator action. A gated decision that has already been resolved and later reaches RESULT_READY remains historical and is not counted again. Any conversation persisted as RUNNING across a Console restart is treated as interrupted process-bound work and is recovered to BLOCKED with BLOCKER attention instead of remaining falsely RUNNING.

### CDU-004B6 ordinary-review semantics and causal audit logging

Ordinary review no longer overloads Reject as both dismissal and corrective return. Close as abandoned is a local terminal action for dead or intentionally discarded conversations and never resumes a department. Return to source starts a corrective round. Request clarification / continue starts a bounded follow-up. Close as accepted closes a completed result locally. Runtime logs now record the operator action before persistence, the persisted action, and either local closure or the exact queued resume request and department.

## CDU-004B6 recovery semantics

Operational conversations persisted as `RUNNING` or `WAITING_SOURCE` are process-bound. On Console startup they are recovered to `BLOCKED / BLOCKER`; they must never remain orphaned with an idle bridge queue.

### CDU-004B6 plan-approval interception correction — 2026-08-07

The operational decision gate now recognizes explicit approval/authorization decisions for Chronicle implementation plans as `IMPLEMENTATION_PLAN_APPROVAL`. The gate is evaluated on the source department's outbound operational request before target routing. A matched request is persisted as `AWAITING_OPERATOR_DECISION`; no target worker is queued until operator resolution. Routine plan drafting/preparation does not trigger this gate. Runtime logs emit `operational_decision_gate_intercepted` with conversation, source, target, domain and title.
### CDU-004B6 revision-work routing refinement
Implementation-plan decision gating now distinguishes approval intent from revision work. `Approve ... implementation plan` and explicit approval of a revised plan are operator-gated; `Revise ... implementation plan` routes to the implementation department even when its context says a later approval is required.

## CDU-004B6 direction-context discrimination — 2026-08-07

A live Project REVISE retest exposed a second false-positive: the revision request was correctly excluded from `IMPLEMENTATION_PLAN_APPROVAL` but was then intercepted as `PRODUCT_DIRECTION` because a preservation constraint mentioned the approved Chronicle product direction. Product/canon direction gates now inspect only title/task action intent; consequence gates continue to inspect the full structured request.

## 2026-08-07 — CDU-004B6 closed

CDU-004B6 decision resolution and workflow resume is closed. Full target-environment validation passes with 279 tests and clean `git diff --check`. Live evidence confirms: Core-source APPROVE returns bounded authorization to Core without automatic mutation; REJECT closes without routing; non-mutating preview returns to Core with commit/push prohibited; resolved decisions are history-only; interrupted `RUNNING` and `WAITING_SOURCE` conversations recover to `BLOCKED / BLOCKER`; Close as abandoned records causal audit events and closes locally with no worker; Project-source implementation-plan approval is intercepted before Core; REVISE resumes Project; `Revise Chronicle implementation plan` routes normally to Core; Core returns the amended plan to Project; and `Approve revised Chronicle implementation plan` is intercepted again and APPROVE resumes Project without automatically beginning implementation.

The live false-positive defects that previously gated revision work as `IMPLEMENTATION_PLAN_APPROVAL` or `PRODUCT_DIRECTION` are fixed and covered by regression tests. Runtime logging now exposes the operator action, selected machine action type, persistence, and exact local-close or resume-enqueue consequence.

Repository closure complete: commit and push succeeded, and the clean post-push snapshot verifies `HEAD == origin/main` at `21643599e7e735a22ae5d6ecafe78bea9fcc5c22`.


## 2026-08-07 — post-B6 planning state

The operator approved the next ordered development sequence: reliability/recovery hardening; main work-state UI; one real Chronicle Console-first E2E; formal Console-first promotion; Tool Adapter Foundation; Godot/local build-test integration; Research source intake; Blender/ComfyUI/image-to-3D pipelines; composite workflows; Chronicle Beta Feedback Hub; then voice accessibility. Project Value Monitor remains a non-blocking deferred feature.
