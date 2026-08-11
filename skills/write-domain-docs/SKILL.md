---
name: write-domain-docs
description: "기존 write-domain-docs 호출을 위한 deprecated 호환 진입점이다. 사용자가 $write-domain-docs를 명시적으로 호출한 경우에만 도메인 용어·역할·상태·사건·업무 규칙 작업을 domain-modeling으로 연결한다. 일반 도메인 모델링 요청에는 자동 사용하지 않으며 새 구현은 domain-modeling을 사용한다."
---

# Write Domain Docs 호환 진입점

이 이름은 이전 호출과의 호환을 위해 유지한다. 새 요청에는 `domain-modeling`을 사용한다.

1. 사용자에게 `write-domain-docs`가 deprecated이며 대체 이름을 짧게 알린다.
2. `../domain-modeling/SKILL.md`를 읽고 사용자의 기존 쓰기·검토 권한을 보존해 적용한다.
3. 사용자가 문서 변경을 요청하지 않았다면 proposed diff나 분석만 제공한다.

형제 스킬을 사용할 수 없는 독립 설치에서는 동작을 복제하지 말고 전체 컬렉션 설치가 필요하다고 알린다.

완료 조건: 기존 호출 의도와 권한을 보존하면서 다음에 사용할 새 이름이 분명하다.
