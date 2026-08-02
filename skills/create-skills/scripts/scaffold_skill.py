#!/usr/bin/env python3
"""Create a safe Agent Skill base directory without overwriting existing files."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
RESOURCE_NAMES = {"assets", "references", "scripts"}


def parse_resources(value: str) -> list[str]:
    if not value:
        return []
    resources = [item.strip() for item in value.split(",") if item.strip()]
    invalid = sorted(set(resources) - RESOURCE_NAMES)
    if invalid:
        raise argparse.ArgumentTypeError(
            f"unsupported resources: {', '.join(invalid)}; "
            f"choose from {', '.join(sorted(RESOURCE_NAMES))}"
        )
    return list(dict.fromkeys(resources))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a skill base directory. Existing targets are never overwritten."
    )
    parser.add_argument("name", help="lowercase hyphen-case skill name")
    parser.add_argument("--path", required=True, help="existing parent directory")
    parser.add_argument(
        "--description",
        required=True,
        help="what the skill does and when it should be used",
    )
    parser.add_argument("--title", help="heading shown in SKILL.md")
    parser.add_argument(
        "--resources",
        default=[],
        type=parse_resources,
        help="comma-separated subset of assets,references,scripts",
    )
    args = parser.parse_args()

    if not NAME_PATTERN.fullmatch(args.name) or len(args.name) > 64:
        parser.error("name must be 1-64 lowercase letters, digits, or hyphen-separated words")
    if not args.description.strip() or len(args.description) > 1024:
        parser.error("description must contain 1-1024 characters")

    parent = Path(args.path).expanduser().resolve()
    if not parent.is_dir():
        parser.error(f"parent directory does not exist: {parent}")

    target = parent / args.name
    if target.exists():
        parser.error(f"target already exists; update it in place instead: {target}")

    title = args.title.strip() if args.title else args.name.replace("-", " ").title()
    if not title or "\n" in title or "\r" in title:
        parser.error("title must be a non-empty single line")

    description = args.description.strip()
    short_description = f"{title} 작업을 일관되고 안전하게 수행"
    if len(short_description) < 25:
        short_description += "하도록 안내"
    if len(short_description) > 64:
        short_description = short_description[:61].rstrip() + "..."

    target.mkdir()
    for resource in args.resources:
        (target / resource).mkdir()
    (target / "agents").mkdir()

    skill_text = (
        "---\n"
        f"name: {args.name}\n"
        f"description: {json.dumps(description, ensure_ascii=False)}\n"
        "---\n\n"
        f"# {title}\n\n"
        "TODO: 품질 기준, 핵심 워크플로와 확인 가능한 완료 조건을 작성한다.\n"
    )
    (target / "SKILL.md").write_text(skill_text, encoding="utf-8")
    openai_yaml = (
        "interface:\n"
        f"  display_name: {json.dumps(title, ensure_ascii=False)}\n"
        f"  short_description: {json.dumps(short_description, ensure_ascii=False)}\n"
        f"  default_prompt: {json.dumps(f'${args.name} 스킬을 사용해 이 작업을 수행하고 결과를 검증해줘.', ensure_ascii=False)}\n"
    )
    (target / "agents" / "openai.yaml").write_text(openai_yaml, encoding="utf-8")
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
