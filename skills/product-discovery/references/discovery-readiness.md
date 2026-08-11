# Discovery readiness

제품 탐색 결과를 다음 단계로 넘길 수 있는지 판단할 때만 읽는다.

## 제품 합의

다음 질문에 근거가 연결되어야 한다.

| 영역 | 확인 질문 |
|---|---|
| Problem | 누구의 어떤 현재 문제가 왜 해결할 가치가 있는가? |
| Outcome | 기능 출시가 아니라 어떤 사용자·제품 결과가 달라지는가? |
| Boundary | 제품과 외부 시스템·운영 책임의 경계는 어디인가? |
| Authority | 누가 제품 결정을 확인할 권한이 있는가? |
| Domain | 핵심 용어, 상태, 사건, 규칙과 예외가 같은 의미인가? |
| Scope | 포함 범위, 비목표와 이후 단계가 구분됐는가? |
| Behavior | 정상·실패·빈 상태·권한·취소·재시도 흐름이 필요한 만큼 확인됐는가? |
| Success | 관찰 신호, 확인된 기준 또는 open ID, 측정 방법과 결정 주체가 있는가? |
| Unknowns | 가정, 충돌, 미해결 질문에 영향과 다음 행동이 있는가? |

Problem, Outcome, Boundary, Authority, Domain, Scope 중 하나가 불명확하면 `discovery-needed`다. 중요한 성공·수용·의존성만 남았으면 `conditional`일 수 있다.

## 승인

`approved`에는 다음이 모두 필요하다.

- 승인 actor
- actor의 권한을 보여 주는 출처
- 승인한 scope와 정확한 revision
- 확인 시점과 승인 evidence

추천, 회의 참석, 문서 존재와 코드 구현은 승인 evidence가 아니다.

## Downstream readiness

각 영역을 `not-ready | conditional | ready`로 별도 판정하고 source·claim·decision·open ID를 evidence로 연결한다.

- `design_ready`: actor, state, error와 accessibility 경계를 추가 제품 정책 없이 탐색할 수 있다.
- `engineering_ready`: 제품 정책을 발명하지 않고 설계·구현 판단을 시작할 수 있다.
- `qa_ready`: 핵심 요구와 예외를 관찰 가능한 검증으로 바꿀 수 있다.
- `ops_ready`: 계측, release, recovery와 책임 경계를 확인할 수 있다.

## 변환 gate

`to-prd`로 넘길 때 다음을 구분한다.

- `ready`: 핵심 제품 합의가 있고 PRD가 새 결정을 만들 필요가 없다.
- `conditional`: 알려진 open item을 명시한 조건부 PRD가 유용하다.
- `blocked`: PRD를 쓰려면 문제·사용자·결과·경계·핵심 규칙 중 하나를 모델이 발명해야 한다.
