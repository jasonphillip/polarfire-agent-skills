#!/usr/bin/env python3
"""Validate plugin metadata, skill sources, and public text without dependencies."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
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
        if line == "metadata:":
            section = "metadata."
            continue
        match = re.fullmatch(r"\s*([\w-]+):\s*(.+?)\s*", line)
        if match:
            out[section + match.group(1)] = match.group(2).strip('"\'')
    return out


def source_paths(path: Path) -> list[str]:
    return re.findall(r"^Source:\s*`([^`]+)`\s*$", path.read_text(encoding="utf-8"), re.M)


def files_for_scan(root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root, capture_output=True, check=True,
    )
    return [root / part.decode() for part in result.stdout.split(b"\0") if part]


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
    if len(skills) != 10:
        errors.append(f"expected 10 skills, found {len(skills)}")
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
        for index, line in enumerate(lines):
            if line == "```" and index + 1 < len(lines):
                if not lines[index + 1].startswith("Source: `"):
                    errors.append(f"{rel}:{index + 1}: code block has no immediate Source")
        paths = source_paths(skill)
        if not paths:
            errors.append(f"{rel}: no Source paths")
        for item in paths:
            target = (source / item).resolve()
            if not target.is_relative_to(source) or not target.is_file():
                errors.append(f"{rel}: invalid Source path: {item}")
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
            errors.append(f"non-text tracked file: {rel}")
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
