# Console Backlog

Status: Active
Version: 1.0.0
Owner: Curvature Console Development Unit

## Active

### CDU-001B — Authoritative CDU documentation

Acceptance: complete approved documentation set in `docs/`, root references updated, repository validation passes.

## Next

### CDU-002 — Shared sequential Browser Bridge queue

- four request sources: Project, Core, Research, CDU;
- one active exchange;
- durable queue and restart recovery;
- visible QUEUED/RUNNING/COMPLETED/FAILED states;
- cancel queued, hold active, retry failed;
- independent drafts and attachments.

### CDU-003 — Tool request and handoff routing

- formal request types;
- CDU inbox and lifecycle;
- result return to requester;
- Project/Core/Research decision routing.

### CDU-004 — Tool adapter foundation

- adapter contract;
- capability registry;
- safe command runner;
- health checks;
- execution ledger;
- artifact registry.

## Planned integrations

- CDU-005 consolidate existing tools under adapter model;
- CDU-006 ComfyUI workflow integration;
- CDU-007 Godot run and validation integration;
- CDU-008 Blender technical asset integration;
- CDU-009 Research source-intake integration;
- CDU-010 composite multi-tool orchestration.

## Deferred

- automatic Git push UI;
- true parallel browser exchanges;
- detachable multi-window workspace;
- local LLM provider;
- paid providers;
- unrestricted shell execution.
