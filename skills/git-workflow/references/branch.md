# Branch workflow

Git branch 이름을 준비·검사하거나 사용자가 명시적으로 요청한 branch 생성·전환·rename을 수행할 때 적용한다.

## 명명 형식

Conventional Commits에는 공식 branch 문법이 없으므로 commit의 type과 scope를 Git ref에 안전한 경로 형태로 옮긴다.

```text
<type>/<description>
<type>/<scope>/<description>
```

예:

```text
feat/add-passkey-sign-in
fix/api/reject-expired-token
refactor/git-workflow/consolidate-skills
docs/readme/document-installation
ci/release/validate-skill-catalog
```

- `type`, `scope`와 `description` segment는 소문자 영문·숫자와 내부 hyphen만 사용한다.
- `description`은 짧은 영어 kebab-case 동작 구문이며 끝에 issue 번호나 의미 없는 날짜를 자동으로 붙이지 않는다.
- `scope`는 파일명이 아니라 최종 commit·PR에서도 유지할 안정적인 컴포넌트 경계일 때만 사용한다.
- 기본 type은 `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `style`, `build`, `ci`, `chore`, `revert`다. 저장소가 허용 type을 제한하면 그 규칙을 우선한다.
- `feature`, `bugfix`, `hotfix`처럼 Conventional Commit type과 중복되는 별도 접두사와 `agent`, 사용자명, 도구명을 기본 prefix로 추가하지 않는다.
- 저장소가 ticket ID, release branch 또는 별도 prefix를 요구하면 저장소 규칙을 적용하고 파생 기본값과의 차이를 기록한다.

branch 이름은 commit header 자체가 아니다. 예를 들어 `feat/auth/add-passkey-sign-in`의 commit과 PR 제목은 `feat(auth): add passkey sign-in`이다. colon, 공백과 괄호가 있는 Conventional Commit header를 branch ref로 그대로 복사하지 않는다.

## 이름을 결정한다

1. 요청과 예상 순변경에서 주효과 하나를 고른다.
2. 주효과에 맞는 type을 정한다. 새 사용자 기능은 `feat`, 결함 수정은 `fix`, 동작을 바꾸지 않는 재구성은 `refactor`다.
3. 저장소에서 안정적인 scope가 확인될 때만 scope segment를 추가한다.
4. description이 branch의 한 결과를 설명하는지와 `and`로 독립 목적을 숨기지 않는지 확인한다.
5. `git check-ref-format --branch <name>` 또는 동등한 검사와 저장소 규칙을 모두 통과시킨다.

diff가 아직 없으면 사용자가 말한 목표만으로 후보를 만들 수 있지만, 확인되지 않은 구현 결과를 이름에 넣지 않는다. type에 따라 release 의미나 versioning이 달라지고 목표가 불명확하면 쓰기 전에 짧게 확인한다.

## 생성·전환한다

쓰기 전에 repository root, `HEAD`, 현재 branch, default/base, working tree와 진행 중인 history operation을 확인한다.

- 사용자가 base를 지정했으면 그 exact local ref를 사용한다.
- 지정하지 않았으면 확인된 remote default branch의 현재 local 또는 remote-tracking snapshot을 base로 사용하고 이름과 SHA를 기록한다.
- 검토나 branch 이름 제안만 요청받았으면 ref나 checkout을 바꾸지 않는다.
- 새 branch 또는 전체 workflow가 명시됐고 이름이 local·remote에 없을 때만 branch를 생성한다.
- 동일 이름이 있으면 대상 SHA와 worktree 사용 여부를 확인하며 기존 branch를 덮어쓰거나 강제로 재설정하지 않는다.
- detached `HEAD`에서는 확인한 base가 없거나 history operation이 진행 중이면 branch 생성을 중단한다.
- dirty worktree에서 branch 생성이 변경을 잃지 않더라도, 현재 변경이 새 branch에 이어지는 사실과 범위를 먼저 확인한다.
- 이미 non-default branch에 있으면 전체 workflow 요청만으로 자동 rename하지 않는다. 게시 전 이름 불일치와 선택 가능한 새 이름을 보고한다.

rename은 사용자가 exact old/new branch를 명시했을 때만 수행한다. published branch rename, remote ref 삭제, upstream 교체가 필요하면 이 mode에서 자동 수행하지 않는다.

완료 뒤 현재 branch, 시작 base SHA, branch `HEAD`, upstream 유무와 남은 working tree를 다시 확인한다.

## 중단 조건

- 이름이 독립적인 여러 결과를 감춘다.
- 저장소 명명 규칙과 파생 Conventional 형식이 충돌한다.
- base가 모호하거나 필요한 object가 local에 없다.
- branch가 이미 다른 SHA 또는 다른 worktree에서 사용 중이다.
- detached `HEAD`, merge, rebase, cherry-pick 또는 revert 상태에서 안전한 새-branch 경계를 확정할 수 없다.
- 요청하지 않은 rename, delete, force update 또는 remote 변경이 필요하다.

완료 조건: 이름이 최종 변경의 type·scope와 일치하고, 명시적으로 허용된 경우에만 exact base에서 branch가 생성·전환되며, 기존 refs와 사용자 변경이 보존됐다.
