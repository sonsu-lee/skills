# 개인 스킬 저장소 설계

상태: 승인된 기본 설계

마지막 수정: 2026-07-14

## 목적

이 저장소는 다음 두 영역을 함께 관리한다.

1. 직접 작성하고 유지보수하는 개인 스킬과 플러그인
2. 외부 스킬의 출처, 분류와 설치 방법을 기록한 카탈로그

외부 스킬 소스는 이 저장소에 복사하거나 미러링하지 않는다. 설치할 때 upstream 저장소, `npx skills` 또는 각 호스트가 제공하는 공식 플러그인을 사용한다.

## 기본 원칙

- `skills/`에는 직접 만든 스킬과 명시적으로 내재화한 스킬만 둔다.
- 외부 스킬은 사용자가 선택한 항목만 카탈로그에 등록한다.
- 외부 파일을 수정하거나 자체 배포본으로 재포장하지 않는다.
- 공용 스킬과 호스트 전용 기능을 설치 단계에서 분리한다.
- 설치는 기존 CLI와 호스트의 플러그인 기능을 우선 사용한다.
- 독자적인 패키지 관리자, dependency resolver 또는 동기화 시스템을 만들지 않는다.
- 코드는 꼭 필요한 범위로 제한하고 표준 라이브러리를 우선한다.
- `docs/DESIGN.md`를 현재 설계의 SSOT로 유지한다.

## 저장소 책임과 경계

### 직접 만든 스킬

직접 만든 스킬은 `skills/<skill-name>/`에 둔다. 각 스킬에는 `SKILL.md`를 필수로 두고, `scripts/`, `references/`, `assets/`, `agents/openai.yaml`은 실제로 필요할 때만 추가한다.

Codex와 Claude Code에서 같은 동작을 제공하는 스킬은 Agent Skills 형식의 `SKILL.md` 하나를 portable SSOT로 사용한다. Codex의 표시 이름과 기본 prompt 같은 호스트 메타데이터만 `agents/openai.yaml`에 분리한다. 평가 prompt는 배포되는 스킬 폴더를 불필요하게 키우지 않도록 저장소 루트의 `evals/<skill-name>/`에서 관리한다.

#### 통합 스킬 작성 흐름

`to-skill` 하나를 스킬 생성, 수정과 구조 정규화의 진입점으로 사용한다. 사용자가 `skill-to-codex`와 `skill-to-claude`를 순서대로 호출하도록 요구하지 않는다. 두 독립 adapter 스킬은 제거하고, 작성 원칙과 호스트별 계약을 `to-skill/references/` 아래의 조건부 reference로 합친다.

일반 프로젝트에서 별도 규칙이 없으면 `.agents/skills/<skill-name>/`을 canonical 원본으로 사용한다. Codex는 이 경로를 직접 사용하고 Claude Code에는 같은 원본을 가리키는 상대경로 symlink만 둔다.

```text
.agents/skills/example-skill/
├── SKILL.md
├── references/            # 필요할 때만
├── scripts/               # 필요할 때만
└── agents/openai.yaml     # Codex metadata가 필요할 때만

.claude/skills/example-skill -> ../../.agents/skills/example-skill
```

이 저장소처럼 배포 원본 경로를 명시한 저장소에서는 해당 규칙을 우선한다. 따라서 이 저장소의 개인 스킬은 계속 `skills/<skill-name>/`에서 관리하고, 소비 프로젝트에서 생성하는 스킬만 기본적으로 `.agents/skills`를 사용한다. 배포 저장소의 원본을 다시 `.agents/skills`에 복제하지 않는다.

`to-skill`은 다음 흐름을 담당한다. 아래 호스트 연결 동작은 일반 소비 프로젝트의 기본값이며, 명시적인 배포 원본 경로가 있는 저장소에서는 해당 저장소의 배치와 배포 규칙을 따른다.

- 새 스킬은 canonical 경로에 portable `SKILL.md`, 필요한 resource와 초기 eval을 만든다. 일반 소비 프로젝트에서는 이어서 Claude symlink를 연결한다.
- 기존 스킬은 canonical 원본만 수정하고 올바른 symlink는 그대로 유지한다.
- 여러 호스트 경로에 물리적 사본이 있으면 내용을 비교한다. 명시적인 정규화 요청이 있고 내용이 완전히 같을 때만 교체 계획을 보여주고 확인을 받은 뒤 Claude 사본을 symlink로 바꾼다. 내용이 다르면 덮어쓰거나 자동 병합하지 않고 충돌을 보고한다.
- `.claude/skills/<skill-name>`에만 물리적 사본이 있으면 자동으로 이동하지 않는다. canonical 이동 경로와 변경될 link를 보여주고 확인을 받은 뒤 `.agents/skills/<skill-name>`으로 옮겨 symlink를 만든다.

