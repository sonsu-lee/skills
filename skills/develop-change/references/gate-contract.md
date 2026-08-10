# 공통 gate와 decision frontier 계약

상태: `candidate-only draft`
schema version: `phase1-foundation-draft-v1`
설계 기준선: `29f39ef1d0418d78542eb4d966b7bea1201eb376d40894610ec758bcf1b19aec`
근거: DEC-010, DEC-045, DEC-049와 `workflow-architecture.md` §8

이 문서는 gate 결과, 다음 행동과 decision frontier를 하나의 공통 의미로 닫는다. Raw 질문·답변, 자유 텍스트 근거와 authorization receipt 본문은 저장하지 않는다.

Machine-readable draft는 [foundation-contract.schema.json](./foundation-contract.schema.json)의 `gate`와 `frontier` 정의가 소유한다.

## Gate record

gate result는 `pass / conditional / blocked`, next action은 `continue / clarify / reauthorize / null`, blocker는 `none / missing_evidence / missing_decision / missing_authorization / scope_expansion / external_dependency`로 닫는다.

| condition | required result | blocker | next action |
| --- | --- | --- | --- |
| 진행 blocker 없음 | `pass` | `none` | 완료면 `null`, 아니면 `continue` |
| 현재 권한·성공 기준을 바꾸지 않는 공개된 가정 | `conditional` | `none` | `continue` |
| 결과 선택을 바꾸는 미결정 | `blocked` | `missing_decision` | `clarify` |
| 안전한 read-only 조사로 해소 가능한 근거 | `blocked` | `missing_evidence` | `continue` |
| 사용자만 제공할 수 있는 필수 근거 | `blocked` | `missing_evidence` | `clarify` |
| capability가 없거나 stale | `blocked` | `missing_authorization` 또는 `scope_expansion` | `reauthorize` |
| 현재 작업에서 해소 불가한 외부 선행조건 | `blocked` | `external_dependency` | `null` |
| blocking defer | `blocked` | 원래 blocker | `null` |

`pass`나 `conditional`에 non-`none` blocker를 두거나, `blocked`에 `none`을 두거나, authorization blocker를 `clarify`로 보내는 조합은 invalid다 (`FND-GATE-001`). Missing evidence는 owner가 `local`이면 `continue`, `user`이면 `clarify`이고 다른 blocker에서 owner는 `none`이다. 전체 진행 상태는 `continue / await_input / partial_block / terminal_blocked`로 따로 기록한다. `pass / conditional`과 local investigation은 `continue`, clarification·reauthorization 대기는 `await_input`, blocking defer에 독립 work가 남으면 `partial_block`, 해소 불가 external dependency나 독립 work 없는 blocking defer는 `terminal_blocked`다. 결과를 바꾸는 assumption은 `blocked / missing_decision / clarify`로 되돌린다 (`FND-GATE-002`).

Top-level gate는 historical unit과 `checkpoint_relevance: future_only` unit을 제외한 current frontier의 exact aggregate다. Current blocked unit이 있으면 blocker 우선순위 `external_dependency > scope_expansion > missing_authorization > missing_decision > missing_evidence`의 첫 tuple을 사용한다. 같은 blocker의 unit은 동일 next action이어야 한다. Blocked가 없고 current conditional unit 또는 provisional profile이 있으면 `conditional / none / continue`, 그 밖에는 `pass / none`이며 `work_remaining`이면 `continue`, 아니면 next action은 null이다. `work_remaining`인 blocked gate는 `partial_block`, 아니면 user interaction은 `await_input`, null action은 `terminal_blocked`다. 선택된 unit이 blocking defer일 때만 top-level `blocking_defer`가 true다. Missing-evidence blocking defer의 owner와 blocked aggregate의 `assumption_effect`는 `none`이다. Blocked가 없고 current assumed unit이 하나라도 있을 때만 `assumption_effect: non_material`이다. 이 aggregate와 다른 top-level gate는 invalid다 (`FND-GATE-002`).

## Decision frontier unit

frontier는 logical task/change마다 stable `frontier_id`, revision, basis fingerprint, exact `visible_unit_ids`, heterogeneous `units[]`와 optional clarification view를 가진다. Unit identity는 `unit_id + revision`이며 이전 revision을 덮어쓰지 않는다. Root unit은 `revision: 1 / predecessor: null`이고, 모든 predecessor·successor ref는 같은 unit ID·gap kind의 인접 revision exact canonical record를 양방향으로 가리킨다. Non-historical current unit은 successor가 없는 lineage leaf이고 current frontier·routing basis와 같아야 한다 (`FND-FRONTIER-005`). `dependency_ids` 각 항목은 같은 frontier의 존재하는 다른 unit ID이며 current dependency graph는 DAG이다. 한 clarification view는 서로 직·간접 dependency path가 없는 pending unit만 batch한다 (`FND-FRONTIER-001`, `FND-FRONTIER-004`).

