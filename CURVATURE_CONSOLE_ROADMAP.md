# CURVATURE CONSOLE ROADMAP

Status: Operational Maintenance
Version: 2.0.0
Owner: Project Curvature
Last Updated: 2026-07-24

# Product Constraint

Normal Console operation must not cost more than the existing ChatGPT Plus
subscription.

The approved workflow uses:

- one shared ChatGPT Project named `Curvature`;
- three persisted department conversations;
- local SQLite state;
- Playwright browser automation;
- ordinary Chrome as visible fallback and observation surface;
- no mandatory paid OpenAI API;
- no automatic commit or push.

# Operational Release

Curvature Console is operational as of commit:

```text
070eecd
```

Verified baseline:

```text
118 automated tests passed
```

# Completed Milestones

- ASSISTANT-001B1 — Repository and Application Foundation
- ASSISTANT-001B2 — Three-Panel Desktop Shell
- Per-Department Attachments
- ASSISTANT-001B3 — Workspace Configuration and Context Loading
- ASSISTANT-001B4 — Local State and Restart Persistence
- ASSISTANT-001B5.1 — Task and Thread Handoff Packages
- ASSISTANT-001B5.2A — Browser Bridge Foundation
- ASSISTANT-001B5.2B — Visible Send and Receive Workflow
- ASSISTANT-001B5.2C / B5.2R — Deterministic URL-Only Routing
- ASSISTANT-001B5.2D — Generated File Download Capture
- ASSISTANT-001B5.2E — Package Review and Safe Apply
- ASSISTANT-001B5.4A — Thread Pressure Foundation
- ASSISTANT-001B5.4B — Pressure Warnings and Handoff Integration
- Hybrid Contenteditable and New-Chat Handoff Lifecycle
- Console Operational Closeout

# Current Development Policy

Broad Console feature development is paused.

```text
Use Console
→ identify a real operational limitation
→ decide whether it blocks Curvature
→ promote the minimum corrective sprint
→ implement once
→ deep live validation in Core
→ department-specific smoke tests only when warranted
```

# Deferred Until Required

## Structured Department Conversation Records

Potential scope:

- separate user and assistant entries;
- timestamps;
- request and route markers;
- restart migration;
- better operation history.

## Expanded Department State Bus

Potential scope:

- structured summaries;
- explicit blockers;
- accepted outputs;
- formal department handoff records.

## Unified Operation Trace

Potential scope:

```text
request
→ context
→ browser exchange
→ response
→ downloads
→ package review
→ repository mutation
→ tests
→ Git state
```

## UX Improvements

Potential scope:

- manual ZIP import into Downloads;
- prominent context-refresh success message;
- richer progress reporting for slow new-chat creation;
- download and package history management.

# Release Maintenance Gate

Any future Console change must preserve:

- all three department panels;
- strict department isolation;
- URL-only routing;
- explicit user approval for repository writes;
- hybrid browser behavior;
- zero mandatory paid API usage;
- no automatic commit or push;
- complete automated tests;
- clean Git state.

# Exact Next Step

Return to the main Project Curvature roadmap and use Console as the normal
coordination and implementation interface.
