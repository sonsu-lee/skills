# Git workflow 평가 자료

- `cases.json`과 `rubric.md`는 통합 진입점, branch 규칙과 mode routing의 현재 평가 계약이다.
- `regression/`은 변경 전 `create-commit`, `create-pull-request`, `review-commit`, `review-pr`의 사례와 rubric을 보존한 기준선이다.
- 기준선 사례를 통합 스킬에 적용할 때 기존 skill ID와 `expected_route`는 대응하는 `git-workflow` mode로 해석하고, 나머지 안전·행동 assertion은 그대로 유지한다.

실제 Git 쓰기와 원격 변경 평가는 원본 저장소가 아닌 격리된 임시 저장소와 테스트용 remote에서 수행한다.
