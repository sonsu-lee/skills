# 초기 외부 스킬 구성 결정

작성일: 2026-07-12
주제: 개인 스킬 저장소의 첫 외부 카탈로그와 설치 profile 범위
리서치 모드: workflow-update-review
확신도: 높음
검색 기준일: 2026-07-12

## 핵심 답변

첫 카탈로그는 React profile 하나와 네 개의 선택 add-on만 공개하는 구성이 적절하다. 저장소 전체나 인기 스킬을 한꺼번에 설치하지 않고, 공용 스킬은 upstream에서 직접 설치하며 plugin·내장 기능·외부 도구는 호스트별 provider로 분리한다.

초기 등록 대상은 Vercel의 React 계열 다섯 개, Matt Pocock의 alignment closure 네 개와 `find-skills`다. Ponytail, `skill-creator`, Codex-for-Claude와 Paperclip은 공용 스킬로 평탄화하지 않고 plugin, host-native capability, tool 또는 reference로 기록한다.

## 주요 결론

- 기본 profile은 `react` 하나로 시작하고 `vercel-composition-patterns`, `vercel-react-best-practices`만 포함한다.
- `view-transitions`, `design-review`, `docs-writing`, `alignment`는 명시적으로 선택하는 add-on으로 둔다.
- `find-skills`와 `skill-authoring`은 저장소 성격과 무관하므로 profile이 아니라 전역 capability로 취급한다.
- Matt의 `grill-me`는 `grilling`, `grill-with-docs`는 `grilling`과 `domain-modeling`에 의존한다. 사용자가 처음 열거한 세 항목만 설치하면 현재 upstream의 의도된 동작이 완성되지 않는다.
- Ponytail은 hooks와 mode 상태를 포함한 provider plugin으로, `skill-creator`는 호스트별 내장 또는 공식 plugin으로 설치한다. 같은 이름의 standalone copy를 추가하지 않는다.
- `getpaperclipai/paperclip`은 설치 source로 사용하지 않는다. 현재 정식 프로젝트는 `paperclipai/paperclip`이며 일반 스킬이 아닌 별도 agent orchestration 도구다.

## 분석

### 1. 기본 profile은 trigger surface가 좁아야 한다

초기 후보를 모두 React profile에 넣으면 일반적인 파일 수정에도 성능, 컴포지션, 애니메이션, UI 감사와 문서 검토가 동시에 후보가 된다. 이는 설치 편의는 높이지만 실제 활성화 충돌과 반복 지시를 늘린다.

`vercel-composition-patterns`는 boolean prop 확산, compound component, context와 재사용 API 설계에 초점이 있다. `vercel-react-best-practices`는 데이터 fetching, waterfall, bundle, rendering과 성능 검증에 초점이 있다. 두 역할은 보완적이므로 React 저장소의 기본 profile에 함께 둘 수 있다. 두 스킬 모두 `rules/`와 compiled `AGENTS.md`를 직접 참조하므로 upstream의 skill directory 전체가 설치 단위다.

적용 우선순위는 다음과 같이 제한한다.

1. 컴포넌트 API와 composition 문제가 중심이면 composition skill이 설계를 소유한다.
2. 데이터, 렌더링, bundle 또는 성능이 중심이면 best-practices skill이 구현과 검증을 소유한다.
3. 둘 다 관련되면 composition이 API 형태를 정하고 best-practices는 성능 검증만 담당한다.
4. 단순 React 파일 편집이라는 이유만으로 두 스킬을 모두 강제하지 않는다.

### 2. 좁거나 무거운 기능은 add-on으로 격리한다

`vercel-react-view-transitions`는 React canary 또는 Next.js의 최신 View Transition API와 네 개의 reference 문서를 전제로 한다. 애니메이션을 요청하거나 실제 View Transition API를 사용할 때만 가치가 있으므로 `view-transitions` add-on이 맞다.

`web-design-guidelines`와 `writing-guidelines`는 로컬 규칙을 포함하지 않고 실행할 때마다 별도 Vercel 저장소의 `main/command.md`를 가져온다. 따라서 설치 commit만으로 실행 내용을 재현할 수 없고 network fetch capability가 필요하다. 두 항목은 각각 `design-review`, `docs-writing` add-on에서 명시적으로 사용하며 runtime source를 카탈로그에 표시한다. `docs-writing`은 README, ADR, API 문서와 prose review에만 사용하고 코드 작성, commit message와 일반 대화에는 적용하지 않는다.

### 3. Matt alignment 항목은 네 개가 하나의 closure다

