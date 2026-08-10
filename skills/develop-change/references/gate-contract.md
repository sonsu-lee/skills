# 공통 gate와 decision frontier 계약

상태: `candidate-only draft`

schema version: `phase1-foundation-draft-v1`

설계 기준선: `29f39ef1d0418d78542eb4d966b7bea1201eb376d40894610ec758bcf1b19aec`
근거: DEC-010, DEC-045, DEC-049와 `workflow-architecture.md` §8

Gate는 **지금 계속해도 되는지**, **무엇을 먼저 알아야 하는지**, **누구에게 물어야 하는지**를 정한다.

핵심은 질문을 많이 만드는 것이 아니다. 에이전트가 확인할 수 있는 사실은 직접 확인하고, 사용자만 결정할 수 있는 현재 질문만 한 번에 묻는다.

## 사용 순서

1. 아직 풀리지 않은 항목을 frontier unit으로 적는다.
2. 각 항목이 사실 조사, 사용자 근거, 사소한 선호, 중요한 결정, 권한, 외부 blocker 중 무엇인지 분류한다.
3. 다른 항목에 의존하지 않는 **현재 frontier**만 고른다.
4. 로컬에서 안전하게 확인할 수 있는 사실은 먼저 조사한다.
5. 사용자 입력이 필요한 현재 질문은 한 번의 clarification view로 묶는다.
6. 답이 일부만 오면 답한 항목만 닫고, 남은 항목으로 새 view를 만든다.
7. frontier가 바뀔 때마다 top-level gate를 다시 계산한다.

## Gate 결과

| 결과 | 뜻 | 다음 행동 |
| --- | --- | --- |
| `pass` | 현재 blocker가 없다 | `continue` 또는 완료 |
| `conditional` | 결과를 바꾸지 않는 안전한 가정을 공개하고 진행한다 | `continue` |
| `blocked` | 현재 효과를 내기 전에 해결할 항목이 있다 | 조사, 질문, 재승인 또는 대기 |

주요 blocker는 다음과 같다.

- `missing_evidence`: 근거가 부족하다. 로컬에서 찾을 수 있으면 조사하고, 사용자만 알면 질문한다.
- `missing_decision`: 결과를 바꾸는 선택이 남았다. 추천안과 영향을 함께 제시하고 질문한다.
- `missing_authorization`: 필요한 capability가 없거나 stale하다. 재승인을 요청한다.
- `scope_expansion`: 기존 승인 범위를 벗어난다. 새 범위를 분리해 승인받는다.
- `external_dependency`: 현재 작업 안에서 풀 수 없는 선행조건이다. blocker를 보고한다.

`pass`인데 blocker가 있거나, authorization 문제를 일반 clarification으로 보내거나, 중요한 결정을 임의 가정하는 조합은 금지한다 (`FND-GATE-001`, `FND-GATE-002`).

## 무엇을 묻고 무엇을 직접 확인하나

| 항목 | 기본 행동 |
| --- | --- |
| `discoverable_fact` | 코드·문서·도구로 직접 조사한다 |
| `user_supplied_evidence` | 사용자가 가진 필수 근거를 요청한다 |
| `incidental_preference` | 결과가 같고 안전하면 가정을 공개하고 진행한다 |
| `material_decision` | 선택지, 영향, 추천안을 보여주고 묻는다 |
| `authorization` | 일반 질문과 섞지 말고 exact capability 재승인을 요청한다 |
| `external_blocker` | 현재 할 수 있는 독립 작업과 막힌 범위를 분리해 보고한다 |

미래에만 필요한 항목은 `future_only`로 미룰 수 있다. 현재 결정을 막는 항목을 미래 일처럼 숨기면 안 된다. 반대로 미래 항목 하나 때문에 지금 가능한 독립 작업까지 막지도 않는다 (`FND-FRONTIER-001`, `FND-FRONTIER-002`).

## 질문은 이렇게 만든다

Grilling 방식처럼 **현재 답할 수 있는 질문만 한 round에 모은다**. 질문 B가 질문 A의 답에 따라 달라지면 A만 먼저 묻는다.

좋은 질문은 다음 정보를 짧게 보여준다.

- 어떤 결정을 내려야 하는가
- 가능한 선택지는 무엇인가
- 각 선택이 결과에 미치는 영향은 무엇인가
- 추천안이 있다면 무엇이고 왜 그런가

예:

> 배포 범위를 정해야 합니다.
>
> A. 내부 사용자만 먼저 활성화 — 되돌리기 쉽고 관측이 빠릅니다. **추천**
>
> B. 전체 활성화 — 한 번에 끝나지만 실패 영향이 큽니다.
>
> 어느 쪽으로 진행할까요?

에이전트가 저장소를 읽으면 알 수 있는 파일 위치, 설정값, 기존 convention은 사용자에게 묻지 않는다. 일부 답만 받았다고 나머지를 답한 것으로 처리하지 않고, 침묵·timeout·`계속`을 결정이나 승인으로 해석하지 않는다 (`FND-FRONTIER-004`).

## 안전한 가정

사소한 선호는 다음 조건이 모두 맞을 때만 가정할 수 있다.

- 이미 승인된 범위 안이다.
- 사용자가 보는 결과와 지속되는 의미가 바뀌지 않는다.
- 외부·파괴적 효과가 없다.
- 쉽게 되돌릴 수 있다.
- 프로젝트 근거가 있다.
- 현재 검증으로 틀린 가정을 발견할 수 있다.

하나라도 `false`이면 중요한 결정·권한·외부 blocker로 다시 분류한다. 모르면 사실 조사나 사용자 근거 요청으로 바꾼다 (`FND-FRONTIER-003`).

## 이력을 잃지 않는다

- frontier unit과 clarification view는 revision을 덮어쓰지 않는다.
- 답변, 근거, stale, scope 변화가 생기면 predecessor를 가리키는 새 revision을 만든다.
- current record는 각 lineage의 마지막 leaf 하나뿐이다.
- authorization unit은 exact current authorization record와 evaluation에 결박한다.
- stale·withdrawn·denied capability가 있으면 dependent side effect는 0건이다 (`FND-FRONTIER-005`, `FND-FRONTIER-006`).

## 기계 계약

정확한 gap/action/state 조합, dependency DAG, top-level aggregate 우선순위, clarification view lifecycle, authorization binding과 canonical digest는 [foundation-contract.schema.json](./foundation-contract.schema.json)의 `gate`와 `frontier` 정의 및 validator가 소유한다.

이 frontier는 질문과 진행 상태를 관리할 뿐 권한을 만들지 않는다. 질문했다는 사실이나 답변 수신 자체는 authorization이 아니다.