canonical 원본이 존재하고 `.claude/skills/<skill-name>` 엔트리가 없을 때만 상대경로 link를 만든다. 이미 올바른 symlink이면 아무것도 바꾸지 않는다. 잘못된 link나 실제 디렉터리가 대상 경로를 차지하면 자동으로 삭제하지 않고, 위 정규화 조건을 충족하지 않는 한 중단한다. 대상 Claude Code가 directory symlink를 지원하지 않으면 조용히 copy mode로 바꾸지 않고 호환성 문제를 보고한다.

portable frontmatter에는 기본적으로 `name`과 `description`만 둔다. Codex 전용 값은 같은 원본 폴더의 `agents/openai.yaml`에 둔다. Claude Code 전용 frontmatter나 plugin 기능이 반드시 필요한 경우에는 공통 원본에 섞기 전에 portability를 검토하고, 단일 원본으로 표현할 수 없으면 일반 작성 흐름과 분리된 호스트 전용 배포 작업으로 보고한다. 기본 흐름은 호스트별 파생본을 만들지 않는다.

Plugin packaging은 첫 스킬 작성 후 자동으로 따라오는 단계가 아니다. 사용자가 배포를 명시적으로 요청했을 때만 해당 호스트의 현재 계약으로 최소 구성하며, version, publisher, marketplace와 동기화 자동화를 추측해서 추가하지 않는다. 내장 또는 공식 `skill-creator`는 단일 호스트 전용 스킬과 최신 제품 기능을 위한 fallback으로 유지한다.

`to-skill`은 개인용 experimental workflow다. 구조 검증과 대표 forward smoke check를 통과했더라도 내장 creator보다 우수하다고 간주하지 않으며, 반복 eval과 baseline 비교 전에는 fallback을 대체하지 않는다.

루트 `evals/`는 runtime 계약이 아니라 개발 데이터다. `to-skill`의 작성, 정규화와 호스트 노출 사례는 `evals/to-skill/`에서 함께 관리하고 공통 portable 입력은 `evals/fixtures/`에서 하나로 유지한다. 현재 테스트는 eval schema와 canonical fixture 구조를 검증한다. 반복 실행, baseline 비교와 비용 측정이 실제로 필요해질 때만 별도 evaluator를 추가한다.

### 외부 스킬

외부 스킬은 `catalog/`에 설치 정보만 기록한다. 카탈로그는 다음 질문에 답할 수 있어야 한다.

- 어떤 용도로 사용하는가?
- 원본 저장소와 스킬 경로는 어디인가?
- 라이선스와 공식 설치 방법은 무엇인가?
- 공용 스킬인가, 특정 호스트 전용인가?
- 함께 설치해야 하는 실제 의존 항목이 있는가?
- 어떤 profile 또는 add-on에 포함되는가?

카탈로그는 upstream 코드의 품질, 안전성 또는 호환성을 대신 보증하지 않는다.

### 설치 도구

초기 설치 도구는 `npx skills`와 호스트별 공식 설치 명령을 호출하는 얇은 wrapper로 만든다. 설치 도구 자체가 upstream clone, 파일 복사 또는 업데이트 알고리즘을 구현하지 않는다.

설치 도구가 독립적인 버전 관리와 배포가 필요할 정도로 커질 때만 별도 저장소로 분리한다.

## 외부 기능 분류

### `shared`

특정 호스트 기능에 의존하지 않는 Agent Skills 호환 스킬이다.

공유 설치에서는 `.agents/skills`를 실제 파일의 SSOT로 사용하고, Claude Code처럼 별도 경로가 필요한 호스트는 symlink로 연결한다.

```text
.agents/skills/example-skill/
.claude/skills/example-skill -> ../../.agents/skills/example-skill
```

symlink를 지원하지 않는 환경에서는 사용자가 명시적으로 copy mode를 선택한다. 설치 도구가 조용히 설치 방식을 바꾸지 않는다.

### `host-specific`

