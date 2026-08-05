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

## Machine-readable automatic request envelope

Required fields:

- `schema_version`: `1`
- `request_type`
- `title`
- `problem_or_need`
- `required_output`
- `constraints`
- `acceptance_criteria`

Allowed request types:

- `CONSOLE_TOOL_REQUEST`
- `CONSOLE_INTEGRATION_REQUEST`
- `CONSOLE_WORKFLOW_REQUEST`
- `CONSOLE_DEFECT`
- `CONSOLE_DECISION_REQUEST`

Valid requests are routed automatically. Invalid blocks are ignored with bounded diagnostics. Departments must not claim delivery; Console owns transport and return.

## Corrective escalation limits

Each automatic escalation chain permits the initial CDU request and one corrective CDU defect request. The second return is terminal for automatic routing. Any further required action is surfaced to the operator. Corrective CONSOLE_DEFECT requests include the latest available Console snapshot and runtime log automatically.
