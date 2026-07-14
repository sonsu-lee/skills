# Claude Code preparation reference

마지막 확인: 2026-07-14

Claude Code discovery, version-sensitive symlink, 전용 frontmatter 또는 배포를 실제로 요청받았을 때만 현재 공식 문서와 함께 확인한다.

## Discovery와 symlink

- project skill은 `.claude/skills/<skill-name>/SKILL.md`, user skill은 `~/.claude/skills/<skill-name>/SKILL.md`에서 발견한다.
- 일반 소비 프로젝트에서는 `.agents/skills/<skill-name>` canonical을 `.claude/skills/<skill-name> -> ../../.agents/skills/<skill-name>` 상대 symlink로 노출한다.
- directory symlink의 공식 지원 기준은 Claude Code v2.1.203 이상이다. 로컬 대상은 `claude --version`으로 확인하고 다른 대상 환경은 그 환경의 버전을 확인한다.
- 대상 버전이 기준보다 낮거나 확인되지 않거나 실제 discovery가 실패하면 symlink를 만들거나 copy로 우회하지 않는다. 호환성 문제를 보고한다.

## Host-specific frontmatter

- portable 원본에는 `name`과 `description`만 유지한다.
- `disable-model-invocation`, `user-invocable`, `argument-hint`, `allowed-tools`, `disallowed-tools`, `model`, `context`, `agent`와 `hooks`는 요청과 대상 버전에서 필요성이 확인된 경우에만 Claude Code 배포본에 둔다.
- 기본값을 다시 쓰지 않고 tool 사전 허용을 일반 권한 확인의 우회로 사용하지 않는다.
- Claude 전용 필드가 필요하면 공용 canonical을 수정하지 않는다. 필요한 차이와 배포 경로를 별도 host-specific 작업으로 보고하고 기본 흐름에서 파생 copy를 자동 생성하지 않는다.

## Plugin과 marketplace

- 사용자가 Claude Code plugin packaging을 명시적으로 요청했을 때만 현재 공식 계약과 대상 환경의 내장 creator를 확인해 사용한다.
- 기본 component discovery로 충분하면 선택적 manifest나 custom path를 만들지 않는다.
- manifest가 필요하면 생성 시점의 공식 문서로 `.claude-plugin/plugin.json`과 component 위치를 확인한다.
- marketplace는 plugin과 별도 요청으로 취급한다.
- publisher, version, author, marketplace와 선택적 metadata를 추측하지 않는다. 필요한 값이 없으면 누락을 보고하고 중단한다.
- Claude API용 skill ZIP과 Claude Code plugin을 같은 배포 형식으로 취급하지 않는다.

## 검증

- portable canonical을 Agent Skills validator로 검증한다.
- `claude --version`, symlink 대상과 새 Claude Code session의 실제 discovery를 기록한다.
- host-specific 배포본이 승인되어 존재하면 portable 본문·resource와 요청한 frontmatter 차이만 있는지 비교한다.
- plugin을 만들었으면 현재 CLI의 validator와 실제 namespace된 명령 로드를 확인한다.

## 공식 출처

- [Extend Claude with skills](https://code.claude.com/docs/en/slash-commands)
- [Create plugins](https://code.claude.com/docs/en/plugins)
- [Plugins reference](https://code.claude.com/docs/en/plugins-reference)
- [Agent Skills specification](https://agentskills.io/specification)
