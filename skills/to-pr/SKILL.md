---
name: to-pr
description: Prepares and publishes focused pull requests with English Conventional Commit titles and minimal English bodies. Use when drafting or revising a PR title or body, opening a PR, or publishing a completed branch for review.
---

# To PR

완료된 branch를 하나의 주제가 분명하고 빠르게 읽히는 PR로 정리한다.

## 입력

- 사용자가 문구만 원하는지 실제 게시까지 원하는지에 대한 요청
- 저장소의 PR 정책과 target base branch
- base 대비 status, commit 목록, 전체 diff와 검증 결과

## 워크플로우

1. 요청을 `문구 작성` 또는 `PR 게시`로 구분한다.
2. base branch를 저장소 기본값과 branch 관계에서 확인한다. 후보가 여러 개면 사용자에게 확인한다.
3. base 대비 status, commit 목록과 전체 diff를 읽는다.
4. 게시 요청에 커밋되지 않은 변경이 있으면 **REQUIRED SUB-SKILL:** Use `to-commit` before publishing.
5. `to-commit`을 적용했다면 status, commit 목록과 전체 diff를 다시 읽고, 실패했거나 변경에 영향받는 검증을 재실행한다.
6. PR 전체를 한 문장으로 설명할 수 있는지 확인한다. 독립적인 주제가 섞였으면 PR을 나눈다.
7. 아래 형식으로 제목과 본문을 작성한다.
8. 문구 작성 요청이면 제목과 본문만 반환하고 외부 상태를 변경하지 않는다.
9. 게시 요청이면 관련 검증이 통과하고 해결되지 않은 blocker가 없는지 확인한다. 이후 인증 상태를 확인하고 branch를 push한 뒤 적절한 GitHub workflow로 PR을 생성하거나 갱신한다.

리뷰 대응, merge와 branch 정리는 수행하지 않는다.

## 제목

- 영어 Conventional Commit 형식을 사용한다.
- squash merge 뒤의 최종 커밋 제목으로 바로 사용할 수 있게 쓴다.
- 마지막 commit이 아니라 PR 전체 결과를 설명한다.
- 한 줄로 설명되지 않으면 제목을 늘리지 말고 PR 범위를 줄인다.

```text
fix(installer): report unavailable host directories
```

## 본문

문제 또는 목적과 변경 결과를 설명하는 짧은 영어 문장 하나를 기본값으로 사용한다. 중요한 접근 방식이나 개념이 있어야 변경을 이해할 수 있을 때만 두 번째 문장을 추가한다.

```text
Fixes silent host omissions by warning about missing project directories and failing when no requested host remains.
```

다음 내용은 리뷰 판단에 꼭 필요할 때만 넣는다.

- 호환성 문제, breaking change, 수동 migration과 알려진 제한
- 선택한 접근 방식과 그 이유

다음 내용은 기본적으로 넣지 않는다.

- `Summary`, `Testing`, `Test Plan` 같은 상투적인 제목
- 변경 파일, commit과 구현 세부사항 목록
- 통과한 일반 테스트와 실행 명령
- 제목이나 diff를 반복한 설명
- 작성 도구나 agent에 대한 메모

문장보다 실제로 더 짧고 명확할 때만 목록을 사용한다.

## 중단 조건

- base 또는 PR 범위가 불명확하면 게시 전에 사용자에게 확인한다.
- 커밋되지 않은 변경, 실패한 검증 또는 해결되지 않은 blocker가 있으면 게시하지 않는다.
- 관련 없는 여러 주제를 하나의 PR 제목으로 포장하지 않는다.
- push 권한이나 GitHub 인증이 없으면 문구와 blocker만 보고한다.

## 결과 보고

문구 작성 요청에는 정확한 영어 제목과 본문만 제공한다. 게시 요청에는 PR URL, base와 head, 제목, 상태, 실행한 검증과 남은 blocker를 보고하되 이 운영 정보로 PR 본문을 부풀리지 않는다.
