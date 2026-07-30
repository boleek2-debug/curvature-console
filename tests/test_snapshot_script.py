"""Integration tests for retained dated repository snapshots."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import zipfile


def _run(*args: str, cwd: Path, env: dict[str, str] | None = None) -> str:
    return subprocess.run(
        args,
        cwd=cwd,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def test_snapshot_script_creates_one_dated_zip_and_latest_symlink(
    tmp_path,
) -> None:
    repo = tmp_path / "curvature-console"
    repo.mkdir()
    (repo / "scripts").mkdir()
    source_script = (
        Path(__file__).parents[1] / "scripts" / "create_current_snapshot.sh"
    )
    script = repo / "scripts" / "create_current_snapshot.sh"
    script.write_bytes(source_script.read_bytes())
    script.chmod(0o755)
    (repo / "tracked.txt").write_text("tracked\n")
    (repo / ".gitignore").write_text("data/snapshots/\n")

    _run("git", "init", cwd=repo)
    _run("git", "add", ".", cwd=repo)
    commit_env = os.environ.copy()
    commit_env.update(
        {
            "GIT_AUTHOR_NAME": "Curvature Test",
            "GIT_AUTHOR_EMAIL": "test@example.invalid",
            "GIT_COMMITTER_NAME": "Curvature Test",
            "GIT_COMMITTER_EMAIL": "test@example.invalid",
        }
    )
    _run("git", "commit", "-m", "Snapshot baseline", cwd=repo, env=commit_env)
    (repo / "untracked.txt").write_text("untracked\n")

    first_output = _run("bash", str(script), cwd=repo)
    snapshot_dir = repo / "data" / "snapshots"
    first_snapshots = sorted(snapshot_dir.glob("curvature-console-snapshot-*.zip"))

    assert len(first_snapshots) == 1
    assert str(first_snapshots[0]) in first_output
    latest = snapshot_dir / "latest.zip"
    assert latest.is_symlink()
    assert latest.resolve() == first_snapshots[0]

    with zipfile.ZipFile(first_snapshots[0]) as archive:
        names = set(archive.namelist())
        assert "tracked.txt" in names
        assert "untracked.txt" in names
        assert "GIT_STATUS.txt" in names
        assert "GIT_DIFF.patch" in names
        assert not any(name.startswith("data/snapshots/") for name in names)
