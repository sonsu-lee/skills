#!/usr/bin/env python3
"""Validate the installable skill catalog and its public documentation."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment setup failure
    raise SystemExit("PyYAML이 필요합니다: python3 -m pip install pyyaml") from exc


ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"
README = ROOT / "README.md"
INTERNAL_SKILL_DIRS = {"develop-change"}
DEPRECATED_SKILLS = {"write-prd", "write-domain-docs", "write-adr"}
NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FRONTMATTER_PATTERN = re.compile(r"\A---\n(.*?)\n---(?:\n|\Z)", re.DOTALL)
MARKDOWN_LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def load_yaml(path: Path, errors: list[str]) -> dict:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        errors.append(f"{path.relative_to(ROOT)}: YAML을 읽을 수 없습니다: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{path.relative_to(ROOT)}: YAML 루트는 mapping이어야 합니다.")
        return {}
    return value


def load_frontmatter(path: Path, errors: list[str]) -> tuple[dict, str]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"{path.relative_to(ROOT)}: 파일을 읽을 수 없습니다: {exc}")
        return {}, ""
    match = FRONTMATTER_PATTERN.match(text)
    if not match:
        errors.append(f"{path.relative_to(ROOT)}: YAML frontmatter가 없습니다.")
        return {}, text
    try:
        value = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        errors.append(f"{path.relative_to(ROOT)}: frontmatter가 올바르지 않습니다: {exc}")
        return {}, text
    if not isinstance(value, dict):
        errors.append(f"{path.relative_to(ROOT)}: frontmatter는 mapping이어야 합니다.")
        return {}, text
    return value, text


def check_relative_links(skill_dir: Path, text: str, errors: list[str]) -> None:
    for raw_target in MARKDOWN_LINK_PATTERN.findall(text):
        raw_target = raw_target.strip()
        if raw_target.startswith("<") and raw_target.endswith(">"):
            target = raw_target[1:-1]
            if "/" not in target and "." not in target:
                continue
        else:
            target = raw_target.split(maxsplit=1)[0]
        if not target or target.startswith(("#", "http://", "https://", "mailto:")):
            continue
        target = unquote(target.split("#", 1)[0].split("?", 1)[0])
        if target and not (skill_dir / target).resolve().exists():
            errors.append(
                f"{skill_dir.relative_to(ROOT)}/SKILL.md: 존재하지 않는 상대 링크: {raw_target}"
            )


def validate_skill(skill_dir: Path, readme_text: str, errors: list[str]) -> None:
    skill_file = skill_dir / "SKILL.md"
    frontmatter, skill_text = load_frontmatter(skill_file, errors)
    name = frontmatter.get("name")
    description = frontmatter.get("description")

    if set(frontmatter) != {"name", "description"}:
        errors.append(
            f"{skill_file.relative_to(ROOT)}: frontmatter key는 name과 description만 허용합니다."
        )
    if name != skill_dir.name:
        errors.append(
            f"{skill_file.relative_to(ROOT)}: name({name!r})과 디렉터리명이 다릅니다."
        )
    if not isinstance(name, str) or len(name) > 64 or not NAME_PATTERN.fullmatch(name):
        errors.append(f"{skill_file.relative_to(ROOT)}: name 형식이 올바르지 않습니다.")
    if not isinstance(description, str) or not description.strip():
        errors.append(f"{skill_file.relative_to(ROOT)}: description이 비어 있습니다.")

    metadata_path = skill_dir / "agents" / "openai.yaml"
    if not metadata_path.is_file():
        errors.append(f"{metadata_path.relative_to(ROOT)}: 호출 메타데이터가 없습니다.")
        metadata = {}
    else:
        metadata = load_yaml(metadata_path, errors)

    interface = metadata.get("interface")
    policy = metadata.get("policy")
    if not isinstance(interface, dict):
        errors.append(f"{metadata_path.relative_to(ROOT)}: interface mapping이 필요합니다.")
        interface = {}
    for key in ("display_name", "short_description", "default_prompt"):
        if not isinstance(interface.get(key), str) or not interface[key].strip():
            errors.append(f"{metadata_path.relative_to(ROOT)}: interface.{key}가 필요합니다.")
    default_prompt = interface.get("default_prompt", "")
    if isinstance(name, str) and isinstance(default_prompt, str) and f"${name}" not in default_prompt:
        errors.append(
            f"{metadata_path.relative_to(ROOT)}: default_prompt에 ${name} 명시 호출 예시가 필요합니다."
        )
    if not isinstance(policy, dict) or not isinstance(
        policy.get("allow_implicit_invocation"), bool
    ):
        errors.append(
            f"{metadata_path.relative_to(ROOT)}: policy.allow_implicit_invocation boolean이 필요합니다."
        )
    elif (name.startswith("to-") or name in DEPRECATED_SKILLS or name == "sonsu") and policy[
        "allow_implicit_invocation"
    ]:
        errors.append(f"{metadata_path.relative_to(ROOT)}: {name}은 explicit-only여야 합니다.")

    if name in DEPRECATED_SKILLS and "deprecated" not in str(description).lower():
        errors.append(f"{skill_file.relative_to(ROOT)}: deprecated 상태와 대체 경로를 설명해야 합니다.")

    readme_row = re.compile(rf"^\| `{re.escape(str(name))}` \|", re.MULTILINE)
    readme_row_count = len(readme_row.findall(readme_text))
    if readme_row_count != 1:
        errors.append(f"README.md: {name} 카탈로그 행은 정확히 하나여야 합니다.")

    if "TODO" in skill_text or "TODO" in metadata_path.read_text(encoding="utf-8"):
        errors.append(f"{skill_dir.relative_to(ROOT)}: 공개 스킬에 TODO가 남아 있습니다.")
    check_relative_links(skill_dir, skill_text, errors)


def main() -> int:
    errors: list[str] = []
    readme_text = README.read_text(encoding="utf-8")
    installable: list[Path] = []

    for child in sorted(path for path in SKILLS_DIR.iterdir() if path.is_dir()):
        if (child / "SKILL.md").is_file():
            installable.append(child)
        elif child.name not in INTERNAL_SKILL_DIRS:
            errors.append(
                f"{child.relative_to(ROOT)}: SKILL.md가 없으면 internal 허용 목록에 등록해야 합니다."
            )

    for skill_dir in installable:
        validate_skill(skill_dir, readme_text, errors)

    documented_names = set(re.findall(r"^\| `([a-z0-9-]+)` \|", readme_text, re.MULTILINE))
    installable_names = {skill_dir.name for skill_dir in installable}
    for stale_name in sorted(documented_names - installable_names):
        errors.append(f"README.md: 설치 대상이 아닌 카탈로그 행이 있습니다: {stale_name}")

    if errors:
        print(f"FAIL: 스킬 카탈로그 오류 {len(errors)}개")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"PASS: installable skill {len(installable)}개와 internal directory {len(INTERNAL_SKILL_DIRS)}개")
    return 0


if __name__ == "__main__":
    sys.exit(main())
