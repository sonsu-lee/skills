# Sonsu Skills

Codex용 개인 Agent Skill 플러그인입니다. 제품 문서 작성, 리서치, Git 작업, 스킬 제작과 개발자 이력서 작성을 지원하며 Claude Code용 manifest도 함께 제공합니다.

## 제공 스킬

| 스킬 | 설명 |
|---|---|
| `create-prd` | 인터뷰를 통해 제품 요구사항 문서를 작성합니다. |
| `write-domain-docs` | 용어, 상태, 전이와 비즈니스 규칙을 정리합니다. |
| `write-adr` | 중요한 아키텍처·기술 결정을 ADR로 작성합니다. |
| `research` | 여러 원문을 교차 검증해 근거 중심으로 조사합니다. |
| `create-commit` | 변경을 의미 단위로 나누어 커밋합니다. |
| `create-pull-request` | 변경 범위와 저장소 규칙에 맞는 PR을 만듭니다. |
| `git-change-review` | worktree, 커밋 또는 PR을 읽기 전용으로 검토합니다. |
| `create-skills` | Agent Skill을 만들거나 개선하고 검증합니다. |
| `write-developer-resume` | 개발자 이력서와 경력기술서를 작성하거나 진단합니다. |

## 설치

사용할 범위와 설치 형태에 맞는 방법을 선택합니다.

| 목적 | 설치 방식 | 적용 범위 | Codex 호출 형식 |
|---|---|---|---|
| 현재 프로젝트에서만 사용 | 독립 스킬 설치 | 현재 프로젝트의 `.agents/skills/` | `$create-prd` |
| 모든 프로젝트에서 사용 | 독립 스킬 전역 설치 | 현재 사용자 | `$create-prd` |
| 플러그인 묶음과 네임스페이스 사용 | Codex 플러그인 설치 | 현재 사용자 | `$skills:create-prd` |

### 현재 프로젝트에 설치

대상 프로젝트 루트에서 다음 명령을 실행합니다. 설치할 스킬을 선택할 수 있으며 Codex는 프로젝트의 `.agents/skills/`에서 스킬을 읽습니다.

```bash
npx skills add sonsu-lee/skills --agent codex
```

이 방식은 해당 프로젝트에만 스킬을 적용하려는 경우에 적합합니다. 설치한 스킬은 플러그인 네임스페이스 없이 `$create-prd`, `$research`처럼 호출합니다.

### 모든 프로젝트에 독립 스킬로 설치

같은 독립 스킬을 현재 사용자의 모든 프로젝트에서 사용하려면 `--global`을 추가합니다.

```bash
npx skills add sonsu-lee/skills --agent codex --global
```

### Codex 플러그인으로 설치

플러그인에 포함된 스킬을 `$skills:<skill-name>` 형식으로 사용하려면 최신 Codex CLI에서 다음 명령을 한 줄씩 차례로 실행합니다. marketplace 등록과 플러그인 설치가 끝나면 Codex가 시작됩니다.

```bash
codex plugin marketplace add sonsu-lee/skills
codex plugin add skills@sonsu-skills
codex
```

Codex 플러그인은 현재 사용자 범위에 설치됩니다. 현재 Codex CLI에는 플러그인을 프로젝트 범위로 설치하는 옵션이 없으므로, 프로젝트에서만 사용하려면 위의 독립 스킬 설치 방식을 사용하세요.

플러그인을 업데이트하거나 제거할 때는 다음 명령을 사용합니다.

```bash
# 업데이트
codex plugin marketplace upgrade sonsu-skills
codex plugin add skills@sonsu-skills

# 제거
codex plugin remove skills@sonsu-skills
codex plugin marketplace remove sonsu-skills
```

## 사용법

설치 방식에 맞는 스킬 이름과 작업을 함께 요청합니다.

```text
# Codex 플러그인 설치
$skills:create-prd로 이 아이디어의 PRD를 작성해줘.
$skills:research로 이 주제를 근거 중심으로 조사해줘.

# Codex 독립 스킬 설치
$create-prd로 이 아이디어의 PRD를 작성해줘.
$research로 이 주제를 근거 중심으로 조사해줘.

# Claude Code
/skills:create-commit 현재 변경을 의미 단위로 커밋해줘.
/skills:git-change-review 현재 worktree를 검토해줘.
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
.agents/plugins/ # Codex marketplace catalog
.codex-plugin/   # Codex manifest
.claude-plugin/  # Claude Code manifest
```