Canonical gap kind:

`discoverable_fact / user_supplied_evidence / incidental_preference / material_decision / authorization / external_blocker`

Resolution action:

`investigate / request_input / assume / defer / report_blocker`

State:

`pending / resolved_by_evidence / assumed / answered / deferred / stale / superseded`

각 unit은 `basis_fingerprint`, `affected_scope`, `checkpoint_relevance: current / future_only`, dependency ID 집합, nullable `authorization_id`, action, state, `defer_effect`, gate result·blocker·next action, interaction kind·requirement·owner와 progress를 가진다. Authorization gap만 존재하는 exact authorization record ID를 가지며 다른 kind는 null이다. Current authorization unit은 current lineage leaf만 가리키고 그 ID를 선택한 authorization evaluation이 정확히 하나여야 한다. 모든 evaluation은 존재하는 current lineage leaf를 선택해야 하며, blocked evaluation은 정확히 하나의 current authorization unit으로 frontier에 드러나 resolved fact 뒤에 숨을 수 없다. 그 unit이 current-relevant면 top-level gate도 blocked로 파생하고, future-only stale이면 explicit nonblocking defer로 남아 current aggregate에서만 제외된다. `blocked_scope_expansion`은 그 exact evaluation에서만 `scope_expansion` unit blocker로 파생하고, 다른 결과에서 이를 자의적으로 선택하지 않는다. Blocked evaluation은 current-relevant한 fresh `request_input`, 같은 derived blocker·null next action을 보존한 blocking defer, 또는 future-only stale의 nonblocking defer만 허용한다. 값은 해당 상태가 허용할 때만 normalized value, assumption 또는 content-free evidence/receipt tuple 중 하나로 나타낸다. Authorization의 `resolved_by_evidence` binding은 generic evidence/ref가 아니라 exact authorization ID·receipt revision·receipt fingerprint여야 한다 (`FND-FRONTIER-001`, `FND-FRONTIER-006`).

## Closed action/state 조합

- `discoverable_fact`: `investigate`; evidence 전 `pending + conditional/continue`, 후 `resolved_by_evidence + pass/continue`.
- `user_supplied_evidence`: `request_input`; input 전 `pending`, 후 `resolved_by_evidence`.
- `incidental_preference`: 현재 무관하면 `defer/nonblocking/deferred`, 관련되고 safe-default 조건이 모두 true면 `assume/assumed`.
- `material_decision`: `request_input`; 전 `pending`, 후 `answered`.
- `authorization`: `request_input`; receipt 전 `pending`, valid receipt 후 `resolved_by_evidence`.
- `external_blocker`: `report_blocker`; 전 `pending`, 회복 evidence 후 `resolved_by_evidence`.
- 여섯 kind 모두 `checkpoint_relevance: future_only`이면 value 없는 `defer/nonblocking/deferred + pass/continue`가 가능하다. `future_only`는 이 조합에만 쓰며, pending·resolved·assumed·answered 또는 blocking-deferred unit은 반드시 `current`다. `current` unit을 nonblocking branch로 보내지 않는다. 이는 그 unit이 현재 checkpoint를 막지 않는다는 뜻일 뿐 전체 workflow 승인이나 effect 권한이 아니다.
- `blocks_dependent_scope` defer는 `discoverable_fact / user_supplied_evidence / material_decision / authorization / external_blocker`에만 가능하며 blocker를 보존하고 next action은 null이다.

`defer_effect`는 action이 `defer`가 아니면 `none`, `defer`이면 `nonblocking` 또는 `blocks_dependent_scope`다. Incidental preference의 blocking defer, defer에 value·assumption·evidence를 materialize한 record, blocking defer의 `pass/continue`는 invalid다 (`FND-FRONTIER-002`).

## Safe default

Safe default는 다음 condition ID 각각이 `true / false / unresolved`와 evidence ref를 가져야 한다.

`within_authorized_scope / observable_result_unchanged / persistent_semantics_unchanged / no_external_or_destructive_effect / simple_local_revert / supported_by_project_evidence / detectable_by_current_validation`

