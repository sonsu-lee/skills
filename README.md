# Sonsu Skills

개인 Agent Skill을 루트 `skills/`에 한 번만 보관하고, 저장소 전체를 Codex와 Claude Code에서 같은 `skills` 플러그인으로 배포한다. Codex manifest와 Claude Code의 기본 skill discovery가 같은 루트 `skills/`를 사용하므로 플러그인별 복사본이나 symlink가 필요 없다.

Codex 플러그인의 skill discovery가 `skills/` 바로 아래 디렉터리를 기준으로 동작하므로 물리 구조는 평탄하게 유지한다. `product-docs`, `git-workflow`, `research`, `skill-authoring`은 설치·버전 경계가 아니라 아래 표와 공유 자료에서만 논리적으로 묶는다.

```text
.
├── .codex-plugin/
│   └── plugin.json
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   ├── audit-git-change/
│   ├── create-commit/
│   ├── create-prd/
│   ├── create-pull-request/
│   ├── create-skills/
│   ├── maintain-domain-docs/
│   ├── record-decision/
│   └── research/
├── shared/                  # 여러 스킬이 실행 중 공유하는 계약
│   ├── git-workflow/
│   └── product-docs/
├── docs/
│   └── design/              # maintainer용 설계·연구 근거
├── evals/
│   └── product-docs/        # Product Docs 교차 스킬 평가 계약
└── skills-lock.json         # 외부에서 설치한 로컬 개발 스킬 잠금
```

`.agents/skills/`와 `.claude/skills/`는 로컬 개발용 설치 경로일 뿐 정본이나 플러그인 입력이 아니다. 둘은 Git에서 제외한다. `.claude-plugin/`은 이 로컬 설치 경로와 무관한 Claude Code 배포 adapter다. Codex 플러그인 bundle은 symlink를 허용하지 않으므로 배포할 때는 로컬 설치물이 섞인 raw worktree가 아니라 Git이 추적하는 repository archive를 사용한다. marketplace 이름과 업데이트 정책을 정하기 전에는 호스트별 marketplace manifest를 두지 않는다.

`.codex-plugin/plugin.json`과 `.claude-plugin/plugin.json`은 같은 plugin ID, version과 `skills/` 정본을 사용하는 얇은 host adapter다. release할 때 두 manifest의 ID와 version을 함께 검증하고 version을 같은 변경에서 올린다. 어느 호스트도 별도의 생성본을 소유하지 않으며, Product Docs나 Git Workflow를 독립 설치·릴리스해야 할 실제 요구가 생길 때만 self-contained plugin root로 분리한다.

Claude Code adapter는 plugin root의 기본 `skills/` 탐색을 사용한다. marketplace 게시 전에는 저장소 루트에서 `claude --plugin-dir .`로 로컬 실행하고 `claude plugin validate . --strict`로 manifest를 검증할 수 있다.

## 스킬 컬렉션

| 그룹 | 스킬 | 역할 |
|---|---|---|
| Product Docs | `create-prd` | 문제, 제품 결과, 범위, 동작, 규칙과 성공 기준을 합의해 PRD로 만든다. |
| Product Docs | `maintain-domain-docs` | 용어, 개념, 역할, 상태, 전이와 비즈니스 규칙을 근거와 함께 유지한다. |
| Product Docs | `record-decision` | 중요한 제품·정책·아키텍처 결정을 선택지, 근거, 결과와 재검토 조건과 함께 남긴다. |
| Git Workflow | `create-commit` | 변경을 의미 단위로 나누고 Conventional Commit으로 안전하게 커밋한다. |
| Git Workflow | `create-pull-request` | base/head diff, merge mode와 저장소 템플릿에 맞는 PR을 준비하거나 생성한다. |
| Git Workflow | `audit-git-change` | worktree, commit range 또는 PR을 변경 없이 감사하고 수정안을 제안한다. |
| Research | `research` | 원문 교차검증, 반증 탐색과 인용 감사를 포함한 범용 조사를 수행한다. |
| Skill Authoring | `create-skills` | Agent Skill을 생성·개선하고 구조, 트리거, 행동과 보안을 검증한다. |

