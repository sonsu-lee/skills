# Compact handoff 계약

적용 상태: 활성화 전 설계 계약.

Handoff는 전체 대화를 복사하지 않고 다음 실행이 안전하게 재개되는 데 필요한 현재 상태만 전달한다.

## 필수 필드

| 필드 | 내용 |
| --- | --- |
| `objective` | 사용자가 기대하는 결과와 종료 지점 |
| `scope` | 포함·제외 대상과 현재 변경 경계 |
| `completed_phase` | 마지막으로 완료한 route. 첫 route도 끝나지 않았으면 `null` |
| `primary_route` | 현재 실행하거나 재개할 route |
| `route_plan` | 아직 남은 단계를 판별할 수 있는 전체 canonical route 계획 |
| `decisions` | 확정된 중요한 선택, 근거와 재검토 조건 |
| `artifacts` | 생성·변경한 파일, 문서, commit 또는 PR의 식별자 |
| `effect_binding` | 현재 task, 실행 capability, target과 basis fingerprint |
| `profile` | 현재 direct/bounded/architectural level과 confirmed/provisional 상태 |
| `foundation_binding` | current routing·gate·frontier의 canonical identity와 실제 record, current leaf까지의 authorization record·evaluation lineage |
| `skill_resolution` | 선택·조합·제외·fallback한 전문 스킬과 이유 |
| `authorization` | 현재 capability 상태와 더 이상 재사용할 수 없는 grant |
| `verification` | 실행한 검사, 결과와 실행하지 못한 검사 |
| `blockers` | 다음 효과를 막는 현재 frontier unit |
| `next_action` | 다음 한 단계와 재개 조건 |
| `next_action_kind` | `continue`, `clarify`, `reauthorize`, `report` 중 foundation gate와 결박된 행동 종류. 다음 행동이 없으면 `null` |

`authorization`은 capability 이름과 상태만 복사하지 않는다. 각 항목에 current authorization record의 식별자와 target·scope·basis fingerprint, `runtime_eligible`을 함께 남긴다. 기록에 없는 capability는 승인되지 않은 것으로 취급한다.

## 갱신 규칙

- phase가 끝나거나 scope, decision, authorization, skill resolution이 바뀌면 successor를 만든다 (`HANDOFF-001`).
- `completed_phase: null`은 계획의 첫 route를 시작했지만 아직 완료하지 않은 상태에서만 쓴다 (`HANDOFF-001`).
- 오래된 grant, 해결된 blocker와 폐기된 artifact를 현재 값처럼 남기지 않는다 (`HANDOFF-002`).
- 경로·명령·PR URL처럼 재개에 필요한 식별자는 정확히 남긴다 (`HANDOFF-003`).
- 검증하지 않은 내용을 완료로 표현하지 않는다 (`HANDOFF-004`).
- 실패한 검증이 하나라도 남아 있으면 deliver route로 진행하지 않고 gate를 blocked로 유지한다 (`HANDOFF-004`).
- 비밀정보, 토큰, 전체 로그와 불필요한 대화 원문은 포함하지 않는다 (`HANDOFF-005`).
- orchestration record 안에 함께 저장할 때 objective, scope, primary route, route plan, decisions, effect binding, profile, foundation binding, skill resolution, authorization, verification과 blocker는 최상위 현재 상태와 동일해야 한다 (`HANDOFF-002`).
- 아직 끝나지 않은 route가 있으면 gate 결과와 관계없이 비어 있지 않은 `next_action`을 남긴다 (`HANDOFF-001`).
- 미완료 handoff의 `next_action_kind`는 `continue`다. blocked handoff도 foundation gate가 로컬 조사를 계속하도록 `continue`를 내리면 그대로 보존하고, `clarify`·`reauthorize`도 그대로 쓴다. 그 밖의 terminal blocker는 `report`를 쓴다 (`HANDOFF-001`).
- 마지막 route가 완료되고 foundation gate의 `work_remaining`이 `false`이면 `next_action`과 `next_action_kind`를 모두 `null`로 둔다 (`HANDOFF-001`).
- 마지막 route가 끝난 상태가 아니면 `primary_route`는 `completed_phase` 바로 다음 계획 단계여야 한다 (`HANDOFF-001`).
- `foundation_binding`의 routing·gate·frontier·authorization snapshot은 foundation semantic validator를 통과해야 하며, routing과 gate의 `work_remaining`은 현재 route 진행 상태와 일치해야 한다.

## 최소 예시

전체 필드와 canonical digest를 가진 회귀 예시는 [`evals/orchestration-record-cases.json`](../evals/orchestration-record-cases.json)의 `base_record.handoff`다. 이 값은 `fixture_only: true`인 synthetic grant를 사용하므로 case runner의 fixture opt-in에서만 통과하며, 일반 `--input` runtime authorization 예시로 사용할 수 없다.

아래는 blocked authorization handoff의 핵심 projection이다. 독립된 전체 record가 아니라, authorization frontier unit과 다음 행동을 기록하는 형태만 보여 준다.

```yaml
foundation_binding:
  fixture_only: false
  routing_ref: {id: routing.payment-alert, revision: 2, digest: <canonical-routing-digest>}
  routing_record:
    # foundation routingEnvelope의 전체 current record
    authorization_ref: {id: authorization.payment-alert.push, revision: 1, digest: <canonical-authorization-digest>}
  gate_ref: {id: gate.payment-alert, revision: 2, digest: <canonical-gate-digest>}
  gate_record:
    result: blocked
    blocker: missing_authorization
    next_action: reauthorize
    work_remaining: true
    # foundation gateEnvelope의 나머지 필드
  frontier_ref: {id: frontier.payment-alert, revision: 3, digest: <canonical-frontier-digest>}
  frontier_record:
    units:
      - unit_id: unit.payment-alert.push
        gap_kind: authorization
        state: pending
        authorization_id: authorization.payment-alert.push
        value_binding: null
        runtime_disposition:
          resolution_action: request_input
          defer_effect: blocks_dependent_scope
          gate_result: blocked
          blocker: missing_authorization
          next_action: reauthorize
          interaction_kind: authorization
          interaction_requirement: required
          interaction_owner: user
          progress: await_input
  authorization_records:
    - authorization_id: authorization.payment-alert.push
      status: not_granted
      runtime_eligible: false
      future_only: false
      fixture_only: false
      # target·scope·basis와 revision/receipt 필드
  authorization_evaluations:
    - selected_authorization_id: authorization.payment-alert.push
      side_effect_intent: dependent
      derived_result: blocked_missing_authorization
      next_action: reauthorize
      dependent_side_effect_count: 0
blockers:
  - missing_authorization
next_action: push capability 재승인 요청
next_action_kind: reauthorize
```
