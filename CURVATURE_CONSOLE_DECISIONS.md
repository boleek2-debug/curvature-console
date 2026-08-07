# Curvature Console Architecture Decisions

Status: Active
Version: 2.0.0
Owner: Curvature Console Development Unit
Last Updated: 2026-08-05

## Durable existing decisions

- Curvature Console is a separate internal application and repository.
- Normal operation requires no additional AI spending beyond ChatGPT Plus.
- Browser Bridge uses ordinary local Chrome, Playwright and persisted URL routing.
- repository writes require review and explicit approval;
- no automatic commit, push or force push;
- Project, Core and Research preserve separate authority and state;
- cross-department work uses explicit handoffs.

## CDU decisions

The detailed CDU decision record is `docs/CONSOLE_DECISIONS.md`.

Accepted on 2026-08-04:

- CDU is the approved Console development authority;
- Support Unit identity is superseded by CDU with compatibility migration;
- local/free/open-source-first tooling policy;
- shared sequential Bridge execution before true parallelism;
- adapter-based tool integration;
- explicit operator approval for controlled actions.

## CDU-004 — Automatic escalation is the default routing model

Accepted: 2026-08-04

When Project, Core or Research is blocked by a missing Console capability, the department emits a structured Console request. Curvature Console routes it to CDU and returns the result to the originating department automatically. The operator is not responsible for copying request templates between workspaces. Operator approval remains required for repository writes, installation, cost, security-sensitive actions and scope changes. Documentation updates are part of completion, not a deferred follow-up.

## CDU-004A — Bounded automatic escalation

Automatic Console escalation may perform one initial CDU request and one corrective CDU defect attempt. A further structured request from the returned source response stops the chain and requires operator action. One logical artifact captured through multiple browser channels is represented once.
## Operator-owned vision and autonomous collaboration

Accepted: 2026-08-05

The operator is the sole owner of Curvature and Chronicle vision, canon and creative direction. Project coordinates, specifies and protects that direction but may not silently invent or alter it. Missing creative decisions remain open and must be returned to the operator as focused questions or options.

Departments may communicate, clarify, test and correct autonomously within their authority. The operator approves meaningful decisions and consequential actions, not routine message transport. Manual handoff approval is therefore a compatibility mechanism to be demoted from the normal operator workflow once durable operational conversations and decision gates are implemented.

## Operator notification policy

Accepted: 2026-08-05

Internal replies do not generate operator-facing modal notifications. Notify only for a final result, an operator decision, a controlled action or a terminal blocker. Opening the notification must expose the complete operational transcript and Accept, Reject and Ask or Continue controls.

## Decision — interdepartmental collaboration uses durable operational conversations

Automatic collaboration is represented by a persistent operational conversation keyed to the escalation chain. Department chat remains the execution substrate, while the Console-owned transcript is the operator review record. Routine internal replies do not create modal notifications. Result-ready, blocked and operator-decision states are surfaced through the review counter.
## Decision — operator reviews outcomes, not message transport
Operational conversations may run without per-message approval. The operator is engaged only for a final result, blocker or genuine decision. Accept closes the result. Reject and Ask / Continue preserve the same conversation and source task, append the operator comment, and resume through the source department.

## Decision — Operational identity is stable across continuation rounds

An operator Ask / Continue action resumes the existing operational conversation. New Browser Bridge request IDs and escalation-chain IDs are implementation details and must not create a second operator-visible conversation. Operator Review must show when a result was reached, when the conversation was closed and how many logical rounds occurred.
## Exact response identity is authoritative for artifact capture
Generated artifacts must be searched only inside the assistant turn whose `data-message-id` was confirmed by response completion. DOM order alone is not authoritative because older file cards may remain later in the rendered conversation.

## Fresh generated artifacts require unique transport identities

Accepted: 2026-08-05

A stable logical artifact filename must not be reused as the browser transport identity across operational-conversation rounds. Every round receives a unique transport filename containing the round number and automatic request identity. CDU must create and attach a new physical file under that exact transport name. Console validates the captured transport name, computes the actual byte count and SHA-256, then maps the file back to the stable logical filename for source-department use. Model-authored claims never override Console-observed file bytes.

## Decision — CDU-004B1–B2C accepted and closed

Accepted: 2026-08-05

Durable operational conversations and Operator Review are the approved execution model for automatic CDU collaboration. Accept closes a result without another exchange. Ask / Continue and Reject resume the same operator-visible conversation and source task. Artifact-producing rounds must use exact assistant-turn scoping and unique transport identities, with Console-observed bytes and hashes treated as authoritative. The implementation is accepted after 251 passing tests and successful live Accept, Ask / Continue and Reject verification.

## 2026-08-05 — Classify attention, not transport noise

Decision: operational conversations expose operator attention only when a completed response is a result, a blocker or an operator decision. Internal interdepartmental routing and progress transitions remain non-modal. Classification is persisted with a human-readable reason, and explicit workflow markers override heuristic phrase detection.

