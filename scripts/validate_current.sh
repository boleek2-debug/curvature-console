#!/usr/bin/env bash
set -uo pipefail

cd "$(dirname "$0")/.."
mkdir -p data/logs
LOG="data/logs/validation-$(date +%Y%m%d-%H%M%S).log"

# Terminal formatting. Keep the live run colourful/readable while storing
# a plain-text validation artifact without ANSI escape sequences.
if [[ -t 1 ]]; then
  GREEN=$'\033[1;32m'
  RED=$'\033[1;31m'
  CYAN=$'\033[1;36m'
  YELLOW=$'\033[1;33m'
  BOLD=$'\033[1m'
  RESET=$'\033[0m'
else
  GREEN=""
  RED=""
  CYAN=""
  YELLOW=""
  BOLD=""
  RESET=""
fi

TMP_LOG="$(mktemp)"
trap 'rm -f "$TMP_LOG"' EXIT

section() {
  printf "\n%s=== %s ===%s\n" "$CYAN$BOLD" "$1" "$RESET"
}

result_line() {
  local label="$1"
  local code="$2"
  if [[ "$code" -eq 0 ]]; then
    printf "%s● PASS%s  %s\n" "$GREEN" "$RESET" "$label"
  else
    printf "%s● FAIL%s  %s (exit %s)\n" "$RED" "$RESET" "$label" "$code"
  fi
}

set +e
{
  printf "%s=== CURVATURE CONSOLE VALIDATION ===%s\n" "$BOLD" "$RESET"
  echo "Date: $(date --iso-8601=seconds)"

  section "PYTEST"
  # Force pytest colour for the live terminal. ANSI codes are stripped
  # from the persisted validation log below.
  python -m pytest -q --color=yes
  PYTEST_EXIT=$?
  echo
  echo "pytest exit code: $PYTEST_EXIT"
  result_line "pytest" "$PYTEST_EXIT"

  section "GIT DIFF CHECK"
  git diff --check
  DIFF_EXIT=$?
  echo
  echo "git diff --check exit code: $DIFF_EXIT"
  result_line "git diff --check" "$DIFF_EXIT"

  section "GIT STATUS"
  git status --short
  STATUS_EXIT=$?
  echo
  echo "git status exit code: $STATUS_EXIT"
  result_line "git status" "$STATUS_EXIT"

  section "SUMMARY"
  if [[ $PYTEST_EXIT -eq 0 && $DIFF_EXIT -eq 0 && $STATUS_EXIT -eq 0 ]]; then
    printf "%s● VALIDATION PASS%s\n" "$GREEN$BOLD" "$RESET"
  else
    printf "%s● VALIDATION FAIL%s\n" "$RED$BOLD" "$RESET"
  fi
} 2>&1 | tee "$TMP_LOG"
set -e

# Preserve a clean, greppable historical artifact.
sed -E $'s/\x1B\\[[0-9;]*[mK]//g' "$TMP_LOG" > "$LOG"

echo
printf "%sLOG FILE:%s %s\n" "$YELLOW$BOLD" "$RESET" "$LOG"

if [[ $PYTEST_EXIT -ne 0 || $DIFF_EXIT -ne 0 || $STATUS_EXIT -ne 0 ]]; then
  exit 1
fi
