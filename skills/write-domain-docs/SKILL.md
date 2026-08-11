---
name: write-domain-docs
description: "기존 write-domain-docs 호출을 위한 deprecated 호환 진입점이다. 사용자가 $write-domain-docs를 명시적으로 호출한 경우에만 도메인 용어·역할·상태·사건·업무 규칙 작업을 domain-modeling으로 연결한다. 일반 도메인 모델링 요청에는 자동 사용하지 않으며 새 구현은 domain-modeling을 사용한다."
---

# Write Domain Docs 호환 진입점

이 이름은 이전 호출과의 호환을 위해 유지한다. 새 요청에는 `domain-modeling`을 사용한다.

이 호환 진입점은 단독 선택 설치를 지원하지 않는다. 독립 스킬로 설치할 때는 `domain-modeling`을 같은 범위에 함께 설치한다. 전체 플러그인 설치에는 두 스킬이 모두 포함된다.

1. 사용자에게 `write-domain-docs`가 deprecated이며 대체 이름을 짧게 알린다.
2. `../domain-modeling/SKILL.md`를 읽고 사용자의 기존 쓰기·검토 권한을 보존해 적용한다.
3. 사용자가 문서 변경을 요청하지 않았다면 proposed diff나 분석만 제공한다.

`domain-modeling`을 사용할 수 없으면 동작을 복제하거나 추측하지 않는다. 누락된 스킬 이름을 밝히고 함께 설치하거나 전체 플러그인을 설치하라고 안내한다.

완료 조건: 기존 호출 의도와 권한을 보존하면서 다음에 사용할 새 이름이 분명하다.
