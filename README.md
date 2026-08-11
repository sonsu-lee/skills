# Sonsu Skills

Codex용 개인 Agent Skill 플러그인입니다. 제품 문서 작성, 리서치, Git 작업, 스킬 제작과 개인 개발자 이력서 검토를 지원하며 Claude Code용 manifest도 함께 제공합니다.

## 제공 스킬

| 스킬 | 설명 |
|---|---|
| `product-discovery` | 제품 문제와 미해결 결정을 근거 중심으로 탐색합니다. |
| `to-prd` | 합의된 제품 컨텍스트를 검증 가능한 PRD로 변환합니다. |
| `write-prd` | 기존 호출을 `product-discovery`·`to-prd` 흐름으로 연결합니다. 호환용·폐기 예정. |
| `domain-modeling` | 용어, 상태, 전이와 비즈니스 규칙을 정본으로 정리합니다. |
| `write-domain-docs` | 기존 호출을 `domain-modeling` 흐름으로 연결합니다. 호환용·폐기 예정. |
| `architecture-decisions` | 아직 결론 없는 기술 선택의 대안과 판단 기준을 검토합니다. |
| `to-adr` | 준비된 아키텍처·기술 결정을 ADR로 변환합니다. |
| `write-adr` | 기존 호출을 `architecture-decisions`·`to-adr` 흐름으로 연결합니다. 호환용·폐기 예정. |
| `to-tickets` | 승인된 계획을 의존성이 드러나는 실행 티켓으로 변환합니다. |
| `research` | 여러 원문을 교차 검증해 근거 중심으로 조사합니다. |
| `create-commit` | 변경을 의미 단위로 나누어 커밋합니다. |
| `create-pull-request` | 변경 범위와 저장소 규칙에 맞는 PR을 만듭니다. |
| `review-commit` | 커밋 전 후보 변경과 이미 생성된 커밋 기록을 읽기 전용으로 검토합니다. |
| `review-pr` | PR의 내용과 merge 준비 상태를 읽기 전용으로 검토합니다. |
| `develop-skill` | Agent Skill을 생성·수정·검토하고 구조와 행동을 검증합니다. |
| `review-dev-resume` | 명시적으로 호출해 내 개발자 이력서와 경력기술서를 읽기 전용으로 진단합니다. |

## 명명 및 구조 원칙

- 스킬 하나는 독립적으로 설명할 수 있는 하나의 큰 주제와 책임을 가집니다.
- 이름은 실제 행동을 나타내는 짧은 동사형 구문을 우선합니다.
- `to-*`는 합의되거나 준비된 컨텍스트를 이름에 적힌 산출물로 변환할 때만 사용합니다.
- `review-*`와 `research`는 상태를 바꾸지 않는 읽기 전용 작업을 나타냅니다.
- 탐색·의사결정·문서화가 각각 독립적으로 호출될 수 있다면 별도 스킬로 분리합니다.
- `SKILL.md`에는 모든 실행의 핵심 절차와 reference 로드 조건을 두고, 긴 공통 계약과 분기별 상세 지침은 `references/`에서 필요한 범위로 읽습니다.

이름 선택, 호출 방식, 분리 기준과 디렉터리 구조의 상세 규칙은 [스킬 명명 및 구조 원칙](docs/design/skill-naming-and-structure.md)을 따릅니다.

## 설치

사용할 범위와 설치 형태에 맞는 방법을 선택합니다.

| 목적 | 설치 방식 | 적용 범위 | Codex 호출 형식 |
|---|---|---|---|
| 현재 프로젝트에서만 사용 | 독립 스킬 설치 | 현재 프로젝트의 `.agents/skills/` | `$product-discovery` |
| 모든 프로젝트에서 사용 | 독립 스킬 전역 설치 | 현재 사용자 | `$product-discovery` |
| 플러그인 묶음과 네임스페이스 사용 | Codex 플러그인 설치 | 현재 사용자 | `$skills:product-discovery` |

`write-prd`, `write-domain-docs`, `write-adr`는 이전 호출을 새 이름으로 연결하는 deprecated 호환 진입점이므로 단독 선택 설치를 지원하지 않습니다. 기존 이름을 계속 사용해야 한다면 독립 스킬 설치에서 다음 companion을 함께 선택하거나 전체 Codex 플러그인을 설치하세요.

- `write-prd`: `product-discovery`, `to-prd`
- `write-domain-docs`: `domain-modeling`
- `write-adr`: `architecture-decisions`, `to-adr`

### 현재 프로젝트에 설치

대상 프로젝트 루트에서 다음 명령을 실행합니다. 설치할 스킬을 선택할 수 있으며 Codex는 프로젝트의 `.agents/skills/`에서 스킬을 읽습니다.

```bash
npx skills add sonsu-lee/skills --agent codex
```

이 방식은 해당 프로젝트에만 스킬을 적용하려는 경우에 적합합니다. 설치한 스킬은 플러그인 네임스페이스 없이 `$product-discovery`, `$research`처럼 호출합니다.

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
$skills:product-discovery로 이 제품 아이디어의 문제와 핵심 결정을 구체화해줘.
$skills:to-prd로 합의된 제품 컨텍스트를 PRD로 작성해줘.
$skills:architecture-decisions로 이 기술 선택의 대안과 판단 기준을 검토해줘.
$skills:to-adr로 내려진 기술 결정을 ADR로 기록해줘.
$skills:to-tickets로 승인된 계획을 실행 가능한 티켓으로 나눠줘.
$skills:research로 이 주제를 근거 중심으로 조사해줘.
$skills:develop-skill로 새 스킬을 만들거나 기존 스킬을 개선해줘.
$skills:review-dev-resume로 내 개발자 이력서를 검토해줘.

# Codex 독립 스킬 설치
$product-discovery로 이 제품 아이디어를 구체화해줘.
$to-prd로 합의된 내용을 PRD로 작성해줘.
$domain-modeling으로 도메인 용어와 상태 전이를 정리해줘.
$architecture-decisions로 기술 선택지를 검토해줘.
$to-adr로 내려진 결정을 ADR로 기록해줘.
$research로 이 주제를 근거 중심으로 조사해줘.
$review-dev-resume로 내 개발자 이력서를 검토해줘.

# Claude Code
/skills:create-commit 현재 변경을 의미 단위로 커밋해줘.
/skills:review-commit 현재 변경을 커밋하기 전에 검토해줘.
/skills:review-commit 최근 커밋 세 개를 검토해줘.
/skills:review-pr 이 PR의 merge 준비 상태를 검토해줘.
/skills:develop-skill 기존 스킬의 트리거와 행동을 개선해줘.
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
