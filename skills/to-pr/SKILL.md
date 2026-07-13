---
name: to-pr
description: Use when preparing or opening a pull request, writing or revising its title or body, or publishing a completed branch for review.
---

# PR로 정리하기

## 원칙

완료된 브랜치를 하나의 주제가 분명한 PR로 만든다. 제목과 본문은 영어로 작성하며, 리뷰에 필요한 맥락만 남긴다.

## 진행 방법

1. base branch 대비 status, commit과 전체 diff를 확인한다.
2. 커밋되지 않은 변경이 있으면 **REQUIRED SUB-SKILL:** Use `to-commit` before continuing.
3. PR 전체를 한 문장으로 설명할 수 있는지 확인한다. 독립적인 주제가 섞였으면 PR을 나눈다.
4. 관련 검증이 통과했고 공개해야 할 제한이나 미해결 문제가 없는지 확인한다.
5. 아래 규칙으로 제목과 본문을 작성한다.
6. branch를 push하고 적절한 GitHub workflow로 PR을 생성하거나 갱신한다.

리뷰 대응, merge와 branch 정리는 이 스킬의 범위가 아니다.

## 제목

- 영어 Conventional Commit 형식을 사용한다.
- squash merge 뒤의 최종 커밋 제목으로 바로 사용할 수 있어야 한다.
- 마지막 커밋이 아니라 PR 전체 결과를 설명한다.
- 한 줄로 설명되지 않으면 제목을 늘리지 말고 PR 범위를 줄인다.

```text
fix(installer): report unavailable host directories
feat(catalog): add validated host providers
```

## 본문

기본값은 문제나 목적과 변경 결과를 설명하는 짧은 영어 문장 하나다. 중요한 접근 방식이나 개념이 있어야 이해할 수 있을 때만 두 번째 문장을 추가한다.

```text
Fixes silent host omissions by warning about missing project directories and failing when no requested host remains.
```

```text
Adds profile-based skill installation with repeatable add-ons. Resolves catalog dependencies before invoking upstream installers.
```

다음 내용은 꼭 필요한 경우가 아니면 넣지 않는다.

- `Summary`, `Testing`, `Test Plan` 같은 상투적인 제목
- 변경 파일, 커밋 또는 구현 세부사항 목록
- 통과한 일반 테스트와 실행 명령
- 제목이나 diff를 그대로 반복한 설명
- 작성 도구나 에이전트에 대한 메모

호환성 문제, breaking change, 수동 migration, 알려진 제한처럼 리뷰와 적용 판단에 필요한 정보는 짧게 명시한다. 목록은 문장보다 실제로 더 짧고 명확할 때만 사용한다.

## 확인할 신호

- 제목이 마지막 커밋이나 리뷰 대응만 설명한다.
- 본문이 템플릿을 채우기 위해 불필요하게 길어진다.
- 검증 결과를 본문에 적었지만 의사결정에는 도움이 되지 않는다.
- PR 하나가 서로 독립적인 여러 결과를 포함한다.

이 신호가 있으면 게시 전에 범위와 문구를 줄인다.
