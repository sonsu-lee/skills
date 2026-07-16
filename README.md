# Personal Skills

직접 만든 portable Agent Skills를 보관하고, 외부 스킬과 호스트 플러그인의 설치 구성을 관리하는 개인 저장소입니다.

## 구조

- `skills/`: 직접 만든 스킬을 보관합니다.
- `evals/`: 개인 스킬의 trigger·output 사례와 공용 portable fixture를 관리합니다.
- `catalog/`: 외부 스킬을 소스 복사 없이 분류하고 설치 방법을 기록합니다.
- `scripts/`: profile을 해석하고 `npx skills`와 호스트 공식 설치 명령을 호출합니다.
- `docs/DESIGN.md`: 저장소의 현재 설계와 작업 원칙을 기록합니다.

외부 카탈로그에는 검토한 profile과 add-on만 등록하며 upstream 소스는 포함하지 않습니다.

### 직접 만든 스킬

| 스킬 | 용도 |
| --- | --- |
| `architecture-red-team` | 소프트웨어 아키텍처를 적대적으로 검토하고 품질 게이트 판정 |
| `to-commit` | 변경을 주제별 영어 Conventional Commit으로 정리 |
| `to-pr` | 완료된 브랜치를 짧은 영어 제목과 본문의 PR로 게시 |
| `to-skill` | Agent Skill 작성·수정·정규화와 host preparation 수행 |

`to-skill`은 새 스킬 작성, 기존 스킬 수정, 다중 host 사본 정규화와 요청된 Codex·Claude Code 준비를 하나의 안전한 workflow로 처리합니다.

## 빠른 시작

설치 전에 catalog 유효성과 실행할 명령을 확인합니다.

```bash
npm run validate
npm run skills:install -- --profile react --host codex --dry-run
```

dry-run 결과가 맞으면 `--dry-run`을 제거합니다.

```bash
npm run skills:install -- --profile react --host codex
```

여러 선택 기능과 host를 함께 지정할 수 있습니다.

```bash
npm run skills:install -- \
  --profile react \
  --with alignment \
  --with skill-authoring \
  --host codex \
  --host claude-code
```

### 선택할 수 있는 구성

| 구분 | 이름 | 용도 |
| --- | --- | --- |
| profile | `react` | React 컴포넌트 설계와 성능 지침 |
| add-on | `view-transitions` | React·Next.js View Transition 구현 |
| add-on | `design-review` | UI·UX·접근성 검토 |
| add-on | `docs-writing` | 문서와 prose 검토 |
| add-on | `alignment` | 계획·설계·도메인 모델 점검 |
| capability | `discovery` | 외부 스킬 탐색 |
| capability | `skill-authoring` | host-native 스킬 작성 도구 |

`--profile`은 한 번만 사용합니다. `--with`와 `--host`는 반복할 수 있습니다. 명시된 dependency는 자동으로 포함되며 중복 항목은 한 번만 설치됩니다.

## 설치 동작

외부 프로젝트는 이 저장소에 복사하거나 미러링하지 않습니다. 설치할 때 upstream 저장소, `npx skills` 또는 호스트의 공식 플러그인을 사용합니다.

- `shared` 스킬은 `npx skills`로 설치합니다.
- 대상 project의 `.agents/skills`를 원본 위치로 사용하며, agent 전용 경로는 기본적으로 symlink로 연결합니다.
- `host-specific` 항목은 허용된 host에서만 설치합니다.
- `host-native` builtin은 이미 사용할 수 있다고 표시합니다.
- shell에서 실행할 수 없는 plugin 명령은 자동 실행하지 않고 수동 명령으로 출력합니다.
- `claude-code`를 요청했는데 `.claude/`가 없으면 warning을 출력하고 해당 host를 건너뜁니다.
- 요청한 host를 모두 건너뛰면 외부 명령을 실행하지 않고 오류로 종료합니다.

## 다른 저장소에서 고정 버전 실행

원격 스크립트를 shell로 바로 전달하지 않습니다. 검토한 전체 commit SHA만 임시 디렉터리에 받은 다음 dry-run부터 실행합니다.

```bash
SKILLS_REF=7e852c3c8483efe19b60c90c567cf4a03940f24b
SKILLS_TMP="$(mktemp -d)"
SKILLS_REPOSITORY="$SKILLS_TMP/repository"

git init -q "$SKILLS_REPOSITORY"
git -C "$SKILLS_REPOSITORY" remote add origin \
  https://github.com/sonsu-lee/skills
git -C "$SKILLS_REPOSITORY" fetch --depth 1 origin "$SKILLS_REF"
git -C "$SKILLS_REPOSITORY" checkout -q --detach FETCH_HEAD
test "$(git -C "$SKILLS_REPOSITORY" rev-parse HEAD)" = "$SKILLS_REF"
git -C "$SKILLS_REPOSITORY" show --stat --oneline HEAD

SKILLS_REPOSITORY="$(cd "$SKILLS_REPOSITORY" && pwd -P)"

node "$SKILLS_REPOSITORY/scripts/install.mjs" \
  --profile react \
  --host codex \
  --dry-run
```

`scripts/install.mjs`, `scripts/validate-catalog.mjs`, `catalog/skills.json`, `catalog/profiles.json`을 확인하세요. 출력된 명령도 검토한 뒤 `--dry-run`을 제거합니다. 명령을 실행한 현재 디렉터리가 스킬을 설치할 대상 project가 됩니다.

```bash
node "$SKILLS_REPOSITORY/scripts/install.mjs" \
  --profile react \
  --host codex
```

실행을 마쳤거나 설치하지 않기로 했다면 임시 checkout과 shell 변수를 정리합니다.

```bash
rm -rf -- "$SKILLS_TMP"
unset SKILLS_REF SKILLS_TMP SKILLS_REPOSITORY
```

새 commit을 사용할 때는 전체 SHA와 변경 내용을 먼저 검토하고 `SKILLS_REF`만 갱신합니다.

## 검증

```bash
npm test
npm run test:e2e
npm run validate
```

자세한 경계와 설치 방향은 [`docs/DESIGN.md`](docs/DESIGN.md), 등록 원칙은 [`catalog/README.md`](catalog/README.md)를 참고하세요.
