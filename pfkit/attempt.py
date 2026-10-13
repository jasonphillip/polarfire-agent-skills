"""Attempt identity for pipeline and manual staged runs."""
from __future__ import annotations

import json
import secrets
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .pipeline import ROOT, write_json
from .reporting import git_revision


def _dirty():
    try:
        result = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain"],
                                text=True, capture_output=True, timeout=10)
        return bool(result.stdout.strip()) if result.returncode == 0 else "unavailable"
    except (OSError, subprocess.TimeoutExpired):
        return "unavailable"


def new(run_dir, argv):
    now = datetime.now(timezone.utc)
    record = {"attempt_id": f"{now:%Y%m%d-%H%M%S}-{secrets.token_hex(4)}",
              "argv": [str(arg) for arg in argv], "started_utc": now.isoformat(),
              "kit_revision": git_revision(ROOT), "dirty": _dirty(),
              "worktree": (ROOT / ".git").is_file()}
    directory = Path(run_dir)
    directory.mkdir(parents=True, exist_ok=True)
    write_json(directory / "attempt.json", record)
    return record


def current(run_dir):
    path = Path(run_dir) / "attempt.json"
    return json.loads(path.read_text()) if path.is_file() else None


def manual(run_dir):
    record = current(run_dir)
    if record is not None:
        return record
    now = datetime.now(timezone.utc)
    record = {"attempt_id": f"manual-{now:%Y%m%d-%H%M%S}-{secrets.token_hex(4)}",
              "argv": [], "started_utc": now.isoformat(),
              "kit_revision": git_revision(ROOT), "dirty": _dirty(),
              "worktree": (ROOT / ".git").is_file()}
    directory = Path(run_dir)
    directory.mkdir(parents=True, exist_ok=True)
    write_json(directory / "attempt.json", record)
    return record
