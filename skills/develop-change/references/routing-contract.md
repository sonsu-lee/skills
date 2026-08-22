# 공통 routing 계약

적용 상태: 저장소 계약 초안. 현재 runtime에서는 사용하지 않는다.

Routing은 **지금 무슨 일을 하는지**와 **얼마나 조심해서 해야 하는지**를 정한다.

쉽게 말하면 다음 두 질문에 답하는 계약이다.

1. 지금은 이해·설계·수정·검증 중 무엇을 하는가?
2. 이 일은 바로 처리해도 되는가, 조금 조사해야 하는가, 구조적 검토가 필요한가?

Routing은 방향만 정한다. 파일 변경, commit, push 같은 권한은 주지 않는다.

## 사용 순서

1. 현재 활동 하나를 `primary_route`로 고른다.
2. 이어서 필요한 활동을 `route_plan`에 순서대로 적는다.
3. 아래 hard floor를 확인해 `direct / bounded / architectural` 중 하나를 고른다.
4. 모르는 hard floor가 있으면 숨기지 말고 `provisional`로 남긴다.
5. gate에서 지금 진행 가능한지 판단한다.
6. 실제 쓰기나 외부 효과가 필요하면 별도의 authorization을 확인한다.
7. 새 근거·범위 변화가 생기면 다음 효과 전에 다시 판단한다.

## Route: 지금 하는 일

| route | 사람이 이해할 말 |
| --- | --- |
| `understand` | 요청과 현재 상태를 이해한다 |
| `shape` | 문제와 범위를 정리한다 |
| `decide` | 선택지를 비교하고 결정을 내린다 |
| `design` | 구현 전에 구조와 계약을 설계한다 |
| `diagnose` | 원인을 찾는다 |
| `change` | 승인된 범위를 실제로 바꾼다 |
| `verify` | 결과와 회귀를 확인한다 |
| `deliver` | commit, PR 등으로 결과를 전달한다 |
| `operate` | 배포·운영 상태를 다룬다 |
| `evolve` | 운영 결과를 바탕으로 다시 개선한다 |

보통은 `diagnose → change → verify`, `design → change → verify → deliver`처럼 흐른다. 이 순서는 자동 권한 사슬이 아니다. 예를 들어 진단을 마쳤다고 수정해도 되는 것은 아니고, 검증을 마쳤다고 push해도 되는 것도 아니다 (`FND-ROUTE-002`).

`route_plan`은 위 표의 단계 순서를 유지하면서 필요 없는 route만 생략한다. 완료한 단계로 되돌아가는 순서나 `verify → change`처럼 역전된 계획은 새 계획과 handoff로 다시 기록한다.

## Profile: 얼마나 조심할 일인가

작은 일을 크게 만들지 말고, 큰 일을 작은 일처럼 취급하지도 않는다.

| profile | 언제 쓰나 |
| --- | --- |
| `direct` | 결과가 정확하고, 기존 의미를 기계적으로 보존하며, 영향이 한 로컬 경계에 있고, 즉시 검증·복구할 수 있을 때 |
| `bounded` | 구조적 hard floor는 없지만 조사·조율·비기계적 판단이 조금 필요할 때 |
| `architectural` | 도메인 규칙, 공개 계약, 신뢰 경계, runtime dependency, 여러 시스템 owner, 데이터 전이, 운영 blast radius 중 하나라도 걸릴 때 |

다음 일곱 축을 확인한다.

`domain_rule / public_contract / trust_boundary / runtime_dependency / multi_system_owner / data_transition / operational_blast_radius`

- 하나라도 `true`이면 `architectural`이다.
- `true`는 없지만 모르는 축이 있으면, 읽기 전용 조사 중에는 `bounded / provisional`로 진행할 수 있다.
- 결정·설계 확정·로컬 변경·외부 효과 직전까지 모르는 축이 남으면 `architectural / provisional`로 올리고 gate를 다시 본다.
- 모든 축이 `false`이고 아래 direct 조건이 전부 맞을 때만 `direct / confirmed`다.

Direct 조건은 결과가 정확함, 구조적 미확정 없음, 단일 로컬 효과 경계, 기존 의미를 보존하는 기계적 변경, 쉬운 복구, 좁고 즉시 가능한 검증, rollout·migration·운영 없음이다 (`FND-PROFILE-001`, `FND-PROFILE-002`).

Runtime dependency가 dev/test 전용이라는 이유만으로 자동으로 작게 보지 않는다. production artifact, runtime, CI 계약, 배포·license·security 책임이 그대로이고 단순 제거와 기존 검증으로 되돌릴 수 있을 때만 구조적 축을 `false`로 둘 수 있다 (`FND-PROFILE-003`).

## 예시

### 오타 한 줄 수정

- route: `change → verify`
- profile: `direct / confirmed`
- 이유: 의미 변화가 없고 즉시 검증·복구할 수 있다.
- 주의: `direct`여도 local change 권한은 별도로 필요하다.

### 실패 원인만 조사

- route: `diagnose`
- profile: 보통 `bounded / confirmed`
- 행동: 로그와 코드를 읽고 원인을 설명한다.
- 주의: 사용자가 fix까지 요청하지 않았다면 `change`로 넘어가지 않는다.

### 공개 API와 데이터 형식 변경

- route: `understand → decide → design → change → verify → deliver`
- profile: `architectural`
- 이유: `public_contract`와 `data_transition`이 hard floor다.

## 꼭 지킬 경계

- 파일 수, diff 크기, 예상 시간, 키워드, 숫자형 risk score만으로 profile을 고르지 않는다 (`FND-ROUTE-001`).
- route가 바뀌어도 profile을 초기화하지 않는다. 새 근거나 scope 변화가 있을 때만 다시 계산한다 (`FND-PROFILE-004`).
- `direct`는 절차를 줄일 수 있다는 뜻이지 권한이 있다는 뜻이 아니다.
- `architectural`은 ADR, 문서 수정, commit 또는 외부 쓰기 승인이 아니다.
- leaf skill마다 이 계약을 복사하지 않는다. 공통 계약을 읽고 같은 의미를 사용한다.

## 기계 계약

정확한 enum, 필드, revision, evidence reference, canonical digest와 전이 조건은 [foundation-contract.schema.json](./foundation-contract.schema.json)의 `routing` 정의와 validator가 소유한다. Routing·gate·authorization reference는 exact ID/revision/digest로 서로 결박한다.

이 초안은 schema·fixture·validator 입력일 뿐 current skill catalog나 runtime을 바꾸지 않는다. `develop-change/SKILL.md` 생성과 invocation·task·leaf·effect·rollout 계약은 이 PR의 범위 밖이다 (`FND-RUNTIME-001`).
