# 공통 authorization 계약

적용 상태: 저장소 계약 초안. 현재 runtime에서는 사용하지 않는다.

Authorization은 **어떤 행동을, 어느 대상과 범위에, 어떤 근거로 해도 되는지**를 적은 한 장짜리 허가다.

“전체적으로 진행해도 된다”는 포괄 허가는 없다. 설계 승인, gate 통과, `계속`, 침묵, 이전 성공도 새로운 행동의 권한이 되지 않는다.

## 사용 순서

1. 지금 필요한 행동을 capability 하나로 정확히 고른다.
2. 대상, 범위, 현재 basis를 record에 결박한다.
3. 실행 직전에 그 record가 current lineage leaf이고 `granted`인지 확인한다.
4. 승인된 행동만 실행한다.
5. 대상·범위·basis·capability가 바뀌면 멈추고 새 승인을 받는다.
6. 실행 후에는 실제 receipt와 record가 일치하는지 검증한다.

## Capability는 서로 독립이다

| 묶음 | capabilities |
| --- | --- |
| 로컬 작업 | `local_change`, `working_artifact_write`, `temporary_work_state`, `workspace_cleanup`, `destructive_local`, `scope_expansion` |
| 문서 | `durable_document_write`, `durable_document_content` |
| Git·GitHub | `branch_create`, `branch_switch`, `stage`, `commit`, `push`, `pr_create`, `merge`, `rebase`, `history_rewrite` |
| 외부 시스템 | `external_write` |

하나를 승인해도 다른 하나는 승인되지 않는다 (`FND-AUTH-001`).

특히 Git 작업은 다음처럼 나뉜다.

- `branch_create`: 승인된 이름과 시작점으로 로컬 branch ref를 만들며, checkout까지 포함할지는 target에 명시한다.
- `branch_switch`: 승인된 기존 branch로 working tree와 `HEAD`를 전환한다.
- `stage`: 승인된 파일의 exact bytes를 Git index에 올린다.
- `commit`: 이미 검증된 exact index tree로 commit을 만들고 branch ref를 이동한다.
- `push`: 승인된 commit range를 remote에 보낸다.
- `pr_create`: 승인된 head/base로 PR을 만든다.
- `merge`, `rebase`, `history_rewrite`: 각각 별도 행동이다.

따라서 branch 생성은 전환 권한을 자동으로 포함하지 않고, `commit`은 staging을 포함하지 않으며, `PR을 만든다`는 말도 push·merge까지 자동으로 포함하지 않는다. `scope_expansion`은 새 범위를 논의할 수 있다는 뜻일 뿐 그 범위를 수정할 권한은 아니다.

## 상태

| status | 뜻 |
| --- | --- |
| `not_applicable` | 이 행동이 현재 작업에 필요하지 않다 |
| `not_granted` | 필요할 수 있지만 아직 허가가 없다 |
| `granted` | exact target·scope·basis에 대해 현재 허가가 있다 |
| `denied` | 사용자가 명시적으로 거절했다 |
| `withdrawn` | 사용자가 기존 허가를 철회했다 |
| `stale` | 대상·범위·basis가 바뀌어 기존 허가를 재사용할 수 없다 |

`withdrawn`과 `stale`은 과거 receipt를 감사 이력으로 보존하지만 실행 권한은 즉시 사라진다. 재승인은 더 새로운 request·authorization·receipt와 새로운 receipt fingerprint를 가진 successor여야 한다 (`FND-AUTH-002`, `FND-AUTH-004`).

## 예시

### 수정은 승인됐지만 PR은 승인되지 않은 경우

- `local_change: granted`
- `branch_create / branch_switch / stage / commit / push / pr_create: not_granted`
- 할 일: 파일을 수정하고 로컬 검증까지만 한다.
- 하지 않을 일: index, commit, remote를 건드리지 않는다.

### commit만 승인된 경우

- 검증된 index tree가 record와 같으면 commit을 만들 수 있다.
- unstaged 변경을 임의로 stage하지 않는다.
- commit 뒤 push하지 않는다.

### 승인 뒤 범위가 늘어난 경우

- 기존 scope 밖 파일이 필요해지면 old grant는 사용할 수 없다.
- `blocked_scope_expansion / reauthorize`로 멈추고 새 범위를 보여준다.
- 새 grant 전 dependent side effect는 0건이다.

## 요청 유형별 기본선

- `answer / review / diagnose`: read-only다. 별도 요청 없이 fix하지 않는다.
- `change / build / fix`: 명시된 범위의 비파괴적 local change와 필요한 local validation까지만 허용할 수 있다. 더 좁은 contract allowlist가 있으면 그것이 우선한다.
- `plan / design`: 승인된 temporary working root의 artifact·state만 다룬다. repository나 canonical 문서 쓰기로 넓히지 않는다.
- canonical 문서 쓰기, 내용 승인, branch 생성·전환, stage, commit, push, PR, merge, rebase, history rewrite는 각각 따로 본다.

## 꼭 지킬 경계

- 실행에는 successor가 없는 current record만 쓴다. 과거 `granted` record를 골라 재생하지 않는다.
- target, scope, basis, file set, branch, command, semantic outcome 또는 capability가 바뀌면 fresh grant를 받는다 (`FND-AUTH-003`).
- exact current grant만 dependent side effect를 허용한다. missing·stale·denied·withdrawn·wrong binding이면 0건이다 (`FND-AUTH-005`).
- 질문, 답변, 추천, gate, profile, skill 설치, telemetry·rollout·trust·runtime 상태는 per-task capability를 대신하지 않는다.

## 기계 계약

정확한 record identity, revision, predecessor, target/scope/basis fingerprint, request·authorization·receipt tuple, canonical digest와 evaluation/frontier binding은 [foundation-contract.schema.json](./foundation-contract.schema.json)의 `authorization` 정의 및 validator가 소유한다.

이 draft의 receipt와 hash는 fixture 전용이다. 실제 grant, Git 동작, 외부 쓰기, telemetry, rollout, trust root 또는 runtime epoch를 만들지 않는다. `develop-change/SKILL.md`, plugin manifest와 active configuration도 이 slice에서 만들거나 바꾸지 않는다 (`FND-RUNTIME-001`).
