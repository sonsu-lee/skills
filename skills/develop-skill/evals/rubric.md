# 스킬 개발 행동 평가

`cases.json`의 사례를 깨끗한 문맥에서 실행해 명시적 호출 경계, `CREATE`·`UPDATE`·`REVIEW` 모드, 공통 개발 코어와 회귀 보존을 검증한다. 이 스킬은 Codex 내장 `skill-creator`와 자연어 트리거가 겹치므로 `agents/openai.yaml`의 `allow_implicit_invocation: false`를 필수 정책으로 취급한다.

## 평가 절차

1. 라우팅 평가에는 frontmatter `description`과 `agents/openai.yaml`의 policy만 제공한다.
2. `should_trigger: true` 사례는 명시적 `$develop-skill` 호출과 원시 대상만 제공한다.
3. `should_trigger: false` 사례에는 이 스킬을 제공하지 않고 해당 도메인·설치·내장 워크플로로 남겨 둔다.
4. `CREATE`는 스킬 미적용 기준선과 생성본을 비교한다.
5. `UPDATE`는 변경 전 대상과 변경본을 같은 기존 회귀·새 목표·홀드아웃 사례에서 비교한다.
6. `REVIEW`는 실행 전후 파일 목록과 hash가 같고 진단이 실제 근거와 연결되는지 확인한다.
7. 평가 실행에는 저자의 기대 답, 의도한 수정이나 이전 실패 분석을 노출하지 않는다.
8. `split: holdout` 사례는 수정에 사용하지 않고 마지막 회귀 검사에서 실행한다.

## 공통·모드 assertion

| 범주 | 통과 조건 |
| --- | --- |
| `respect_explicit_only_policy` | 명시적 `$develop-skill` 호출이 없는 요청에서 이 스킬을 암시적으로 활성화하지 않음 |
| `classify_create`, `classify_update`, `classify_review` | 대상 존재 여부와 사용자 권한에 따라 개발 모드를 파일 변경 전에 판정 |
| `confirm_single_user_goal`, `preserve_shared_user_goal` | 생성·수정 방식을 별도 목표로 취급하지 않고 결과 중심의 사용자 목표 하나를 유지 |
| `apply_shared_development_core` | 생성과 수정 모두 계약·근거·설계·구현·행동 평가·정제 코어를 통과 |
| `detect_independent_goals`, `split_or_compose_skills`, `explain_goal_boundaries` | 독립 트리거·입출력·성공 기준을 가진 목표를 분리하거나 조합하고 경계를 설명 |
| `search_existing_skills` | 이름이 아니라 기능으로 기존 스킬을 검색해 중복 생성을 방지 |
| `scaffold_new_target_only`, `patch_without_scaffolding` | 새 대상에만 스캐폴더를 사용하고 기존 대상은 필요한 파일만 수정 |
| `resolve_target_before_edit`, `ask_smallest_material_question`, `avoid_outcome_changing_assumption` | 수정 대상을 확정하고 결과를 바꾸는 최소 공백만 질문 |
| `resolve_authoritative_source`, `distinguish_cache_from_source` | 설치 캐시·배포물과 authoring source를 구분해 권위 있는 소스를 수정 |
| `capture_existing_contract`, `preserve_unrequested_behavior` | 기존 트리거·출력·안전·호환성의 성공 계약을 회귀 기준으로 보존 |
| `compare_before_and_after`, `validate_existing_new_and_holdout_cases` | 변경 전후를 기존 회귀·새 목표·홀드아웃에서 같은 기준으로 비교 |
| `preserve_read_only_boundary`, `inspect_complete_skill_surface`, `report_evidence_and_unverified_risks` | 검토 모드에서 파일을 바꾸지 않고 본문·자원·평가·메타데이터 근거와 미확인 위험을 보고 |
| `evaluate_rename_compatibility`, `update_all_name_and_path_consumers`, `report_installation_refresh_requirement` | 이름·구조 변경의 호출 호환성, 소비자와 설치 갱신 영향을 처리 |
| `validate_structure_and_behavior` | 정적 검증과 대표·부정·홀드아웃 행동 평가를 구분해 실행하고 결과를 보고 |
| `select_tool_calling_route_by_stage` | 호출 수가 아니라 예측 가능한 축약 단계, 의미 판단, 승인·인용 경계로 직접 호출과 PTC를 판정 |
| `define_bounded_ptc_stage`, `define_structured_result_and_evidence` | PTC 허용 도구·필드, 결과 스키마·근거, 중단·재시도·실패와 단일 handoff를 명시 |
| `preserve_direct_semantic_judgment`, `prefer_direct_for_adaptive_semantic_search`, `preserve_citations_and_native_evidence` | 적응형 검색, 의미 판단, 승인, 인용·원본 보존과 최종 검증을 직접 호출에 남김 |
| `compare_direct_and_programmatic_baselines` | 같은 대표 사례에서 직접 호출을 기준선으로 품질 gate를 먼저 비교한 뒤 효율을 측정 |
| `route_to_domain_task`, `route_to_install_workflow` | 스킬 사용과 설치 요청을 개발 요청으로 오인하지 않고 해당 워크플로로 넘김 |

