#!/usr/bin/env python3
"""Validate a Codex-oriented Agent Skill; strict metadata parsing uses PyYAML."""

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


def count_yaml_mapping_key(lines: list[str], key: str) -> int:
    """Count block- or flow-style mapping keys while ignoring quoted scalar text."""
    escaped_key = re.escape(key)
    key_token = rf"(?:{escaped_key}|\"{escaped_key}\"|'{escaped_key}')\s*:"
    block_key = re.compile(rf"^\s*(?:-\s*)?{key_token}")
    flow_key = re.compile(rf"\s*{key_token}")
    count = 0

    for line in lines:
        if block_key.match(line):
            count += 1

        quote: str | None = None
        escaped = False
        index = 0
        while index < len(line):
            character = line[index]
            if quote == '"':
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == quote:
                    quote = None
            elif quote == "'":
                if character == quote:
                    if index + 1 < len(line) and line[index + 1] == quote:
                        index += 1
                    else:
                        quote = None
            elif character in {'"', "'"}:
                quote = character
            elif character == "#":
                break
            elif character in "{[,":
                if flow_key.match(line, index + 1):
                    count += 1
            index += 1

    return count


def has_quoted_yaml_mapping_key(lines: list[str]) -> bool:
    """Detect quoted mapping keys without rejecting quoted scalar values."""
    double_quoted = r'"(?:\\.|[^"\\])*"'
    single_quoted = r"'(?:''|[^'])*'"
    quoted_key = rf"(?:{double_quoted}|{single_quoted})\s*:"
    block_key = re.compile(rf"^\s*(?:[-?]\s*)?{quoted_key}")
    flow_key = re.compile(rf"\s*{quoted_key}")

    for line in lines:
        if block_key.match(line):
            return True

        quote: str | None = None
        escaped = False
        index = 0
        while index < len(line):
            character = line[index]
            if quote == '"':
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == quote:
                    quote = None
            elif quote == "'":
                if character == quote:
                    if index + 1 < len(line) and line[index + 1] == quote:
                        index += 1
                    else:
                        quote = None
            elif character in {'"', "'"}:
                quote = character
            elif character == "#":
                break
            elif character in "{[,":
                if flow_key.match(line, index + 1):
                    return True
            index += 1

    return False


def unquoted_yaml_surface(line: str) -> str:
    """Mask quoted scalar text and comments, preserving YAML surface punctuation."""
    surface: list[str] = []
    quote: str | None = None
    escaped = False
    index = 0
    while index < len(line):
        character = line[index]
        if quote == '"':
            surface.append(" ")
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                quote = None
        elif quote == "'":
            surface.append(" ")
            if character == quote:
                if index + 1 < len(line) and line[index + 1] == quote:
                    surface.append(" ")
                    index += 1
                else:
                    quote = None
        elif character in {'"', "'"}:
            quote = character
            surface.append(" ")
        elif character == "#" and (index == 0 or line[index - 1].isspace()):
            break
        else:
            surface.append(character)
        index += 1
    return "".join(surface)


def has_disallowed_strict_yaml_surface(lines: list[str]) -> bool:
    """Reject advanced key and flow syntax outside normal quoted scalar values."""
    for line in lines:
        surface = unquoted_yaml_surface(line)
        if any(character in surface for character in "{}[]"):
            return True
        if any(character in surface for character in "!&*"):
            return True
        if re.search(r"(?:^|\s)(?:-\s*)?<<\s*:", surface):
            return True
        if re.match(r"^\s*(?:-\s*)?\?(?:\s|$)", surface):
            return True
    return False


def validate_strict_yaml_document(
    text: str, config: Path, findings: list[Finding]
) -> bool:
    """Parse the complete metadata document with the parser used by OpenAI tooling."""
    try:
        import yaml  # type: ignore[import-not-found]
    except ImportError:
        add(
            findings,
            "error",
            config,
            "strict openai.yaml validation requires PyYAML",
        )
        return False

    try:
        document = yaml.safe_load(text)
    except yaml.YAMLError:
        add(findings, "error", config, "invalid openai.yaml syntax")
        return False

    if not isinstance(document, dict):
        add(findings, "error", config, "openai.yaml must be a mapping")
        return False
    return True


