# Git Workflow

커밋 생성, pull request 생성과 읽기 전용 변경 감사를 분리해 제공하는 개인 Codex 플러그인이다. Git과 저장소에 이미 구성된 도구를 사용하며 GitHub 인증, MCP 서버나 별도 SDK를 번들하지 않는다.

## 스킬

- `$git-workflow:create-commit`: 변경을 의미 단위로 나누고 영어 Conventional Commit 메시지로 커밋한다.
- `$git-workflow:create-pull-request`: 저장소 템플릿과 base/head diff로 PR을 준비하거나, audit gate를 통과한 경우 생성한다.
- `$git-workflow:audit-git-change`: worktree, commit range 또는 PR을 변경 없이 감사하고 findings와 수정된 보고서 산출물을 함께 제시한다.

## 공통 원칙

- PR은 하나의 승인·배포·되돌리기 단위다. 기본 선호는 squash지만 저장소가 commit 보존 전략을 쓰면 각 commit을 최종 history 기준으로 검사한다.
- 내부 commit은 그 목적을 리뷰 가능한 의미 단위로 나눈다.
- Conventional Commit 제목은 영어 한 줄이며 body와 footer는 필요할 때 허용한다.
- 저장소의 `AGENTS.md`, `CONTRIBUTING`, commitlint, hooks와 PR template을 우선한다.
- PR 제목은 Conventional Commit 형식의 전체 변경 요약이다. squash와 merge commit에서는 저장소의 실제 title/message source를 확인하고, 새 squash·merge commit과 rebase 결과의 서명을 source commit에서 추론하지 않는다.
- Before/After screenshot은 실제로 접근 가능한 이미지가 있는 시각 변경에만 선택적으로 포함한다.
- audit은 읽기 전용이며 수정된 commit plan, 메시지와 PR 초안을 제안할 수 있지만 적용하지 않는다.

GitHub 인증이나 commit signing이 샌드박스 격리 때문에 실패한 것으로 의심되면 실패를 곧바로 미인증으로 단정하지 않는다. 현재 실행 환경이 허용할 때만 제한된 외부 진단을 한 번 수행하고, commit·push·PR의 실제 상태를 다시 확인해 중복 실행을 막는다. repository-controlled hook은 host 권한 재시도의 신뢰 경계로 취급하며, 외부 권한으로 조용히 실행하지 않는다. 이 절차는 사용자가 직접 호출하는 네 번째 스킬이 아니라 생성·감사 스킬이 조건부로 읽는 내부 reference다.

플러그인의 런타임에는 Python 패키지나 PyYAML이 필요하지 않다. YAML 파일은 Codex용 정적 interface 설정이며, 별도 Python 스크립트를 번들하지 않는다.

세부 기준은 [변경 정책](references/change-policy.md)과 [호스트 인증 및 서명 재확인](references/host-auth-and-signing.md)에 있다.

세 스킬은 플러그인 공통 reference를 함께 사용하는 plugin-scoped skills다. 개별 skill 디렉터리만 따로 복사해 설치하는 방식은 지원하지 않는다.
