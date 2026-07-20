#!/usr/bin/env bash
set -euo pipefail

REPOSITORY_ROOT="$(
  cd "$(dirname "${BASH_SOURCE[0]}")/.."
  pwd
)"
PYTHON="/home/seb/miniconda3/envs/curvature-console/bin/python"

if [[ ! -x "$PYTHON" ]]; then
  printf 'Curvature Console Python not found: %s\n' "$PYTHON" >&2
  exit 1
fi

cd "$REPOSITORY_ROOT"
exec "$PYTHON" -m curvature_console.main
