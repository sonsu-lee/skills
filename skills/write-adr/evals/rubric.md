# Write ADR Compatibility Evaluation Rubric

- `$write-adr` 명시 호출에만 반응한다.
- 미해결 기술 선택은 `architecture-decisions`, 준비된 ADR 기록은 `to-adr`로 연결한다.
- 두 단계를 한 번에 실행하거나 기존 전체 워크플로를 복제하지 않는다.
- 단독 선택 설치는 지원하지 않으며 `architecture-decisions`와 `to-adr`를 함께 설치해야 한다고 밝힌다.
- 필요한 companion이 없으면 누락된 이름을 정확히 알리고, 대체 워크플로를 복제하거나 사용할 수 없는 스킬로 라우팅하지 않는다.