## DEC-CDU-2026-08-06-05 — Explicit operational requests remain distinct from supervised handoffs

Decision: Background Project/Core/Research collaboration uses a new explicit `BEGIN_CURVATURE_OPERATIONAL_REQUEST` block. Existing `BEGIN_CURVATURE_HANDOFF_PROPOSAL` blocks remain supervised and operator-approved.

Reason: Generalising operational conversations must not silently remove operator approval from established handoff semantics. Explicit protocol separation makes autonomy intentional, auditable and bounded.

Safety boundary: one continuation request per existing conversation round and a six-hop routing limit; exceeding the limit becomes `OPERATOR_DECISION`.

## CDU-004B5 — decision-gate authority

Operational routing may proceed autonomously only while the requested work remains within department authority and has no operator-owned consequence. Product direction, scope, canon, art direction, cost, installation, security-sensitive actions, shared repository mutation and unresolved cross-department conflict must stop before execution and request a structured operator decision with question, options and consequences.


## CDU-004B6 — bounded decision resolution

Accepted for validation: 2026-08-06

A pending decision presents context-specific operator options and one Confirm decision action. Each option carries an explicit machine action type such as APPROVE, REJECT, REVISE, LIMITED_APPROVAL or REQUEST_NON_MUTATING_PREVIEW. The preview action is valid only for a concrete non-mutating repository path: run validation and prepare a patch/diff without commit or push. Console executes the selected action type without inferring intent from the label. Repository, installation, purchase and security operations remain delegated to the authorized source department; Console never performs them directly. Ordinary result review uses explicit consequence labels and keeps local closure separate from source-department continuation.

## CDU-004B6 — ordinary review actions must describe consequences

Accepted for validation: 2026-08-06

Ordinary result review uses four distinct actions. Close as accepted and Close as abandoned are local terminal actions and must never start a department worker. Return to source starts a corrective round in the source department and requires an operator reason. Request clarification / continue starts a bounded source-department follow-up and requires an operator instruction. A recovered interrupted conversation may be closed as abandoned without asking the source department to confirm that it is dead. Every operator action must produce a causal runtime audit record before any worker is queued.

## 2026-08-07 — CDU-004B6 closure decision

Decision: close CDU-004B6 after 279 passing target-environment tests, clean `git diff --check`, and live evidence for bounded APPROVE/REJECT/REVISE/non-mutating-preview resolution, interrupted-work recovery, causal operator audit logging, Project-source pre-routing interception, revision-work routing, and revised-plan approval.

Invariant: decision gates stop operator-owned decisions before target execution, but revision/preparation work that merely references an existing approved direction must route normally. Approval returns bounded authority to the source department; it does not itself execute implementation, repository mutation, installation, purchase, or security-sensitive work.

## 2026-08-07 — Post-B6 execution order

Decision: after CDU-004B6 closure, the next active milestone is CDU-004B7 Console-first reliability and recovery hardening. Major new integrations must wait until the operational foundation has been interruption/restart/retry audited.

Approved order: B7 hardening → main work-state UI → one real Chronicle Console-first E2E → Console-first promotion → Tool Adapter Foundation → Godot/local build-test integration → Research source intake → Blender/ComfyUI/controlled image-to-3D pipelines → composite workflows → Chronicle Beta Feedback Hub → voice accessibility.

Project Value Monitor remains deferred and non-blocking. It may be implemented only when it does not slow the critical operational path.

## 2026-08-07 — B7 transport state is separate from workflow state

Decision: Browser Bridge execution state must be persisted as its own durable ledger rather than inferred from Operational Conversation or supervised-handoff status. A logical workflow may span multiple transport attempts, while each Browser Bridge request has one immutable request ID and one independently auditable lifecycle.

B7A records transport truth only. It must not auto-resend after restart. B7C will reconcile non-terminal ledger records and must distinguish work that was never submitted from work that may already exist in ChatGPT before offering or performing retry.

## 2026-08-07 — B7B transport failure closes workflow state immediately

Decision: Browser Bridge transport failure/cancellation must not leave an operational conversation in a process-owned state until the next Console restart. When an exchange associated with `RUNNING` or `WAITING_SOURCE` work fails or is cancelled, the conversation becomes `BLOCKED` immediately, receives `BLOCKER` attention and records the transport reason in its timeline.

Transport cancellation is not equivalent to abandoning the logical workflow. `CANCELLED` remains an explicit operator workflow-close action; a cancelled transport becomes `BLOCKED` so the operator can inspect whether retry/reconciliation is appropriate.

Legacy supervised handoffs left in `SENT`, `RETURN_SENT` or `UPDATE_SENT` across restart recover to `HELD`, not to an automatic resend. B7C will decide retry only after durable Browser Exchange reconciliation.
