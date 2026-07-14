# Codex preparation reference

마지막 확인: 2026-07-14

Codex metadata, invocation, MCP 또는 배포를 실제로 요청받았을 때만 현재 공식 문서와 함께 확인한다.

## Skill과 discovery

- Codex는 repository의 `.agents/skills` 경로와 user의 `~/.agents/skills` 등 공식 discovery 위치에서 skill을 찾는다.
- 일반 소비 프로젝트에서는 `.agents/skills/<skill-name>`을 canonical로 직접 사용한다.
- runtime trigger는 portable `SKILL.md`의 `description`이 결정한다. 명시 호출과 적용 가능한 암시 호출을 각각 평가한다.
- `agents/openai.yaml`은 canonical 디렉터리 안에서 UI metadata, invocation policy와 tool dependency만 확장한다.
- 기본 interface는 `display_name`, `short_description`, `$skill-name`을 포함한 `default_prompt`다. 실제 asset이나 요청이 없으면 icon과 색상을 추가하지 않는다.
- `policy.allow_implicit_invocation`의 기본값은 `true`다. 기본 동작이면 생략하고, 자동 선택이 부적절하다는 근거가 있을 때만 끈다.

## MCP

- 실제 workflow에 필요한 MCP server만 선언한다.
- server 식별자, description, transport와 URL을 현재 연결 정보에서 확인한 뒤 `dependencies.tools`에 둔다.
- MCP metadata는 권한 확인이나 외부 쓰기 승인을 대신하지 않는다.

## Plugin과 marketplace

- 사용자가 packaging을 명시적으로 요청했을 때만 현재 공식 계약과 내장 `$plugin-creator`를 사용한다.
- plugin entry point와 component path는 생성 시점의 공식 문서와 creator validator로 확인한다.
- skill, hook, asset, MCP와 app component는 실제 요청에 필요한 것만 포함한다.
- marketplace는 plugin과 별도 요청으로 취급한다.
- publisher, version, marketplace policy, authentication, category와 install metadata를 추측하지 않는다. 필요한 값이 없으면 누락을 보고하고 중단한다.

## 검증

- Agent Skills validator로 canonical skill을 검증한다.
- `agents/openai.yaml`이 있으면 interface 필드, `$skill-name` prompt와 요청한 policy·dependency만 포함하는지 확인한다.
- plugin을 만들었으면 `$plugin-creator`의 현재 검증 흐름과 새 Codex task에서의 실제 로드를 확인한다.
- 변경된 파일, 명시·암시 invocation 결과, plugin 또는 marketplace가 생략된 이유를 구분해 보고한다.

## 공식 출처

- [Build skills](https://learn.chatgpt.com/docs/build-skills)
- [Build plugins](https://learn.chatgpt.com/docs/build-plugins)
- [Agent Skills specification](https://agentskills.io/specification)