현재 Matt Pocock upstream에서 다음 관계가 확인된다.

```text
grill-me ───────────> grilling
grill-with-docs ────> grilling
grill-with-docs ────> domain-modeling
domain-modeling ────> CONTEXT-FORMAT.md
domain-modeling ────> ADR-FORMAT.md
```

따라서 `alignment` add-on은 다음 네 skill directory를 같은 source revision에서 설치한다.

- `grilling`
- `grill-me`
- `domain-modeling`
- `grill-with-docs`

이 add-on은 계획, 설계 또는 도메인 용어를 실제로 stress-test할 때 명시적으로 선택한다. 기본 planning workflow에 자동으로 연결하지 않는다. `grill-me`와 `grill-with-docs`의 `disable-model-invocation`은 Claude Code 확장 metadata이므로 다른 호스트에서도 동일한 강제력이 있다고 가정하지 않는다.

### 4. profile 밖 capability는 provider로 분리한다

`find-skills`는 `npx skills`, skills.sh와 network를 이용해 다른 스킬을 검색하고 설치까지 제안한다. 특정 저장소 종류와 무관하고 description 범위가 넓으므로 project profile이나 add-on에 넣지 않는다. 설치기가 지원하는 전역 utility로만 기록한다.

`skill-authoring`도 하나의 shared `skill-creator` 파일로 만들지 않는다.

- Codex는 시스템 `skill-creator`를 사용하고 별도 설치하지 않는다.
- Claude Code는 공식 `skill-creator@claude-plugins-official` provider를 사용한다.

이렇게 하면 두 호스트의 같은 basename이 `.agents/skills`에서 충돌하지 않는다.

### 5. plugin과 tool을 skill로 추출하지 않는다

Ponytail은 여섯 스킬뿐 아니라 hooks와 mode state를 함께 제공한다. standalone skill과 plugin을 동시에 설치하면 같은 trigger와 항상 적용되는 지시가 중복될 수 있다. 카탈로그에는 Ponytail plugin provider 하나만 기록하고 개별 스킬을 shared profile에 추가하지 않는다.

OpenAI `codex-plugin-cc`의 `adversarial-review.md`는 일반 skill이 아니라 Claude Code plugin command다. `${CLAUDE_PLUGIN_ROOT}`의 scripts, prompt, schema와 Codex CLI에 의존하므로 `/codex:adversarial-review`를 제공하는 plugin 전체가 설치 단위다.

사용자가 제시한 `getpaperclipai/paperclip`은 정식 upstream으로 사용하지 않는다. 정식 `paperclipai/paperclip`은 Node server와 React UI를 포함하는 agent orchestration control plane이며, 내부 `paperclip` skill은 해당 runtime의 API와 인증 환경에 의존한다. 일반 Agent Skill로 추출하지 않고 tool/reference 항목으로만 남긴다.

## 비교 또는 판단 프레임

| 공개 항목 | 구성 | 활성 범위 | 초기 상태 |
| --- | --- | --- | --- |
| profile `react` | composition-patterns, react-best-practices | React component API와 성능 작업 | 등록 |
| add-on `view-transitions` | react-view-transitions | 명시적 animation 작업 | 등록 |
| add-on `design-review` | web-design-guidelines | UI/UX/a11y review | 등록 |
| add-on `docs-writing` | writing-guidelines | 문서와 prose review | 등록 |
| add-on `alignment` | grilling closure 네 개 | 계획·설계·도메인 stress-test | 등록 |
| global `discovery` | find-skills | 스킬 검색과 설치 지원 | 등록, profile 제외 |
| capability `skill-authoring` | Codex built-in, Claude plugin | 스킬 작성·평가 | provider만 등록 |
| Ponytail | multi-host plugin | 최소화 workflow와 hooks | plugin 후보 |
| Codex-for-Claude | Claude Code plugin | adversarial review 등 | plugin 후보 |
| Paperclip | 별도 application/tool | 지속 agent orchestration | reference-only |

## 리스크와 한계

- `web-design-guidelines`와 `writing-guidelines`는 실행 시 외부 `main`을 읽으므로 설치 revision과 실제 규칙 revision이 다를 수 있다.
- Vercel의 두 runtime-fetch wrapper와 `find-skills`는 개별 frontmatter에 license가 없고 repository README 또는 실제 runtime source의 MIT 표기에 의존한다. 이 저장소는 소스를 재배포하지 않지만 카탈로그에 근거 수준을 표시해야 한다.
- `disable-model-invocation` 같은 host 확장 metadata는 다른 호스트에서 무시될 수 있다. explicit 사용 정책은 설치 위치 또는 host-native 설정으로 보장해야 한다.
- profile 이름과 구성은 초기값이다. 실제 사용에서 중복 trigger가 반복되면 기본 profile에서 해당 항목을 빼고 add-on 또는 on-demand로 낮춘다.
- 이번 평가는 배포 구조와 activation surface를 검토한 것이며, 각 rule의 기술적 정확성을 모두 검증한 것은 아니다. React와 Next.js의 시간 민감 API는 사용 시 공식 문서를 다시 확인한다.

