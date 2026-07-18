# ARCHITECTURE DECISIONS

Status: Active  
Version: 1.0.0  
Owner: Project Curvature  
Last Updated: 2026-07-18

---

# Purpose

This document records durable Curvature Console architecture and product decisions that must survive sprint changes, handoffs and documentation rewrites.

A decision remains active until it is explicitly superseded by a later decision in this file.

---

# ADR-001 — Separate Internal Console

Status: Accepted  
Date: 2026-07-18

## Context

Project Curvature requires persistent coordination between Project, Core and Research without merging their responsibilities into gameplay systems or the Curvature Platform.

## Decision

Curvature Console is a separate internal desktop application and repository.

It is not:

- Curvature Platform;
- World Core;
- Chronicle Client;
- gameplay;
- a public player interface.

It provides three permanent and equal workspaces:

- Curvature Project;
- Curvature Core;
- Curvature Research.

## Consequences

- each department preserves independent state;
- authority boundaries are explicit;
- attachments are isolated by department;
- cross-department work requires an explicit handoff;
- Project Curvature repository access remains read-only during the MVP.

---

# ADR-002 — Zero Additional AI Cost

Status: Accepted  
Date: 2026-07-18

## Context

The initial ASSISTANT-001B5 plan proposed direct OpenAI Responses API integration.

API use is billed separately from ChatGPT Plus and could create substantial recurring costs under the user's real development-message volume, large contexts, code files, documentation and research workload.

The user explicitly decided not to pay more than the existing ChatGPT Plus subscription for normal Curvature Console operation.

## Decision

Curvature Console must not require additional AI spending beyond the user's existing ChatGPT Plus subscription.

The default and MVP architecture therefore:

- does not use the paid OpenAI API;
- does not require an OpenAI API key;
- does not send automatic model requests;
- does not perform paid background requests;
- does not perform paid web-search or tool requests;
- does not hide, defer or silently accumulate usage charges;
- keeps official ChatGPT as the primary AI conversation interface;
- uses Curvature Console as the local coordination, context, persistence and transfer layer.

ASSISTANT-001B5 is renamed:

```text
ASSISTANT-001B5 — ChatGPT Plus Workflow Integration
```

The intended workflow is manual and user-controlled:

```text
Console prepares a department transfer package
→ user previews it
→ user copies it
→ user pastes it into official ChatGPT
→ user receives a response under ChatGPT Plus
→ user copies the response
→ user imports it into the selected Console department
```

## Prohibited Default Behavior

Curvature Console must not:

- require billing setup;
- require prepaid API credits;
- ask for `OPENAI_API_KEY` as part of normal installation;
- invoke paid APIs through a Send button;
- perform automatic retries that can incur charges;
- perform automatic paid research;
- treat ChatGPT Plus as if it grants API access;
- use unsupported browser automation to bypass official product controls.

## Future Reconsideration

Paid provider integration may be reconsidered only through a new explicit architecture decision.

Such integration must be:

- optional;
- disabled by default;
- separated from the normal Plus workflow;
- protected by visible spending limits;
- protected by explicit user approval;
- documented with current pricing and privacy implications;
- removable without breaking core Console functions.

## Consequences

Positive:

- predictable cost;
- no surprise API billing;
- no API key management;
- no paid-request failure mode;
- preserves the user's existing workflow;
- Console remains useful offline for preparation and persistence.

Trade-offs:

- transfer to and from ChatGPT is initially manual;
- attached files must be uploaded manually;
- automatic background AI work is unavailable;
- responses cannot arrive directly through the Console without a future supported integration.

---

# ADR-003 — Read-Only Project Repository During MVP

Status: Accepted  
Date: 2026-07-18

## Context

Curvature Console loads Project Curvature context, but automatic writes would create authority, safety and Git-integrity risks before the handoff system is complete.

## Decision

During the MVP, access to:

```text
~/Curvature
```

remains read-only.

## Consequences

- Console may load configured documents;
- Console may prepare proposed changes;
- Console may not write repository files;
- Console may not execute commits or pushes;
- user-controlled replacement files and Git commands remain the implementation workflow.
