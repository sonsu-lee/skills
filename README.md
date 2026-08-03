# Sonsu Skills

Codex와 Claude Code에서 함께 사용하는 개인 Agent Skill 컬렉션입니다. 제품 문서 작성, 리서치, Git 작업, 스킬 제작과 개발자 이력서 작성을 지원합니다.

## 제공 스킬

| 스킬 | 설명 |
|---|---|
| `create-prd` | 인터뷰를 통해 제품 요구사항 문서를 작성합니다. |
| `maintain-domain-docs` | 용어, 상태, 전이와 비즈니스 규칙을 정리합니다. |
| `record-decision` | 제품·정책·아키텍처 결정을 근거와 함께 기록합니다. |
| `research` | 여러 원문을 교차 검증해 근거 중심으로 조사합니다. |
| `create-commit` | 변경을 의미 단위로 나누어 커밋합니다. |
| `create-pull-request` | 변경 범위와 저장소 규칙에 맞는 PR을 만듭니다. |
| `audit-git-change` | worktree, 커밋 또는 PR을 읽기 전용으로 검토합니다. |
| `create-skills` | Agent Skill을 만들거나 개선하고 검증합니다. |
| `write-developer-resume` | 개발자 이력서와 경력기술서를 작성하거나 진단합니다. |

## 사용법

플러그인을 연결한 뒤 스킬 이름과 작업을 함께 요청합니다.

```text
# Codex
$skills:create-prd로 이 아이디어의 PRD를 작성해줘.
$skills:research로 이 주제를 근거 중심으로 조사해줘.

# Claude Code
/skills:create-commit 현재 변경을 의미 단위로 커밋해줘.
/skills:audit-git-change 현재 worktree를 검토해줘.
```

각 스킬의 자세한 동작과 옵션은 `skills/<skill-name>/SKILL.md`에서 확인할 수 있습니다.

## 로컬 확인

Claude Code에서는 저장소 루트에서 플러그인을 직접 불러오고 manifest를 검증할 수 있습니다.

```bash
claude --plugin-dir .
claude plugin validate . --strict
```

## Research 공급자 설정 (선택)

`research`는 기본 검색 도구만으로 사용할 수 있습니다. Exa 또는 Perplexity를 사용하려면 아래 선언을 유지하고 대응하는 환경변수를 설정합니다.

<!-- research-provider-opt-in:v1:start -->
```yaml
providers:
  exa:
    env: EXA_API_KEY
  perplexity:
    env: PERPLEXITY_API_KEY
```
<!-- research-provider-opt-in:v1:end -->

API 키 값은 출력하거나 저장소에 커밋하지 마세요.

## 저장소 구조

```text
skills/          # 스킬 본문, 참고 자료, 템플릿과 평가 fixture
evals/           # 스킬 간 회귀 평가
docs/            # 설계 및 연구 문서
.codex-plugin/   # Codex manifest
.claude-plugin/  # Claude Code manifest
```
