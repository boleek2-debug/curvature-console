# ROADMAP

Status: Active
Version: 0.4.0
Owner: Project Curvature
Last Updated: 2026-07-18

---

# Completed Milestones

## ASSISTANT-001B1 — Repository and Application Foundation

Completed and verified.

## ASSISTANT-001B2 — Three-Panel Desktop Shell

Completed and verified.

## Per-Department Attachments

Completed and verified.

## ASSISTANT-001B3 — Workspace Configuration and Context Loading

Completed and verified:

- workspace definitions and roles
- read-only repository access
- automatic context loading
- context preview and refresh
- automated tests

---

# Active Milestone

## ASSISTANT-001B4 — Local State and Conversation Persistence

Goal:

Restore each department to its previous operational state after application restart.

Required deliverables:

- SQLite schema
- independent department state
- conversation transcript persistence
- draft persistence
- attachment metadata persistence
- persistent pasted screenshots
- splitter layout persistence
- Focus mode persistence
- restart continuity
- automated tests

Scope rule:

B4 stores local operational state only.

It must not add AI integration, State Bus, handoffs or repository writes.

---

# Planned Milestones

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
