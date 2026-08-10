# 공통 routing 계약

상태: `candidate-only draft`
schema version: `phase1-foundation-draft-v1`
설계 기준선: `29f39ef1d0418d78542eb4d966b7bea1201eb376d40894610ec758bcf1b19aec`
근거: DEC-009, DEC-034, DEC-044, DEC-049와 `workflow-architecture.md` §5

이 문서는 개발 작업의 route와 profile을 공통 envelope로 표현하는 정본이다. Phase 1에서는 schema·fixture·validator 입력으로만 쓰며 current skill catalog, producer, consumer 또는 gate를 바꾸지 않는다. Invocation disposition, task binding, leaf resolver, effect trace와 rollout은 `phase1-invocation-contract`가 소유한다.

Machine-readable draft는 [foundation-contract.schema.json](./foundation-contract.schema.json)의 `routing` 정의가 소유한다.

## Routing envelope

`routing_envelope`는 다음 필드를 정확히 한 번 가진다.

- `routing_id`, `revision`, `logical_task_id`, `basis_fingerprint`: stable identity와 현재 근거를 결박한다. Routing basis는 current frontier record, 모든 non-historical current unit과 authorization evaluation의 basis와 exact equality여야 하며 historical unit·authorization record만 old basis를 보존할 수 있다.
- `primary_route`: 현재 route 하나.
- `route_plan`: 중복 없는 non-empty route 순서. `primary_route`가 반드시 포함된다.
- `profile`, `profile_status`, `profile_checkpoint`, `unresolved_architectural_axes`: 강도, 판정 시점과 미확정 hard floor를 분리한다. Checkpoint는 `read_only_discovery / before_material_decision / before_design_commitment / before_local_change / before_external_effect`로 닫는다.
- `architectural_axes`: 아래 일곱 ID 각각의 `true / false / unresolved`와 non-empty evidence reference.
- `runtime_dependency_assessment`: dependency 변화 종류와 dev/test-only 예외의 다섯 조건을 structured tri-state로 기록한다.
- `direct_conditions`: 아래 일곱 ID 각각의 `true / false / unresolved`와 non-empty evidence reference.
- `transition`: 이전 revision이 있을 때 predecessor ID, 이전·현재 route/profile, closed reason과 side-effect 전 적용 여부를 기록한다.
- `gate_ref`, `authorization_ref`: 같은 revision에서 판정한 gate와 current authorization record의 exact ID·revision·canonical digest를 참조할 뿐, 그 값을 복제하거나 새 권한을 만들지 않는다.

Unknown field, 숫자형 risk score, `unknown` profile, 파일 수·diff 크기·예상 시간 또는 키워드만으로 만든 분류는 금지한다 (`FND-ROUTE-001`).

## Route

route enum은 다음 열 개로 닫는다.

`understand / shape / decide / design / diagnose / change / verify / deliver / operate / evolve`

route는 활동의 순서이지 자동 권한 사슬이 아니다. 여러 route가 필요하면 `route_plan`에 순서대로 두고 완료한 route를 재실행하지 않는다. 읽기 전용 diagnose는 변경 요청이나 유효한 `local_change` 없이 `change`로 넘어가지 않는다. `deliver`, `operate`와 `evolve`도 각자의 성공 기준과 capability를 다시 판정한다 (`FND-ROUTE-002`).

기본 다음 route 후보는 다음과 같다. 이 표 밖의 전이는 금지가 아니라 근거가 필요한 비기본 전이다.

| current | default successors |
| --- | --- |
| `understand` | `shape`, `decide`, `diagnose` |
| `shape` | `decide`, `design`, `change` |
| `decide` | `design`, `change` |
| `design` | `change`, `verify` |
| `diagnose` | `change`, `verify` |
| `change` | `verify` |
| `verify` | `deliver`, `operate`, `evolve` |
| `deliver` | `operate` |
| `operate` | `verify`, `evolve` |
| `evolve` | `change`, `verify` |

## Profile 파생

architectural axis ID는 다음 일곱 개다.

