# Console Development Unit Roadmap

Status: Active
Version: 2.0.0
Owner: Curvature Console Development Unit

## Completed baseline

- departmental workspace, persistence and context loading;
- Browser Bridge and URL routing;
- generated-file capture;
- package review and safe apply;
- supervised handoffs and return path;
- Console Development Unit diagnostics and chat;
- attachments, screenshot paste and downloads;
- Support Unit to CDU identity migration;
- resilient attachment readiness.

## Current milestone

### CDU-004A — Artifact deduplication and escalation chain control

Automated validation passed with 243 tests. The live Core → CDU → Core retest on 2026-08-05 confirmed duplicate suppression, exactly one returned artifact, exact content verification and source-department acceptance. Documentation closure and repository finalisation remain.

## Ordered capability milestones

1. Close CDU-004A documentation and repository state.
2. Durable interdepartmental operational conversations.
3. Separate operational transcripts from main department chats.
4. Notify only for final results, operator decisions, controlled actions and terminal blockers.
5. Conversation Review with Accept, Reject and Ask or Continue.
6. Replace operator-approved message transport with autonomous departmental collaboration.
7. Enforce consequence-based decision gates and operator-owned Chronicle vision.
8. Add restart-safe persistence, recovery, attempt control and idempotency.
9. Rebuild the main Console surface around work state and review queues.
10. Execute the complete Curvature Console-first migration test.
11. Promote Console to the primary operator interface.
12. Continue real-requirement-driven tool adapters and composite orchestration.
13. Add later one-click speech playback and local voice dictation.

The authoritative detailed plan is `CURVATURE_CONSOLE_FIRST_ACTION_PLAN.md`.

## Promotion rule

A candidate integration enters implementation only when a real Project, Core, Research or CDU requirement supplies inputs, outputs, constraints and acceptance criteria.
