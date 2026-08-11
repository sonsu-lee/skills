# Write PRD Compatibility Evaluation Rubric

- `$write-prd` 명시 호출에만 반응한다.
- deprecated 이름임을 짧게 알리고 미해결 제품 탐색은 `product-discovery`, 준비된 PRD 변환은 `to-prd`로 연결한다.
- 두 단계를 한 번에 실행하거나 이전의 전체 워크플로를 복제하지 않는다.
- 사용자의 기존 호출 의도와 쓰기 권한을 보존한다.
- 형제 스킬이 설치되지 않았으면 추측으로 대체하지 않고 전체 컬렉션 설치 필요성을 알린다.