`domain_rule / public_contract / trust_boundary / runtime_dependency / multi_system_owner / data_transition / operational_blast_radius`

direct condition ID는 다음 일곱 개다.

`exact_outcome / no_unresolved_architectural_axis / single_local_effect_boundary / mechanical_existing_semantics / simple_local_revert / narrow_immediate_validation / no_rollout_migration_or_operations`

validator는 다음 우선순위를 그대로 적용한다 (`FND-PROFILE-001`).

1. architectural axis가 하나라도 `true`이면 `architectural`이다.
2. `true`는 없고 하나라도 `unresolved`이면 읽기 전용 조사 checkpoint에서는 `bounded / provisional`이다. 의미 결정, 설계 확정, local change 또는 외부 효과 checkpoint에서 unresolved가 남으면 `architectural / provisional`로 올리고 gate를 다시 판정한다.
3. 모든 axis가 `false`이고 모든 direct condition이 `true`이면 `direct / confirmed`다.
4. 그 밖은 `bounded / confirmed`다.

`profile_status: provisional`은 non-empty `unresolved_architectural_axes`와 exact equality이고 `bounded` 또는 `architectural`에서 유효하다. `confirmed`이면 unresolved 집합은 비어야 한다. Axis 하나가 이미 `true`여서 profile이 architectural이어도 다른 unresolved axis를 숨기지 않는다 (`FND-PROFILE-002`).

`runtime_dependency_assessment.change_kind`는 `none / production_or_runtime / dev_test_only`다. `none`은 다섯 조건을 모두 `not_applicable`로 두고 axis를 `false`, `production_or_runtime`은 axis를 `true`로 둔다. `dev_test_only`는 production artifact, runtime, CI 계약, 배포·license·security 책임 불변과 단순 제거+기존 검증의 다섯 조건이 모두 `true`일 때만 axis를 `false`, 하나라도 `false`이면 `true`, 나머지는 `unresolved`로 둔다. Assessment와 axis는 같은 non-empty evidence reference에 결박한다 (`FND-PROFILE-003`).

Initial transition은 predecessor/from fields와 `applied_before_side_effect`가 모두 null이다. 이후 transition은 predecessor, 이전 route/profile과 `applied_before_side_effect=true`를 반드시 가진다. Route 전환과 leaf handoff는 profile을 초기화하지 않는다. `route_progress`는 profile을 바꾸지 않고, profile은 `new_evidence / scope_changed / hard_floor_detected / hard_floor_resolved`로만 바뀐다. 하강은 `hard_floor_resolved`에서 모든 hard floor가 해소되고 profile에 의존한 결정·설계·변경을 시작하기 전에만, 상승은 다음 side effect보다 먼저 허용한다 (`FND-PROFILE-004`).

## Envelope 경계

- `direct`는 ceremony를 줄이는 실행 profile일 뿐 authorization이 아니다.
- `architectural`은 ADR, canonical 문서, commit 또는 외부 쓰기 승인이 아니다.
- `gate_ref`와 `authorization_ref`, gate의 `routing_ref`는 exact ID/revision/digest envelope만 공유한다. Digest는 referent 종류별 domain separator `phase1-foundation-routing-record-v1\n`, `phase1-foundation-gate-record-v1\n`, `phase1-foundation-authorization-record-v1\n` 뒤에 referent record의 RFC 8785 JCS bytes를 붙인 SHA-256이다. Reference cycle을 피하기 위해 referent 안의 nested identity reference에서는 `digest`만 canonical payload에서 제외하고 `id / revision`은 보존한다. Validator는 ID·revision뿐 아니라 이 digest를 실제 referent bytes에서 재계산한다.
- 같은 의미를 leaf skill에 복사하지 않는다. leaf-only 실행은 plugin bundle의 이 정본을 read-only로 해석할 수 있어야 한다.

이 draft를 current runtime 계약으로 공개하거나 `develop-change/SKILL.md`를 생성하는 행위는 이 slice 범위 밖이다 (`FND-RUNTIME-001`).