특정 호스트의 CLI, 명령 디렉터리, 도구 또는 하위 에이전트에 의존하는 스킬이다. 해당 호스트만 발견할 수 있는 위치에 설치하며 `.agents/skills`에 공용으로 두지 않는다.

### `host-native`

동일한 논리 기능을 호스트의 내장 스킬이나 공식 플러그인으로 제공하는 경우다. 공용 파일 하나를 설치하는 대신 호스트별 provider를 선택한다.

예를 들어 `skill-authoring` 기능은 다음처럼 처리한다.

```text
Codex
└── 내장 skill-creator 사용

Claude Code
└── skill-creator@claude-plugins-official 사용
```

스킬 frontmatter에는 호스트를 강제로 제한하는 표준 트리거가 없다. 따라서 호스트 격리는 `description` 문구가 아니라 설치 위치와 공식 플러그인 경계로 보장한다.

이 `skill-authoring` provider는 catalog에서 설치할 수 있는 host-native fallback이다. 직접 만든 portable 스킬의 기본 작성 흐름은 통합된 `to-skill`을 사용한다.

## Catalog 모델

카탈로그 데이터 파일은 첫 설치 대상이 확정될 때 추가한다. 초기 후보를 미리 등록하지 않는다.

### 스킬 선언

각 항목은 필요에 따라 다음 정보를 가진다.

- 저장소 내부 고유 ID
- 표시 이름과 사용 목적
- 종류: skill, plugin, command 또는 tool
- upstream 저장소와 원본 경로
- 라이선스 링크
- 배포 방식: `shared`, `host-specific`, `host-native`
- 호스트별 provider와 공식 설치 명령
- 실제 실행에 필요한 명시적 dependency
- 소속 profile과 add-on
- 설치 부작용과 신뢰 관련 주의사항
- 마지막 확인 날짜

`provider`와 배포 방식은 이 저장소의 설치 메타데이터다. 외부 `SKILL.md`에 추가하거나 upstream 트리거로 취급하지 않는다.

### 연계 항목

연계되는 스킬은 다음 두 방식으로만 묶는다.

- 실제 실행에 반드시 필요하면 명시적 dependency로 등록한다.
- 함께 사용하기 좋은 정도라면 같은 profile 또는 add-on에 포함한다.

소스 내용을 분석해 dependency closure를 자동 추론하거나 벡터 유사도로 관계를 계산하지 않는다. 순환 dependency와 존재하지 않는 ID는 설치 전에 오류로 처리한다.

## Profile과 Add-on

저장소 성격에 맞는 기본 profile은 하나만 선택한다. 선택 기능은 반복 가능한 `--with`로 합성한다.

```bash
node scripts/install.mjs --profile react --host codex
node scripts/install.mjs --profile react --with design-review --host codex
node scripts/install.mjs --profile react --with alignment --host codex --host claude-code
```

규칙은 다음과 같다.

- `--profile`은 필수이며 한 번만 사용한다.
- `--with`는 여러 번 지정할 수 있다.
- `--host`는 하나 이상 명시하며 여러 번 지정할 수 있다.
- profile과 add-on에 중복된 항목은 한 번만 설치한다.
- dependency는 대상보다 먼저 설치한다.
- profile, add-on과 실제 구성원은 catalog에서 명시적으로 관리한다.
- 초기 설치기는 호스트를 자동 감지하지 않는다.

## 설치 흐름

설치 도구는 다음 순서로 동작한다.

1. 하나의 profile과 여러 `--with`를 읽는다.
2. profile, add-on과 명시적 dependency를 합친다.
3. 중복을 제거하고 유효성을 검사한다.
4. 각 항목의 배포 방식과 호스트 provider를 선택한다.
5. `shared`는 `npx skills`의 canonical copy와 symlink 방식을 사용한다.
6. `host-specific`은 해당 호스트에만 설치한다.
7. `host-native`는 내장 기능을 확인하거나 공식 플러그인을 설치한다.
8. 설치, 생략과 실패 결과를 요약한다.

초기 구현은 Node 표준 라이브러리를 사용한다. 긴 abstraction, 범용 plugin framework와 새 runtime dependency를 추가하지 않는다.

### 초기 설치기 상세

초기 설치기는 project scope만 지원한다. `--global`과 `--copy`를 노출하지 않고 `npx skills`의 기본 canonical `.agents/skills` 및 agent별 symlink 동작을 사용한다.

