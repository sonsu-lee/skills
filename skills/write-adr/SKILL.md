---
name: write-adr
description: "기존 write-adr 호출을 위한 deprecated 호환 진입점이다. 사용자가 $write-adr를 명시적으로 호출한 경우에만 아직 결론 없는 기술 선택은 architecture-decisions로, 이미 내려진 결정의 ADR 기록은 to-adr로 연결한다. 일반 ADR·기술 비교 요청에는 자동 사용하지 않으며 새 구현은 architecture-decisions 또는 to-adr를 사용한다."
---

# Write ADR 호환 진입점

이 이름은 이전 호출과의 호환을 위해 유지한다. 새 요청에는 `architecture-decisions` 또는 `to-adr`를 사용한다.

1. 사용자에게 `write-adr`가 deprecated이며 대체 이름을 짧게 알린다.
2. 선택 결과나 실제 rationale이 미해결이면 `../architecture-decisions/SKILL.md`를 읽고 적용한다.
3. 결정, actor와 실제 근거가 준비됐고 ADR 산출물을 원하면 `../to-adr/SKILL.md`를 읽고 적용한다.
4. 두 단계가 필요하면 결정을 먼저 준비하고 별도 단계에서 ADR 변환을 제안한다.

형제 스킬을 사용할 수 없는 독립 설치에서는 동작을 복제하지 말고 전체 컬렉션 설치가 필요하다고 알린다.

완료 조건: 기존 호출 의도는 보존하면서 실제 책임과 다음에 사용할 새 이름이 분명하다.
