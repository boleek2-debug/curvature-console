# Console Tool Request Protocol

Status: Approved
Version: 1.0.0
Owner: Curvature Console Development Unit

## Request types

- CONSOLE_TOOL_REQUEST
- CONSOLE_INTEGRATION_REQUEST
- CONSOLE_WORKFLOW_REQUEST
- CONSOLE_DEFECT
- CONSOLE_DECISION_REQUEST

## Required fields

- request identifier;
- requesting department;
- problem or development need;
- required input;
- required output;
- expected formats;
- validation requirements;
- priority;
- constraints;
- local execution requirement;
- network permission;
- licence and cost restrictions;
- hardware assumptions;
- security considerations;
- acceptance criteria.

## CDU response states

- ACCEPTED
- NEEDS_CLARIFICATION
- DEFERRED
- REJECTED
- IMPLEMENTING
- VALIDATING
- RELEASED
- CLOSED

## Routing

- scope and priority questions go to Project;
- Chronicle implementation contracts go to Core;
- source, evidence and licensing questions go to Research;
- Console architecture, integration and workflow execution remain with CDU.
