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