관련 preference에서 일곱 condition이 모두 `true`일 때만 `incidental_preference / assume`이 가능하며 unit-level gate는 `conditional / none / continue`다. `unresolved`이면 누가 근거를 소유하는지에 따라 `discoverable_fact` 또는 `user_supplied_evidence`, `false`이면 결과·scope에 따라 `material_decision`, `authorization` 또는 `external_blocker`로 재분류한다 (`FND-FRONTIER-003`).

## Interaction과 view

- `clarification` interaction은 user-supplied evidence 또는 material decision의 pending `request_input`에만 쓴다.
- `authorization` interaction은 authorization의 pending `request_input`에만 쓴다.
- 두 interaction은 항상 `required`이며 progress는 `await_input` 또는 `partial_block`이다.
- logical task/change와 interaction owner마다 fresh pending interaction은 최대 하나다. 한 clarification interaction은 서로 다른 kind의 여러 pending unit을 하나의 view에 묶을 수 있다.
- Frontier는 prior immutable view를 `clarification_view_history[]`, exact current lineage leaf를 nullable `clarification_view`로 보존한다. 각 view는 `round_id`, revision, nullable exact `predecessor_view_ref`, closed `transition_cause`, renderer version, state, owner, basis, visible IDs, tagged `units[]`와 `accepted_shorthand[]`를 가진다. 모든 lifecycle state에서 `decision`은 exact `material_decision`, `evidence_request`는 exact `user_supplied_evidence` unit lineage ID를 가리킨다. Root는 `revision: 1 / pending / initial_presentation`뿐이다. 같은 round의 `pending → consumed / expired`는 각각 `response_consumed / basis_expired`, `consumed → pending`은 미응답 ID의 strict non-empty subset을 가진 `partial_response_remaining`, `expired → pending`은 `basis_refreshed`다. Partial response에서 제거된 decision ID는 exact current `answered / deferred` material-decision unit, 제거된 evidence-request ID는 exact current `resolved_by_evidence / deferred` user-evidence unit으로 남아야 하며 unit을 소실해 답변 이력을 가장할 수 없다. 닫힌 view 뒤 별도 round를 열 때만 `new_interaction`과 새 round revision 1을 쓴다. History는 한 갈래 exact predecessor chain이고 current view만 successor가 없는 leaf다.
- `decision` unit은 content-free decision ref, unique option ID별 label·impact ref와 nullable recommended option을, `evidence_request` unit은 requested evidence·alternative evidence·sensitivity ref를 가진다. 모든 lifecycle state와 history record에서 view unit ID는 frontier가 보존한 unit lineage에 실제 존재해야 하며, view 내부 unit ID·option·shorthand와 `visible_unit_ids` exact set 및 canonical digest를 검증한다. Current pending view는 추가로 같은 owner의 current pending clarification unit exact set과 frontier basis에 결박한다. Shorthand는 decision unit의 실제 option만 가리키고 evidence request에는 적용하지 않는다. `view_digest`는 자신을 제외한 view record의 canonical JSON 앞에 `phase1-clarification-view-v1\n`을 붙인 UTF-8 bytes의 SHA-256이다. Predecessor ref digest는 predecessor의 exact `view_digest`다. Digest·basis·unit set이나 lifecycle이 바뀌면 새 revision을 발행한다.
- 일부 답만 온 batch에 old view를 재사용하거나 침묵·timeout을 답·승인으로 처리하지 않는다 (`FND-FRONTIER-004`).

## History와 authorization 상태

`stale / superseded` revision은 immutable history이며 runtime disposition, interaction과 next action이 모두 null이다. 같은 atomic update에서 predecessor를 가리키는 current successor를 생성해야 한다. Historical revision만 남기거나 same revision을 덮어쓰는 전이는 invalid다 (`FND-FRONTIER-005`).

Authorization `denied`는 current pending unit의 blocking defer를 만든다. `withdrawn`은 기존 resolved revision을 superseded history로 만들고 blocking-deferred successor를 같은 update에서 만든다. Current-required `stale`은 stale history와 fresh pending reauthorization successor를, future-only stale은 nonblocking deferred successor를 만든다. Future-only stale이 later-current가 되면 complete auth tuple을 보존한 relevance successor와 stale unit history 뒤 fresh current pending reauthorization successor를 같은 update에서 만든다. 네 경우 모두 기존 capability로 dependent side effect를 실행할 수 없다 (`FND-FRONTIER-006`).

이 frontier는 질문을 만들기 위한 상태이며 질문했다는 사실이나 답변 수신 자체가 authorization을 대신하지 않는다.
