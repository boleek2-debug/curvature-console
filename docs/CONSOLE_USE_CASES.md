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
