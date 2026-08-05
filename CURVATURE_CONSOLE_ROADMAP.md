# Curvature Console Roadmap

Status: Active
Version: 4.0.0
Owner: Curvature Console Development Unit
Last Updated: 2026-08-05

## Completed foundation

The operational foundation includes departmental workspaces, persistence, Browser Bridge, URL routing, generated-file capture, package review and safe apply, supervised handoffs, return path, CDU diagnostics/chat, attachments, screenshot paste, downloads, identity migration and resilient attachment readiness.

## Current

### CDU-004A — Artifact Deduplication and Escalation Chain Control

Automated validation and the live Core → CDU → Core retest passed. Documentation closure, commit, push and clean snapshot remain before milestone closure.

## Approved development direction

The capability-based Console-first plan for the complete Curvature organisation is authoritative in `docs/CURVATURE_CONSOLE_FIRST_ACTION_PLAN.md`.

Immediate ordered work after CDU-004A closure:

1. durable operational conversations;
2. separate interdepartmental transcript history;
3. result/blocker/decision-only operator notifications;
4. Conversation Review with Accept, Reject and Ask;
5. automatic departmental collaboration with decision gates;
6. operator-owned vision enforcement;
7. persistence, recovery and idempotency;
8. full Curvature Console-first migration test;
9. later one-click speech playback and local dictation.

Tool adapters and integrations remain on the roadmap, but they follow the operational Console-first foundation and real Project/Core/Research requirements.

## CDU-004 — Automatic Tool Escalation, Return and Documentation Closure

Deliver:

- structured missing-capability requests emitted by Project, Core and Research;
- automatic routing to Console Development Unit;
- shared-queue serialization;
- automatic result return to the source department;
- original-request linkage;
- captured artifact path reporting;
- operator approval gates for writes, installs, cost, security and scope;
- documentation updates as a mandatory completion condition;
- automated and live end-to-end verification.

## CDU-004A — Artifact Deduplication and Escalation Chain Control

Delivered logical artifact deduplication, bounded corrective escalation, automatic defect context and operator-stop semantics. Automated validation passed with 243 tests, and the 2026-08-05 live retest confirmed one logical artifact, duplicate suppression, automatic return and Core acceptance. Documentation closure, commit, push and clean snapshot are the remaining closure steps.
