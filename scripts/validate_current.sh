#!/usr/bin/env bash
set -uo pipefail

cd "$(dirname "$0")/.."
mkdir -p data/logs
LOG="data/logs/validation-$(date +%Y%m%d-%H%M%S).log"

set +e
{
  echo "=== CURVATURE CONSOLE VALIDATION ==="
  echo "Date: $(date --iso-8601=seconds)"
  echo
  echo "=== PYTEST ==="
  python -m pytest -q
  PYTEST_EXIT=$?
  echo
  echo "pytest exit code: $PYTEST_EXIT"
  echo
  echo "=== GIT DIFF CHECK ==="
  git diff --check
  DIFF_EXIT=$?
  echo
  echo "git diff --check exit code: $DIFF_EXIT"
  echo
  echo "=== GIT STATUS ==="
  git status --short
  STATUS_EXIT=$?
  echo
  echo "git status exit code: $STATUS_EXIT"
  echo
  echo "=== END ==="
} > >(tee "$LOG") 2>&1
set -e

echo
echo "LOG FILE: $LOG"

if [[ $PYTEST_EXIT -ne 0 || $DIFF_EXIT -ne 0 || $STATUS_EXIT -ne 0 ]]; then
  exit 1
fi
