# Console UI Actions

Status: Active baseline
Version: 1.0.0
Owner: Curvature Console Development Unit

## Existing key actions

### Send Task

Input: department draft and attachments. Starts one Browser Bridge exchange. Fails visibly and preserves unsent state.

### Thread Handoff

Creates or continues a department conversation using a comprehensive context package and persists the verified route.

### Bridge Controls

Creates, reviews, approves, delivers, returns, holds or closes supervised handoffs.

### Package Review / Apply

Reviews a package, classifies file operations, requires approval, backs up targets, applies atomically and reports Git state.

### Console Development Unit

Opens diagnostics and Console Development Chat. Can attach current diagnostics, latest log, files and screenshots; captures generated downloads.

### Create Diagnostic Report

Collects repository, log, snapshot and operational state into a timestamped report.

## Planned actions

### Queue Request

Adds a Project, Core, Research or CDU exchange to the shared sequential queue.

### Cancel Queued / Hold Active / Retry Failed

Controls queue items without changing target, content or attachments silently.

### Prepare Console Tool Request

Creates a structured request and routes it to CDU after operator review.

### Run Tool Workflow

Invokes an approved adapter workflow with visible parameters, approvals, progress, logs, artifacts and validation.
