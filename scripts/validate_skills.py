#!/usr/bin/env python3
"""Validate active SKILL.md frontmatter (stdlib, optional PyYAML)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = ROOT / "catalog.json"
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

try:
    import yaml  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover
    yaml = None


def split_frontmatter(text: str, rel: str) -> list[str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{rel}: SKILL.md must start with '---'")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError(f"{rel}: frontmatter closing '---' is missing") from exc
    return lines[1:end]


def block_value(lines: list[str], start: int) -> tuple[str, int]:
    parts: list[str] = []
    index = start
    while index < len(lines) and (lines[index].startswith((" ", "\t")) or not lines[index].strip()):
        parts.append(lines[index].strip())
        index += 1
    return " ".join(part for part in parts if part), index


def minimal_frontmatter(lines: list[str], rel: str) -> dict[str, str]:
    result: dict[str, str] = {}
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip() or line.lstrip().startswith("#") or line.startswith((" ", "\t")):
            index += 1
            continue
        key, sep, value = line.partition(":")
        if not sep:
            raise ValueError(f"{rel}: invalid frontmatter line: {line!r}")
        key = key.strip()
        value = value.strip()
        if key in {"name", "description"}:
            if key in result:
                raise ValueError(f"{rel}: duplicate {key!r} in frontmatter")
            if value in {">", ">-", "|", "|-"} or not value:
                value, index = block_value(lines, index + 1)
            else:
                index += 1
            if len(value) >= 2 and value[0] in "\"'" and value[-1] == value[0]:
                value = value[1:-1]
            result[key] = value
            continue
        index += 1
    return result


def load_frontmatter(lines: list[str], rel: str) -> dict[str, Any]:
    if yaml is not None:
        try:
            data = yaml.safe_load("\n".join(lines))
        except yaml.YAMLError as exc:
            raise ValueError(f"{rel}: invalid YAML frontmatter: {exc}") from exc
        if data is None:
            return {}
        if not isinstance(data, dict):
            raise ValueError(f"{rel}: frontmatter must be a YAML mapping")
        return data
    return minimal_frontmatter(lines, rel)


def main() -> int:
    try:
        catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read catalog.json: {exc}", file=sys.stderr)
        return 1

    skills = [skill for skill in catalog.get("skills", []) if skill.get("status") == "active"]
    parser = "PyYAML" if yaml is not None else "minimal parser (PyYAML not installed)"
    errors: list[str] = []
    for skill in skills:
        rel = skill["path"]
        skill_file = ROOT / rel / "SKILL.md"
        if not skill_file.is_file():
            errors.append(f"{rel}: SKILL.md is missing")
            continue
        try:
            lines = split_frontmatter(skill_file.read_text(encoding="utf-8"), rel)
            data = load_frontmatter(lines, rel)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        name = data.get("name")
        description = data.get("description")
        if not isinstance(name, str) or not name.strip():
            errors.append(f"{rel}: frontmatter name is missing")
        elif not NAME_RE.fullmatch(name):
            errors.append(f"{rel}: name is not kebab-case: {name}")
        elif name != skill["name"]:
            errors.append(f"{rel}: name {name!r} does not match catalog name {skill['name']!r}")
        if not isinstance(description, str) or not description.strip():
            errors.append(f"{rel}: frontmatter description is missing or empty")

    if errors:
        print(f"skill validation failed ({parser}):", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"skill validation passed: {len(skills)} active skills ({parser})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
