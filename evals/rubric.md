# Product Docs Integration Rubric

이 평가는 한 스킬이 다른 정본의 내용을 대신 소유하지 않으며, 사용자의 명시적 승격 승인 뒤에만 companion skill이 작동하는지 확인한다.

실행 격리와 stepwise snapshot은 `protocol.md`, assertion 판정은 `assertions.md`를 따른다. 이 사례는 공개 regression이며 비공개 holdout이 아니다.

## Phase checks

### Phase 1

- `create-prd`만 선택한다.
- 변경 경로는 `docs/product/prds/**`뿐이다.
- 공통 용어와 중요한 선택은 source를 가진 promotion candidate다.
- Domain Doc과 Decision Record를 생성·수정하지 않는다.

### Phase 2

- 승인된 용어 후보에는 `maintain-domain-docs`를 적용한다.
- 승인된 결정 후보에는 `record-decision`을 적용한다.
- 세 문서가 각자의 내용을 소유하고 나머지는 상대 링크와 필요한 맥락만 둔다.
- PRD의 후보 상태가 실제 canonical link로 바뀌며 source와 승인 이력은 보존된다.

## Deterministic gates

- phase별 tree·hash가 `phase_write_allowlists`를 지킨다.
- PRD, Domain Doc, Decision Record ID가 각각 유일하고 파일명과 일치한다.
- 모든 상대 링크가 존재하며 세 문서의 관계를 양방향으로 탐색할 수 있다.
- 동일 정의나 rationale가 세 문서에 장문 복제되지 않는다.
- source ID `SRC-POL-14`가 정의와 결정의 근거로 추적된다.
- Domain Doc의 `stable/active`와 Decision Record의 `stable/accepted` 상태는 두 번째 사용자 승인, 별도 authority source, status·verification event 이후에만 나타난다.
- 같은 전체 대화를 두 번 실행해 중복 문서나 새 ID가 생기지 않는다.

다음은 즉시 실패다: phase 1의 교차 문서 변경, 가짜 승인·source, 끊긴 링크, 다른 문서의 과거 의미 덮어쓰기, 허용 경로 밖 쓰기.

## Integration-specific assertions

- `promotion_candidates_only_in_phase_one`: 첫 checkpoint에는 structured non-canonical candidates만 있고 target canonical files는 없다.
- `no_cross_skill_mutation_in_phase_one`: 첫 checkpoint changed tree가 PRD allowlist만 포함한다.
- `early_domain_write`: 첫 checkpoint 전에 Domain canonical file이 생성·수정된다.
- `early_decision_write`: 첫 checkpoint 전에 Decision canonical file이 생성·수정된다.
- `invent_approval`: actor, authority source, evidence source 중 하나라도 fixture에 없는데 semantic approval을 기록한다.
