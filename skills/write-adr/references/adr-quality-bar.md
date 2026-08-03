# ADR Quality Bar

## Significance gate

다음 질문 중 하나 이상에 `yes`면 별도 기록이 유용할 가능성이 높다.

- 되돌리기 어렵거나 변경 비용이 큰가?
- 여러 팀, 시스템, 컴포넌트 또는 저장소에 영향을 주는가?
- 보안, 개인정보, 규제, 데이터, API, 신뢰성 같은 경계를 정하는가?
- 실제로 기각한 대안을 나중에 다시 논의할 가능성이 있는가?
- 의도적 부채, 예외, 위험 수용이 있는가?
- 결과물만 보고 rationale를 복원하기 어려운가?

모두 `no`면 issue, pull request, code comment처럼 더 가까운 기록을 우선 검토한다.

## Required contract

모든 기록에 다음이 있어야 한다.

- 안정 ID, `kind: architecture`, title, document `status`, decision `workflow_status`
- 한 문장의 decision statement
- decision scope와 context
- decision makers 또는 아직 미정이라는 명시
- decision drivers
- 실제 고려한 options와 status quo 여부
- outcome 또는 proposed outcome
- rationale의 근거 유형과 source
- positive, negative, neutral consequences 중 실제 관련 항목
- confirmation 방식 또는 확인이 아직 미정이라는 표시
- event-based revisit trigger 또는 재검토가 필요 없는 이유
- 관련 PRD, Domain Doc, ADR, evidence link

짧은 결정은 짧게 기록한다. 내용이 없는 섹션을 문구로 채우지 않는다.

## Workflow status rules

| `workflow_status` | 필수 증거 | 금지 |
|---|---|---|
| proposed | 제안자, 제안된 선택, 열린 쟁점 | 승인된 것처럼 서술 |
| accepted | 권한 있는 decision maker의 명시적 승인과 확인 시점 또는 신뢰할 수 있는 승인 source | 모델 추천·침묵·코드 존재만으로 승인 추론 |
| rejected | 실제로 검토한 proposal, 기각 주체와 실제 이유 | 적용 결과를 accepted처럼 서술 |
| deprecated | 더 이상 권장하지 않는 이유와 현재 영향 | 과거 선택·rationale 삭제 |
| superseded | 유효한 새 ADR 링크와 양방향 관계 | 기존 본문을 새 결정에 맞춰 재작성 |

`implemented`는 document status나 decision workflow가 아니다. Confirmation event로 기록한다.

각 non-proposed workflow transition은 frontmatter `status_events`에 안정 event ID, from/to document status와 workflow status, actor, authority source, evidence source, evidence kind, occurred time 또는 명시적 unknown, scope를 기록한다. 이 배열이 상태 이력의 유일한 정본이며 본문은 최신 event ID만 참조한다. 마지막 event의 `to_status`와 `to_workflow_status`는 현재 frontmatter 값과 같아야 한다. 고위험 decision은 `user_attestation`만으로 accepted 처리하지 않는다.

## Provenance of rationale

각 rationale 항목을 분류한다.

- `evidence`: 데이터, 사용자 조사, repository artifact, 정책처럼 확인 가능한 사실
- `constraint`: 반드시 지켜야 하는 외부 또는 내부 제한
- `assumption`: 결정 당시 참이라고 가정했으나 검증되지 않은 전제
- `judgment`: decision maker의 경험, 가치, 우선순위 판단
- `unknown`: source에서 복원할 수 없는 내용

다음은 hard fail이다.

- 실제로 논의하지 않은 option을 과거 사실로 추가
- “업계 표준”, “최선”, “간단함” 같은 순환·무출처 rationale
- 개인 선호를 객관적 evidence로 표시
- dissent, uncertainty, negative consequence 숨김
- 과거 기록에 없는 rationale를 모델이 채움
- 가짜 source, 승인자, 날짜, threshold

현재 사람이 과거 이유를 회상한 것은 `retrospective account`로 표시하고 당시 기록과 구분한다.

## Option quality

- 한 option은 실제로 가능한 coherent choice다.
- 실제 status quo 또는 do-nothing이 논의됐다면 포함한다.
- 선택된 option과 rejected option을 같은 수준의 구체성으로 서술한다.
- 선택하지 않은 안을 허수아비로 만들지 않는다.
- trade-off는 driver별 차이를 보여 주되 근거 없는 점수표를 만들지 않는다.
- 다른 독립 결정이 option 안에 섞이면 별도 ADR로 분리한다.

## Consequence and confirmation checks

각 consequence에는 `observed | expected | unknown`을 구분하고 가능하면 owner 또는 source를 둔다. 이 결정 때문에 새로 생기는 운영 비용, lock-in, migration, 사용자 harm, 접근성, 보안, 개인정보, 팀 의존성을 관련 있는 만큼 확인한다.

Confirmation Plan은 관찰 가능해야 한다.

- test 또는 automated check
- 시스템 metric 또는 운영 observation
- policy, security, privacy review
- architecture fitness function
- 정해진 stakeholder verification

확인 방법을 알 수 없으면 꾸며내지 않고 open item으로 둔다.

Confirmation Event는 append-only이며 criterion ID, date, `pending | passed | failed | unknown`, actor, evidence를 가진다. 실패는 accepted status를 자동 변경하지 않는다.

## Revisit and deliberate debt

calendar reminder보다 decision assumptions와 직접 연결된 event를 우선한다.

- 원래 assumption이 깨짐
- 비용, 처리량, 오류율, 지원 부담이 decision maker가 정한 조건을 넘음
- 법률, 기술 정책, 계약, threat model 변경
- 의존 기술의 지원 종료 또는 capability 변화
- 반복적인 workaround나 예외 증가
- 시스템 경계, 사용량, 운영 context 변경

임시 선택에는 debt가 deliberate인지, reason, mitigation, owner, trigger를 기록한다. 수치 조건은 source가 있을 때만 쓴다.

## Supersession integrity

- 새 ADR의 `supersedes`와 이전 ADR의 `superseded_by`가 서로 가리킨다.
- 새 successor가 `stable/accepted`이고 valid accepted status event를 가져야 이전 record가 `deprecated/superseded`가 될 수 있다.
- proposed successor는 `proposes_to_supersede`만 사용하고 이전 accepted record를 변경하지 않는다.
- 대상 파일과 ID가 존재한다.
- chain에 cycle이 없다.
- 이전 기록의 decision, context, 당시 rationale는 semantic hash 관점에서 보존된다.
- 새 결정의 context에는 무엇이 바뀌어 재검토했는지 적는다.
- `deprecated/superseded` record의 마지막 status event는 그 전환을 나타내며, 같은 작업에서 accepted된 matching successor가 존재해야 한다.

불변 영역은 Decision, 당시 Context, Decision Drivers, Considered Options, Outcome and Rationale, 최초 decided_at, 원래 approval actor와 source다. status·confirmation·review·errata events와 `superseded_by`는 append-only다.

## Review result

finding을 다음으로 분류한다.

- `blocking`: decision statement, authority, status, actual rationale, conflicting source가 불명확
- `important`: consequence, confirmation, revisit trigger, trace link가 부족
- `editorial`: 의미를 바꾸지 않는 링크·표현·형식 개선

각 finding에 위치, evidence, 역사 왜곡 위험, proposed action을 포함한다.
