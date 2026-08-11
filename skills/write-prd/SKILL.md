---
name: write-prd
description: "기존 write-prd 호출을 위한 deprecated 호환 진입점이다. 사용자가 $write-prd를 명시적으로 호출한 경우에만 제품 탐색은 product-discovery로, 합의된 컨텍스트의 PRD 변환은 to-prd로 연결한다. 일반 PRD·제품 요구사항 요청에는 자동 사용하지 않으며 새 구현은 product-discovery 또는 to-prd를 사용한다."
---

# Write PRD 호환 진입점

이 이름은 이전 호출과의 호환을 위해 유지한다. 새 요청에는 `product-discovery` 또는 `to-prd`를 사용한다.

## 라우팅

1. 사용자에게 `write-prd`가 deprecated이며 대체 이름을 간단히 알린다.
2. 문제, 사용자, 결과, 범위와 핵심 규칙에 미해결 결정이 있으면 `../product-discovery/SKILL.md`를 읽고 해당 워크플로를 적용한다.
3. 핵심 제품 컨텍스트가 준비됐고 PRD 산출물을 원하면 `../to-prd/SKILL.md`를 읽고 해당 워크플로를 적용한다.
4. 둘 다 필요하면 discovery를 먼저 완료하고 별도 단계에서 PRD 변환을 제안한다. 미래 단계의 지침을 미리 실행하지 않는다.

형제 스킬을 사용할 수 없는 독립 설치에서는 동작을 복제하거나 추측하지 말고 전체 컬렉션 설치가 필요하다고 알린다.

완료 조건: 기존 호출 의도는 보존하면서 실제 책임과 다음에 사용할 새 스킬 이름이 분명하다.
