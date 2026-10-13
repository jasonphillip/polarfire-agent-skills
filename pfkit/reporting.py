"""Collect local provenance without invoking Git commands."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from importlib.metadata import distributions
from pathlib import Path
from .pipeline import ROOT, sha256, write_json


def git_revision(directory):
    git = Path(directory) / ".git"
    if git.is_file():
        line = git.read_text().strip()
        git = (Path(directory) / line.removeprefix("gitdir: ")).resolve()
    common = git
    if (git / "commondir").is_file():
        common = (git / (git / "commondir").read_text().strip()).resolve()
    head = git / "HEAD"
    if not head.exists():
        return "unavailable"
    value = head.read_text().strip()
    if value.startswith("ref: "):
        ref = value[5:]
        loose = git / ref
        if not loose.exists():
            loose = common / ref
        if loose.exists():
            return loose.read_text().strip()
        packed = common / "packed-refs"
        if packed.exists():
            for line in packed.read_text().splitlines():
                if line.endswith(" " + ref):
                    return line.split()[0]
        return "unresolved:" + ref
    return value


def append_log(run_dir, command, code):
    path = Path(run_dir) / "commands.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as stream:
        stream.write(json.dumps({"time_utc": datetime.now(timezone.utc).isoformat(),
                                 "command": command, "exit_code": code}) + "\n")


def report(run_dir):
    directory = Path(run_dir)
    directory.mkdir(parents=True, exist_ok=True)
    attempt_path = directory / "attempt.json"
    attempt_id = json.loads(attempt_path.read_text()).get("attempt_id") if attempt_path.is_file() else None
    versions = sorted({f"{name}=={dist.version}" for dist in distributions()
                       if (name := dist.metadata.get("Name"))})
    (directory / "pip-freeze.txt").write_text("\n".join(versions) + "\n")
    revs = {"kit": git_revision(ROOT)}
    for name in ("tychon-quantum-sensing", "vectorblox-sdk", "icicle-kit-reference-design"):
        revs[name] = git_revision(ROOT / "deps" / name)
    write_json(directory / "revisions.json", revs)
    artifacts = {}
    for path in sorted(directory.rglob("*")):
        if path.is_file() and path.name not in ("artifacts.json", "summary.md"):
            artifacts[str(path.relative_to(directory))] = sha256(path)
    write_json(directory / "artifacts.json", artifacts)
    lines = ["# Run summary", "", "Revisions are in `revisions.json`. Commands and exit codes are in `commands.jsonl`.",
             "Package versions are in `pip-freeze.txt`. Artifact hashes are in `artifacts.json`.", ""]
    for name in ("dataset.manifest.json", "training.json", "eval.json", "export.manifest.json", "compile.json", "sim.json", "infer.json", "compare.json"):
        path = directory / name
        if path.exists():
            record = json.loads(path.read_text())
            source_id = record.get("attempt_id")
            status = record.get("status", "not run")
            if attempt_id is not None and source_id != attempt_id:
                label = f"stale (attempt {source_id or 'unknown'})"
            elif status == "failed":
                label = "failed"
            elif status in ("completed", "passed") and source_id is not None and source_id == attempt_id:
                label = "recorded"
            else:
                label = "not run"
            lines.append(f"- {name}: {label}")
        else:
            lines.append(f"- {name}: not run")
    (directory / "summary.md").write_text("\n".join(lines) + "\n")
    return directory / "summary.md"
