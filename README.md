# Sonsu Skills

Codex용 개인 Agent Skill 플러그인입니다. 소프트웨어 변경 오케스트레이션, 제품 문서 작성, 리서치, Git 작업, 스킬 제작과 개인 개발자 이력서 검토를 지원하며 Claude Code용 manifest도 함께 제공합니다.

## 제공 스킬

| 스킬 | 설명 |
|---|---|
| `recommend-skill` | 현재 목표와 준비 상태에 맞는 다음 스킬과 호출 방법을 추천합니다. |
| `product-discovery` | 제품 문제와 미해결 결정을 근거 중심으로 탐색합니다. |
| `to-prd` | 합의된 제품 컨텍스트를 검증 가능한 PRD로 변환합니다. |
| `domain-modeling` | 용어, 상태, 전이와 비즈니스 규칙을 정본으로 정리합니다. |
| `architecture-decisions` | 아직 결론 없는 기술 선택의 대안과 판단 기준을 검토합니다. |
| `to-adr` | 준비된 아키텍처·기술 결정을 ADR로 변환합니다. |
| `to-tickets` | 승인된 계획을 의존성이 드러나는 실행 티켓으로 변환합니다. |
| `research` | 여러 원문을 교차 검증해 근거 중심으로 조사합니다. |
| `develop-change` | 하나의 소프트웨어 변경을 이해·설계·구현·검증·전달까지 오케스트레이션하고 필요한 전문 스킬을 조합합니다. |
| `present-result` | 전문 결과의 의미를 유지하면서 결론·영향·다음 행동을 쉬운 말로 전달합니다. |
| `git-workflow` | Conventional Branch 명명부터 Conventional Commit, PR 생성과 읽기 전용 검토까지 하나의 흐름으로 관리합니다. |
| `develop-skill` | Agent Skill을 생성·수정·검토하고 구조와 행동을 검증합니다. |
| `review-dev-resume` | 명시적으로 호출해 내 개발자 이력서와 경력기술서를 읽기 전용으로 진단합니다. |

## 워크플로 선택

어떤 스킬부터 사용할지 모르면 `$recommend-skill`을 명시적으로 호출합니다. `recommend-skill`은 전문 작업이나 상태 변경을 대신 수행하지 않고, 현재 단계에 맞는 다음 스킬 하나와 정확한 호출 예시를 안내합니다.

`develop-change`, `recommend-skill`, `develop-skill`과 `review-dev-resume`를 제외한 전문 스킬은 목표가 자연어 요청에 명확하면 이름을 직접 쓰지 않아도 자동으로 선택될 수 있습니다. 자동 선택은 파일, Git 또는 외부 시스템 변경 권한이 아니며, 각 스킬은 사용자가 요청한 동작과 내부 승인 gate 안에서만 상태를 바꿉니다.

`0.3.0`부터 대표 진입점의 호출 이름이 `$sonsu`에서 `$recommend-skill`로 변경되었습니다. 기존 프롬프트나 자동화에서도 호출 이름을 함께 변경해야 합니다.

`0.4.0`부터 Git 진입점은 `$git-workflow` 하나로 통합되었습니다. 기존 `$create-commit`, `$create-pull-request`, `$review-commit`, `$review-pr` 호출은 `$git-workflow`와 요청할 mode로 바꿔야 합니다.

`0.4.1`부터 branch 이름은 별도 Conventional Branch 1.1.0 명세를 따릅니다. commit message와 PR 제목은 계속 Conventional Commits 형식을 사용합니다.

`0.5.0`부터 `git-workflow`, `to-*`와 다른 전문 스킬은 목표가 자연어 요청에 명확하면 이름을 직접 쓰지 않아도 자동으로 선택될 수 있습니다. `recommend-skill`, `develop-skill`과 `review-dev-resume`는 계속 명시적으로 호출합니다.

`0.6.0`부터 전문 스킬의 최종 사용자 응답에는 `present-result`가 마지막 표현 단계로 적용됩니다. 원본 PRD·ADR·코드·티켓과 상태·ID·근거는 바꾸지 않고, 결론과 실제 영향, 다음 행동을 쉬운 말로 먼저 전달합니다. 작업 스킬과 `present-result`를 함께 설치하면 공통 표현 규칙 전체를 사용합니다. 작업 스킬만 독립 설치해도 각 스킬의 최소 대체 규칙이 적용되어 고정 출력 형식과 필수 필드는 유지하고, 자유 서술 영역만 쉬운 말로 전달합니다.

