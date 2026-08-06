# Console Use Cases

Status: Active
Version: 1.0.0
Owner: Curvature Console Development Unit

## Verified use cases

- send department tasks through ChatGPT Plus;
- preserve department routes and continuity;
- send files and pasted screenshots;
- receive arbitrary generated files;
- review and safely apply repository packages;
- supervise interdepartmental handoffs and returns;
- collect diagnostics, logs and repository state;
- develop Console through the Console Development Chat.

## Planned use cases

### Sequential multi-department work

Operator prepares several requests; Console executes complete exchanges one at a time and records each result.

### Console tool request

Project, Core or Research specifies a missing capability; CDU assesses, implements, validates and returns it.

### ComfyUI workflow

Console selects a registered workflow, validates inputs, runs it remotely, tracks queue state and captures outputs with provenance.

### Godot validation

Console launches an approved project or test, captures logs/screenshots and returns evidence to Core.

### Blender technical processing

Console invokes an approved headless script for import, inspection, conversion or validation without deciding art direction.

### Research source intake

Console acquires permitted sources, records access classification and checksums, extracts usable content and hands it to Research without deciding conclusions.

## Use case: Core lacks a Console tool

1. Project assigns an implementation task to Core.
2. Core determines that a required Console capability does not exist.
3. Core emits a structured Console request in its normal response.
4. Console validates and queues the request to CDU automatically.
5. CDU implements or assesses the capability and reports required approvals.
6. Console captures generated artifacts and returns the CDU result to Core.
7. Core resumes the original task without operator copy/paste.
8. The workflow closes only after tests, live validation and documentation are current.

## Duplicate generated-file channels

When ChatGPT exposes one generated file through both an Estuary fetch response and a native browser download, Console computes a logical signature from canonical filename, size and SHA-256. The duplicate technical capture is deleted and only one artifact is returned to the source department.
## Use case: background Project ↔ Core conversation

1. The operator gives Project a Chronicle goal or decision.
2. Project converts the approved intent into requirements without inventing new creative direction.
3. Console opens a durable Project ↔ Core operational conversation.
4. Project and Core clarify feasibility and implementation consequences without operator message transport.
5. The operator receives no reply-by-reply popups.
6. Console notifies the operator only when a final result, real decision, controlled action or terminal blocker exists.
7. Conversation Review shows the full transcript, recommendation, artifacts and evidence.
8. Accept closes or advances the work; Reject and Ask continue the same conversation.

## Use case: operator-owned vision gap

When a requirement depends on an unmade creative decision, Project must not fill the gap. It gathers relevant consequences from Core and Research, then presents the operator with a focused question, options and recommendation.

## UC — Review a background Core ↔ CDU conversation

1. Core emits an automatic Console request.
2. Console creates one durable operational conversation for the escalation chain.
3. Core and CDU exchanges continue without modal reply notifications.
4. Console appends the request, CDU response, artifacts and returned Core assessment to the same transcript.
5. When the chain reaches a result, blocker or operator decision, the Operational Conversations button shows a review count.
6. The operator opens the review window and reads the complete history without opening the underlying ChatGPT chats.
## Operator reviews an operational result
1. Departments complete or block a background operational conversation.
2. Console shows one review count instead of per-message popups.
3. Operator opens the full transcript.
4. Accept closes the result. Reject or Ask / Continue requires a comment and resumes the same source task.
5. The operator action and subsequent department response remain in the same durable history.

## Continue one operational conversation

When the operator selects Ask / Continue, Console records the comment in the existing conversation, resumes the source department and appends any subsequent CDU exchange as another round of the same conversation. The operator sees one list entry with updated round count and lifecycle timestamps.

## Use case: background production-department request

1. A source department emits an explicit `BEGIN_CURVATURE_OPERATIONAL_REQUEST` block.
2. Console validates the target, task, context, expected output, constraints and acceptance criteria.
3. Console opens or resumes one durable operational conversation and routes the request in the shared Browser Bridge queue.
4. The target works within its authority and may use the existing CDU escalation path when Console capability is missing.
5. Console captures the target response and artifacts and returns them to the source department automatically.
6. The source either emits one further operational request in the same conversation or stops at RESULT, BLOCKER or OPERATOR_DECISION.
7. Supervised handoff proposals remain separate and still require operator approval.
