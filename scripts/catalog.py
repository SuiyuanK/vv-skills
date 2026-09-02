#!/usr/bin/env python3
"""Validate the vv-skills catalog and render the generated README index."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = ROOT / "catalog.json"
README_PATH = ROOT / "README.md"
START_MARKER = "<!-- catalog:start -->"
END_MARKER = "<!-- catalog:end -->"
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
ALLOWED_KINDS = {"self", "third-party"}
ALLOWED_STATUSES = {"active", "archived"}
ALLOWED_PLATFORMS = {
    "arch-linux",
    "cinnamon",
    "cross-platform",
    "gnome",
    "linux",
    "linux-x86_64",
    "ubuntu-linux",
    "wayland",
    "windows",
}
KIND_LABELS = {"self": "自研", "third-party": "第三方"}
PLATFORM_LABELS = {
    "arch-linux": "Arch/CachyOS",
    "cinnamon": "Cinnamon/Nemo",
    "cross-platform": "跨平台",
    "gnome": "GNOME",
    "linux": "Linux",
    "linux-x86_64": "Linux x86_64",
    "ubuntu-linux": "Ubuntu/Linux",
    "wayland": "Wayland",
    "windows": "Windows",
}


class CatalogError(RuntimeError):
    """Raised when catalog invariants are violated."""


def load_catalog() -> dict[str, Any]:
    try:
        data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogError(f"cannot read {CATALOG_PATH.name}: {exc}") from exc
    if not isinstance(data, dict):
        raise CatalogError("catalog root must be an object")
    return data


def require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CatalogError(f"{label} must be a non-empty string")
    return value


def frontmatter_name(skill_file: Path) -> str | None:
    lines = skill_file.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        return None
    for line in lines[1:]:
        if line == "---":
            break
        if line.startswith("name:"):
            return line.partition(":")[2].strip().strip('"\'')
    return None


def validate_catalog(data: dict[str, Any]) -> list[dict[str, Any]]:
    if data.get("schema_version") != 1:
        raise CatalogError("schema_version must be 1")

    categories = data.get("categories")
    skills = data.get("skills")
    if not isinstance(categories, list) or not categories:
        raise CatalogError("categories must be a non-empty array")
    if not isinstance(skills, list) or not skills:
        raise CatalogError("skills must be a non-empty array")

    category_ids: set[str] = set()
    category_names: set[str] = set()
    category_orders: set[int] = set()
    for index, category in enumerate(categories):
        label = f"categories[{index}]"
        if not isinstance(category, dict):
            raise CatalogError(f"{label} must be an object")
        category_id = require_string(category.get("id"), f"{label}.id")
        category_name = require_string(category.get("name"), f"{label}.name")
        order = category.get("order")
        if not NAME_RE.fullmatch(category_id):
            raise CatalogError(f"{label}.id is invalid: {category_id}")
        if not isinstance(order, int) or order < 0:
            raise CatalogError(f"{label}.order must be a non-negative integer")
        if category_id in category_ids or category_name in category_names or order in category_orders:
            raise CatalogError(f"duplicate category id, name, or order at {label}")
        category_ids.add(category_id)
        category_names.add(category_name)
        category_orders.add(order)

    names: set[str] = set()
    paths: set[str] = set()
    active_paths: set[str] = set()
    normalized: list[dict[str, Any]] = []

    for index, raw_skill in enumerate(skills):
        label = f"skills[{index}]"
        if not isinstance(raw_skill, dict):
            raise CatalogError(f"{label} must be an object")
        skill = dict(raw_skill)
        name = require_string(skill.get("name"), f"{label}.name")
        path = require_string(skill.get("path"), f"{label}.path")
        kind = require_string(skill.get("kind"), f"{label}.kind")
        category = require_string(skill.get("category"), f"{label}.category")
        summary = require_string(skill.get("summary"), f"{label}.summary")
        status = require_string(skill.get("status"), f"{label}.status")
        platforms = skill.get("platforms")
        dependencies = skill.get("dependencies")

        if not NAME_RE.fullmatch(name):
            raise CatalogError(f"{label}.name is invalid: {name}")
        if name in names or path in paths:
            raise CatalogError(f"duplicate skill name or path: {name}")
        if kind not in ALLOWED_KINDS:
            raise CatalogError(f"{label}.kind must be one of {sorted(ALLOWED_KINDS)}")
        if category not in category_ids:
            raise CatalogError(f"{label}.category is unknown: {category}")
        if status not in ALLOWED_STATUSES:
            raise CatalogError(f"{label}.status must be one of {sorted(ALLOWED_STATUSES)}")
        if "|" in summary or "\n" in summary:
            raise CatalogError(f"{label}.summary cannot contain a table delimiter or newline")
        if not isinstance(platforms, list) or not platforms or not all(isinstance(item, str) for item in platforms):
            raise CatalogError(f"{label}.platforms must be a non-empty string array")
        unknown_platforms = set(platforms) - ALLOWED_PLATFORMS
        if unknown_platforms:
            raise CatalogError(f"{label}.platforms contains unknown values: {sorted(unknown_platforms)}")
        if len(platforms) != len(set(platforms)):
            raise CatalogError(f"{label}.platforms contains duplicates")
        if not isinstance(dependencies, list) or not dependencies or not all(
            isinstance(item, str) and item.strip() and "|" not in item and "\n" not in item
            for item in dependencies
        ):
            raise CatalogError(f"{label}.dependencies must be a non-empty safe string array")

        if status == "active":
            if "/" in path or not NAME_RE.fullmatch(path):
                raise CatalogError(f"active skill {name} must use a valid top-level directory path")
            skill_file = ROOT / path / "SKILL.md"
            if not skill_file.is_file():
                raise CatalogError(f"active skill entrypoint is missing: {skill_file.relative_to(ROOT)}")
            actual_name = frontmatter_name(skill_file)
            if actual_name != name:
                raise CatalogError(f"frontmatter name mismatch for {path}: expected {name}, got {actual_name!r}")
            active_paths.add(path)
        elif not path.startswith("archive/"):
            raise CatalogError(f"archived skill {name} must live below archive/")

        upstream = skill.get("upstream")
        if kind == "third-party":
            if not isinstance(upstream, dict):
                raise CatalogError(f"{label}.upstream is required for third-party skills")
            repository = require_string(upstream.get("repository"), f"{label}.upstream.repository")
            branch = require_string(upstream.get("branch"), f"{label}.upstream.branch")
            baseline = require_string(upstream.get("baseline"), f"{label}.upstream.baseline")
            if not repository.startswith("https://"):
                raise CatalogError(f"{label}.upstream.repository must use https")
            if not NAME_RE.fullmatch(branch):
                raise CatalogError(f"{label}.upstream.branch is invalid: {branch}")
            if not COMMIT_RE.fullmatch(baseline):
                raise CatalogError(f"{label}.upstream.baseline must be a 40-character lowercase commit hash")
            version = upstream.get("version")
            if version is not None:
                require_string(version, f"{label}.upstream.version")
        elif upstream is not None:
            raise CatalogError(f"{label}.upstream is only allowed for third-party skills")

        supersedes = skill.get("supersedes", [])
        if not isinstance(supersedes, list) or not all(
            isinstance(item, str) and NAME_RE.fullmatch(item) for item in supersedes
        ):
            raise CatalogError(f"{label}.supersedes must be an array of valid skill names")
        if name in supersedes or len(supersedes) != len(set(supersedes)):
            raise CatalogError(f"{label}.supersedes contains an invalid or duplicate name")

        names.add(name)
        paths.add(path)
        normalized.append(skill)

    discovered = {
        child.name
        for child in ROOT.iterdir()
        if child.is_dir() and not child.name.startswith(".") and (child / "SKILL.md").is_file()
    }
    missing_from_catalog = discovered - active_paths
    missing_from_disk = active_paths - discovered
    if missing_from_catalog or missing_from_disk:
        raise CatalogError(
            "top-level active skill mismatch: "
            f"unlisted={sorted(missing_from_catalog)}, missing={sorted(missing_from_disk)}"
        )

    third_party_count = sum(skill["kind"] == "third-party" and skill["status"] == "active" for skill in normalized)
    if third_party_count != 3:
        raise CatalogError(f"expected exactly 3 active third-party skills, found {third_party_count}")

    return normalized


def render_block(data: dict[str, Any], skills: list[dict[str, Any]]) -> str:
    categories = sorted(data["categories"], key=lambda item: item["order"])
    active = [skill for skill in skills if skill["status"] == "active"]
    self_count = sum(skill["kind"] == "self" for skill in active)
    third_party_count = sum(skill["kind"] == "third-party" for skill in active)
    lines = [
        START_MARKER,
        "",
        f"当前收录 **{len(active)} 个 active skills**：**{self_count} 个自研**、**{third_party_count} 个第三方**。",
    ]

    for category in categories:
        members = sorted(
            (skill for skill in active if skill["category"] == category["id"]),
            key=lambda item: item["name"],
        )
        if not members:
            continue
        lines.extend(
            [
                "",
                f"### {category['name']}",
                "",
                "| Skill | 类型 | 平台 | 用途 | 依赖摘要 |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for skill in members:
            platforms = "、".join(PLATFORM_LABELS[item] for item in skill["platforms"])
            dependencies = "、".join(skill["dependencies"])
            lines.append(
                f"| [`{skill['name']}`](./{skill['path']}/SKILL.md) | "
                f"{KIND_LABELS[skill['kind']]} | {platforms} | {skill['summary']} | {dependencies} |"
            )

    lines.extend(["", END_MARKER])
    return "\n".join(lines)


def read_readme() -> str:
    try:
        return README_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        raise CatalogError(f"cannot read {README_PATH.name}: {exc}") from exc


def catalog_region(text: str) -> tuple[int, int]:
    if text.count(START_MARKER) != 1 or text.count(END_MARKER) != 1:
        raise CatalogError("README must contain exactly one catalog marker pair")
    start = text.index(START_MARKER)
    end = text.index(END_MARKER, start) + len(END_MARKER)
    return start, end


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="validate catalog and README without writing")
    mode.add_argument("--render", action="store_true", help="validate catalog and update README index")
    args = parser.parse_args()

    try:
        data = load_catalog()
        skills = validate_catalog(data)
        expected = render_block(data, skills)
        readme = read_readme()
        start, end = catalog_region(readme)

        if args.render:
            updated = readme[:start] + expected + readme[end:]
            README_PATH.write_text(updated, encoding="utf-8")
            print(f"rendered README catalog: {sum(skill['status'] == 'active' for skill in skills)} active skills")
            return 0

        current = readme[start:end]
        if current != expected:
            raise CatalogError("README catalog is stale; run: python scripts/catalog.py --render")
        print(f"catalog check passed: {sum(skill['status'] == 'active' for skill in skills)} active skills")
        return 0
    except CatalogError as exc:
        print(f"catalog error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
