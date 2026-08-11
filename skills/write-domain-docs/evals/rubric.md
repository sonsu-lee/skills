# Write Domain Docs Compatibility Evaluation Rubric

- `$write-domain-docs` 명시 호출에만 반응한다.
- deprecated 이름임을 짧게 알리고 `domain-modeling`으로 연결한다.
- 기존 사용자의 쓰기·검토 권한과 요청 범위를 보존한다.
- 단독 선택 설치는 지원하지 않으며 `domain-modeling`을 함께 설치해야 한다고 밝힌다.
- companion이 없으면 누락된 이름을 정확히 알리고, 대체 워크플로를 복제하거나 사용할 수 없는 스킬로 라우팅하지 않는다.