def top_level_yaml_block(
    lines: list[str], key: str
) -> tuple[list[tuple[int, str]], int] | None:
    """Return one exact top-level block and its direct-child indentation."""
    headers = [
        index
        for index, line in enumerate(lines)
        if re.match(rf"^{re.escape(key)}\s*:", line)
    ]
    if (
        len(headers) != 1
        or lines[headers[0]].strip() != f"{key}:"
        or count_yaml_mapping_key(lines, key) != 1
    ):
        return None

    block: list[tuple[int, str]] = []
    for index, line in enumerate(lines[headers[0] + 1 :], headers[0] + 1):
        if line and not line[:1].isspace() and not line.lstrip().startswith("#"):
            break
        block.append((index, line))

    content_indents = [
        len(line) - len(line.lstrip(" "))
        for _, line in block
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not content_indents:
        return None
    return block, min(content_indents)


def validate_openai_yaml(
    root: Path,
    skill_name: str,
    findings: list[Finding],
    require_explicit_invocation_policy: bool = False,
) -> None:
    config = root / "agents" / "openai.yaml"
    if not config.exists():
        add(findings, "warning", config, "agents/openai.yaml is recommended for Codex UI metadata")
        if require_explicit_invocation_policy:
            add(
                findings,
                "error",
                config,
                "policy.allow_implicit_invocation must be explicitly set to true or false",
            )
        return
    text = config.read_text(encoding="utf-8")
    lines = text.splitlines()
    if require_explicit_invocation_policy and not validate_strict_yaml_document(
        text, config, findings
    ):
        return
    if require_explicit_invocation_policy and has_quoted_yaml_mapping_key(lines):
        add(
            findings,
            "error",
            config,
            "strict openai.yaml validation does not allow quoted mapping keys",
        )
    if require_explicit_invocation_policy and has_disallowed_strict_yaml_surface(lines):
        add(
            findings,
            "error",
            config,
            "strict openai.yaml validation allows only plain block mapping keys; "
            "tags, anchors, aliases, explicit or merge keys, and flow collections "
            "are not allowed",
        )
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

    if require_explicit_invocation_policy:
        interface_block = top_level_yaml_block(lines, "interface")
        valid_interface = interface_block is not None
        if interface_block is not None:
            block, direct_indent = interface_block
            for field in ("display_name", "short_description", "default_prompt"):
                direct_fields = [
                    line
                    for _, line in block
                    if re.fullmatch(
                        rf" +{field}\s*:\s*(?P<quote>[\"'])(?P<value>.+)"
                        rf"(?P=quote)\s*",
                        line,
                    )
                ]
                valid_interface = valid_interface and (
                    len(direct_fields) == 1
                    and len(direct_fields[0]) - len(direct_fields[0].lstrip(" "))
                    == direct_indent
                    and count_yaml_mapping_key(lines, field) == 1
                )
        if not valid_interface:
            add(
                findings,
                "error",
                config,
                "interface must be exactly one top-level block whose display_name, "
                "short_description, and default_prompt each appear exactly once as "
                "quoted direct children without nested, flow-style, or quoted-key shadows",
            )

    short_description = field_values.get("short_description", "")
    if short_description and not 25 <= len(short_description) <= 64:
        add(findings, "error", config, "interface.short_description must be 25-64 characters")
    if f"${skill_name}" not in field_values.get("default_prompt", ""):
        add(findings, "error", config, f"default_prompt must mention ${skill_name}")

    if require_explicit_invocation_policy:
        policy_block = top_level_yaml_block(lines, "policy")
        valid_policy = False
        if policy_block is not None:
            block, direct_indent = policy_block
            policy_keys = [
                (index, line)
                for index, line in block
                if re.fullmatch(
                    r" +allow_implicit_invocation\s*:\s*(?:true|false)\s*",
                    line,
                )
            ]

            valid_policy = (
                len(policy_keys) == 1
                and len(policy_keys[0][1]) - len(policy_keys[0][1].lstrip(" "))
                == direct_indent
                and count_yaml_mapping_key(lines, "allow_implicit_invocation") == 1
            )
        if not valid_policy:
            add(
                findings,
                "error",
                config,
                "policy.allow_implicit_invocation must appear exactly once as a direct "
                "child of top-level policy and use an unquoted true or false",
            )


def validate_skill(
    root: Path,
    profile: str,
    require_explicit_invocation_policy: bool = False,
) -> list[Finding]:
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
    validate_openai_yaml(
        root,
        name or root.name,
        findings,
        require_explicit_invocation_policy,
    )
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
    parser.add_argument(
        "--require-explicit-invocation-policy",
        action="store_true",
        help="require policy.allow_implicit_invocation to be an explicit boolean",
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable output")
    args = parser.parse_args()

    root = Path(args.skill_directory).expanduser().resolve()
    findings = validate_skill(
        root,
        args.profile,
        args.require_explicit_invocation_policy,
    )
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
