#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
REPO_NAME="$(basename "$REPO_ROOT")"
SNAPSHOT_DIR="${REPO_ROOT}/data/snapshots"
STAMP="$(date +%Y%m%d-%H%M%S)"
SHORT_HEAD="$(git -C "$REPO_ROOT" rev-parse --short HEAD)"
OUTPUT_FILE="${SNAPSHOT_DIR}/${REPO_NAME}-snapshot-${STAMP}-${SHORT_HEAD}.zip"
LATEST_LINK="${SNAPSHOT_DIR}/latest.zip"

mkdir -p "$SNAPSHOT_DIR"
cd "$REPO_ROOT"

echo "Repository: $REPO_ROOT"
echo "Output:     $OUTPUT_FILE"

python - "$REPO_ROOT" "$OUTPUT_FILE" <<'PY'
from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path

repo_root = Path(sys.argv[1]).resolve()
output_file = Path(sys.argv[2]).resolve()
snapshot_directory = output_file.parent

result = subprocess.run(
    [
        "git",
        "-C",
        str(repo_root),
        "ls-files",
        "--cached",
        "--others",
        "--exclude-standard",
        "-z",
    ],
    check=True,
    capture_output=True,
)

relative_paths = [
    Path(raw.decode("utf-8"))
    for raw in result.stdout.split(b"\0")
    if raw
]

excluded_parts = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}

files: list[Path] = []

for relative_path in relative_paths:
    absolute_path = (repo_root / relative_path).resolve()

    if absolute_path == output_file:
        continue
    if snapshot_directory in absolute_path.parents:
        continue
    if relative_path.suffix == ".pyc":
        continue
    if any(part in excluded_parts for part in relative_path.parts):
        continue
    if not absolute_path.is_file():
        continue

    files.append(relative_path)

files.sort(key=lambda path: path.as_posix())


def git_text(*arguments: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo_root), *arguments],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.rstrip()


git_commit = git_text("rev-parse", "HEAD")
git_branch = git_text("branch", "--show-current")
git_status = git_text("status", "--short", "--branch")
git_log = git_text("log", "-10", "--oneline", "--decorate")
git_diff = git_text("diff", "--binary")
git_diff_staged = git_text("diff", "--cached", "--binary")

snapshot_info = "\n".join(
    [
        "Curvature Console current-state snapshot",
        "",
        f"Repository: {repo_root}",
        f"Branch: {git_branch}",
        f"Commit: {git_commit}",
        "",
        "Git status:",
        git_status or "(clean)",
        "",
        f"Included files: {len(files)}",
        "",
    ]
)

metadata = {
    "SNAPSHOT_INFO.txt": snapshot_info,
    "GIT_HEAD.txt": git_commit + "\n",
    "GIT_BRANCH.txt": git_branch + "\n",
    "GIT_STATUS.txt": (git_status or "(clean)") + "\n",
    "GIT_LOG.txt": git_log + "\n",
    "GIT_DIFF.patch": git_diff,
    "GIT_DIFF_STAGED.patch": git_diff_staged,
}

with zipfile.ZipFile(
    output_file,
    mode="w",
    compression=zipfile.ZIP_DEFLATED,
    compresslevel=9,
    strict_timestamps=False,
) as archive:
    for name, content in metadata.items():
        archive.writestr(name, content)

    for relative_path in files:
        archive.write(
            repo_root / relative_path,
            arcname=relative_path.as_posix(),
        )

print(f"Created: {output_file}")
print(f"Included files: {len(files)}")
PY

ln -sfn "$(basename "$OUTPUT_FILE")" "$LATEST_LINK"

echo
ls -lh "$OUTPUT_FILE"
echo
echo "Snapshot ready:"
echo "$OUTPUT_FILE"
