#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
REPO_NAME="$(basename "$REPO_ROOT")"
OUTPUT_DIR="${HOME}"
OUTPUT_FILE="${OUTPUT_DIR}/${REPO_NAME}-current.zip"

cd "$REPO_ROOT"

echo "Repository: $REPO_ROOT"
echo "Output:     $OUTPUT_FILE"

rm -f "$OUTPUT_FILE"

python - "$REPO_ROOT" "$OUTPUT_FILE" <<'PY'
from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path

repo_root = Path(sys.argv[1]).resolve()
output_file = Path(sys.argv[2]).resolve()

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

excluded_names = {
    "curvature-console-current.zip",
}

excluded_parts = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}

files: list[Path] = []

for relative_path in relative_paths:
    if relative_path.name in excluded_names:
        continue

    if relative_path.suffix == ".pyc":
        continue

    if any(part in excluded_parts for part in relative_path.parts):
        continue

    absolute_path = repo_root / relative_path

    if not absolute_path.is_file():
        continue

    files.append(relative_path)

files.sort(key=lambda path: path.as_posix())

git_commit = subprocess.run(
    ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
    check=True,
    capture_output=True,
    text=True,
).stdout.strip()

git_branch = subprocess.run(
    ["git", "-C", str(repo_root), "branch", "--show-current"],
    check=True,
    capture_output=True,
    text=True,
).stdout.strip()

git_status = subprocess.run(
    ["git", "-C", str(repo_root), "status", "--short", "--branch"],
    check=True,
    capture_output=True,
    text=True,
).stdout.rstrip()

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

with zipfile.ZipFile(
    output_file,
    mode="w",
    compression=zipfile.ZIP_DEFLATED,
    compresslevel=9,
) as archive:
    archive.writestr("SNAPSHOT_INFO.txt", snapshot_info)

    for relative_path in files:
        absolute_path = repo_root / relative_path
        archive.write(
            absolute_path,
            arcname=relative_path.as_posix(),
        )

print(f"Created: {output_file}")
print(f"Included files: {len(files)}")
PY

echo
ls -lh "$OUTPUT_FILE"
echo
echo "Snapshot ready:"
echo "$OUTPUT_FILE"
