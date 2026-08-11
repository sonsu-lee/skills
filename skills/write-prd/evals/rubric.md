# Write PRD Compatibility Evaluation Rubric

- `$write-prd` 명시 호출에만 반응한다.
- deprecated 이름임을 짧게 알리고 미해결 제품 탐색은 `product-discovery`, 준비된 PRD 변환은 `to-prd`로 연결한다.
- 두 단계를 한 번에 실행하거나 이전의 전체 워크플로를 복제하지 않는다.
- 사용자의 기존 호출 의도와 쓰기 권한을 보존한다.
- 단독 선택 설치는 지원하지 않으며 `product-discovery`와 `to-prd`를 함께 설치해야 한다고 밝힌다.
- 필요한 companion이 없으면 누락된 이름을 정확히 알리고, 대체 워크플로를 복제하거나 사용할 수 없는 스킬로 라우팅하지 않는다.