플러그인으로 설치하면 Codex에서는 `$skills:<skill-name>`, Claude Code에서는 `/skills:<skill-name>` 형식으로 명시적으로 호출한다.

```text
$skills:create-prd로 이 아이디어를 full 깊이로 인터뷰하고 PRD를 작성해줘.
$skills:maintain-domain-docs로 반복되는 정산 용어와 상태 전이를 정본으로 정리해줘.
$skills:record-decision으로 수동 검토를 선택한 실제 근거와 재검토 조건을 남겨줘.
$skills:research로 이 주제를 근거 중심으로 조사해줘.
$skills:create-commit으로 현재 변경을 의미 단위로 커밋해줘.
/skills:create-prd 이 아이디어를 full 깊이로 인터뷰하고 PRD를 작성해줘.
```

## 공유 계약

Product Docs 세 스킬은 `shared/product-docs/document-contract.md`의 저장 및 상호 연결 규칙을 공유한다. PRD가 다른 두 문서의 내용을 소유하지는 않는다. 도메인 지식이나 장기 보존할 결정이 발견되면 승격 후보를 제시하고, 사용자가 승인한 뒤 해당 스킬로 정본을 만든다. 한 작업에서 세 문서를 모두 요청해도 PRD → 승인된 promotion candidate → companion skill 순서로 처리하며, 쓰기 요청·의미 승인·문서 소유권을 별도로 확인한다.

저장소에 기존 규칙이 없을 때 Product Docs의 기본 저장 경로는 다음과 같다.

```text
docs/
├── product/prds/
├── domain/
└── decisions/
```

OpenWiki 같은 파생 위키는 이후 이 정본들을 읽어 탐색 문서를 만들 수 있다. 생성된 위키를 정본으로 간주하거나 `openwiki/` 아래에 제품 결정을 직접 기록하지 않는다. `visibility`와 `publication`은 정책 힌트일 뿐 OpenWiki 접근 제어가 아니다. 연결할 때는 `.openwikiignore` 또는 별도 staging/export projection으로 비공개 입력을 먼저 제외하고 결과를 검증해야 한다.

Git Workflow 세 스킬은 `shared/git-workflow/change-policy.md`를 공유한다. PR은 하나의 승인·배포·되돌리기 단위로 취급하고, 내부 commit은 리뷰 가능한 의미 단위로 나눈다. 저장소의 `AGENTS.md`, `CONTRIBUTING`, commitlint, hooks와 PR template을 우선하며, 읽기 전용 감사는 수정안을 제안할 수 있지만 적용하지 않는다. 격리된 실행 환경의 인증·서명 오류는 `shared/git-workflow/host-auth-and-signing.md`의 재확인 절차를 따른다.

Git Workflow에는 다음 원칙도 공통으로 적용한다.

- Conventional Commit 제목은 영어 한 줄이며 body와 footer는 필요할 때 허용한다.
- PR 제목은 전체 변경을 요약하는 Conventional Commit 형식으로 만든다.
- squash를 기본 선호로 두되 저장소가 commit 보존 전략을 쓰면 각 commit을 최종 history 기준으로 검사한다.
- 새 squash·merge commit과 rebase 결과의 서명을 source commit에서 추론하지 않는다.
- Before/After screenshot은 실제 이미지에 접근할 수 있는 시각 변경에만 포함한다.
- GitHub 인증이나 signing 실패가 격리 때문일 수 있으면 실패를 곧바로 미인증으로 단정하지 않고, 허용된 최소 읽기 전용 진단 뒤 실제 상태를 재확인해 중복 실행을 막는다.

