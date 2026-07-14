---
name: to-commit
description: Organizes working-tree changes into coherent, verified commits with English Conventional Commit messages. Use when creating, staging, splitting, amending, squashing, or rewriting Git commits, or before another workflow runs git commit.
---

# To Commit

현재 작업 트리의 변경을 리뷰와 추적에 유용한 하나 이상의 커밋으로 정리한다.

## 입력

- 저장소의 명시적인 커밋 정책과 검증 명령
- `git status --short`, 관련 diff와 기존 commit history
- 현재 작업과 사용자가 미리 만들어 둔 변경의 경계

## 워크플로우

1. 저장소 정책과 현재 branch 상태를 확인한다.
2. status와 diff를 읽고 관련 없는 변경, generated file과 기존 사용자 변경을 구분한다.
3. 아래 기준으로 커밋 단위와 순서를 먼저 정한다.
4. 파일 전체가 한 단위라면 해당 경로만 staging한다. 한 파일에 여러 단위가 섞였다면 `git add -p` 또는 동등한 방식으로 해당 hunk만 staging한다.
5. `git diff --cached`로 실제 커밋 범위를 다시 확인한다.
6. 해당 단위를 증명하는 가장 좁고 완전한 검증을 실행한다.
7. 영어 Conventional Commit 메시지로 커밋한다.
8. 남은 변경에 같은 절차를 반복하고 최종 status와 commit 목록을 확인한다.

## 커밋 단위

- 한 커밋은 결과를 한 문장으로 설명할 수 있는 하나의 주제만 담는다.
- 하나의 동작을 이루는 구현과 테스트는 같은 커밋에 둔다.
- 준비 리팩터링, 동작 변경, 독립적인 문서·설정 변경은 의도가 다르면 나눈다.
- 파일 종류나 작업 시간순으로 기계적으로 나누지 않는다.
- history는 `준비 → 동작 변경 → 독립 문서·설정`처럼 논리적 흐름을 보여준다.
- 각 커밋은 가능한 한 checkout, test와 build가 가능한 상태를 유지한다.

## 메시지

```text
<type>[optional scope]: <description>
```

- 제목은 영어 한 줄로 작성하고 마침표로 끝내지 않는다.
- `feat`, `fix`, `docs`, `refactor`, `test`, `build`, `ci`, `chore`, `perf`, `revert` 중 의미가 맞는 type을 사용한다.
- scope는 구분에 실제로 도움이 될 때만 사용한다.
- 파일이나 테스트 작업을 나열하지 말고 전달되는 결과를 설명한다.
- 관련 없는 내용을 `and`로 연결해야 한다면 커밋을 나눈다.
- `WIP`, `fix2`, `final update`, `address review` 같은 작업 기록을 남기지 않는다.

```text
refactor(installer): isolate host availability checks
fix(installer): report unavailable host directories
docs(installer): explain host directory requirements
```

## 중단 조건

- 변경의 소유권이나 범위가 불명확하면 staging 전에 사용자에게 확인한다.
- `git diff --cached` 검토나 해당 단위에 필요한 검증을 생략했거나 완료하지 못하면 blocker를 보고하고 변경을 커밋하지 않는다.
- 검증에 실패하면 이유를 보고하고 승인 없이 커밋하지 않는다.
- 공유된 history의 rewrite나 force-push가 필요하면 영향과 복구 방법을 설명하고 명시적인 승인을 받는다.
- 관련 없는 사용자 변경을 숨기거나 자동으로 함께 커밋하지 않는다.

## 결과 보고

생성하거나 수정한 commit hash와 메시지, 실행한 검증, 남은 변경과 blocker를 정확히 보고한다. Push와 PR 생성은 수행하지 않는다.
