# Curvature Console Architecture Decisions

Status: Active
Version: 2.0.0
Owner: Curvature Console Development Unit
Last Updated: 2026-08-04

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
