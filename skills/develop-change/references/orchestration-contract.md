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
6. 전달이 요청되었으면 branch 생성·전환을 포함한 Git capability를 각각 확인한 뒤 `git-workflow`를 적용한다.
7. [handoff-contract.md](./handoff-contract.md)의 compact handoff를 갱신한다.

## 기계 검증

`orchestration-contract.schema.json`은 구조, route·profile·gate 조건과 blocker 결박을 검증한다. JSON Schema가 표현하지 못하는 다음 교차 필드 규칙은 `validate_orchestration_record.py`가 소유한다.

- `skill_resolution.decisions`의 `skill_id`는 한 번만 나타난다.
- 같은 responsibility의 활성 스킬은 모두 `composed`로 명시하지 않는 한 하나만 `selected`한다.
- `selected`와 `composed` 스킬은 현재 `primary_route`를 적용 범위에 포함한다.
- scope의 include/exclude와 verification의 passed/failed/not_run은 서로 겹치지 않는다.
- handoff의 completed phase는 route plan에 있고 primary route보다 뒤에 있지 않는다.
- blocked handoff는 비어 있지 않은 next action을 남긴다.
- 같은 capability·target·scope·basis authorization binding에는 current leaf가 하나만 있다.
- handoff의 objective, scope, decisions, profile, foundation binding, skill resolution, authorization, verification과 blocker는 같은 레코드의 현재 최상위 상태와 일치한다.

효과 실행이나 handoff 재개 전에는 schema 검증과 semantic validator를 모두 통과해야 한다. validator 회귀 사례는 다음 명령으로 확인한다.

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