```bash
npm run skills:install -- --profile react --host codex
npm run skills:install -- --profile react --with alignment --host codex --host claude-code
npm run skills:install -- --profile react --host codex --dry-run
```

- `--profile`은 필수이며 한 번만 사용한다.
- `--with`는 add-on과 전역 capability 이름을 받는다.
- `--host`는 필수이며 반복할 수 있다.
- `--dry-run`은 실행할 명령과 host-native 안내를 출력하고 외부 명령을 호출하지 않는다.
- 같은 upstream repository와 host 조합의 연속된 스킬은 하나의 `npx skills add` 명령으로 묶는다.
- `shared`는 모든 요청 host를 `npx skills`의 `--agent`에 전달한다.
- `host-specific`은 해당 항목이 허용한 host만 전달하고 대상이 없으면 생략한다.
- `host-native`의 `builtin` provider는 이미 사용 가능하다고 보고하고 설치하지 않는다.
- shell에서 실행할 수 없는 plugin slash command는 자동 실행하지 않고 수동 명령으로 출력한다.
- 명시적으로 요청한 `claude-code`의 `.claude/`가 없으면 warning을 출력하고 해당 host를 생략한다.
- 요청한 host가 모두 생략되면 외부 명령을 실행하지 않고 오류로 종료한다.
- 외부 명령이 실패하면 즉시 중단하고 종료 코드를 오류로 보고한다.

## 업데이트와 자동화

외부 소스를 보관하지 않으므로 기존의 주간 미러 동기화, lock 파일, 자동 업데이트 PR과 자동 병합은 구현하지 않는다. 외부 스킬 업데이트는 `npx skills`와 각 호스트의 플러그인 관리 기능을 따른다.

카탈로그 항목이 실제로 생긴 뒤 필요하면 매주 다음 상태만 점검할 수 있다.

- upstream 저장소와 스킬 경로가 존재하는가?
- 공식 플러그인과 설치 명령이 유효한가?
- 라이선스 링크가 유효한가?
- 마지막 확인 이후 upstream 변경이 있었는가?

이 작업은 소스 동기화가 아니라 카탈로그 상태 확인이다. 관련 항목은 upstream 저장소 단위로 한 번에 확인한다.

GitHub Actions를 추가할 때는 checkout, runtime 설정과 PR 작업에 기존 Action을 우선 사용한다. workflow 안에 긴 Bash 로직을 작성하거나 기존 Action이 제공하는 기능을 별도 스크립트로 다시 구현하지 않는다.

## 변경 작업과 PR 운영

구현은 아래 단계별로 별도 브랜치와 PR을 사용한다. 하나의 PR은 한 문장으로 설명할 수 있는 변경만 포함한다.

1. 작업 단계에 맞는 `codex/` 브랜치를 만든다.
2. 관련 파일만 수정하고 범위에 맞는 검증을 실행한다.
3. Conventional Commit 형식으로 하나의 일관된 커밋을 만든다.
4. PR 본문에 변경 이유, 범위, 영향과 검증 결과를 간단히 기록한다.
5. Codex 리뷰가 달리면 지적 내용을 그대로 수용하지 않고 현재 설계와 실제 diff를 기준으로 검토한다.
6. 타당한 문제는 같은 PR에서 수정하고 다시 검증한다.
7. 잘못되었거나 적용하지 않을 의견은 근거를 남긴다.
8. 해결되지 않은 문제와 실패한 검사가 없을 때만 PR을 병합한다.

PR을 병합한 뒤 다음 단계의 브랜치와 PR을 시작한다. 여러 단계를 하나의 PR에 미리 묶지 않는다.

## 문서 운영

`docs/DESIGN.md`를 현재 승인된 설계의 SSOT로 유지한다. 목적, 범위, 주요 결정과 전체 흐름은 이 문서만 읽어도 이해할 수 있어야 한다.

세부 설명이 길어질 때만 `docs/design/` 아래에 보조 문서를 추가하고 이 문서에서 연결한다. 조사 결과와 비교 자료는 `research/reports/`에 두어 승인된 설계와 분리한다.

날짜별로 같은 설계 문서를 반복 생성하지 않는다. 중요한 결정이 변경되면 이 문서를 먼저 갱신한다.

## 구현 단계

### 1. 설계 문서 정리

- 미러 중심 설계를 현재 경계로 교체한다.
- README와 외부 카탈로그 설명을 일치시킨다.
- 외부 후보와 설치 데이터는 추가하지 않는다.