`0.7.0`부터 `$develop-change`가 구현·검증·전달을 잇는 명시 호출 오케스트레이터로 추가되었습니다. 일반 구현 요청 및 `git-workflow`와의 경합을 평가하기 전까지 implicit invocation은 비활성화합니다.

| 현재 상태 | 다음 스킬 |
|---|---|
| 제품 문제나 범위 결정이 열려 있음 | `product-discovery` |
| 제품 컨텍스트가 합의되어 PRD가 필요함 | `to-prd` |
| 도메인 용어·상태·업무 규칙을 정리함 | `domain-modeling` |
| 기술 선택의 대안과 판단 기준이 열려 있음 | `architecture-decisions` |
| 내려진 기술 결정을 ADR로 남김 | `to-adr` |
| 승인된 계획을 실행 작업으로 나눔 | `to-tickets` |
| 하나의 소프트웨어 변경을 이해부터 구현·검증·전달까지 진행 | `develop-change` |
| 이미 나온 전문 결과를 쉽게 풀어 전달함 | `present-result` |
| 브랜치, commit, push, PR 또는 Git 산출물 검토 | `git-workflow` |

`develop-change`는 `$develop-change` 또는 `$skills:develop-change`로 명시 호출합니다. 호출은 필요한 스킬 조합을 선택할 뿐 파일·Git·외부 상태 변경 권한을 만들지 않습니다.

`review-dev-resume`는 `recommend-skill`의 추천 대상이 아니며, `$review-dev-resume` 또는 `$skills:review-dev-resume`로 직접 호출할 때만 사용합니다.

## 명명 및 구조 원칙

- 스킬 하나는 독립적으로 설명할 수 있는 하나의 큰 주제와 책임을 가집니다.
- 이름은 실제 행동을 나타내는 짧은 동사형 구문을 우선합니다.
- `to-*`는 합의되거나 준비된 컨텍스트를 이름에 적힌 산출물로 변환할 때만 사용합니다.
- `review-*`와 `research`는 상태를 바꾸지 않는 읽기 전용 작업을 나타냅니다.
- `git-workflow`는 하나의 Git 변경 수명 주기를 단일 진입점으로 제공하되, 준비·검토 mode와 branch·commit·PR 쓰기 mode의 권한을 내부에서 분리합니다.
- `develop-change`는 route·gate·권한·handoff를 관리하는 얇은 제어 계층이며, 언어·DB·프레임워크 규칙은 프로젝트 지침과 적용 가능한 전문 스킬에서 가져옵니다.
- 탐색·의사결정·문서화가 각각 독립적으로 호출될 수 있다면 별도 스킬로 분리합니다.
- `SKILL.md`에는 모든 실행의 핵심 절차와 reference 로드 조건을 두고, 긴 공통 계약과 분기별 상세 지침은 `references/`에서 필요한 범위로 읽습니다.

이름 선택, 호출 방식, 분리 기준과 디렉터리 구조의 상세 규칙은 [스킬 명명 및 구조 원칙](docs/design/skill-naming-and-structure.md)을 따릅니다.

## 설치

사용할 범위와 설치 형태에 맞는 방법을 선택합니다.

| 목적 | 설치 방식 | 적용 범위 | Codex 호출 형식 |
|---|---|---|---|
| 현재 프로젝트에서만 사용 | 독립 스킬 설치 | 현재 프로젝트의 `.agents/skills/` | `$recommend-skill` |
| 모든 프로젝트에서 사용 | 독립 스킬 전역 설치 | 현재 사용자 | `$recommend-skill` |
| 플러그인 묶음과 네임스페이스 사용 | Codex 플러그인 설치 | 현재 사용자 | `$skills:recommend-skill` |

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
$skills:recommend-skill로 이 작업에 맞는 다음 스킬을 찾아줘.
$skills:product-discovery로 이 제품 아이디어의 문제와 핵심 결정을 구체화해줘.
$skills:to-prd로 합의된 제품 컨텍스트를 PRD로 작성해줘.
$skills:architecture-decisions로 이 기술 선택의 대안과 판단 기준을 검토해줘.
$skills:to-adr로 내려진 기술 결정을 ADR로 기록해줘.
$skills:to-tickets로 승인된 계획을 실행 가능한 티켓으로 나눠줘.
$skills:research로 이 주제를 근거 중심으로 조사해줘.
$skills:develop-change로 이 변경을 이해하고 필요한 전문 스킬을 조합해 구현·검증한 뒤 Draft PR까지 진행해줘.
$skills:present-result로 위 결과를 의미를 유지하면서 이해하기 쉽게 정리해줘.
$skills:git-workflow로 이 변경의 브랜치를 만들고 Conventional Commit으로 커밋한 뒤 draft PR을 생성해줘.
$skills:git-workflow로 이 PR의 merge 준비 상태를 읽기 전용으로 검토해줘.
$skills:develop-skill로 새 스킬을 만들거나 기존 스킬을 개선해줘.
$skills:review-dev-resume로 내 개발자 이력서를 검토해줘.

