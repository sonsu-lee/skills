# 공통 authorization 계약

상태: `candidate-only draft`
schema version: `phase1-foundation-draft-v1`
설계 기준선: `29f39ef1d0418d78542eb4d966b7bea1201eb376d40894610ec758bcf1b19aec`
근거: DEC-015, DEC-028, DEC-045, DEC-049와 `workflow-architecture.md` §3.5·§10

Authorization은 사용자 의도, gate 통과나 workflow 진행 상태가 아니라 exact capability record다. 이 문서는 per-task 공통 capability만 소유한다. Telemetry pilot, implicit rollout/trust transition과 runtime-epoch admission은 각 후속 계약이 별도 소유한다.

Machine-readable draft는 [foundation-contract.schema.json](./foundation-contract.schema.json)의 `authorization` 정의가 소유한다.

## Capability enum과 비함의성

Per-task capability enum은 다음 값으로 닫는다.

`local_change / working_artifact_write / temporary_work_state / workspace_cleanup / durable_document_write / durable_document_content / stage_and_commit / push / pr_create / merge / rebase / history_rewrite / destructive_local / external_write / scope_expansion`

Capability마다 `not_applicable / not_granted / granted / denied / withdrawn / stale` 상태를 독립적으로 기록한다. 하나의 capability는 다른 capability를 묵시적으로 부여하지 않는다 (`FND-AUTH-001`).

- `stage_and_commit`은 승인된 file set의 staging을 포함하지만 push를 포함하지 않는다.
- `push`, `pr_create`, `merge`, `rebase`는 각각 별도 capability다.
- `external_write`는 이름이 없는 외부 쓰기의 fallback이며 위 구체 capability를 포괄하지 않는다.
- `history_rewrite`는 이름이 없는 history 변경의 fallback이며 rebase나 merge를 포괄하지 않는다.
- `scope_expansion`은 새 범위를 논의할 권한일 뿐 그 범위를 실행할 capability가 아니다.
- 설계 승인, gate pass, profile, 추천, 침묵, `계속`, leaf 설치와 local change는 telemetry·rollout·trust·runtime admission 권한이 아니다.

## Authorization record

Record identity는 `authorization_id`, positive revision, optional predecessor ID·revision·canonical digest와 logical task/change ID로 구성한다. Canonical digest는 `phase1-foundation-authorization-record-v1\n` 뒤에 nested identity-reference digest만 제외한 record의 RFC 8785 JCS bytes를 붙인 SHA-256이다. Successor가 가리키는 record는 immutable history이며, successor가 없는 lineage leaf만 current frontier·routing·evaluation에 사용할 수 있다. 한 predecessor에 successor를 둘 이상 만들지 않는다. 모든 record는 다음 exact binding을 가진다.

- `capability`
- `target_fingerprint`
- `scope_fingerprint`
- `basis_fingerprint`
- `request_revision`
- `authorization_revision`
- `receipt_revision`
- `receipt_fingerprint`
- `status`

`not_applicable`은 request·authorization·receipt tuple이 모두 null이다. `not_granted`는 nullable request revision만 가질 수 있고 authorization·receipt는 null이다. `denied`는 거절된 request revision만 non-null이다. `granted`는 target·scope·basis와 request/authorization/receipt revision, receipt fingerprint가 모두 non-null이고 현재 관측과 일치해야 한다. `withdrawn / stale`는 직전 grant의 complete receipt tuple을 감사 history로 보존하지만 runtime capability는 즉시 무효다. `future_only: true`는 stale revision에만 허용하며 relevance successor 이후에는 immutable historical fact로 보존한다 (`FND-AUTH-002`).

Target, scope, basis, file set, branch, command, semantic outcome 또는 capability가 바뀌면 이전 grant를 재사용하지 않는다. `durable_document_content`는 exact target·item revision·raw byte SHA-256, `stage_and_commit`은 file set·bytes·message, `push`는 head·range에 결박한다 (`FND-AUTH-003`).

## 상태 전이

허용 전이는 다음과 같다.