## 실행 권고

1. 다음 PR에서 위 항목만 machine-readable catalog에 등록한다. 외부 소스 파일은 포함하지 않는다.
2. catalog validator는 ID 중복, 존재하지 않는 dependency, dependency cycle, profile 중복과 provider 누락을 검사한다. 검증 실패 시 catalog 변경을 되돌린다.
3. installer는 `react` profile 하나와 네 add-on만 공개하고, `discovery`와 `skill-authoring`은 별도 capability 경로로 처리한다.
4. `web-design-guidelines`와 `writing-guidelines` 설치 결과에는 runtime network dependency를 표시한다.
5. Ponytail과 Codex-for-Claude는 초기 project profile에서 제외하고 사용자가 plugin을 선택할 때 host provider로 추가한다.
6. 첫 실제 설치 후 같은 명령의 반복 실행, `.agents/skills` SSOT, Claude symlink와 host-native 이름 충돌이 없는지 검증한다. 충돌이 생기면 해당 항목을 profile에서 제거하고 on-demand로 되돌린다.

## 참고 출처

### 내용 근거

- Agent Skills specification: https://agentskills.io/specification
- OpenAI Build skills: https://learn.chatgpt.com/docs/build-skills
- Claude Code skills: https://code.claude.com/docs/en/slash-commands
- Claude Code official skill-creator: https://code.claude.com/docs/en/slash-commands#run-evals-with-skill-creator
- Vercel Agent Skills snapshot: https://github.com/vercel-labs/agent-skills/tree/f8a72b9603728bb92a217a879b7e62e43ad76c81
- Vercel composition patterns: https://github.com/vercel-labs/agent-skills/tree/f8a72b9603728bb92a217a879b7e62e43ad76c81/skills/composition-patterns
- Vercel React best practices: https://github.com/vercel-labs/agent-skills/tree/f8a72b9603728bb92a217a879b7e62e43ad76c81/skills/react-best-practices
- Vercel React view transitions: https://github.com/vercel-labs/agent-skills/tree/f8a72b9603728bb92a217a879b7e62e43ad76c81/skills/react-view-transitions
- Vercel web design guidelines: https://github.com/vercel-labs/agent-skills/blob/f8a72b9603728bb92a217a879b7e62e43ad76c81/skills/web-design-guidelines/SKILL.md
- Vercel writing guidelines: https://github.com/vercel-labs/agent-skills/blob/f8a72b9603728bb92a217a879b7e62e43ad76c81/skills/writing-guidelines/SKILL.md
- Vercel find-skills snapshot: https://github.com/vercel-labs/skills/blob/3176ae424e50bb7d3f20a7e085f31912b3f325d2/skills/find-skills/SKILL.md
- Matt Pocock Skills snapshot: https://github.com/mattpocock/skills/tree/391a2701dd948f94f56a39f7533f8eea9a859c87
- Matt domain-modeling: https://github.com/mattpocock/skills/tree/391a2701dd948f94f56a39f7533f8eea9a859c87/skills/engineering/domain-modeling
- Matt grill-with-docs: https://github.com/mattpocock/skills/blob/391a2701dd948f94f56a39f7533f8eea9a859c87/skills/engineering/grill-with-docs/SKILL.md
- Matt grill-me: https://github.com/mattpocock/skills/blob/391a2701dd948f94f56a39f7533f8eea9a859c87/skills/productivity/grill-me/SKILL.md
- Matt grilling: https://github.com/mattpocock/skills/blob/391a2701dd948f94f56a39f7533f8eea9a859c87/skills/productivity/grilling/SKILL.md
- Ponytail snapshot: https://github.com/DietrichGebert/ponytail/tree/14a0d79548d4de8fc2de95c1b94bb0de63a739d3
- OpenAI Codex-for-Claude snapshot: https://github.com/openai/codex-plugin-cc/tree/db52e28f4d9ded852ab3942cea316258ae4ef346
- Paperclip official repository: https://github.com/paperclipai/paperclip

### 형식 참고

- Local AI research workflow report standard
