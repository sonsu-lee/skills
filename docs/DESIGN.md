# 개인 스킬 저장소 설계

상태: 승인된 기본 설계
마지막 수정: 2026-07-11

## 목적

이 저장소는 다음 두 종류의 스킬을 한곳에서 배포한다.

1. 사용자가 직접 작성하고 유지보수하는 스킬
2. 외부 upstream을 수정 없이 따라가는 미러 스킬

외부 스킬은 검토된 포크가 아니라 빠르게 최신 상태를 전달하는 의존성 미러다. 저장소는 upstream 변경을 일주일에 한 번 확인하고, 관련 스킬을 그룹 단위로 갱신하는 PR을 만든다. 검사를 통과한 PR은 자동 병합한다.

## 기본 원칙

- 외부 미러 파일은 직접 수정하지 않는다.
- upstream의 추가, 수정, 삭제를 그대로 반영한다.
- 출처, 라이선스와 동기화 commit을 항상 추적할 수 있어야 한다.
- 관련 스킬은 같은 upstream commit을 기준으로 한 번에 갱신한다.
- GitHub Actions가 제공하는 기능은 별도 스크립트로 다시 구현하지 않는다.
- 표준 라이브러리와 기존 CLI로 해결할 수 있는 기능은 새 의존성이나 자체 CLI로 만들지 않는다.
- 설치된 스킬은 `.agents/skills`를 SSOT로 사용하고 에이전트별 경로는 symlink로 연결한다.
- 설계는 `docs/DESIGN.md`를 주 문서로 지속해서 갱신한다.

## 저장소 구조

목표 구조는 다음과 같다.

```text
.
├── skills/
│   ├── owned/
│   │   └── example-skill/
│   └── mirrored/
│       └── example-skill/
├── registry/
│   ├── sources.json
│   └── lock.json
├── catalog/
│   └── README.md
├── third-party/
│   ├── licenses/
│   └── THIRD_PARTY_NOTICES.md
├── scripts/
│   └── sync.mjs
├── tests/
│   └── sync.test.mjs
├── docs/
│   ├── DESIGN.md
│   └── design/
├── .github/
│   └── workflows/
│       ├── sync-upstreams.yml
│       └── validate.yml
├── LICENSE
└── README.md
```

이 구조를 처음부터 모두 만들지는 않는다. 각 파일과 디렉터리는 해당 기능을 구현하는 단계에서만 추가한다.

## 스킬 영역

### `skills/owned`

사용자가 직접 작성하고 유지보수하는 스킬을 보관한다. 내용, 버전과 배포 책임은 이 저장소에 있다.

### `skills/mirrored`

upstream 스킬 디렉터리의 실제 복사본을 보관한다. 이 파일은 설치 대상이며 다음 규칙을 따른다.

- upstream 파일만 둔다.
- 이 저장소 전용 metadata를 섞지 않는다.
- 동기화 과정 외에는 수정하지 않는다.
- upstream에서 삭제된 파일도 다음 동기화 때 삭제한다.

`npx skills`가 기본 탐색할 수 있도록 owned와 mirrored 스킬을 모두 `skills/` 아래에 둔다.

## Catalog와 Registry

### `catalog/README.md`

사람이 스킬을 찾아보기 위한 문서다. 실제 스킬 파일을 포함하지 않고 다음 정보를 보여준다.

- 이름과 설명
- 소속 그룹
- upstream 저장소와 원본 경로
- 라이선스
- 마지막 동기화 commit
- 설치 명령

Catalog는 사람이 직접 수정하지 않는다. Registry와 lock을 기준으로 자동 생성한다.

### `registry/sources.json`

사람이 관리하는 upstream 선언이다. 최상위 단위는 개별 스킬이 아니라 그룹이다. 각 그룹은 다음 정보를 가진다.

- 고유 그룹 ID
- upstream repository
- 하나의 branch, tag 또는 commit ref
- 라이선스 식별자와 원본 라이선스 경로
- 그룹에 포함된 스킬 이름과 upstream 상대경로

초기에는 하나의 그룹이 하나의 upstream repository와 ref만 참조한다. 여러 repository를 하나의 그룹으로 묶는 기능은 실제 필요가 생길 때만 추가한다.

### `registry/lock.json`

동기화 과정이 자동 생성하는 상태다. 그룹별로 다음 정보를 기록한다.

- 실제로 동기화한 upstream commit
- 그룹 구성 스킬의 tree hash
- 마지막 동기화 시각

같은 그룹의 스킬은 항상 같은 upstream commit을 기준으로 기록하고 갱신한다.

## 그룹 단위 동기화

관련 스킬은 같은 upstream repository와 ref 안에서 명시적으로 그룹에 등록한다.

