# 스킬 해석과 경합 계약

적용 상태: 활성화 전 설계 계약.

Skill resolver는 현재 작업에 필요한 전문 지침을 선택한다. 스킬을 많이 로드하는 것이 목표가 아니며, 동일 책임을 가진 지침을 무조건 합치지 않는다.

## 입력

- 현재 `route`와 `profile`
- 사용자가 명시한 스킬
- 프로젝트의 `AGENTS.md`, `CLAUDE.md`, README와 설정
- 현재 세션에서 실제로 사용 가능한 스킬 목록과 호출 정책
- 설치·호환성·도구 의존성·출처를 확인할 수 있는 후보
- 활성 authorization과 decision frontier

## 판정 순서

1. 시스템·개발자 지침과 프로젝트 규칙을 binding constraint로 고정한다 (`RESOLVE-001`).
2. 사용자가 명시한 스킬을 찾고 현재 환경에서 실제로 읽고 사용할 수 있는지 확인한다 (`RESOLVE-002`).
3. 현재 route에 직접 기여하는 후보만 남긴다 (`RESOLVE-003`).
4. 후보마다 책임, 구체성, 버전·프레임워크 호환성, 필요한 도구, 출처와 effect boundary를 기록한다 (`RESOLVE-004`).
5. 아래 경합 규칙으로 `selected / composed / rejected / blocked / fallback` 중 하나를 결정한다 (`RESOLVE-005`).
6. 선택된 스킬이 요구하는 reference와 선행조건을 적용하되, 사용자 권한을 넓히지 않는다 (`RESOLVE-006`).

플러그인이 제공하는 스킬은 런타임에서 노출된 canonical ID를 그대로 기록한다. 예를 들어 `skills:git-workflow`나 `github:github`의 namespace를 제거하지 않아 서로 다른 플러그인의 동명 스킬을 합치지 않는다.

## 후보 우선순위

우선순위는 무조건적인 승자 순서가 아니라 동률 해소 기준이다.

1. 사용자가 현재 요청에서 명시한, 사용 가능한 스킬
2. 현재 저장소가 함께 버전 관리하는 프로젝트 전용 스킬
3. 설치되어 있고 현재 기술·버전·도구와 호환되는 전문 스킬
4. 공식 문서나 프로젝트가 고정한 원문
5. 호스트의 기본 구현 능력과 저장소 관례

더 높은 후보라도 프로젝트 binding constraint를 위반하거나 현재 버전과 호환되지 않으면 선택하지 않는다.

## 경합 처리

| 관계 | 처리 |
| --- | --- |
| 책임이 서로 보완적 | 적용 순서와 각 책임을 정해 `composed` |
| 같은 책임, 한 후보가 더 구체적·호환됨 | 더 구체적인 하나를 `selected`, 다른 후보는 이유와 함께 `rejected` |
| 스킬과 프로젝트 규칙 충돌 | 프로젝트 규칙을 적용하고 스킬의 충돌 부분을 제외 |
| 사용자가 명시한 스킬이 없음 | 임의 대체를 숨기지 않고 fallback 또는 blocker를 공개 |
| 설치·도구·버전이 맞지 않음 | 호환되지 않는 후보를 제외하고 공식 원문 또는 기본 능력으로 fallback |
| 결과를 바꾸는 충돌을 해소할 근거가 없음 | `blocked`로 두고 material decision을 요청 |

## 설치와 외부 탐색

- 사용자가 설치 또는 탐색을 요청하지 않았다면 새 스킬이나 플러그인을 임의 설치하지 않는다.
- 이미 사용 가능한 관련 스킬은 해당 스킬의 지침을 완전히 읽고 적용한다.
- 특정 제품·라이브러리·프레임워크 규칙이 최신성에 민감하면 공식 문서를 우선한다.
- 외부 스킬을 사용하려면 출처, 현재 버전·도구 호환성과 작업 범위를 확인한다.
- 안전하게 검증하지 못한 외부 지침은 authoritative rule로 승격하지 않는다.

## Planned capability

아래 식별자는 확장점을 설명할 뿐 현재 스킬 ID가 아니다.

- `typescript-javascript-practices`
- `frontend-framework-practices`
- `database-orm-practices`
- `testing-quality-practices`
- `security-operations-practices`

실제 후보가 등록되기 전에는 `skill_id`를 만들거나 `selected`로 기록하지 않는다 (`RESOLVE-007`).
