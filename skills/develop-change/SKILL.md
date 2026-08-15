---
name: develop-change
description: "명시 호출로 하나의 소프트웨어 변경을 이해·설계·구현·검증·전달까지 오케스트레이션하고, 프로젝트 규칙과 사용자가 만든 스킬·설치된 전문 스킬을 경합 없이 조합한다. 사용자가 여러 개발 단계를 하나의 흐름으로 진행하거나 구현부터 테스트와 Draft PR까지 이어 달라고 할 때 사용한다. 단일 기술 지식 조회, 제품 문서 변환만 하는 요청, Git 작업만 하는 요청에는 사용하지 않는다."
---

# Develop Change

하나의 변경 목표를 필요한 단계만 거쳐 검증 가능한 결과와 재개 지점으로 만든다. 제어 평면을 제공하되, 특정 언어·DB·프레임워크의 세부 규칙을 범용 정답처럼 내장하지 않는다.

## 1. 핵심 계약을 읽는다

모든 호출에서 다음 reference를 처음부터 끝까지 읽는다.

- [오케스트레이션 계약](references/orchestration-contract.md): 단계, 책임과 완료 조건
- [Routing 계약](references/routing-contract.md): route와 direct/bounded/architectural profile
- [Gate 계약](references/gate-contract.md): decision frontier, 조사·질문·blocker
- [Authorization 계약](references/authorization-contract.md): local change, 문서, Git, 외부 효과의 독립 권한

사용자가 만든 스킬을 명시했거나 현재 구현에 언어·프레임워크·DB·테스트·보안 전문 규칙이 필요하면 [스킬 해석과 경합 계약](references/skill-resolution-contract.md)을 읽는다. 둘 이상의 phase를 거치거나 작업이 중단될 수 있거나 commit·PR까지 요청되었으면 [Compact handoff 계약](references/handoff-contract.md)을 추가로 읽는다.

## 2. 목표와 종료 지점을 고정한다

다음을 현재 저장소와 요청에서 직접 확인한다.

- 원하는 동작과 사용자에게 보이는 결과
- 포함·제외 범위
- 완료 지점: 이해, 설계, 구현, 검증, commit, Draft PR 또는 운영 단계
- 적용되는 `AGENTS.md`, `CLAUDE.md`, README, contribution·CI·보안 규칙
- 현재 branch, dirty 변경, 관련 코드·테스트·문서와 검증 명령

저장소에서 확인할 수 있는 사실을 사용자에게 묻지 않는다. 결과를 바꾸는 선택이나 사용자만 가진 근거가 없을 때만 현재 frontier의 질문을 묶어 제시한다.

## 3. Route, profile과 gate를 정한다

1. 현재 활동을 `primary_route`로 정하고 필요한 후속 활동만 `route_plan`에 둔다.
2. 구조적 hard floor를 확인해 `direct`, `bounded`, `architectural`을 정한다.
3. 현재 decision frontier를 조사하고 `pass`, `conditional`, `blocked`를 계산한다.
4. scope나 근거가 달라지면 다음 효과 전에 다시 계산한다.

작고 명확한 변경은 불필요한 discovery·ADR·ticket 문서를 만들지 않는다. 공개 계약, 데이터 전이, 신뢰 경계, runtime dependency나 운영 blast radius가 걸리면 파일 수가 적어도 architectural로 다룬다.

## 4. 구현 지식과 스킬을 해석한다

현재 route에 필요한 후보만 확인한다.

1. 시스템·개발자 지침과 프로젝트 규칙을 binding constraint로 고정한다.
2. 사용자가 특정 스킬을 명시했으면 실제로 사용 가능한지 확인하고 전체 지침을 읽는다.
3. 저장소에 포함되거나 현재 세션에 설치된 관련 스킬이 있으면 현재 기술·버전·도구와의 호환성을 확인한다.
4. 책임이 보완적이면 적용 순서와 경계를 정해 함께 사용한다.
5. 책임이 겹치면 사용자 지정, 저장소 적합성, 구체성, 호환성과 추적 가능한 근거로 하나를 선택한다.
6. 스킬과 프로젝트 규칙이 충돌하면 프로젝트 규칙을 적용하고 충돌 부분을 제외한다.
7. 결과를 바꾸는 경합을 근거로 해소할 수 없으면 material decision으로 막는다.

관련 스킬을 찾지 못하면 다음 순서로 처리한다.

- 프로젝트의 현재 코드·문서·설정
- 최신성이 필요한 경우 공식 라이브러리·프레임워크 문서
- Codex의 기본 구현 능력과 저장소 관례

