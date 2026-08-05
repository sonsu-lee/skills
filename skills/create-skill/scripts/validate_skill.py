#!/usr/bin/env python3
"""Validate a newly created Codex-oriented Agent Skill using only the Python standard library."""

from __future__ import annotations

import argparse
import ast
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import unquote

NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LINK_PATTERN = re.compile(r"!?\[[^\]]*]\(([^)]+)\)")
TOP_LEVEL_KEY = re.compile(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$")
CODEX_KEYS = {"name", "description"}
PORTABLE_KEYS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}
FORBIDDEN_ROOT_DOCS = {
    "changelog.md",
    "installation_guide.md",
    "quick_reference.md",
    "readme.md",
}
PLACEHOLDERS = ("TODO", "TBD", "[PLACEHOLDER]", "<skill-name>")


@dataclass
class Finding:
    level: str
    path: str
    message: str


def add(findings: list[Finding], level: str, path: Path, message: str) -> None:
    findings.append(Finding(level, str(path), message))


def split_frontmatter(text: str) -> tuple[str, str] | None:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    try:
        end = next(index for index, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration:
        return None
    return "\n".join(lines[1:end]), "\n".join(lines[end + 1 :]).strip()


def without_fenced_code(text: str) -> str:
    """Return Markdown with fenced code blocks removed."""
    kept: list[str] = []
    fence: str | None = None
    for line in text.splitlines():
        stripped = line.lstrip()
        marker = "```" if stripped.startswith("```") else "~~~" if stripped.startswith("~~~") else None
        if marker:
            if fence is None:
                fence = marker
            elif marker == fence:
                fence = None
            continue
        if fence is None:
            kept.append(line)
    return "\n".join(kept)


def parse_top_level(frontmatter: str) -> tuple[dict[str, str], list[str]]:
    values: dict[str, str] = {}
    duplicates: list[str] = []
    lines = frontmatter.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        if line[:1].isspace() or not line.strip():
            index += 1
            continue
        match = TOP_LEVEL_KEY.match(line)
        if not match:
            index += 1
            continue
        key, value = match.groups()
        if key in values:
            duplicates.append(key)
        if value.strip() in {">", ">-", "|", "|-"}:
            block: list[str] = []
            index += 1
            while index < len(lines) and (lines[index][:1].isspace() or not lines[index].strip()):
                block.append(lines[index].strip())
                index += 1
            values[key] = " ".join(part for part in block if part)
            continue
        values[key] = value.strip().strip("\"'")
        index += 1
    return values, duplicates


def validate_markdown_links(root: Path, findings: list[Finding]) -> None:
    for source in root.rglob("*.md"):
        text = without_fenced_code(source.read_text(encoding="utf-8"))
        for raw_target in LINK_PATTERN.findall(text):
            target = raw_target.strip()
            if target.startswith("<") and target.endswith(">"):
                target = target[1:-1]
            target = target.split("#", 1)[0].strip()
            if not target or re.match(r"^[a-z][a-z0-9+.-]*:", target, re.IGNORECASE):
                continue
            if any(token in target for token in ("<", ">", "$")):
                continue
            target = unquote(target.split(" ", 1)[0])
            if target.startswith(("/", "~")):
                add(findings, "error", source, f"local link must be relative: {raw_target}")
                continue
            resolved = (source.parent / target).resolve()
            try:
                resolved.relative_to(root)
            except ValueError:
                add(findings, "error", source, f"link escapes the skill directory: {raw_target}")
                continue
            if not resolved.exists():
                add(findings, "error", source, f"missing linked path: {raw_target}")


def validate_python(root: Path, findings: list[Finding]) -> None:
    for script in root.rglob("*.py"):
        try:
            ast.parse(script.read_text(encoding="utf-8"), filename=str(script))
        except (SyntaxError, UnicodeDecodeError) as exc:
            add(findings, "error", script, f"Python syntax error: {exc}")
        if script.parent.name == "scripts":
            first_line = script.read_text(encoding="utf-8").splitlines()[:1]
            if not first_line or not first_line[0].startswith("#!"):
                add(findings, "warning", script, "script has no shebang")


def validate_openai_yaml(root: Path, skill_name: str, findings: list[Finding]) -> None:
    config = root / "agents" / "openai.yaml"
    if not config.exists():
        add(findings, "warning", config, "agents/openai.yaml is recommended for Codex UI metadata")
        return
    text = config.read_text(encoding="utf-8")
    field_values: dict[str, str] = {}
    for field in ("display_name", "short_description", "default_prompt"):
        match = re.search(
            rf"^\s+{field}:\s*(?P<quote>[\"'])(?P<value>.+)(?P=quote)\s*$",
            text,
            re.MULTILINE,
        )
        if not match:
            add(findings, "error", config, f"missing or unquoted interface.{field}")
            continue
        raw_value = match.group("value")
        if match.group("quote") == '"':
            try:
                field_values[field] = json.loads(f'"{raw_value}"')
            except json.JSONDecodeError:
                add(findings, "error", config, f"invalid quoted interface.{field}")
        else:
            field_values[field] = raw_value.replace("''", "'")
    short_description = field_values.get("short_description", "")
    if short_description and not 25 <= len(short_description) <= 64:
        add(findings, "error", config, "interface.short_description must be 25-64 characters")
    if f"${skill_name}" not in field_values.get("default_prompt", ""):
        add(findings, "error", config, f"default_prompt must mention ${skill_name}")


def validate_skill(root: Path, profile: str) -> list[Finding]:
    findings: list[Finding] = []
    skill_file = root / "SKILL.md"
    if not root.is_dir():
        add(findings, "error", root, "skill directory does not exist")
        return findings
    if not skill_file.is_file():
        add(findings, "error", skill_file, "SKILL.md is required")
        return findings

    text = skill_file.read_text(encoding="utf-8")
    parsed = split_frontmatter(text)
    if parsed is None:
        add(findings, "error", skill_file, "frontmatter must start and end with ---")
        return findings
    frontmatter, body = parsed
    values, duplicates = parse_top_level(frontmatter)
    allowed = CODEX_KEYS if profile == "codex" else PORTABLE_KEYS

    for duplicate in duplicates:
        add(findings, "error", skill_file, f"duplicate frontmatter field: {duplicate}")
    for required in ("name", "description"):
        if not values.get(required):
            add(findings, "error", skill_file, f"missing frontmatter field: {required}")
    for unexpected in sorted(set(values) - allowed):
        add(findings, "error", skill_file, f"unsupported {profile} frontmatter field: {unexpected}")

    name = values.get("name", "")
    if name:
        if not NAME_PATTERN.fullmatch(name) or len(name) > 64:
            add(findings, "error", skill_file, "name must be 1-64 lowercase hyphen-case characters")
        if name != root.name:
            add(findings, "error", skill_file, f"name must match directory name: {root.name}")

    description = values.get("description", "")
    if len(description) > 1024:
        add(findings, "error", skill_file, "description exceeds 1024 characters")
    if not body:
        add(findings, "error", skill_file, "skill body is empty")
    prose = without_fenced_code(text)
    for marker in PLACEHOLDERS:
        if marker in prose:
            add(findings, "error", skill_file, f"placeholder remains: {marker}")

    line_count = len(text.splitlines())
    if line_count > 500:
        add(findings, "warning", skill_file, f"SKILL.md has {line_count} lines; use progressive disclosure")

    for child in root.iterdir():
        if child.is_file() and child.name.casefold() in FORBIDDEN_ROOT_DOCS:
            add(findings, "error", child, "extraneous root documentation is not part of a skill bundle")

    references = root / "references"
    if references.is_dir():
        for item in references.rglob("*"):
            if item.is_file() and len(item.relative_to(references).parts) > 1:
                add(findings, "warning", item, "keep references one level deep when practical")

    for item in root.rglob("*"):
        if not item.is_symlink():
            continue
        try:
            item.resolve().relative_to(root)
        except ValueError:
            add(findings, "error", item, "symlink points outside the skill directory")

    validate_markdown_links(root, findings)
    validate_python(root, findings)
    validate_openai_yaml(root, name or root.name, findings)
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_directory")
    parser.add_argument(
        "--profile",
        choices=("codex", "portable"),
        default="codex",
        help="frontmatter compatibility profile",
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable output")
    args = parser.parse_args()

    root = Path(args.skill_directory).expanduser().resolve()
    findings = validate_skill(root, args.profile)
    errors = [finding for finding in findings if finding.level == "error"]
    warnings = [finding for finding in findings if finding.level == "warning"]

    if args.json:
        print(
            json.dumps(
                {
                    "valid": not errors,
                    "errors": [asdict(item) for item in errors],
                    "warnings": [asdict(item) for item in warnings],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        for finding in findings:
            print(f"{finding.level.upper()}: {finding.path}: {finding.message}")
        print(f"{'PASS' if not errors else 'FAIL'}: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
