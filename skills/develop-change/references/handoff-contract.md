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
| `foundation_binding` | current gate·frontier의 canonical identity와 실제 record, authorization record·evaluation |
| `skill_resolution` | 선택·조합·제외·fallback한 전문 스킬과 이유 |
| `authorization` | 현재 capability 상태와 더 이상 재사용할 수 없는 grant |
| `verification` | 실행한 검사, 결과와 실행하지 못한 검사 |
| `blockers` | 다음 효과를 막는 현재 frontier unit |
| `next_action` | 다음 한 단계와 재개 조건 |

`authorization`은 capability 이름과 상태만 복사하지 않는다. 각 항목에 current authorization record의 식별자와 target·scope·basis fingerprint, `runtime_eligible`을 함께 남긴다. 기록에 없는 capability는 승인되지 않은 것으로 취급한다.

## 갱신 규칙

- phase가 끝나거나 scope, decision, authorization, skill resolution이 바뀌면 successor를 만든다 (`HANDOFF-001`).
- `completed_phase: null`은 계획의 첫 route를 시작했지만 아직 완료하지 않은 상태에서만 쓴다 (`HANDOFF-001`).
- 오래된 grant, 해결된 blocker와 폐기된 artifact를 현재 값처럼 남기지 않는다 (`HANDOFF-002`).
- 경로·명령·PR URL처럼 재개에 필요한 식별자는 정확히 남긴다 (`HANDOFF-003`).
- 검증하지 않은 내용을 완료로 표현하지 않는다 (`HANDOFF-004`).
- 비밀정보, 토큰, 전체 로그와 불필요한 대화 원문은 포함하지 않는다 (`HANDOFF-005`).
- orchestration record 안에 함께 저장할 때 objective, scope, primary route, route plan, decisions, effect binding, profile, foundation binding, skill resolution, authorization, verification과 blocker는 최상위 현재 상태와 동일해야 한다 (`HANDOFF-002`).
- 아직 끝나지 않은 route가 있으면 gate 결과와 관계없이 비어 있지 않은 `next_action`을 남긴다 (`HANDOFF-001`).

## 최소 예시

```yaml
objective:
  summary: 결제 실패 알림 구현
  finish_line: Draft PR 전달
scope:
  include:
    - API 오류 분류
    - UI 알림
    - 회귀 테스트
  exclude:
    - 결제 제공자 변경
completed_phase: verify
primary_route: deliver
route_plan: [understand, design, change, verify, deliver]
decisions:
  - summary: 기존 error code를 공개 계약으로 유지
    reason: 기존 클라이언트 호환성을 보존한다
    reconsider_when: 공개 API version이 바뀔 때
artifacts:
  - src/payments/error.ts
effect_binding:
  logical_task_id: task.payment-alert
  capability: push
  target_fingerprint: cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc
  basis_fingerprint: dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd
profile:
  level: bounded
  confidence: confirmed
foundation_binding:
  gate_ref:
    id: gate.payment-alert
    revision: 2
    digest: bd17db229dd12b57adc8806ca18344d5c1830cc8efe9453f93910d3997579222
  frontier_ref:
    id: frontier.payment-alert
    revision: 3
    digest: e30ec63c8e285bd79a969933517b2b94b22e5092c103c64b3e3303e56ed07adf
  gate_record:
    gate_id: gate.payment-alert
    revision: 2
    routing_ref:
      id: routing.payment-alert
      revision: 2
      digest: eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee
    result: blocked
    blocker: missing_authorization
    next_action: reauthorize
    progress: await_input
    work_remaining: true
    missing_evidence_owner: user
    assumption_effect: none
    blocking_defer: true
  frontier_record:
    frontier_id: frontier.payment-alert
    revision: 3
    logical_task_id: task.payment-alert
    basis_fingerprint: dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd
    visible_unit_ids: [unit.payment-alert.push]
    units:
      - unit_id: unit.payment-alert.push
        revision: 1
        predecessor_unit_ref: null
        successor_unit_ref: null
        gap_kind: authorization
        state: pending
        basis_fingerprint: dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd
        affected_scope: ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
        checkpoint_relevance: current
        dependency_ids: []
        value_binding: null
        safe_default_conditions: []
        authorization_id: null
        runtime_disposition: null
    clarification_view_history: []
    clarification_view: null
  authorization_record: null
  authorization_evaluation: null
skill_resolution:
  status: pass
  decisions: []
  planned_capabilities: []
  fallback: 프로젝트 규칙과 기본 TypeScript 구현 능력
authorization: []
verification:
  passed:
    - npm test -- payments
  failed: []
  not_run:
    - 전체 e2e는 로컬 제공자 부재
blockers:
  - branch_create·branch_switch·stage·commit·push·pr_create 권한 없음
next_action: 필요한 Git capability 재승인 요청
```
