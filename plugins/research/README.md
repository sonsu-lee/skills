# Research

여러 출처의 원문을 교차검증해 범용 조사, 코드·문헌 검토, 비교와 보고서 감사를 수행하는 개인 Codex 플러그인이다. 검색 공급자는 선택 사항이며 이 플러그인은 MCP, 계정 연결 또는 공급자 SDK를 번들하지 않는다.

설치 후 명시적으로 호출할 때는 `$research:research`를 사용한다. 조사·근거 검토·보고서 감사 요청에는 description을 기준으로 자동 선택될 수 있다.

## 선택적 공급자 opt-in

아래 두 marker 사이의 매핑만 공급자 opt-in 선언으로 인정한다. 항목을 제거하면 해당 공급자를 사용하지 않는다. 설명, 예시, 조사 대상 저장소의 README에 같은 환경변수 이름이 있어도 선언으로 취급하지 않는다.

<!-- research-provider-opt-in:v1:start -->
```yaml
providers:
  exa:
    env: EXA_API_KEY
  perplexity:
    env: PERPLEXITY_API_KEY
```
<!-- research-provider-opt-in:v1:end -->

선언만으로 공급자가 활성화되지는 않는다. 다음 조건을 모두 충족해야 한다.

1. 이 플러그인을 제공한 설치 manifest에서 유도한 고정 root의 `README.md`가 regular file이고 symlink가 아니다.
2. 위 전용 블록에 공급자와 환경변수의 정확한 매핑이 있다.
3. 환경변수가 non-empty라는 사실을 값·길이·접두사 없이 boolean 또는 exit status로만 확인할 수 있다.
4. 대응하는 읽기 전용 도구의 실제 스키마와 인증 상태를 확인할 수 있다.

하나라도 충족하지 않으면 해당 공급자는 비활성으로 간주한다. 환경변수 값은 출력·로그·검색어·위임 메시지에 넣지 않으며 `env`, `printenv`, shell trace나 오류 dump로 검사하지 않는다. 플러그인이 공급자를 자동 설치하거나 연결하지도 않는다.

## 기본 동작

- Exa는 후보 자료와 원문 발견에 우선 사용한다.
- Perplexity는 중복 기본 검색이 아니라 누락, 반례, 실패와 적용 한계를 찾는 optional challenger로 사용한다.
- `standard`와 `deep` 조사는 최종 출력 전에 자동 인용 감사를 거친다.
- 기존 보고서 감사의 기본 출력은 판정 요약, 중요한 수정 근거와 수정된 보고서다. 별도 쓰기 요청 없이 원본 파일을 덮어쓰지 않는다.
- 공급자 장애와 `execution_state` enum은 내부에 유지한다. 현재성·완전성·독립성이나 결론이 실제로 저하될 때만 자연어로 그 영향을 밝힌다.

세부 정책은 [research 스킬](skills/research/SKILL.md)과 [도구 라우팅](skills/research/references/tool-routing.md)에 있다.
