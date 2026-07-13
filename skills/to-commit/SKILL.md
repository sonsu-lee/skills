---
name: to-commit
description: Use when creating, splitting, staging, amending, squashing, or rewriting Git commits, or before another workflow runs git commit.
---

# 커밋으로 정리하기

## 원칙

현재 변경을 작업 의도가 드러나는 하나 이상의 검증된 커밋으로 정리한다. 커밋은 작업 중 거친 순서가 아니라 리뷰와 추적에 유용한 논리적 흐름을 보여줘야 한다.

## 진행 방법

1. `git status --short`와 관련 diff를 확인한다.
2. 기존 사용자 변경과 현재 작업을 구분한다. 관련 없는 변경은 staging하지 않는다.
3. 한 문장으로 설명할 수 있는 주제별로 커밋을 나눈다.
4. 준비 리팩터링, 동작 변경, 독립적인 문서·설정 변경처럼 의도가 다르면 분리한다.
5. 하나의 동작을 이루는 구현과 테스트는 같은 커밋에 둔다. 파일 종류만으로 나누지 않는다.
6. 각 단위에 필요한 최소한의 완전한 검증을 실행한다. 시간 압박은 검증 생략의 근거가 아니다.
7. 명시적인 경로만 staging하고 `git diff --cached`로 최종 범위를 확인한다.
8. 영어 Conventional Commit 메시지로 커밋한다.

각 커밋은 가능한 한 저장소가 정상 동작하는 상태를 유지해야 한다. 실패하는 테스트만 먼저 커밋하거나 `WIP`, `fix2`, `final update`, `address review` 같은 작업 기록을 남기지 않는다.

## 메시지 형식

```text
<type>[optional scope]: <description>
```

- 제목은 영어 한 줄로 작성한다.
- `feat`, `fix`, `docs`, `refactor`, `test`, `build`, `ci`, `chore`, `perf`, `revert` 중 의미가 맞는 type을 사용한다.
- scope는 구분에 실제로 도움이 될 때만 쓴다.
- 관련 없는 내용을 `and`로 연결해야 한다면 커밋을 나눈다.
- 테스트 추가나 파일 수정을 나열하지 말고 커밋이 전달하는 결과를 설명한다.
- 마침표로 끝내지 않는다.

```text
fix(auth): preserve sessions after token refresh
refactor(installer): isolate host availability checks
docs(installer): explain host directory requirements
```

## 확인할 신호

- `git add -A`가 관련 없는 사용자 변경까지 포함한다.
- 하나의 커밋이 서로 독립적인 문제를 해결한다.
- 구현과 테스트를 기계적으로 별도 커밋으로 나눈다.
- 커밋 하나만 checkout하면 테스트나 빌드가 깨진다.
- 서두른다는 이유로 diff 확인이나 검증을 생략한다.
- 메시지가 변경 결과가 아니라 작업 과정을 설명한다.

이 신호가 있으면 커밋하기 전에 범위와 순서를 다시 정리한다.
