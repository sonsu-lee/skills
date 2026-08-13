# 원격 검증 재확인

PR 또는 hosted signature 증거를 읽지 못했을 때 실제 미인증과 실행 환경 격리를 구분하기 위해 사용한다. 정상 조회에서는 읽지 않는다.

## 오류를 분류한다

먼저 현재 환경의 오류를 다음 중 하나로 기록한다.

- 명시적 인증 실패: 호스트가 401·403 또는 자격증명 거부를 반환했다.
- 네트워크 실패: DNS, TLS, proxy, 연결 또는 timeout 문제다.
- 도구 부재: 필요한 connector나 CLI를 사용할 수 없다.
- 환경 격리 가능성: sandbox 안에서 credential store, agent socket, keychain 또는 host session이 보이지 않는다.
- 불명확: 오류만으로 실제 계정 상태와 환경 격리를 구분할 수 없다.

환경 안에서 credential이 보이지 않는다는 사실만으로 사용자가 실제로 로그아웃됐거나 권한이 없다고 단정하지 않는다.

## 최소 진단 원칙

- 시스템·사용자 승인 정책이 허용할 때만 PR과 동일한 host를 읽기 전용으로 최대 한 번 재확인한다.
- repository, PR 식별자, expected base/head SHA와 필요한 evidence를 사전에 고정한다.
- 구조화된 connector나 host API를 우선하고, CLI가 필요하면 exact hostname과 PR 또는 commit identifier를 literal argument로 전달한다.
- 진단 전후 local Git 상태와 원격 PR 상태가 바뀌지 않았는지 확인한다.
- 외부 진단을 사용할 수 없거나 결과가 계속 불명확하면 환경을 `unverified`로 두고 영향을 기록한다.

GitHub CLI를 사용해야 할 때 허용되는 인증 확인은 다음 수준으로 제한한다.

```text
gh auth status --active --hostname <remote-host>
```

출력에서는 계정명, credential 위치와 환경 세부사항을 불필요하게 재출력하지 않는다. token 값은 어떤 경우에도 읽거나 출력하지 않는다.

## Hosted signature 증거

- hosted verification status가 exact commit SHA에 연결되는지 확인한다.
- source commit의 verified 상태를 squash, rebase 또는 아직 생성되지 않은 merge commit의 signature로 대체하지 않는다.
- final commit이 아직 없으면 commit 상태는 `not_created`로 두고, 확인 가능한 signing path만 별도로 기록한다.
- verifier program, SSH allowed-signers·revocation file 또는 trust store가 branch/worktree-controlled이면 hosted 결과와 섞어 승인하지 않는다.
- signature evidence에 접근할 수 없으면 `unverified`로 두며 unsigned라고 추측하지 않는다.

## 금지되는 fallback

다음을 수행하지 않는다.

- `gh auth login`, `gh auth refresh`, `gh auth switch`, `gh auth token`, `--show-token`
- account, remote, protocol 또는 credential helper 변경
- fetch, push, commit, PR 생성·수정·병합
- broad full-access 요청이나 다른 host 진단
- 서명 비활성화, `--no-gpg-sign`, `commit.gpgsign=false`, `--no-verify`
- credential·key·token·개인정보 원문 출력

완료 조건: 동일 host의 읽기 증거만 추가됐고, 실패 원인과 미확인 영향이 구분되며 local·remote 상태가 바뀌지 않았다.