그룹 구성원 중 하나라도 변경되면 다음을 하나의 작업으로 처리한다.

1. 그룹의 upstream ref를 한 번 가져온다.
2. 모든 구성 스킬을 같은 commit에서 읽는다.
3. 그룹 전체의 미러를 갱신한다.
4. lock, catalog와 third-party notice를 갱신한다.
5. 하나의 PR을 생성한다.
6. 그룹 전체 검사가 성공할 때만 자동 병합한다.

구성원 하나를 가져오거나 검사하지 못하면 그룹 전체를 반영하지 않는다. 일부만 새 버전이고 일부는 이전 버전인 상태를 만들지 않는다.

## 동기화 일정

정기 동기화는 매주 월요일 오전 9시 17분 일본 시간에 실행한다.

```yaml
on:
  schedule:
    - cron: "17 0 * * 1"
  workflow_dispatch:
```

정기 실행 외에 `workflow_dispatch`로 수동 동기화를 허용한다. 소유하지 않은 upstream에 webhook 설치를 요구하거나 GitHub App을 운영하지 않는다.

## GitHub Actions 원칙

범용 작업은 기존 Action과 CLI에 맡긴다.

- 저장소 checkout: `actions/checkout`
- Node 환경: `actions/setup-node`
- 스킬 형식 검사: `skills-ref`
- 변경 PR 생성: 유지보수되는 PR 생성 Action
- 자동 병합 설정: 유지보수되는 auto-merge Action
- 실행 일정과 수동 실행: GitHub Actions native trigger

Action은 가능하면 전체 commit SHA로 고정한다. 긴 Bash 로직을 workflow 안에 작성하거나 checkout, PR 생성, 자동 병합을 자체 스크립트로 다시 구현하지 않는다.

프로젝트 전용 코드는 manifest를 읽고 선택한 upstream 경로를 미러에 반영하는 부분으로 제한한다.

## 동기화 코드 원칙

초기 커스텀 코드는 `scripts/sync.mjs` 하나로 시작한다. Node 표준 라이브러리를 우선 사용하며 다음 작업만 담당한다.

1. Registry 읽기
2. 요청한 그룹의 upstream과 source path 확인
3. 그룹 구성 스킬 복사와 삭제 반영
4. lock 갱신
5. catalog와 third-party notice 생성
6. 변경 유무와 실패 지점 보고

작성 규칙은 다음과 같다.

- 꼭 필요한 코드만 작성한다.
- 한 번만 사용하는 abstraction을 만들지 않는다.
- 표준 라이브러리로 충분한 기능에 dependency를 추가하지 않는다.
- 읽기 쉬운 함수와 변수 이름을 사용한다.
- 주석은 코드가 하는 일이 아니라 그 선택이 필요한 이유를 설명할 때만 쓴다.
- 로컬 변경을 자동 stash하거나 조용히 덮어쓰지 않는다.
- 에러를 삼키지 않고 실패한 group, source와 path를 표시한다.
- 파일이 실제로 읽기 어려워질 때만 역할별 모듈로 분리한다.

테스트는 Node 내장 test runner를 사용한다. 별도 테스트 프레임워크는 추가하지 않는다.

최소 검증 범위는 다음과 같다.

- 최초 미러 생성
- upstream 파일 수정 반영
- upstream 파일 삭제 반영
- 반복 실행 시 no-op
- upstream 접근 실패 시 기존 미러 보존
- 그룹 구성원 하나의 실패 시 그룹 전체 미반영
- lock과 catalog 갱신

## PR과 자동 병합

동기화 PR은 그룹별로 생성한다. 제목은 그룹과 새 upstream commit을 식별할 수 있어야 한다.

PR 본문에는 다음을 기록한다.

- upstream repository
- 이전 commit과 새 commit
- upstream 비교 링크
- 갱신된 스킬
- 추가, 변경, 삭제된 파일
- script, hook, MCP 또는 license 변경 여부
- 검사 결과

다음 조건을 모두 만족하면 자동 병합한다.

- upstream repository, ref와 source path가 유효하다.
- 모든 구성원에 유효한 `SKILL.md`가 있다.
- 스킬 이름 충돌이 없다.
- source directory 밖을 가리키는 symlink가 없다.
- 선언된 upstream 라이선스가 존재한다.
- lock과 실제 tree hash가 일치한다.
- 생성한 catalog와 notice가 최신이다.
- 동기화를 다시 실행했을 때 추가 diff가 없다.
- repository 검사가 성공한다.

이 검사는 미러의 구조와 추적 가능성을 보장한다. upstream 콘텐츠의 품질이나 안전성을 이 저장소가 별도로 보증한다는 의미는 아니다.

