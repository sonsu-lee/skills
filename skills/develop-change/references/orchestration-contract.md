# develop-change 오케스트레이션 계약

적용 상태: 활성화 전 설계 계약. `develop-change/SKILL.md`가 생기기 전까지 런타임에서 사용하지 않는다.

## 책임

`develop-change`는 변경 작업의 제어 평면만 소유한다. 구현 코드를 대신 정의하는 범용 프레임워크나 TypeScript·DB·UI 규칙 모음이 아니다.

| 계약 ID | 규칙 |
| --- | --- |
| `ORCH-001` | 요청의 목표, 범위와 종료 지점을 먼저 식별한다. |
| `ORCH-002` | routing, profile, gate와 authorization을 서로 다른 판정으로 유지한다. |
| `ORCH-003` | 현재 단계에 필요한 전문 스킬만 선택하고, 선택 이유와 적용 범위를 추적한다. |
| `ORCH-004` | 구현은 프로젝트 규칙과 호스트의 기본 구현 능력을 사용하며, 전문 스킬은 지식·절차를 보완한다. |
| `ORCH-005` | 단계 완료나 스킬 선택을 다음 side effect의 권한으로 해석하지 않는다. |
| `ORCH-006` | 새 근거, 범위 변화 또는 충돌이 생기면 다음 효과 전에 route, gate, resolution과 authorization을 다시 본다. |
| `ORCH-007` | 모든 종료는 검증 결과, 남은 위험과 재개 가능한 handoff를 남긴다. |
| `ORCH-008` | 실제 스킬이 없는 확장점은 `planned capability`로만 기록하고 선택·실행된 스킬처럼 표현하지 않는다. |

## 단계

`understand → shape → decide → design → diagnose → change → verify → deliver`

모든 요청이 모든 단계를 거치지는 않는다.

- 오타처럼 의미를 보존하는 작은 변경: `understand → change → verify`
- 원인 조사만 요청: `understand → diagnose`
- 일반 기능 구현: `understand → design → change → verify`
- 중요한 기술 선택을 포함한 구현과 PR: `understand → decide → design → change → verify → deliver`

단계 이름은 [routing-contract.md](./routing-contract.md)의 route enum을 사용한다. `operate`와 `evolve`가 필요한 요청은 같은 계약으로 확장하되, 운영 효과의 별도 권한을 확인한다.

## 실행 순서

1. [routing-contract.md](./routing-contract.md)를 읽어 `primary_route`, `route_plan`과 profile을 정한다.
2. [gate-contract.md](./gate-contract.md)를 읽어 현재 decision frontier와 blocker를 계산한다.
3. [authorization-contract.md](./authorization-contract.md)를 읽어 현재 단계에 필요한 capability만 확인한다.
4. [skill-resolution-contract.md](./skill-resolution-contract.md)에 따라 전문 스킬을 선택·조합하거나 fallback을 정한다.
5. 승인된 범위에서 변경하고 저장소가 제공하는 가장 좁은 검증부터 실행한다.
6. 전달이 요청되었으면 Git capability를 각각 확인한다. `branch_create`, `branch_switch`, `stage`, `commit`, `push`, `pr_create`에는 `git-workflow`를 적용한다. 지원 범위 밖인 `merge`, `rebase`, `history_rewrite`는 별도의 compatible workflow를 선택하고, 없으면 fallback 또는 blocked로 기록한다.
7. [handoff-contract.md](./handoff-contract.md)의 compact handoff를 갱신한다.

## 기계 검증

`orchestration-contract.schema.json`은 구조, route·profile·gate 조건과 blocker 결박을 검증한다. JSON Schema가 표현하지 못하는 다음 교차 필드 규칙은 `validate_orchestration_record.py`가 소유한다.

