# Domain Documentation Quality Bar

## Entry types

도메인 지식을 가장 작은 유용한 semantic unit으로 나눈다.

| Type | 필수 내용 |
|---|---|
| Domain Concept | context, preferred term, 구별 정의, aliases, examples·counterexamples, 관계, source |
| Domain Rule | statement, scope, precondition, outcome 또는 invariant, exceptions, examples, source |
| Domain State Model | 대상 concept, states, initial·terminal, transitions, actor, trigger, guard, effect, prohibited transitions, source |

역할, 사건, 값, 프로세스는 Domain Concept의 분류로 기록하거나 저장소 관례에 맞춘다.

## Terminology integrity

- ID는 의미의 정체성을 나타내며 label 변경만으로 바꾸지 않는다.
- locale + bounded context당 preferred term은 하나다.
- alias는 동일 개념임이 확인된 admitted term이다.
- deprecated term에는 replacement, reason, date 또는 event를 둔다.
- 같은 label의 context별 다른 의미는 별도 ID다.
- exact equivalence는 label 유사성이 아니라 의미, qualifier, 범위의 동일성을 요구한다.
- 일반어는 domain-specific meaning이 없으면 추가하지 않는다.

다음은 hard fail이다.

- context가 다른 concept의 조용한 병합
- 의미를 바꾸면서 같은 ID의 과거 정의 덮어쓰기
- deprecated history 삭제
- 같은 locale·context에 preferred term 둘 이상
- AI 추론만으로 canonical 또는 human-verified 상태 부여

## Definition checks

정의는 다음을 통과해야 한다.

1. **Distinctive**: 인접 개념과 구별하는 특성이 있다.
2. **Non-circular**: 자기 term이나 서로 순환하는 정의에 의존하지 않는다.
3. **Scoped**: bounded context와 의미를 바꾸는 qualifier가 있다.
4. **Substitutable**: 문장 속 term을 정의로 바꿔도 본래 뜻이 유지된다.
5. **Minimal**: 절차, rationale, 예시를 정의 문장에 섞지 않는다.
6. **Grounded**: source 또는 명시적 domain owner 결정으로 추적된다.
7. **Bounded by examples**: positive example과 counterexample이 경계를 확인한다.

정의 후보에서 role, 시간 범위, 상태, 권한, 보류·hold 조건이 빠지면 qualifier 누락 후보로 보고 질문한다.

## Rule checks

각 rule에서 관련 있는 항목을 검사한다.

- 적용 context와 대상
- trigger 또는 preconditions
- 결과, 의무 또는 invariant
- 명시적 exceptions
- edge example과 counterexample
- authoritative source와 owner
- enforcement 또는 observation link: test, schema, code, policy
- 다른 rule과의 conflict 및 precedence

한시적인 feature scope나 현재 구현 편의는 지속적인 domain rule로 자동 승격하지 않는다. 아키텍처·기술 선택의 이유만 ADR 후보다.

## State model checks

각 transition은 다음 shape을 갖는다.

```text
{from-state} --[{actor}, {trigger}, {guard}]--> {to-state}
effect: {observable-domain-effect}
source: {source-id}
```

검사할 것:

- initial state와 필요한 terminal state
- 도달 불가능한 state와 빠져나올 수 없는 비의도적 state
- actor, trigger, guard, effect 누락
- prohibited transition과 실패 결과
- 동시 사건 또는 재시도의 의미
- code enum, schema constraint, test와의 drift

구현에만 존재하는 transition은 candidate drift다. 의도 확인 없이 정본에 추가하지 않는다.

## Provenance and lifecycle

- `sources`의 각 항목은 안정 ID, 확인 가능한 resource, title을 가진다.
- 원문과 normalized statement를 연결한다.
- source authority와 적용 범위를 설명한다.
- AI 생성물과 OpenWiki는 secondary discovery evidence다.
- source에는 가능한 범위에서 authority, scope, locator, version 또는 commit, observed date를 보존한다.
- 사람이 실제로 확인한 경우에만 `verified`에 사람 식별자 또는 역할과 시점을 기록한다.
- source가 변경·삭제되거나 정해진 freshness를 넘으면 `needs-review` 또는 stale로 표시한다.
- 두 권위 source가 충돌하면 기존 canonical statement를 바꾸지 않고 challenge와 양쪽 source를 기록해 `stable/disputed` 또는 `stable/needs-review`로 둘 수 있다. 새 concept가 아직 draft라면 `draft/disputed`다.

Open Knowledge Format v0.2를 표방하면:

- `status`는 `draft`, `stable`, `deprecated` 중 하나다.
- 제품 흐름 상태는 `workflow_status`로 분리한다.
- `sources[].id`를 citation identity로 사용한다.
- `generated`, `verified`, `stale_after`는 실제 정보가 있을 때만 쓴다.
- claim-level attribution에는 안정 source ID를 사용하고 `claim_kind`와 `review_state`를 분리한다. OKF bundle을 표방하면 body footnote label을 `sources[].id`와 연결한다.
- 전체 bundle 규칙을 충족하지 않으면서 OKF compliant라고 선언하지 않는다.

## Impact audit

의미 있는 변경 전에 inbound·outbound 관계를 검색한다.

- 다른 Domain Concept, Rule, State Model
- PRD의 term, rule, requirement, acceptance criteria
- ADR의 context와 consequences
- 코드 symbol, test name, schema enum, API field
- 문서 index와 파생 wiki

찾은 문자열이 실제 semantic reference인지 확인한다. confirmed affected link와 단순 text match를 구분한다.

## Review result

발견을 다음으로 분리한다.

- `blocking`: identity, context, 권위, semantic change가 미결정
- `needs-review`: source drift, qualifier, relation, verification이 불충분
- `safe-editorial`: 의미를 바꾸지 않는 링크·오탈자·형식 변경

각 finding에는 대상 ID, 근거, 변경 종류, 영향, owner 또는 확인 질문을 둔다.

## Lifecycle graph

- `supersedes`와 `superseded_by`는 양방향이며 target이 존재한다.
- rename은 기본적으로 ID와 path를 유지한다.
- merge는 삭제가 아니라 deprecated tombstone과 canonical replacement를 남긴다.
- split은 기존 ID를 deprecated하고 새 IDs와 mapping을 만든다.
- graph에 cycle이 없어야 한다.
- `stable/disputed`는 기존 canonical statement가 그대로라는 뜻이다. 대체 의미를 같은 ID에 쓰지 않는다.
