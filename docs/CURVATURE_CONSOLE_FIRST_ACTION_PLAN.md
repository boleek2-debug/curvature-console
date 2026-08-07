# Curvature Console-first Action Plan

Status: Approved direction
Version: 1.0.0
Owner: Project Curvature operator
Maintained by: Curvature Console Development Unit
Approved: 2026-08-05

## Purpose

This plan defines the ordered capabilities required to make Curvature Console the primary operating interface for the whole Curvature organisation, including Curvature Chronicle development.

The plan is capability-based rather than calendar-based. Work advances when the preceding capability is implemented, tested live, documented and safely closed. No week or day estimate is part of acceptance.

## Current progress — 2026-08-07

Steps 1–8 are materially implemented through CDU-004B6. Step 9 is now the active hardening milestone as CDU-004B7. After that, the agreed order is step 10 main work-state UI, step 11 real Chronicle E2E, step 12 Console-first promotion, then requirement-driven tool adapters and integrations.

The approved post-promotion integration order is Godot/local build-test tooling first, Research source intake second, then Blender/ComfyUI/controlled image-to-3D pipelines and composite orchestration. Chronicle Beta Feedback Hub is planned for the stage when functional test builds exist. Voice remains later.

## Governing principles

1. The operator owns the vision, canon, product direction and final creative decisions.
2. Project coordinates and specifies the operator's vision; it does not author or silently change that vision.
3. Departments may communicate and collaborate autonomously inside their authority.
4. The operator approves decisions and consequential actions, not message transport.
5. Missing operator decisions remain explicitly open; they are never treated as permission to invent.
6. Console owns routing, persistence, operational conversations, artifacts, approval surfaces, recovery and auditability.
7. Repository writes, installs, cost, security-sensitive actions, scope changes, commits and pushes remain controlled actions.
8. Every milestone closes only after implementation, automated tests, required live evidence, current documentation and a clean repository snapshot.

## Authority model

### Operator

The operator owns:

- Curvature and Chronicle vision;
- canon, world, characters, appearance and artistic direction;
- product goals and priorities;
- acceptance of material scope changes;
- final decisions when departments cannot proceed within delegated authority.

### Project

Project owns:

- translating operator intent into requirements and plans;
- identifying ambiguity and asking focused questions;
- coordinating Core, Research and CDU;
- checking that delivered work remains faithful to the operator's approved direction;
- presenting options, consequences and recommendations when an operator decision is required.

Project must not independently invent or change Chronicle vision, canon, characters, art direction, gameplay direction or other creative decisions reserved to the operator.

### Core

Core owns Chronicle architecture, implementation, schemas, persistence, validation, testing and repository integration. Core does not decide product vision or research truth.

### Research

Research owns sources, evidence, provenance, confidence and research conclusions supported by the available material. Research does not decide product direction.

### Console Development Unit

CDU owns Curvature Console, Browser Bridge, queues, routing, operational workflows, integrations, diagnostics, artifacts, safe apply support, Console validation and Console documentation. CDU does not decide Chronicle direction or implement Chronicle product work that belongs to Core.

## Ordered action plan

### 1. Close automatic Console escalation

Complete and live-verify the automatic department-to-CDU-to-source workflow.

Required outcome:

- a department emits a structured missing-capability request;
- Console routes it automatically to CDU;
- CDU returns the result and artifacts;
- Console deduplicates equivalent captures;
- the source department resumes the original task;
- escalation attempts are bounded and terminate on success or a real operator blocker;
- the operator performs no manual copy-and-paste transport.

### 2. Introduce durable operational conversations

Create a persistent conversation record for every interdepartmental collaboration.

Each conversation records:

- source task and request identity;
- participants;
- complete chronological transcript;
- artifacts and validation evidence;
- decisions, blockers and recommendations;
- current state and terminal result;
- linkage across restart and retry.

Required states include running, waiting, testing, correcting, blocked, awaiting operator decision, result ready, accepted, rejected and closed.

### 3. Separate operational history from department chats

Interdepartmental exchanges must appear in a dedicated operational conversation rather than flooding the main department histories.

