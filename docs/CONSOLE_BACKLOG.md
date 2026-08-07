# Console Backlog

Status: Active
Version: 2.0.0
Owner: Curvature Console Development Unit
Last Updated: 2026-08-07

## Active

### CDU-004B7 — Console-first reliability and recovery hardening

Current decomposition:

- **B7A — Durable Browser Exchange Ledger:** implemented and target-validated at 283 tests; persist every queued Browser Bridge exchange and its execution lifecycle before adding automatic recovery;
- **B7B — Failure / Cancel State Closure:** implementation prepared for target validation; close operational ghosts immediately on transport failure/cancel and recover interrupted supervised-handoff transport states to `HELD`;
- **B7C — Restart Reconciliation + Idempotent Retry:** reconcile durable exchanges after restart instead of blind resend;
- **B7D — Live Crash / Recovery Matrix:** kill/restart at controlled checkpoints and verify truthful recovery.

Audit/closure scope:

- audit restart recovery for all process-bound operational states;
- verify queue persistence and safe recovery semantics;
- verify retry/idempotency and stable logical identity;
- verify artifact dedupe and fresh transport identity across retry/recovery;
- verify nested CDU escalation and return across interruption;
- verify decision-gate state and operator action causality across restart;
- verify cancellation, hold and retry behaviour;
- verify Thread Pressure state across handoff/restart;
- add regression tests for every defect found;
- close with focused live evidence, current docs and clean repository state.

## Next

### Main Console Work-State UI

Prioritise active work, queued work, operator decisions, results ready, blockers, recent completed work and CDU/tool problems.

### Real Chronicle Console-first E2E

Run one real operator-originated Chronicle goal through the departments actually required, including artifacts, validation, documentation and one meaningful operator decision or final acceptance. No manual ChatGPT message transport.

### Console-first promotion

After the real E2E workflow is restart-safe and documented, make Console the primary Curvature operating interface and leave browser chats as execution substrate / diagnostic fallback.

### Tool Adapter Foundation

- adapter contract;
- capability registry;
- safe command runner;
- health checks;
- execution ledger;
- artifact registry.

## Planned integration order

1. Godot and local Chronicle build/test tooling;
2. Research source intake;
3. Blender technical asset tooling;
4. ComfyUI image-generation workflow;
5. controlled image-to-3D pipeline with provenance, review and approval;
6. composite multi-tool orchestration;
7. Chronicle Beta Feedback Hub once functional builds exist.

## Deferred

### Project Value Monitor — non-blocking post-foundation feature

- daily informational estimate of Project Asset Value and Potential Company Valuation as separate measures;
- show range, midpoint, confidence, daily change and historical graph;
- explain valuation changes using concrete project progress/drivers rather than arbitrary per-commit increments;
- update at most once daily by default;
- schedule only after the operational Console workflow is stable so it does not slow current development.

- automatic Git push UI;
- true parallel browser exchanges;
- detachable multi-window workspace;
- local LLM provider;
- paid providers;
- unrestricted shell execution.
