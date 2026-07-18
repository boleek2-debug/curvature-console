# ROADMAP

Status: Active
Version: 0.3.0
Owner: Project Curvature
Last Updated: 2026-07-18

---

# Completed Milestones

## ASSISTANT-001B1 — Repository and Application Foundation

Completed and verified.

## ASSISTANT-001B2 — Three-Panel Desktop Shell

Completed and verified:

- Project, Core and Research visible simultaneously
- independent conversation and input areas
- resizable splitter
- focus and restore
- automated tests

## Per-Department Attachments

Completed and verified:

- independent queues
- files, screenshots and drag-and-drop
- removal and clearing
- metadata display
- automated tests

---

# Active Milestone

## ASSISTANT-001B3 — Workspace Configuration and Context Loading

Goal:

Give each department a controlled, explicit and previewable context package.

Required deliverables:

- YAML workspace definitions
- role documents
- repository reader
- document loader
- read-only repository access
- visible loaded-context list
- context preview
- per-workspace refresh
- refresh-all control
- load-error reporting
- automated tests

Scope rule:

B3 loads local configuration and documents only.

It must not add AI, persistence, State Bus or handoffs.

---

# Planned Milestones

## ASSISTANT-001B4 — Local State and Conversation Persistence

- SQLite schema
- conversation persistence
- department state
- attachment metadata persistence
- layout persistence
- restart continuity

## ASSISTANT-001B5 — AI Provider Integration

- provider abstraction
- OpenAI Responses provider
- multimodal attachments
- background requests
- independent department conversations
- error handling

## ASSISTANT-001B6 — Department State Bus and Handoffs

- department summaries
- controlled cross-department awareness
- handoff creation
- handoff attachments
- handoff status transitions
- authority boundaries

## ASSISTANT-001B7 — MVP Verification and Closeout

- end-to-end three-department workflow
- restart continuity
- authority-boundary verification
- documentation
- packaging instructions
