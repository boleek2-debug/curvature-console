# ROADMAP

Status: Active
Version: 0.2.0
Owner: Project Curvature
Last Updated: 2026-07-18

---

# Completed Milestone

## ASSISTANT-001B1 — Repository and Application Foundation

Completed and verified:

- standalone repository
- reproducible Conda environment
- package structure
- application entry point
- minimal main window
- automated tests
- successful desktop launch

---

# Active Milestone

## ASSISTANT-001B2 — Three-Panel Desktop Shell

Goal:

Create the first real Curvature Console interface with all three departments visible simultaneously.

Required deliverables:

- Curvature Project panel
- Curvature Core panel
- Curvature Research panel
- horizontal splitter
- equal initial widths
- independent panel scrolling
- independent conversation areas
- independent input areas
- department headers and status
- resizable panels
- temporary panel focus
- restoration to the three-panel layout
- automated tests

Scope rule:

B2 implements the visual and interaction shell only.

It must not add AI integration, persistence, context loading or handoffs.

---

# Planned Milestones

## ASSISTANT-001B3 — Workspace Configuration and Context Loading

- workspace definitions
- role documents
- repository reader
- document loader
- context preview
- manual refresh

## ASSISTANT-001B4 — Local State and Conversation Persistence

- SQLite schema
- conversation persistence
- department state
- layout persistence
- restart continuity

## ASSISTANT-001B5 — AI Provider Integration

- provider abstraction
- OpenAI Responses provider
- background requests
- independent department conversations
- error handling

## ASSISTANT-001B6 — Department State Bus and Handoffs

- department summaries
- controlled cross-department awareness
- handoff creation
- handoff status transitions
- authority boundaries

## ASSISTANT-001B7 — MVP Verification and Closeout

- end-to-end three-department workflow
- restart continuity
- authority-boundary verification
- documentation
- packaging instructions