### 2. 설치 대상 선정

- 후보를 하나씩 조사한다.
- skill, plugin, command와 tool을 구분한다.
- 중복, 라이선스, 호스트 종속성과 실제 dependency를 확인한다.
- 사용자가 승인한 항목만 등록 대상으로 정한다.

### 3. 최소 Catalog 선언

- 승인된 첫 항목과 profile이 생길 때만 기계 판독 가능한 catalog 파일을 추가한다.
- `shared`, `host-specific`, `host-native`와 provider를 표현한다.
- schema와 유효성 검사도 실제 데이터에 필요한 범위로 제한한다.

### 4. 얇은 설치 도구

- 하나의 `--profile`과 반복 가능한 `--with`를 지원한다.
- `npx skills`와 호스트 공식 설치 명령을 호출한다.
- 공용 SSOT, 호스트 격리, dependency 순서와 반복 실행을 검증한다.

### 5. 개인 스킬 통합 작성 흐름

- 사용자의 지시에 따라 스킬을 하나씩 작성한다.
- `to-skill` 하나에서 portable 작성, 기존 사본 정규화와 호스트 노출을 처리한다.
- 호스트별 metadata·invocation·packaging 규칙은 조건부 reference로 분리한다.
- plugin과 개인 marketplace는 배포 요청이 있을 때만 추가한다.

### 6. 선택적 자동화와 분리

- 실제 카탈로그 운영에 필요할 때만 주간 상태 검사를 추가한다.
- 설치 도구가 독립적으로 성장할 때만 별도 CLI 저장소로 분리한다.

## 초기 후보 범위

현재 논의한 외부 프로젝트와 스킬은 조사 후보일 뿐 등록 대상이 아니다. 특히 Matt Pocock의 스킬은 `domain-modeling`, `grill-me`, `grill-with-docs`만 우선 후보로 남기고 나머지는 중복 여부를 확인한 뒤 제외할 수 있다.

외부 `skill-creator`는 공용 스킬 후보가 아니라 host-native fallback provider로 취급한다. 직접 만든 `to-skill`은 개인 portable 작성과 양쪽 호스트 노출을 통일하는 별도 계층이다. Ponytail 계열, Vercel 스킬, 명령 파일과 Paperclip은 종류와 배포 방식을 확인한 후 사용자가 하나씩 선택한다.

## 성공 기준

- 외부 스킬 소스가 저장소에 복사되어 있지 않다.
- `skills/`에는 직접 만든 스킬만 들어간다.
- 외부 항목의 출처, 라이선스, 종류와 설치 방법을 카탈로그에서 확인할 수 있다.
- 일반 소비 프로젝트의 공용 스킬은 `.agents/skills` SSOT와 Claude symlink를 사용한다.
- 호스트 전용 스킬은 다른 호스트에 노출되지 않는다.
- 같은 논리 기능을 호스트별 provider로 연결할 수 있다.
- 사용자는 `to-skill` 하나로 스킬을 생성, 수정하거나 canonical 구조로 정규화할 수 있다.
- `skill-to-codex`와 `skill-to-claude`는 독립 스킬이나 공개 trigger로 남지 않고 `to-skill`의 조건부 reference로만 존재한다.
- 공용 스킬의 Codex와 Claude Code 설치는 호스트별 물리적 사본 없이 같은 portable 원본을 사용한다.
- 다른 내용을 가진 기존 사본과 잘못된 symlink를 자동으로 덮어쓰거나 삭제하지 않는다.
- 호스트별 adaptation 세부 규칙은 필요할 때만 읽는 reference로 분리된다.
- 이 배포 저장소에서는 `skills/<skill-name>`만 원본으로 사용하고 `to-skill`이 `.agents/skills` 복제본이나 `.claude/skills` symlink를 만들지 않는다.
- 호스트 plugin과 marketplace는 명시적인 배포 요청이 있을 때만 생성된다.
- profile 하나와 여러 `--with`를 조합할 수 있다.
- 실제 dependency와 편의상 묶은 add-on이 구분된다.
- 설치 도구는 기존 CLI와 공식 플러그인 기능을 재사용한다.
- 각 구현 단계가 독립된 PR로 검토되고, 해결되지 않은 리뷰 문제 없이 병합된다.
- 초기 범위에는 미러링 시스템, 자체 package manager와 불필요한 dependency가 없다.
