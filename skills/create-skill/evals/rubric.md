# 스킬 생성 행동 평가

`cases.json`의 사례를 깨끗한 문맥에서 실행해 명시적 호출 경계, 신규 생성 판단과 단일 목표 응집성을 검증한다. 이 스킬은 Codex 내장 `skill-creator`와 자연어 트리거가 겹치므로 `agents/openai.yaml`의 `allow_implicit_invocation: false`를 필수 정책으로 취급한다.

## 평가 절차

1. 라우팅 평가에는 frontmatter description과 `agents/openai.yaml`의 policy만 제공한다.
2. `should_trigger: true` 사례는 명시적 `$create-skill` 호출을 보존하고 대상 스킬과 필요한 reference만 제공한다.
3. `should_trigger: false` 사례에서는 이 스킬을 제공하지 않으며, 암시적 신규 생성 요청은 내장 `skill-creator` 경로로 남겨 둔다.
4. 행동 평가에는 원시 요청과 격리된 임시 작업 공간만 제공하고 저자의 기대 답이나 이전 실패 분석은 숨긴다.
5. 생성 전후 파일 목록과 hash를 비교해 기존 스킬이나 범위 밖 파일이 바뀌지 않았는지 확인한다.
6. `split: holdout` 사례는 수정에 사용하지 않고 마지막 회귀 검사에서 실행한다.

## assertion

| 범주 | 통과 조건 |
| --- | --- |
| `respect_explicit_only_policy` | 명시적 `$create-skill` 호출이 없는 요청에서 이 스킬을 암시적으로 활성화하지 않음 |
| `confirm_single_user_goal`, `derive_single_user_goal` | 결과 중심의 주된 사용자 목표를 한 문장으로 표현하고 독립 목표가 섞이지 않았음을 확인 |
| `detect_independent_goals`, `split_or_compose_skills`, `explain_goal_boundaries` | 독립 트리거·입력·성공 기준을 가진 목표를 분리하거나 기존 스킬 조합으로 라우팅하고 경계를 설명 |
| `search_existing_skills`, `classify_before_writing` | 이름이 아니라 기능으로 기존 스킬을 찾고 `CREATE_NEW` 여부를 파일 생성 전에 판정 |
| `create_new_skill_only`, `preserve_existing_files` | `CREATE_NEW`일 때만 새 디렉터리를 만들고 기존 스킬과 범위 밖 파일을 보존 |
| `resolve_creation_location` | 대상 호스트와 생성 위치를 확인한 뒤에만 파일을 생성 |
| `state_safe_assumptions` | 결과를 바꾸지 않는 기본값은 알리고 진행하며 중요한 공백만 질문 |
| `validate_structure_and_behavior` | 정적 검증과 대표·부정·홀드아웃 행동 평가를 구분해 실행하고 결과를 보고 |
| `report_route` | `USE_EXISTING`, `COMPOSE_EXISTING`, `EXISTING_SKILL_WORK`, `CREATE_NEW`, `NO_SKILL` 중 실제 판정을 설명 |
| `route_to_existing_skill_work`, `route_to_existing_skill_review`, `handle_as_one_off_task` | 신규 생성이 아닌 요청을 해당 작업 경로로 넘기고 이 스킬을 활성화하지 않음 |

## 금지 assertion

- `implicit_create_skill_activation`: 명시 호출이 없는데 이 스킬을 자동 활성화
- `modify_existing_skill`: 신규 생성 workflow에서 기존 스킬을 수정
- `create_duplicate_skill`: 같은 목표의 기존 스킬이 있는데 새 스킬 생성
- `combine_independent_goals`, `create_multi_topic_skill`: 독립 목표를 한 스킬에 결합
- `overwrite_existing_target`: 경로 충돌을 무시하고 기존 파일 덮어쓰기
- `create_before_location_check`: 대상 호스트와 생성 위치를 확인하기 전에 파일 생성
- `invent_outcome_changing_requirements`: 결과를 바꾸는 정보를 근거 없이 결정
- `skip_behavior_evaluation`: 정적 validator만으로 행동 품질 통과를 주장
- `create_skill_activation`, `create_new_skill`: 부정 사례에서 신규 생성 workflow 또는 파일 생성을 수행

## 필수 gate

- 명시적 긍정 사례에서 신규 생성 판단, 단일 목표 계약과 구조·행동 검증이 모두 관찰된다.
- 모든 암시적·근접 부정 사례에서 `create-skill`이 활성화되지 않는다.
- 내장 `skill-creator`와 경쟁하는 암시 호출 정책이 다시 활성화되지 않는다.
- 기존 스킬과 범위 밖 파일은 변경되지 않는다.
- 홀드아웃의 독립 목표가 한 스킬로 합쳐지지 않는다.
- `must_not`이 하나라도 나타나면 다른 점수로 상쇄하지 않는다.
