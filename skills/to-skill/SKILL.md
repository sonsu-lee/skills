---
name: to-skill
description: Use when creating or revising a portable Agent Skill, normalizing Codex and Claude Code copies into one canonical source, or preparing requested host metadata or packaging.
---

# To Skill

하나의 portable Agent Skill 원본을 작성·수정하고 Codex와 Claude Code의 노출을 안전하게 정규화한다. 호스트별 확장은 공용 원본과 분리한다.

## 워크플로우

1. 저장소 지침과 기존 skill, eval, discovery 경로를 먼저 읽는다.
2. 요청을 새 작성, 기존 수정, 다중 host 사본 정규화, host preparation으로 분류한다.
3. 실제 파일, symlink 대상과 내용을 변경 전에 조사한다. 불명확한 경로나 충돌을 추측하지 않는다.
4. 새 작성이나 수정이면 책임과 비책임을 한 문장으로 정하고 positive, near-miss negative와 관찰 가능한 output eval을 먼저 기록한다.
5. portable 원본에는 필요한 `SKILL.md`, `references/`, `scripts/`, `assets/`만 둔다. 본문은 간결한 명령형으로 쓰고 reference chain은 한 단계로 유지한다.
6. 아래 canonical 정책과 정규화 안전 규칙을 적용한다.
7. 요청된 host preparation만 수행하고 portable 원본과 제품별 metadata를 분리한다.
8. 구조 validator, 관련 eval과 저장소 검증을 실행하고 변경, no-op, 충돌과 남은 작업을 구분해 보고한다.

새 스킬 작성, 책임 경계 또는 평가 tradeoff를 판단할 필요가 있을 때만 [작성 원칙](references/authoring-principles.md)을 읽는다.

`agents/openai.yaml`, Codex invocation, MCP, plugin 또는 packaging이 요청될 때만 [Codex 참고](references/codex.md)를 읽는다.

Claude Code discovery, symlink·version, host-specific frontmatter, plugin 또는 packaging이 요청될 때만 [Claude Code 참고](references/claude-code.md)를 읽는다.

## Portable 계약

- 디렉터리명과 같은 kebab-case `name`을 사용한다.
- 공용 `SKILL.md` frontmatter에는 `name`과 `description`만 둔다.
- `description`에 실제 사용자의 trigger 표현과 책임 경계를 구체적으로 쓴다.
- 상세 규격은 조건부 reference로, 반복되는 결정론적 작업은 검증된 script로 분리한다.
- 별도 README, 작성 과정 문서, 사용하지 않는 resource와 호스트 전용 필드를 추가하지 않는다.

## Canonical 배치

일반 소비 프로젝트에서는 다음 배치를 기본으로 사용한다. Codex는 canonical을 직접 사용하고 Claude Code에는 상대 symlink만 노출한다.

```text
.agents/skills/<skill-name>/
.claude/skills/<skill-name> -> ../../.agents/skills/<skill-name>
```

**배포 저장소 예외:** 저장소 지침이 배포 원본 경로를 지정하면 그 규칙을 우선한다. 이 distribution repository에서는 `skills/<skill-name>`만 원본으로 두고 `.agents/skills` 복제본이나 `.claude/skills` symlink를 만들지 않는다.

## 정규화 안전 규칙

- canonical이 있고 Claude entry가 없을 때만 새 상대 symlink를 만든다.
- Claude entry가 이미 올바른 상대 symlink면 아무것도 바꾸지 않는다.
- canonical과 Claude에 있는 두 물리 사본이 완전히 같아도 사용자가 정규화를 명시적으로 요청한 경우에만 교체 계획을 보여준다. 확인을 받은 뒤에만 Claude 사본을 상대 symlink로 교체한다.
- 두 물리 사본의 내용이 다르면 충돌을 보고하고 중단한다. 자동 병합, 덮어쓰기, 승자 선택이나 backup 이동을 하지 않는다.
- Claude 물리 사본만 있으면 canonical 이동 경로와 symlink 변경을 보여준다. 확인을 받은 뒤에만 사본을 canonical로 이동하고 상대 symlink를 만든다.
- 잘못되거나 깨진 symlink, 또는 위 분기로 안전하게 식별되지 않은 실제 디렉터리가 Claude entry를 점유하면 중단한다. 자동 삭제나 교체를 하지 않는다.
- 대상 Claude Code가 directory symlink를 지원하지 않으면 copy fallback을 만들지 않는다. 호환성 문제와 확인한 버전을 보고한다.

## Host preparation

- Codex metadata는 같은 canonical 디렉터리의 `agents/openai.yaml`에 둔다. 요청되지 않은 invocation policy, MCP dependency와 UI 값을 추가하지 않는다.
- Claude Code 전용 frontmatter가 꼭 필요하면 공용 원본에 섞지 않는다. 기본 흐름에서 파생 copy를 자동 생성하지 말고 별도 host-specific 배포 작업으로 분리해 보고한다.
- plugin이나 marketplace는 사용자가 명시적으로 요청한 경우에만 대상 host의 현재 공식 계약과 내장 creator로 최소 구성한다.
- publisher, version, marketplace, 인증 정보와 선택적 metadata를 추측하거나 placeholder로 만들지 않는다.

## 중단 조건

- 기존 스킬과 책임이 같으면 새 스킬을 만들지 말고 기존 canonical을 수정한다.
- 요청이 여러 책임으로 갈리거나 canonical을 결정할 수 없으면 필요한 선택을 확인한다.
- 내용 충돌, 잘못된 link, 지원되지 않는 symlink 또는 필수 배포 값 누락을 자동 우회하지 않는다.
- 검증이 실패하거나 eval이 기대 동작을 입증하지 못하면 완료로 보고하지 않는다.