- `not_granted → granted / denied`
- `granted → withdrawn / stale`
- `denied → not_granted`는 strictly newer request revision과 null authorization·receipt를 가진 successor에서만 가능하다.
- `stale(future_only: true) → stale(future_only: false)`는 complete binding·receipt tuple을 byte-for-byte 보존한 relevance-reopen successor에서만 가능하다. 역방향 전이와 같은 relevance로의 재발행은 금지한다.
- `withdrawn / stale`는 immutable history다. 재승인은 request·authorization·receipt revision이 각각 strictly newer이고 receipt fingerprint가 immediate predecessor뿐 아니라 lineage의 어떤 prior grant receipt와도 다른 successor에서만 가능하다. 같은 logical task·capability·target·scope·basis binding은 disconnected root를 둘 수 없고 connected lineage의 root와 current leaf만 각각 하나다.

`denied`와 `withdrawn`은 사용자의 명시적 거절·철회다. `stale`은 basis·target·scope 변화이지 사용자 거절이 아니다. Current-required stale capability는 fresh `reauthorize` interaction을 만들고, future-only stale은 nonblocking defer로 둘 수 있다. 어느 경우든 fresh grant 전 dependent side effect는 0건이다 (`FND-AUTH-004`).

## 작업 유형별 기본 경계

- `change / build / fix` 요청은 명시된 범위 안의 비파괴적 local change와 필요한 local validation을 허용할 수 있지만, contract가 exact target을 좁혔다면 그 allowlist가 우선한다.
- `answer / review / diagnose`는 read-only다. 별도 승인 없이 fix하지 않는다.
- `plan / design`은 승인된 temporary working root의 artifact·state만 허용하며 repository나 canonical 문서 쓰기로 확장하지 않는다.
- Canonical 문서 작성, 내용 승인, staging/commit, push, PR, merge, rebase와 history rewrite는 서로 다른 승인이다.

Validator는 실행 시점의 current lineage leaf와 exact target/scope/basis를 대조한다. Historical predecessor는 status가 과거 `granted`여도 frontier current unit·routing·evaluation에서 선택할 수 없다. 모든 evaluation은 존재하는 current leaf를 선택한다. Current authorization frontier unit은 같은 authorization ID를 선택한 evaluation 정확히 하나와 결박하고 그 evaluation의 `allowed / blocked_missing_authorization / blocked_scope_expansion` 결과에서 resolved·missing-authorization·scope-expansion disposition을 파생한다. 역방향으로 모든 blocked evaluation은 정확히 하나의 current authorization unit으로 드러나 unrelated resolved unit 뒤에 숨길 수 없다. Current-relevant unit은 top-level blocked gate로 올라가고 future-only stale unit은 explicit nonblocking defer로 남는다. Resolved unit의 receipt binding은 generic ref가 아니라 exact `authorization_id / receipt_revision / receipt_fingerprint` tuple이다. Blocked evaluation은 current-relevant한 fresh request interaction, 같은 derived blocker를 보존한 blocking defer, 또는 future-only stale의 nonblocking defer 중 하나다. Evaluation은 `side_effect_intent: none / dependent`를 소유한다. Exact current granted record만 `allowed / continue`이며 `dependent`일 때만 dependent side effect 1건, `none`이면 0건이다. Missing, stale, denied, withdrawn, wrong basis 또는 다른 capability는 `blocked_missing_authorization / reauthorize`, target·scope 불일치는 `blocked_scope_expansion / reauthorize`이며 dependent side effect는 0건이다 (`FND-AUTH-005`).

Evaluation ID와 selected current leaf는 envelope 안에서 각각 unique이고 evaluation basis는 current routing·frontier basis와 같다. Routing이 current `not_granted` leaf를 선택하면 exact evaluation·current authorization unit을 각각 하나 가져야 하며, 그 두 record 없이 capability 비적용을 표현할 때는 `not_applicable`을 쓴다 (`FND-AUTH-005`, `FND-FRONTIER-006`).

## Phase 1 경계

이 draft는 실제 grant, receipt, trust root, rollout artifact, telemetry root 또는 runtime epoch를 생성하지 않는다. `develop-change/SKILL.md`, plugin manifest와 active configuration도 이 slice에서 만들거나 바꾸지 않는다. Fixture 안의 receipt와 hash는 `fixture_only`이며 실제 승인 증거로 사용할 수 없다 (`FND-RUNTIME-001`).