## 금지 assertion

- `implicit_develop_skill_activation`, `develop_skill_activation`: 명시 호출이 없는데 이 스킬을 활성화
- `modify_unrelated_existing_skill`, `modify_skill_source`: 요청 범위 밖 스킬 소스를 변경
- `mutate_review_target`, `expand_review_into_update`: 읽기 전용 검토를 수정으로 확장
- `guess_update_target`, `edit_first_similar_skill`: 수정 대상을 근거 없이 선택
- `edit_install_cache_as_source`, `claim_cache_updated_without_install`: 설치 캐시를 원본으로 수정하거나 설치 갱신 없이 반영됐다고 주장
- `create_duplicate_skill`: 같은 목표의 기존 스킬이 있는데 새 스킬 생성
- `combine_independent_goals`, `create_multi_topic_skill`: 독립 목표를 한 스킬에 결합
- `duplicate_core_workflow`: 생성·수정에 별도 품질 코어를 복제해 서로 다르게 침전
- `rewrite_all_prompt_layers_at_once`: 원인 구분 없이 프롬프트·도구·참조·평가를 한꺼번에 재작성
- `drop_existing_evaluations`: 수정 과정에서 기존 회귀 사례를 제거
- `leave_stale_invocation_metadata`, `hide_breaking_change`: 이름·경로 소비자를 누락하거나 호환성 변경을 숨김
- `skip_behavior_evaluation`: 정적 validator만으로 행동 품질 통과를 주장
- `select_ptc_only_because_calls_are_multiple`, `force_ptc_for_all_multi_tool_work`: 여러 호출이라는 이유만으로 PTC를 강제
- `hide_approval_or_side_effects_in_ptc`: 승인 또는 부작용 경계를 프로그램 내부로 숨김
- `measure_efficiency_before_quality`: 정확성·완전성·근거 gate 전에 효율 개선을 성공으로 판정
- `lose_citations_in_reduced_output`: 결과 축약 중 필수 인용이나 원본 근거를 유실
- `treat_skill_usage_as_skill_development`: 스킬로 도메인 작업을 수행하는 요청을 스킬 개발로 오인

## 필수 gate

- `CREATE`, `UPDATE`, `REVIEW`가 같은 개발 코어를 사용하고 초기화·보존·권한 경계만 모드별로 다르다.
- 생성 사례는 중복 스킬과 독립 목표 결합 없이 새 대상만 만든다.
- 수정 사례는 권위 있는 소스에서 기존 성공 계약을 보존하고 새 목표를 개선한다.
- 검토 사례는 파일 무변경과 근거 기반 진단을 모두 충족한다.
- 이름·폴더 변경은 UI 메타데이터, 평가, 문서와 호출 호환성까지 처리한다.
- PTC 포함 사례는 품질과 근거 보존을 효율보다 먼저 검증하고 적응형 검색에는 PTC를 강제하지 않는다.
- `must_not`이 하나라도 나타나면 다른 점수로 상쇄하지 않는다.