Main department panels show concise status only, while the complete exchange remains available on demand.

### 4. Replace reply-by-reply interruption with meaningful notifications

Do not show a modal or operator-facing alert for every internal reply.

Notify the operator only when:

- a final result is ready;
- an operator decision is required;
- a controlled action requires approval;
- a blocker cannot be resolved autonomously;
- departments cannot reach a valid conclusion inside their authority.

### 5. Build Conversation Review

Opening a result or decision notification shows:

- the complete interdepartmental transcript;
- source task and participants;
- artifacts, tests and documentation status;
- agreed facts, unresolved points and risks;
- final result or decision request;
- department recommendation and consequences.

The review surface provides Accept, Reject and Ask or Continue, plus a free-text operator response.

Reject and Ask continue the same operational conversation rather than creating disconnected handoffs.

### 6. Demote manual handoffs to an internal transport mechanism

Handoff records may remain internally for identity, audit and routing, but routine department communication must no longer require operator approval.

Departments may consult, clarify, test and correct autonomously. The operator becomes involved only at a genuine decision, controlled action, blocker or final acceptance point.

### 7. Implement decision gates based on authority and consequence

Operator approval is required for:

- Chronicle vision, canon, character or art-direction decisions;
- changes in product direction or material scope;
- new cost or paid services;
- installations and security-sensitive actions;
- repository mutation, apply, commit or push according to policy;
- unresolved interdepartmental conflicts;
- final results explicitly designated for operator acceptance.

Routine consultation, evidence exchange, technical clarification, testing and correction inside approved scope do not require approval.

### 8. Enforce operator-owned vision

Prompts, transfer packages, conversation policies and review logic must enforce:

- operator intent is authoritative;
- Project coordinates but does not originate creative direction;
- missing decisions are surfaced as questions;
- departments may recommend but may not silently establish canon;
- implementation choices must preserve the approved vision unless the operator accepts a change.

### 9. Add persistence, recovery and idempotency

Before Console-first promotion:

- conversations and queues survive restart;
- interrupted work resumes from a safe checkpoint;
- retries do not duplicate messages, actions or artifacts;
- request and escalation identities remain stable;
- attempt limits and terminal states are enforced;
- operators can see where and why a workflow stopped.

### 10. Rebuild the main Console surface around work state

The main interface should prioritise:

- active tasks;
- background operational conversations;
- decisions awaiting the operator;
- results ready for review;
- blockers and controlled actions;
- recent completed work;
- diagnostics requiring attention.

The interface must not treat every internal message as a primary operator event.

### 11. Execute a complete Curvature workflow test

The migration test must demonstrate an operator-originated Chronicle goal moving through Project, Core, Research and CDU as required, including autonomous departmental collaboration, artifact handling, testing, documentation closure and one meaningful operator decision or final acceptance.

The test must complete without manually opening ChatGPT to transport messages or decide which department should reply next.

### 12. Promote Console to Console-first operation

Promotion occurs only when the full workflow is live-verified, restart-safe and documented.

After promotion:

- Console is the primary operator interface;
- ChatGPT browser conversations remain the execution substrate and emergency diagnostic fallback;
- routine task routing, department collaboration, artifact handling and decisions are managed through Console.

### 13. Add voice accessibility after operational stability

Voice features are useful but are not migration blockers.

Planned later capabilities:

- one-click playback of a message or full operational conversation, similar to ChatGPT's speaker control;
- local speech synthesis without manual selection or copying;
- local voice dictation and long voice notes;
- raw and structured transcripts preserved together;
- safe review before sending, with future low-interaction operation where appropriate.

## Completion definition

The action plan is complete when:

- departments collaborate without the operator acting as messenger;
- Project cannot invent or alter the operator's vision;
- unresolved creative choices are returned to the operator as focused decisions;
- internal conversations are separate, durable and restart-safe;
- the operator receives only meaningful result, blocker and decision notifications;
- Accept, Reject and Ask operate on the same conversation history;
- retries and artifacts are idempotent and deduplicated;
- Console controls the normal Curvature workflow end to end;
- code, tests, documentation and repository state remain synchronized.
