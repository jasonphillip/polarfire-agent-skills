#!/usr/bin/env python3
"""Validate plugin metadata, skill sources, and public text without dependencies."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

NAME = "polarfire-agent-skills"
VERSION = "2026.10.0"
# Keep forbidden spellings out of the pack, including this checker.
BANNED = tuple(bytes.fromhex(code).decode() for code in (
    "626565", "4265656c696e6b", "737061726b32", "737061726b33",
    "777331", "5461696c7363616c65", "2f686f6d652f", "50686173652049",
    "4b5050", "53424952", "64656c6976657261626c65",
))
JSON_FILES = (
    "plugin.json",
    ".claude-plugin/marketplace.json",
    ".codex-plugin/plugin.json",
    ".cursor-plugin/plugin.json",
    ".cursor-plugin/marketplace.json",
    ".agents/plugins/marketplace.json",
)
REQUIRED_DOCS = (
    "README.md", "SOURCES.md", "docs/install.md", "docs/getting-started.md",
    "docs/scope.md", "docs/pipeline.md", "docs/hardware.md", "docs/claims.md",
    "docs/validation.md", "docs/release-notes.md",
)
SKILL_NAMES = {
    "adapt-your-model", "claim-log", "dataset-and-training",
    "fabric-watchdog-fallback", "hls4ml-libero-route", "kit-program",
    "kit-run-inference", "libero-build", "smarthls-fixed-point",
    "vbx-compile", "vbx-export-int8", "vbx-ops-guard",
}


def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ValueError("frontmatter opening marker absent")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError("frontmatter closing marker absent") from exc
    out: dict[str, str] = {}
    section = ""
    for line in lines[1:end]:
        if line in ("metadata:", "tools:", "skills:"):
            section = "metadata." if line == "metadata:" else ""
            continue
        match = re.fullmatch(r"\s*([\w-]+):\s*(.+?)\s*", line)
        if match:
            out[section + match.group(1)] = match.group(2).strip('"\'')
    return out


def source_paths(path: Path) -> list[str]:
    return re.findall(r"^Source:\s*`([^`]+)`\s*$", path.read_text(encoding="utf-8"), re.M)


def files_for_scan(root: Path) -> list[Path]:
    files: list[Path] = []
    for directory, subdirs, names in os.walk(root):
        relative = Path(directory).relative_to(root)
        excluded = {".git", "__pycache__", ".venv", "deps", "reports"}
        if relative == Path("probes"):
            excluded.add("out")
        subdirs[:] = [name for name in subdirs if name not in excluded]
        files.extend(Path(directory) / name for name in names)
    return files


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    source = args.source.resolve()
    errors: list[str] = []
    if not source.is_dir():
        errors.append(f"source root absent: {source}")
    skills = sorted((root / "skills").glob("*/SKILL.md"))
    if {skill.parent.name for skill in skills} != SKILL_NAMES:
        errors.append("skill set differs from expected names")
    for skill in skills:
        rel = skill.relative_to(root)
        try:
            fields = frontmatter(skill)
        except ValueError as exc:
            errors.append(f"{rel}: {exc}")
            continue
        for key in ("name", "description", "license", "metadata.author", "metadata.version"):
            if not fields.get(key):
                errors.append(f"{rel}: {key} absent")
        if fields.get("name") != skill.parent.name:
            errors.append(f"{rel}: name differs from folder")
        if fields.get("metadata.version") != VERSION:
            errors.append(f"{rel}: version differs from plugin")
        lines = skill.read_text(encoding="utf-8").splitlines()
        paths = source_paths(skill)
        for item in paths:
            target = (source / item).resolve()
            if not target.is_relative_to(source) or not target.is_file():
                errors.append(f"{rel}: invalid Source path: {item}")
        if "## Checks" not in lines or not lines[-1].startswith("- Read "):
            errors.append(f"{rel}: final Checks section absent")
        if not 40 <= len(lines) <= 90:
            errors.append(f"{rel}: expected 40 to 90 lines, found {len(lines)}")
    for item in REQUIRED_DOCS:
        if not (root / item).is_file():
            errors.append(f"required document absent: {item}")
    install = (root / "docs/install.md").read_text(encoding="utf-8")
    for marker in ("2.1.296", "0.157.1", "--plugin-dir", "--marketplace", "Cursor"):
        if marker not in install:
            errors.append(f"docs/install.md: expected installation detail absent: {marker}")
    if not re.search(r"(?m)^Marketplace install: (tested \d{4}-\d{2}-\d{2}|not yet tested)\b", install):
        errors.append("docs/install.md: 'Marketplace install:' status line absent or undated")
    readme = (root / "README.md").read_text(encoding="utf-8")
    if "Cursor-Compatible" in readme:
        errors.append("README.md: untested Cursor badge present")
    agent = root / "agents/polarfire-bringup.md"
    try:
        fields = frontmatter(agent)
    except (OSError, ValueError) as exc:
        errors.append(f"agents/polarfire-bringup.md: {exc}")
    else:
        for key, expected in (("name", "polarfire-bringup"), ("license", "Apache-2.0"),
                              ("metadata.author", "Jason Phillip"),
                              ("metadata.version", VERSION), ("metadata.stage", "beta")):
            if fields.get(key) != expected:
                errors.append(f"agents/polarfire-bringup.md: {key} differs")
        agent_text = agent.read_text(encoding="utf-8")
        for section, expected in (("tools", ("Read", "Grep", "Glob", "Bash")),
                                  ("skills", tuple(skill.parent.name for skill in skills))):
            match = re.search(rf"(?m)^{section}:\n((?:  - [^\n]+\n)+)", agent_text)
            values = re.findall(r"(?m)^  - ([^\n]+)$", match.group(1)) if match else []
            if set(values) != set(expected) or len(values) != len(expected):
                errors.append(f"agents/polarfire-bringup.md: {section} list differs")
        if not fields.get("description"):
            errors.append("agents/polarfire-bringup.md: description absent")
    for item in JSON_FILES:
        path = root / item
        if not path.is_file():
            errors.append(f"missing JSON: {item}")
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid JSON: {item}: {exc}")
            continue
        if data.get("name") != NAME or data.get("version") != VERSION:
            errors.append(f"{item}: name or version differs")
        if item == ".codex-plugin/plugin.json" and data.get("skills") != "./skills/":
            errors.append(f"{item}: skills directory differs")
        for plugin in data.get("plugins", []):
            if plugin.get("name") != NAME or plugin.get("version") != VERSION:
                errors.append(f"{item}: plugin name or version differs")
    for path in files_for_scan(root):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Binary artifacts are not public prose.
            continue
        for term in BANNED:
            if re.search(r"(?<![A-Za-z0-9])" + re.escape(term) + r"(?![A-Za-z0-9])", text, re.I):
                errors.append(f"{rel}: forbidden text present")
    if errors:
        print(f"FAIL: {len(errors)} issue(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"PASS: {len(skills)} skills, {len(JSON_FILES)} JSON files, source paths, and public text")
    return 0


if __name__ == "__main__":
    sys.exit(main())