사용자가 탐색·설치를 요청하지 않았다면 새 스킬이나 플러그인을 임의 설치하지 않는다. TypeScript, 프런트엔드, DB/ORM, 테스트·품질, 보안·운영 확장점에 실제 스킬이 없으면 `planned capability`로만 기록하고 선택된 스킬처럼 표현하지 않는다.

## 5. 필요한 전문 단계를 결합한다

현재 단계에 실제로 필요할 때만 다음 스킬을 사용한다.

| 필요 | companion skill |
| --- | --- |
| 제품 문제·사용자·범위·성공 기준이 열려 있음 | `product-discovery` |
| 중요한 기술 대안과 trade-off가 열려 있음 | `architecture-decisions` |
| 여러 원문의 교차 검증이 결과를 좌우함 | `research` |
| 합의된 제품 컨텍스트를 PRD로 남김 | `to-prd` |
| 용어·상태·업무 규칙을 정본화함 | `domain-modeling` |
| 내려진 기술 결정을 ADR로 남김 | `to-adr` |
| 승인된 큰 계획을 실행 단위로 나눔 | `to-tickets` |
| Agent Skill 자체를 개발·검증함 | `develop-skill` |
| branch·commit·push·PR을 준비·생성함 | `git-workflow` |

companion skill을 선택했다는 사실은 그 스킬의 상태 변경 권한이 아니다. 각 스킬의 지침과 사용자 요청 범위가 모두 허용하는 행동만 수행한다.

## 6. 변경한다

- 현재 프로젝트의 구조, 타입, 오류 처리, 데이터 경계와 기존 패턴을 먼저 따른다.
- 적용 가능한 구현 스킬이나 공식 문서가 있으면 그 범위의 규칙을 사용한다.
- 증상을 가리는 우회보다 확인된 원인을 해결한다.
- 공개 API, schema, migration과 사용자 동작이 바뀌면 관련 문서를 같은 변경에서 맞춘다.
- DB 변경은 transaction 경계, migration 순서, index·query 영향, rollback과 데이터 호환성을 확인한다.
- 관계없는 dirty·untracked 변경을 수정, 정리, stage 또는 게시하지 않는다.
- 범위가 커지면 기존 승인을 재사용하지 않고 gate와 authorization을 다시 확인한다.

## 7. 검증한다

변경과 가장 가까운 검사부터 넓힌다.

1. 변경된 로직을 직접 검증하는 단위·회귀 테스트
2. 관련 typecheck, lint와 정적 검사
3. 필요한 build·통합·migration 검사
4. UI가 바뀌면 실제 렌더링과 상호작용의 시각 확인
5. README의 설치·실행·사용 예시와 실제 코드·설정의 일치
6. base와 비교한 최종 diff에서 범위 이탈, 비밀정보와 불필요한 추상화 확인

실행하지 못한 검사는 실행한 것처럼 표현하지 않고 이유와 남은 위험을 남긴다.

## 8. 요청된 방식으로 전달한다

사용자가 branch, commit, push 또는 PR을 요청했으면 `git-workflow`를 적용하고 각 capability를 독립적으로 확인한다. 스택 PR을 명시했고 현재 환경에 스택 도구·스킬이 있으면 foundation에서 integration 순서의 선형 stack을 사용한다. 사용할 수 없으면 일반 PR을 스택처럼 꾸미지 말고 정확한 제한을 알린다.

merge, rebase, history rewrite, force-push, branch 삭제와 배포는 사용자가 별도로 요청하고 해당 workflow가 지원할 때만 수행한다.

## 9. Handoff와 결과를 남긴다

다음을 간결하게 보고한다.

- 완료한 결과와 사용자에게 보이는 변화
- 포함·보존한 범위
- route와 마지막 완료 phase
- 적용·제외·fallback한 스킬과 경합 판단
- 중요한 결정과 재검토 조건
- 변경한 artifact, commit과 PR 식별자
- 실행한 검증, 실패와 미확인 항목
- 남은 blocker와 다음 한 단계

완료 조건: 요청된 종료 지점까지 결과가 검증되었거나 정확한 blocker가 기록되고, 실제 효과가 현재 권한을 벗어나지 않으며, 다음 작업이 handoff만으로 안전하게 재개된다.

최종 사용자 응답에는 `present-result`를 마지막 표현 단계로 적용한다. 독립 설치에서 사용할 수 없으면 이 스킬의 고정 출력 형식과 필수 필드를 그대로 둔 채 자유 서술 영역에서만 결론·영향·다음 행동을 쉬운 말로 쓴다. 어느 경로에서도 판정·근거·권한·ID와 산출물은 바꾸지 않는다.
