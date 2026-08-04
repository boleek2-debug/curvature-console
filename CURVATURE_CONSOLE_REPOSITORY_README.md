# Curvature Console Repository

Curvature Console is the local development control plane and orchestration platform for Project Curvature.

It contains three permanent Chronicle department workspaces:

- Curvature Project;
- Curvature Core;
- Curvature Research.

It also contains the Curvature Console Development Unit, which owns Console development, diagnostics, integrations and workflow tooling without taking over Chronicle department authority.

## Current verified base

```text
Repository: ~/curvature-console
Branch: main
Commit: 2aad8a866ef78660d1c5369d88334bac49611016
Remote: origin/main at the same commit
Working tree: clean in the supplied snapshot
```

## Core capabilities

- independent department state, context, drafts and attachments;
- deterministic ChatGPT Plus Browser Bridge;
- generated-file capture;
- supervised handoffs and return path;
- package review, safe apply, backup and rollback;
- Console Development Chat with diagnostics, screenshots and downloads;
- validation logs and repository snapshots;
- no mandatory paid API and no automatic Git push.

## Authoritative CDU documentation

The Console Development Unit documentation lives under `docs/`:

- role and authority;
- product vision;
- architecture and workflow;
- integration registry and tool request protocol;
- backlog and roadmap;
- decisions, test matrix, UI actions and use cases;
- security/cost policy and current state snapshot.

## Run and validate

```bash
cd ~/curvature-console
conda activate curvature-console
python -m curvature_console.main
./scripts/validate_current.sh
```

## Governing rule

Project, Core and Research define Chronicle work. CDU ensures that Console can support, automate, route, record, validate and operate the approved process.
