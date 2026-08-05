# Console Product Vision

Status: Approved
Version: 1.1.0
Owner: Curvature Console Development Unit

## Purpose

Curvature Console is the local development control plane for Project Curvature. It should reduce manual movement of prompts, files, logs, artifacts and status between departments and tools while preserving explicit authority and operator control.

## Product principles

1. Local-first, free-first and open-source-first.
2. One visible operator action may orchestrate many tools.
3. Complex workflows retain approval points, previews, retries and rollback.
4. Every result must be attributable to a request, tool, run and artifact.
5. Console must never silently spend money, push Git changes or mutate repositories.
6. Project, Core, Research and CDU keep separate roles and continuity.
7. Browser automation remains deterministic, observable and recoverable.
8. Real use determines priority; speculative integrations remain candidates.

## Long-term product direction

Console should evolve from a departmental coordination tool into a controlled orchestration platform that can:

- queue and route work across four dedicated conversations;
- invoke local and remote tools through adapters;
- track progress, logs and artifacts;
- preserve provenance and restart continuity;
- validate results against explicit acceptance criteria;
- return results to the requesting department;
- support one-button, multi-stage workflows without removing operator control.
## Console-first organisational direction

Console is intended to become the primary operator interface for the whole Curvature organisation. Departments collaborate through durable operational conversations in the background, while the operator is interrupted only for meaningful decisions, controlled actions, terminal blockers and final results.

Console autonomy is operational, not creative. The operator owns Chronicle vision and canon. Project coordinates and specifies that vision and must not independently replace it.

The complete ordered direction is maintained in `CURVATURE_CONSOLE_FIRST_ACTION_PLAN.md`.