plugin root의 `shared/` 계약을 읽는 Product Docs와 Git Workflow 스킬은 이 저장소 전체를 플러그인으로 설치하는 것이 기본이다. `create-skills`와 `research`의 실행 reference는 각 skill 디렉터리 안에 있으며, Research의 선택 공급자 opt-in만 아래 루트 설정을 사용한다.

## Research 공급자 opt-in

검색 공급자는 선택 사항이며 이 플러그인은 MCP, 계정 연결 또는 공급자 SDK를 번들하지 않는다. 아래 두 marker 사이의 매핑만 공급자 opt-in 선언으로 인정한다. 항목을 제거하면 해당 공급자를 사용하지 않는다.

<!-- research-provider-opt-in:v1:start -->
```yaml
providers:
  exa:
    env: EXA_API_KEY
  perplexity:
    env: PERPLEXITY_API_KEY
```
<!-- research-provider-opt-in:v1:end -->

선언만으로 공급자가 활성화되지는 않는다. 다음 조건을 모두 충족해야 한다.

1. 설치 manifest에서 유도한 고정 플러그인 루트의 이 README가 regular file이고 symlink가 아니다.
2. 위 전용 블록에 공급자와 환경변수의 정확한 매핑이 있다.
3. 환경변수가 non-empty라는 사실을 값·길이·접두사 없이 boolean 또는 exit status로만 확인할 수 있다.
4. 대응하는 읽기 전용 도구의 실제 스키마와 인증 상태를 확인할 수 있다.

하나라도 충족하지 않으면 해당 공급자는 비활성으로 간주한다. 환경변수 값은 출력·로그·검색어·위임 메시지에 넣지 않으며 `env`, `printenv`, shell trace나 오류 dump로 검사하지 않는다. 플러그인이 공급자를 자동 설치하거나 연결하지도 않는다.

Research는 다음을 기본으로 한다.

- Exa는 후보 자료와 원문 발견에 우선 사용한다.
- Perplexity는 중복 기본 검색이 아니라 누락, 반례, 실패와 적용 한계를 찾는 optional challenger로 사용한다.
- `standard`와 `deep` 조사는 최종 출력 전에 자동 인용 감사를 거친다.
- 기존 보고서 감사는 판정 요약, 중요한 수정 근거와 수정된 보고서를 기본 출력으로 하며 별도 쓰기 요청 없이 원본을 덮어쓰지 않는다.
- 공급자 장애와 내부 실행 상태는 현재성·완전성·독립성이나 결론을 실제로 저하시킬 때만 자연어로 알린다.

## 검증

행동 평가 suite가 있는 7개 skill은 저장소 전용 structured fixture인 `evals/cases.json`과 필요한 evaluator rubric을 보유한다. `evals/product-docs/cases.json`은 Product Docs의 공개 교차 스킬 회귀 suite다. 이 파일들은 공식 skill-creator의 `evals/evals.json` 스키마가 아니라 fixture repository, multi-turn checkpoint와 `must`/`must_not` assertion ID를 보존하는 이 저장소의 회귀 계약이다. 이 사례들은 개발 계약이지 비공개 holdout이 아니다. 실제 모델 비교는 `evals/product-docs/protocol.md`에 따라 `evals/`를 제외한 runtime snapshot에서 실행하고, release holdout과 runtime canary는 플러그인 밖에서 관리해야 한다.

이 저장소에는 plugin·skill schema validator가 읽을 구조와 저장소 전용 JSON 평가 계약이 포함돼 있다. 링크, cross-document ID, 평가 분포까지 한 명령으로 검사하는 전용 static runner와 모델 호출·파일 tree/hash oracle·반복 신뢰성 runner는 포함하지 않는다. 외부 검증기가 확인해야 할 범위는 `evals/product-docs/protocol.md`, `evals/product-docs/README.md`와 각 rubric에 명시했다. Product Docs의 연구 근거와 적용 한계는 `docs/design/product-docs-research-basis.md`에 정리되어 있다.
