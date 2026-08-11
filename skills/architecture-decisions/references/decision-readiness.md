# Decision readiness

기술 선택을 확정하거나 ADR 기록 단계로 넘길 때만 읽는다.

## 필수 항목

- 하나의 decision statement와 명확한 scope
- 결정이 필요한 실제 context와 시점
- 확인된 제약, quality attribute와 비목표
- 같은 기준으로 비교한 둘 이상의 실제 대안 또는 단일 대안만 가능한 근거
- 선택 결과와 실제 rationale
- decision actor와 권한 근거
- consequence, 위험과 후속 검증
- 관찰 가능한 revisit trigger

## 상태

- `exploration-needed`: 문제, 제약 또는 실제 대안을 모델이 발명해야 한다.
- `proposed`: 비교와 추천은 있지만 권한 있는 선택 evidence가 없다.
- `accepted`: actor, authority, 선택 scope와 evidence가 확인됐다.
- `rejected`: 대안을 선택하지 않기로 한 actor와 evidence가 있다.
- `deferred`: 결정을 미룬 이유, 다음 event와 영향이 있다.

코드에 구현되어 있다는 사실만으로 `accepted`를 만들지 않는다. retrospective record라면 decision time, record time과 provenance confidence를 구분한다.

## ADR 변환 gate

- `ready`: 결정문, 선택한 대안, 실제 rationale, actor·evidence와 consequence가 있다.
- `conditional`: 과거 결정이 분명하지만 일부 근거는 unknown으로 남겨야 한다.
- `blocked`: 선택 결과, 실제 rationale 또는 결정 권한을 추측해야 한다.
