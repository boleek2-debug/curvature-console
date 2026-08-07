# Console Development Unit Roadmap

Status: Active
Version: 3.0.0
Owner: Curvature Console Development Unit
Last Updated: 2026-08-07

## Completed operational foundation

The Console now includes the shared Browser Bridge queue, automatic CDU escalation and return, durable operational conversations, separate transcript review, meaningful result/blocker/decision attention, same-conversation continuation, exact artifact capture and transport identity, general Project/Core/Research collaboration, authority/consequence decision gates, bounded operator resolution, causal operator audit logging, and restart recovery for interrupted operational states.

CDU-004B6 closed after 279 automated tests and live Project/Core decision-resolution verification.

## Current milestone

### CDU-004B7 — Console-first reliability and recovery hardening

Audit the already-built operational foundation before adding major new capability. The milestone targets restart, interruption, retry, idempotency and safe terminal-state behaviour across queues, operational conversations, artifacts, nested CDU escalation, decision gates, cancellation/hold/retry and Thread Pressure.

## Ordered capability milestones

1. CDU-004B7 reliability and recovery hardening.
2. Rebuild the main Console surface around active work, queued work, decisions, results, blockers and recent completed work.
3. Execute one real operator-originated Chronicle workflow end to end through whatever departments are actually required.
4. Promote Console to the primary Curvature operator interface only after that workflow is restart-safe and documented.
5. Build the Tool Adapter Foundation: adapter contract, capability registry, safe runner, health checks, execution ledger and artifact registry.
6. Integrate Godot and local Chronicle build/test tooling.
7. Add Research source-intake tooling.
8. Add Blender, ComfyUI and controlled image-to-3D asset pipelines with provenance and approval.
9. Add composite one-button workflows.
10. Add the Chronicle Beta Feedback Hub when functional test builds exist.
11. Add one-click speech playback and local dictation after operational stability.

## Parallel / deferred

Project Value Monitor remains non-blocking: daily Project Asset Value and Potential Company Valuation, each with range, midpoint, confidence, daily delta, history and evidence-based change drivers. It must not displace critical Console-first work.

## Promotion rule

A new integration enters implementation only when a real Project, Core, Research or CDU requirement supplies inputs, outputs, constraints and acceptance criteria.