# Codex 독립 스킬 설치
$recommend-skill로 이 작업에 맞는 다음 스킬을 찾아줘.
$product-discovery로 이 제품 아이디어를 구체화해줘.
$to-prd로 합의된 내용을 PRD로 작성해줘.
$domain-modeling으로 도메인 용어와 상태 전이를 정리해줘.
$architecture-decisions로 기술 선택지를 검토해줘.
$to-adr로 내려진 결정을 ADR로 기록해줘.
$research로 이 주제를 근거 중심으로 조사해줘.
$develop-change로 이 기능을 구현하고 테스트한 뒤 결과를 전달해줘.
$present-result로 위 결과를 이해하기 쉽게 정리해줘.
$git-workflow로 이 변경을 브랜치부터 draft PR까지 진행해줘.
$review-dev-resume로 내 개발자 이력서를 검토해줘.

# Claude Code
/skills:develop-change 이 변경을 이해부터 구현·검증·Draft PR까지 진행해줘.
/skills:git-workflow 현재 변경에 맞는 브랜치를 만들고 의미 단위로 커밋해줘.
/skills:git-workflow 최근 커밋 세 개를 읽기 전용으로 검토해줘.
/skills:git-workflow 이 PR의 merge 준비 상태를 읽기 전용으로 검토해줘.
/skills:git-workflow 현재 브랜치를 draft PR로 올려줘.
/skills:develop-skill 기존 스킬의 트리거와 행동을 개선해줘.
```

각 스킬의 자세한 동작과 옵션은 `skills/<skill-name>/SKILL.md`에서 확인할 수 있습니다.

## Git 워크플로와 브랜치 이름

`git-workflow`는 branch, commit과 PR이 같은 주효과를 설명하도록 연결하되 이름 형식은 독립적으로 검증합니다. branch는 [Conventional Branch 1.1.0](https://conventionalbranch.org/), commit message와 PR 제목은 [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/)을 사용합니다.

PR 본문은 기본 브랜치의 저장소 템플릿, repository owner의 기본 `.github` 템플릿 순으로 사용합니다. 적용할 템플릿이 하나면 그대로 따르고, 복수 후보가 모호하면 선택을 요청합니다. 템플릿이 없으면 `Summary`, `Changes`, `Verification`과 필요한 경우에만 `Notes`를 포함하는 fallback 형식을 먼저 보여주고 확인받은 뒤 작성합니다. 실행하지 않은 검증은 이유와 함께 표시하며 빈 선택 절은 남기지 않습니다.

```text
# branch
<type>/<description>

# commit과 PR 제목
<type>[optional scope][!]: <description>
```

Conventional Branch의 purpose prefix는 `feature`·`feat`, `bugfix`·`fix`, `hotfix`, `release`, `chore`이며 agent source prefix는 `ai`, `copilot`, `cursor`, `claude`, `codex`입니다. 예를 들어 Codex가 만든 branch는 `codex/adopt-conventional-branch`, commit과 PR 제목은 `fix(git-workflow): adopt Conventional Branch naming`처럼 작성할 수 있습니다. branch prefix는 source를, commit type과 scope는 변경 의미를 나타낼 수 있으므로 서로 같을 필요는 없습니다. 더 구체적인 저장소 규칙이 있으면 그 규칙을 우선합니다.

이름·메시지·계획·검토 요청은 읽기 전용입니다. `git-workflow`는 Git 작업 요청에서 자동으로 선택될 수 있지만, branch 생성, commit, push와 PR 생성은 사용자가 해당 동작 또는 전체 흐름을 명시적으로 요청한 경우에만 수행합니다.

## 로컬 확인

Claude Code에서는 저장소 루트에서 플러그인을 직접 불러오고 manifest를 검증할 수 있습니다.

```bash
python3 scripts/validate_skill_catalog.py
python3 skills/develop-change/scripts/validate_orchestration.py --activation active
python3 -m unittest discover -s tests -v
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
  develop-change # 명시 호출 변경 오케스트레이터와 계약·평가
evals/           # 스킬 간 회귀 평가
docs/            # 설계 및 연구 문서
scripts/         # 저장소 단위 결정론적 검증기
.agents/plugins/ # Codex marketplace catalog
.codex-plugin/   # Codex manifest
.claude-plugin/  # Claude Code manifest
```