- `skill_resolution.decisions`의 `skill_id`는 한 번만 나타난다.
- 활성 스킬이 둘 이상이면 responsibility가 같거나 서로 보완적인지와 무관하게 적용 순서대로 나열하고 모두 `composed`로 명시한다. `selected`는 단일 활성 스킬에만 쓴다.
- `selected`와 `composed` 스킬은 현재 `primary_route`를 적용 범위에 포함한다.
- `selected`와 `composed` 스킬은 현재 읽을 수 있는 `SKILL.md` 원문에 exact-bound된 locator·version·content digest provenance를 가진다. repository-relative locator는 `--input` 검증을 실행한 현재 working directory를 검증 대상 repo root로 삼아 그 안에서만 해석하며, plugin source는 manifest name과 skill frontmatter name으로 canonical ID를 만든다. version은 plugin manifest version 또는 원문에 결박된 immutable `content-sha256:<digest>` revision을 쓰고, manifest가 없는 독립 source는 후자만 허용한다. `--input` 검증은 같은 working directory에서 `codex debug prompt-input`의 model-visible effective catalog를 다시 읽어 같은 canonical ID와 declared/resolved source locator가 정확히 한 번 있는지도 확인한다.
- 활성 스킬의 `required_tools`는 현재 `PATH`에서 실행 가능한 명령이어야 한다. 하나라도 없으면 compatible active decision으로 전달하지 않는다.
- 단일 활성 스킬은 `selected`여야 한다. 활성 스킬이 둘 이상일 때만 실제 적용 순서대로 모두 `composed`한다.
- 같은 source·responsibility의 compatible 후보 중 더 높은 specificity 후보를 거절하고 더 낮은 후보를 활성화할 수 없다.
- 같은 source·responsibility의 compatible 후보를 둘 이상 활성화할 때 더 높은 specificity 후보가 있으면 낮은 후보는 `composed`로도 남길 수 없다.
- blocked skill resolution은 `blocked` decision을 하나 이상 가지며, 각 decision의 `frontier_unit_ref`를 서로 다른 visible pending `material_decision` unit의 canonical identity에 결박한다. 스킬 경합과 무관한 다른 material decision까지 skill decision으로 투영하지 않는다.
- skill resolution의 logical task, basis fingerprint와 routing ref는 현재 effect binding·foundation routing identity와 일치한다. scope나 근거·routing이 바뀌면 resolution을 다시 만든다.
- `route_plan`은 canonical route 순서를 유지한다.
- scope의 include/exclude와 verification의 passed/failed/not_run은 서로 겹치지 않는다.
- `verification.failed`가 남아 있으면 deliver route와 terminal handoff의 gate는 blocked여야 한다.
- terminal `verify` handoff는 passed/failed/not_run 중 최소 한 건의 검증 결과를 남긴다.
- handoff의 completed phase는 첫 route 시작 전에는 `null`, 그 뒤에는 route plan에 있으면서 primary route보다 뒤에 있지 않는다.
- 마지막 route가 끝난 상태가 아니면 handoff의 primary route는 completed phase 바로 다음 계획 단계다.
- blocked 상태이거나 완료되지 않은 route가 남은 handoff는 비어 있지 않은 next action과 foundation gate에 맞는 `next_action_kind`를 남긴다.
- planned capability ID는 `selected`나 `composed` skill ID로 기록하지 않는다.
- 거절된 user-named 스킬과 같은 responsibility의 활성 대체 후보가 없으면 fallback을 남기거나 resolution을 blocked로 둔다.
- 같은 capability·target·scope·basis authorization binding에는 stale·withdrawn history를 제외한 current leaf가 하나만 있다.
- authorization current leaf는 status 이름이 아니라 다른 record의 `predecessor_authorization_ref`가 가리키지 않는 lineage record로 판별한다. 과거 granted summary도 successor가 있으면 current 중복으로 세지 않는다.
- design은 승인된 temporary working root에 한해 `working_artifact_write`, `temporary_work_state`를 선택적으로 받고, change는 `local_change`, `durable_document_write`, `durable_document_content`, deliver는 `branch_create`, `branch_switch`, `stage`, `commit`, `push`, `pr_create`, `merge`, `rebase`, `history_rewrite`, operate는 `external_write`, evolve는 `local_change`만 effect capability로 받는다. capability가 있으면 current effect·scope에 exact-bound된 runtime-eligible current grant가 필요하고, 없으면 gate는 blocked여야 한다. 그 밖의 read-only route capability는 `null`이다.
- foundation authorization lineage의 각 record는 최상위와 handoff `authorization`에 정확히 하나의 summary로 투영한다. summary가 가리키는 record가 없는 경우와 lineage record를 summary에서 누락하거나 중복한 경우를 모두 거절한다.
- side-effect route는 현재 effect의 capability·target·scope·basis와 정확히 일치하는 dependent authorization evaluation을 한 건만 가진다. 다른 evaluation은 `side_effect_intent: none`, `dependent_side_effect_count: 0`이어야 한다.
- read-only route 또는 effect capability가 `null`인 route의 authorization evaluation은 `side_effect_intent: none`, `dependent_side_effect_count: 0`이어야 한다.
- foundation routing·gate·frontier ref는 함께 저장한 실제 record의 canonical identity와 일치한다. 전체 snapshot은 foundation semantic validator를 그대로 통과해야 하며 routing 결정, gate의 `work_remaining`, frontier 상태·disposition과 authorization lineage가 현재 orchestration 상태에 결박된다.
- authorization snapshot은 current leaf만 잘라 저장하지 않고 root부터 current leaf까지의 record/evaluation lineage를 보존한다.
- 최상위 blocker는 foundation gate의 blocker를 정확히 투영한다.
- visible frontier에서 `answered`인 각 `material_decision` unit은 최상위 `decisions`의 정확히 한 항목과 결박한다. 항목의 `frontier_unit_ref`는 unit canonical identity, `decision_ref`는 unit의 `normalized_value` ref와 같아야 하며 summary·reason·reconsider condition을 함께 보존한다.
- `conditional` gate 중 `assumption_effect: non_material`인 경우에만 assumption이 필요하다. 각 assumption은 current assumed frontier unit의 canonical identity·assumption ref·safe-default evidence와 exact-bound되고 검증 방법을 가진다. 조사 중인 discoverable fact처럼 `assumption_effect: none`이면 assumptions는 비어 있어야 한다.
- provisional profile은 어떤 side-effect checkpoint도 통과할 수 없다.
- handoff의 objective, scope, primary route, route plan, decisions, effect binding, profile, foundation binding, skill resolution, authorization, verification과 blocker는 같은 레코드의 현재 최상위 상태와 일치한다.
- terminal side-effect route handoff는 실행 결과를 다시 확인할 수 있는 artifact 식별자를 최소 한 건 남긴다.

