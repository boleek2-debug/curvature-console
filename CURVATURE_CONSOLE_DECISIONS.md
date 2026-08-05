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