## 실패와 복구

### Fetch 실패

기존 미러를 유지하고 PR을 만들지 않는다. workflow를 실패 처리하며 빈 결과로 기존 파일을 덮어쓰지 않는다.

### Upstream 삭제

파일 삭제는 그대로 반영한다. 스킬 경로 자체가 사라지면 구조 검사에 실패하고 사람이 Registry를 수정할 때까지 자동 병합하지 않는다.

### 이름 변경

새 스킬로 자동 추정하지 않는다. 기존 경로가 사라진 실패로 처리하고 Registry를 명시적으로 수정한다.

### 잘못된 upstream 변경

마지막 sync PR을 revert하거나 Registry의 ref를 검증된 commit SHA로 임시 고정한다. upstream 문제가 해결되면 원래 추적 ref로 되돌린다.

## 설치 SSOT와 Symlink

프로젝트 설치에서는 `.agents/skills`가 실제 파일을 보관하는 SSOT다.

```text
.agents/skills/example-skill/
.claude/skills/example-skill -> ../../.agents/skills/example-skill
```

전역 설치에서도 같은 구조를 사용한다.

```text
$HOME/.agents/skills/example-skill/
$HOME/.claude/skills/example-skill -> ../../.agents/skills/example-skill
```

초기 설치는 자체 CLI 대신 `npx skills`의 canonical copy와 symlink 방식을 사용한다. 여러 에이전트가 같은 `.agents/skills` 내용을 보게 하고 에이전트별 독립 복사본을 기본값으로 만들지 않는다.

symlink를 지원하지 않는 환경에서는 사용자가 명시적으로 copy mode를 선택해야 한다. 조용한 자동 fallback으로 설치 형태를 섞지 않는다.

자체 CLI는 다음 요구가 실제로 발생할 때 별도 설계한다.

- 설치 preset 또는 group 단위 선택
- 여러 host의 plugin 설치 명령 통합
- 새 기기에서 전체 설치 상태 복원
- 설치 상태와 mirror 상태 통합 진단
- 기존 `npx skills` lock과 update 기능으로 해결되지 않는 재현성

## 문서 운영

`docs/DESIGN.md`를 설계의 SSOT로 유지한다. 목적, 범위, 주요 결정과 전체 흐름은 항상 이 문서만 읽어도 이해할 수 있어야 한다.

세부 내용이 길어질 때만 다음과 같은 보조 문서를 추가한다.

```text
docs/design/sync.md
docs/design/install.md
docs/design/distribution.md
```

보조 문서는 상세 설명만 담당하고 `docs/DESIGN.md`에서 연결한다. 날짜별로 비슷한 설계 문서를 반복 생성하지 않고 기존 문서를 계속 수정한다. 중요한 결정이 뒤집힐 때만 별도 decision 문서를 추가한다.

조사 결과는 `research/reports/`에 두어 승인된 설계와 분리한다.

## 구현 단계

1. `docs/DESIGN.md` 작성과 검토
2. `skills/owned`와 `skills/mirrored` 경계 구성
3. 빈 group Registry와 lock 추가
4. 최소 동기화 스크립트와 내장 테스트 추가
5. Catalog와 third-party notice 생성 연결
6. 주 1회 GitHub Actions 동기화 추가
7. 그룹별 PR 생성과 검사 통과 시 자동 병합 연결
8. `npx skills` symlink 설치 검증
9. 사용자가 선택한 첫 upstream 그룹 등록
10. 실제 사용 결과에 따라 plugin manifest 필요성 판단
11. 기존 도구가 부족할 때만 자체 CLI 설계

초기 등록 대상은 이 설계에서 정하지 않는다. 사용자가 선택한 스킬을 이후 하나씩 조사하고 그룹에 추가한다.

## 성공 기준

- 등록된 그룹이 없어도 동기화가 정상적으로 no-op 처리된다.
- 관련 스킬이 하나의 upstream commit과 하나의 PR로 갱신된다.
- 반복 동기화는 추가 diff를 만들지 않는다.
- upstream 실패가 기존 미러를 훼손하지 않는다.
- 변경이 없으면 PR이 생기지 않는다.
- 검사 실패 PR은 자동 병합되지 않는다.
- 검사 성공 PR은 자동 병합된다.
- mirrored directory에는 upstream 파일 외의 metadata가 없다.
- Catalog만 읽어도 출처, 라이선스, 설치 방법과 동기화 commit을 확인할 수 있다.
- `.agents/skills` 한 곳의 실제 파일을 여러 에이전트가 symlink로 공유한다.
- 초기 구현에는 불필요한 dependency, 자체 package manager와 plugin framework가 없다.