효과 실행이나 handoff 재개 전에는 schema 검증과 semantic validator를 모두 통과해야 한다. validator 회귀 사례는 다음 명령으로 확인한다.

회귀 결과의 `actual_rules`와 `expected_rules`는 집합이 아니라 중복을 보존한 목록이다. 같은 rule이 서로 다른 predicate에서 발생하면 발생 횟수까지 일치해야 한다.

`routing_ref`, `gate_ref`, `frontier_ref`, authorization ref의 digest는 각각 foundation의 `phase1-foundation-*-record-v1` canonical digest를 그대로 쓴다.

authorization의 `scope_fingerprint`는 UTF-8 바이트 `develop-change-scope-v1\n` 뒤에 `{"exclude":[...],"include":[...]}` payload의 canonical JSON을 이어 붙여 SHA-256으로 계산한다. canonical JSON은 key를 정렬하고 공백 없이 인코딩하며, `include`와 `exclude` 배열의 항목 순서는 현재 scope에 기록된 순서를 그대로 보존한다.

`effect_binding.logical_task_id`는 `task.objective.` 뒤에 `SHA256(b"develop-change-objective-v1\n" + canonical_json(objective))`를 붙여 만든다. objective의 summary나 finish line이 바뀌면 foundation routing·authorization과 같은 logical task identity를 재사용할 수 없다.

```bash
python3 skills/develop-change/scripts/validate_orchestration_record.py \
  --cases skills/develop-change/evals/orchestration-record-cases.json
```

## 완료 조건

- 요청된 종료 지점까지의 route가 완료되었거나 정확한 blocker가 기록되었다.
- 변경된 동작과 문서가 일치한다.
- 실행한 검증과 실행하지 못한 검증이 구분된다.
- 선택한 스킬, 제외한 경합 후보와 fallback이 설명 가능하다.
- 실제 side effect가 현재 authorization 범위를 벗어나지 않는다.
- 다음 세션이 원문 대화를 재구성하지 않고 handoff에서 재개할 수 있다.
